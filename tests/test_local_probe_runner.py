"""End-to-end runner using synthetic transport and key sentinels only."""
import copy
import importlib
import json
from pathlib import Path
import sys
import types

import pytest

from agents.model_transport import ProviderResponse

FIXTURES = json.loads((Path(__file__).parent / "fixtures/provider_probes.json").read_text())
COMMIT, DIRTY = "a" * 40, "b" * 64


def runner():
    assert importlib.util.find_spec("evals.local_runner") is not None, "P2.1 explicit runner is missing"
    return importlib.import_module("evals.local_runner")


def wiring(monkeypatch, provider="groq", status=200):
    module = runner()
    calls, keys = [], []
    def key_loader(name):
        keys.append(name)
        return "SECRET-SENTINEL"
    def post(provider, model, body, **kwargs):
        calls.append((provider, model, body))
        assert kwargs["api_key"] == "SECRET-SENTINEL"
        return ProviderResponse(status, {"x-ratelimit-remaining-tokens": 7900}, copy.deepcopy(FIXTURES[provider]) if status == 200 else None)
    monkeypatch.setattr(module, "_local_key", key_loader)
    monkeypatch.setattr(module, "post_json", post)
    monkeypatch.setattr(module.time, "time", lambda: 2000000000)
    return module, calls, keys


def run(module, directory, provider="groq", **kwargs):
    return module.run_probe(provider, directory, COMMIT, DIRTY, offline=True, **kwargs)


def test_explicit_opt_in_required_before_storage_or_credentials(tmp_path, monkeypatch):
    module, calls, keys = wiring(monkeypatch)
    with pytest.raises(ValueError, match="request_failed"):
        module.run_probe("groq", tmp_path / "new", COMMIT, DIRTY)
    assert calls == keys == [] and not (tmp_path / "new").exists()


@pytest.mark.parametrize("provider,name", (("gemini", "PITCHCRAFT_GEMINI_API_KEY_LOCAL"), ("groq", "PITCHCRAFT_GROQ_API_KEY_LOCAL")))
def test_exact_local_route_safe_durable_result_and_cache_hit(provider, name, tmp_path, monkeypatch, capsys):
    module, calls, keys = wiring(monkeypatch)
    directory = tmp_path / "private"
    result = run(module, directory, provider)
    assert result["event"] == "accepted"
    assert keys == [name] and len(calls) == 1
    assert run(module, directory, provider) == result
    assert keys == [name] and len(calls) == 1
    data = "".join(p.read_text() for p in directory.iterdir() if p.is_file())
    assert "SECRET-SENTINEL" not in data and "PRIVATE-REASONING" not in data
    assert 'Return only' not in data and 'authorization' not in data
    assert len((directory / "ledger.jsonl").read_text().splitlines()) == 2
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("status", (401, 403, 429, 500))
def test_failure_never_retries_or_counts_as_reusable_success(status, tmp_path, monkeypatch):
    module, calls, keys = wiring(monkeypatch, status=status)
    result = run(module, tmp_path / "private")
    assert result["event"] == "rejected"
    with pytest.raises(ValueError, match="request_failed"):
        run(module, tmp_path / "private")
    assert len(calls) == 1 and len(keys) == 1


def test_crash_reservation_blocks_duplicate_even_without_response(tmp_path, monkeypatch):
    module, calls, keys = wiring(monkeypatch)
    def crash(*a, **k):
        raise KeyboardInterrupt()
    monkeypatch.setattr(module, "post_json", crash)
    directory = tmp_path / "private"
    with pytest.raises(KeyboardInterrupt):
        run(module, directory)
    with pytest.raises(ValueError, match="request_failed"):
        run(module, directory)
    assert len(keys) == 1
    assert len((directory / "ledger.jsonl").read_text().splitlines()) == 1


def test_budget_is_shared_between_identities_and_requires_one_minute_pacing(tmp_path, monkeypatch):
    module, calls, keys = wiring(monkeypatch)
    directory = tmp_path / "private"
    run(module, directory)
    with pytest.raises(ValueError, match="budget_spent"):
        run(module, directory, "gemini")
    assert len(calls) == 1
    monkeypatch.setattr(module.time, "time", lambda: 2000000060)
    assert run(module, directory, "gemini")["event"] == "accepted"
    with pytest.raises(ValueError, match="budget_spent"):
        module.run_probe("groq", directory, "c" * 40, DIRTY, offline=True)
    assert len(calls) == len(keys) == 2


@pytest.mark.parametrize("damage", ("partial", "changed", "extra", "lock"))
def test_tampered_partial_or_locked_ledger_fails_before_reading_key(damage, tmp_path, monkeypatch):
    module, calls, keys = wiring(monkeypatch)
    directory = tmp_path / "private"
    run(module, directory)
    ledger = directory / "ledger.jsonl"
    if damage == "partial":
        ledger.write_text(ledger.read_text() + '{"incomplete":')
    elif damage == "changed":
        ledger.write_text(ledger.read_text().replace('"reserved_tokens":4096', '"reserved_tokens":0'))
    elif damage == "extra":
        (directory / "extra.json").write_text('"SECRET-SENTINEL"')
    else:
        (directory / "runner.lock").write_text("")
    with pytest.raises(ValueError, match="request_failed"):
        run(module, directory)
    assert len(keys) == len(calls) == 1


def test_transport_exception_is_closed_and_conservatively_debited(tmp_path, monkeypatch):
    module, calls, keys = wiring(monkeypatch)
    def fail(*a, **k):
        raise RuntimeError("SECRET-SENTINEL")
    monkeypatch.setattr(module, "post_json", fail)
    result = run(module, tmp_path / "private")
    assert result["code"] == "request_failed" and result["total_tokens"] is None
    assert "SENTINEL" not in json.dumps(result)
    with pytest.raises(ValueError, match="request_failed"):
        run(module, tmp_path / "private")


def test_rejected_or_missing_key_is_key_unavailable_and_sends_nothing(tmp_path, monkeypatch):
    module, calls, keys = wiring(monkeypatch)
    def missing(name):
        keys.append(name)
        raise ValueError("request_failed")
    monkeypatch.setattr(module, "_local_key", missing)
    result = run(module, tmp_path / "private")
    assert result["event"] == "rejected" and result["code"] == "key_unavailable"
    assert result["http_status"] is None and calls == []
    with pytest.raises(ValueError, match="request_failed"):
        run(module, tmp_path / "private")
    assert len(keys) == 1


@pytest.mark.parametrize("error,code", (("ConnectionTimeout", "connection_failed_timeout"),
                                        ("ConnectionFailed", "connection_failed_other")))
def test_transport_failure_before_status_keeps_its_closed_sub_code(error, code, tmp_path, monkeypatch):
    import agents.model_transport as transport
    module, calls, keys = wiring(monkeypatch)
    def fail(*a, **k):
        raise getattr(transport, error)()
    monkeypatch.setattr(module, "post_json", fail)
    result = run(module, tmp_path / "private")
    assert result["code"] == code and result["http_status"] is None
    assert len(keys) == 1


def test_probe_uses_the_d49_writer_timeout(tmp_path, monkeypatch):
    module, calls, keys = wiring(monkeypatch)
    timeouts = []
    original = module.post_json
    def post(provider, model, body, **kwargs):
        timeouts.append(kwargs["timeout"])
        return original(provider, model, body, **kwargs)
    monkeypatch.setattr(module, "post_json", post)
    run(module, tmp_path / "private")
    assert timeouts == [120]


def test_pre_existing_connection_failed_rows_stay_readable():
    store = importlib.import_module("evals.local_store")
    result = runner().parse_probe("groq", ProviderResponse(503, {}, None))
    result.update(code="connection_failed", http_status=None)
    store.validate_result(result)


@pytest.mark.parametrize("code", ("key_unavailable", "connection_failed", "connection_failed_timeout", "connection_failed_other"))
def test_no_status_codes_cannot_carry_an_http_status(code):
    store = importlib.import_module("evals.local_store")
    result = runner().parse_probe("groq", ProviderResponse(503, {}, None))
    result["code"] = code
    with pytest.raises(ValueError):
        store.validate_result(result)
    result["http_status"] = None
    store.validate_result(result)


def test_ledger_generations_are_fixed_and_closed_generations_take_no_probe(monkeypatch, capsys):
    module = runner()
    # Generation 1 is closed: it spent its Gemini probe and must take no Groq probe,
    # so across generations each provider still gets the owner-authorized count.
    # Generations 1 and 2 spent their authorized probes (Gemini twice, Groq once)
    # and stay closed; generation 3 spent its Gemini probe; generation 4 (a Groq re-probe) never ran
    # and is closed; generation 5 spent its one Gemini probe (accepted); generation 6 is the owner's one
    # Groq probe with the user-agent fix.
    assert module.LEDGERS == {"1": (".local/p2-1", frozenset()),
                              "2": (".local/p2-1-gen2", frozenset()),
                              "3": (".local/p2-1-gen3", frozenset()),
                              "4": (".local/p2-1-gen4", frozenset()),
                              "5": (".local/p2-1-gen5", frozenset()),
                              "6": (".local/p2-1-gen6", frozenset({"groq"}))}
    seen = []
    monkeypatch.setattr(module, "verify_checkout", lambda *a: None)
    monkeypatch.setattr(module, "run_probe", lambda provider, directory, *a, **k: seen.append((provider, directory)) or {"event": "accepted"})
    base = ["--owner-pc-offline", "--commit", COMMIT, "--dirty-digest", DIRTY]
    refused = [("1", "gemini"), ("1", "groq"), ("2", "gemini"), ("2", "groq"), ("3", "gemini"), ("3", "groq"),
               ("4", "gemini"), ("4", "groq"), ("5", "gemini"), ("5", "groq"),
               ("6", "gemini")]
    for generation, provider in refused:
        assert module.main(base + ["--provider", provider, "--ledger-generation", generation]) == 1
        assert '"budget_spent"' in capsys.readouterr().out
    assert seen == []
    module.main(base + ["--provider", "groq", "--ledger-generation", "6"])
    assert seen == [("groq", module.ROOT / ".local/p2-1-gen6")]
    for extra in ([], ["--ledger-generation", "../elsewhere"]):
        with pytest.raises(SystemExit):
            module.main(base + ["--provider", "groq"] + extra)


def test_registry_loader_accepts_new_key_shape(monkeypatch):
    module = runner()
    value = "AQ.Ab8RN6" + "x" * 44
    class Handle:
        def __enter__(self): return self
        def __exit__(self, *a): pass
    registry = types.SimpleNamespace(HKEY_CURRENT_USER=1, KEY_READ=2, REG_SZ=3)
    registry.OpenKey = lambda *a: Handle()
    registry.QueryValueEx = lambda handle, name: (value, registry.REG_SZ)
    monkeypatch.setitem(sys.modules, "winreg", registry)
    monkeypatch.setattr(module.os, "name", "nt")
    assert module._local_key("PITCHCRAFT_GEMINI_API_KEY_LOCAL") == value


def test_import_and_key_loader_never_fall_back_to_process_or_production_env(monkeypatch):
    module = runner()
    for name in ("GEMINI_API_KEY", "GROQ_API_KEY", "PITCHCRAFT_GROQ_API_KEY_LOCAL"):
        monkeypatch.setenv(name, "SECRET-SENTINEL")
    with pytest.raises(ValueError, match="request_failed"):
        module._local_key("GROQ_API_KEY")


@pytest.mark.parametrize("damage", ("acl", "invalid-source", "invalid-provider"))
def test_preflight_failures_do_not_load_keys(damage, tmp_path, monkeypatch):
    module, calls, keys = wiring(monkeypatch)
    if damage == "acl":
        store = importlib.import_module("evals.local_store")
        def fail(*a):
            raise OSError("SECRET-SENTINEL")
        monkeypatch.setattr(store, "protect", fail)
        callback = lambda: run(module, tmp_path / "private")
    elif damage == "invalid-source":
        callback = lambda: module.run_probe("groq", tmp_path, "invalid", DIRTY, offline=True)
    else:
        callback = lambda: run(module, tmp_path, "mistral")
    with pytest.raises(ValueError):
        callback()
    assert keys == calls == []


def test_registry_loader_uses_only_exact_user_entry_and_never_prints(monkeypatch, capsys):
    module = runner()
    queries = []
    class Handle:
        def __enter__(self): return self
        def __exit__(self, *a): pass
    registry = types.SimpleNamespace(HKEY_CURRENT_USER=1, KEY_READ=2, REG_SZ=3)
    def open_key(hive, path, reserved, access):
        queries.append((hive, path, reserved, access))
        return Handle()
    def query(handle, name):
        queries.append(name)
        return "TEST-ONLY-LOCAL-SENTINEL", registry.REG_SZ
    registry.OpenKey, registry.QueryValueEx = open_key, query
    monkeypatch.setitem(sys.modules, "winreg", registry)
    monkeypatch.setattr(module.os, "name", "nt")
    assert module._local_key("PITCHCRAFT_GROQ_API_KEY_LOCAL") == "TEST-ONLY-LOCAL-SENTINEL"
    assert queries == [(1, "Environment", 0, 2), "PITCHCRAFT_GROQ_API_KEY_LOCAL"]
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("branch,actual,given", (("v2", COMMIT, COMMIT), ("v2", "c" * 40, COMMIT), ("other", COMMIT, COMMIT)))
def test_cli_source_pin_checks_real_checkout_before_credential_access(branch, actual, given, tmp_path):
    module = runner()
    gitdir = tmp_path / ".git"
    (gitdir / "refs/heads").mkdir(parents=True)
    (gitdir / "HEAD").write_text(f"ref: refs/heads/{branch}\n")
    (gitdir / f"refs/heads/{branch}").write_text(actual + "\n")
    if branch == "v2" and actual == given:
        module.verify_checkout(tmp_path, given)
    else:
        with pytest.raises(ValueError, match="request_failed"):
            module.verify_checkout(tmp_path, given)
