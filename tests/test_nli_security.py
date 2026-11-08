"""Security controls around the NLI: the provisioner's redirect check, the worker interpreter and environment, and fail-closed edges."""

from __future__ import annotations

import json
import math
from pathlib import Path
import subprocess
import sys
import urllib.request

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import test_llm_report_writer as tlw  # noqa: E402
import test_nli_admission as tna  # noqa: E402
from agents import nli_admission as na  # noqa: E402
from agents import nli_cache as nc  # noqa: E402
from agents import writer_checks as wc  # noqa: E402
from evals import provision_nli_cache as pv  # noqa: E402

parts = tlw.parts


# --- the provisioner's redirect handler --------------------------------------------------------------------------------------------


@pytest.mark.parametrize("target", ["https://evil.com/x", "http://cdn.hf.co/x", "https://huggingface.co@evil.com/x", "https://huggingface.co.evil.com/x", "ftp://huggingface.co/x"])
def test_a_redirect_to_another_host_or_a_plain_http_url_is_refused(target):
    handler = pv._HttpsHostsOnly()
    request = urllib.request.Request("https://huggingface.co/a")

    with pytest.raises(pv.Refused):
        handler.redirect_request(request, None, 302, "Found", {}, target)


def test_a_redirect_to_a_hugging_face_content_host_is_followed():
    handler = pv._HttpsHostsOnly()
    request = urllib.request.Request("https://huggingface.co/a")

    followed = handler.redirect_request(request, None, 302, "Found", {}, "https://cas-bridge.xethub.hf.co/x/y")

    assert followed is not None and followed.full_url == "https://cas-bridge.xethub.hf.co/x/y"


def test_a_stale_part_file_from_a_killed_run_is_removed_not_treated_as_an_unlisted_file(tmp_path):
    (tmp_path / "config.json.part").write_bytes(b"half")

    class Boom:
        def open(self, request, timeout=None):
            raise pv.Refused("stop here")

    with pytest.raises(pv.Refused):
        pv.provision(tmp_path, Boom())

    assert not list(tmp_path.glob("*.part"))


# --- the worker interpreter and environment ------------------------------------------------------------------------------------------


class FakeRun:
    def __init__(self, stdout="[0.5]", code=0):
        self.stdout, self.code, self.calls = stdout, code, []

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, self.code, stdout=self.stdout, stderr="")


@pytest.fixture
def worker(monkeypatch):
    monkeypatch.setattr(nc, "verify_cache", lambda directory: Path(directory))
    fake = FakeRun()
    monkeypatch.setattr(nc.subprocess, "run", fake)
    return fake


def test_the_interpreter_is_only_the_explicit_argument_and_the_child_gets_no_key_variables(worker, tmp_path, monkeypatch):
    python = tmp_path / "python.exe"
    python.write_bytes(b"")
    for name in ("PITCHCRAFT_GEMINI_API_KEY_LOCAL", "PITCHCRAFT_GROQ_API_KEY_LOCAL", "GEMINI_API_KEY", "GROQ_API_KEY", "PYTHONPATH"):
        monkeypatch.setenv(name, "secret-value")
    monkeypatch.setenv("PITCHCRAFT_NLI_PYTHON", "elsewhere.exe")

    assert nc.scores(tmp_path, [("p", "s")], python=python) == [0.5]

    argv, kwargs = worker.calls[0]
    assert argv[0] == str(python) and argv[1] == "-I" and argv[3] == "--worker"
    assert set(kwargs["env"]) <= {"SystemRoot", "WINDIR", "PATH", "TEMP", "TMP", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY", "TOKENIZERS_PARALLELISM"}
    assert "secret-value" not in json.dumps(kwargs["env"]) and "secret-value" not in kwargs["input"]


def test_without_an_explicit_interpreter_the_current_one_is_used(worker, tmp_path):
    nc.scores(tmp_path, [("p", "s")])

    assert worker.calls[0][0][0] == sys.executable


@pytest.mark.parametrize("name", ["python.exe", "notpython.exe", "pythonw.exe"])
def test_only_a_file_named_python_is_accepted(worker, tmp_path, name):
    path = tmp_path / name
    path.write_bytes(b"")

    result = nc.scores(tmp_path, [("p", "s")], python=path)

    assert (result == [0.5]) is (name == "python.exe")


def test_a_missing_interpreter_and_a_symlink_to_one_give_none(worker, tmp_path):
    assert nc.scores(tmp_path, [("p", "s")], python=tmp_path / "python.exe") is None
    real = tmp_path / "real.exe"
    real.write_bytes(b"")
    link = tmp_path / "python.exe"
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("symlinks are not available here")
    assert nc.scores(tmp_path, [("p", "s")], python=link) is None


@pytest.mark.parametrize("stdout,code", [("[0.5]", 1), ("[1.5]", 0), ("[-0.1]", 0), ("[NaN]", 0), ("[0.5, 0.5]", 0), ("x" * 5000, 0), ("{}", 0), ("", 0)])
def test_a_failed_oversize_malformed_or_out_of_range_worker_answer_gives_none(monkeypatch, tmp_path, stdout, code):
    monkeypatch.setattr(nc, "verify_cache", lambda directory: Path(directory))
    monkeypatch.setattr(nc.subprocess, "run", FakeRun(stdout, code))

    assert nc.scores(tmp_path, [("p", "s")]) is None


def test_scores_allow_a_long_timeout_but_entails_keeps_its_120_second_bound(worker, tmp_path):
    cal = {"threshold": 0.4, "identity": nc.identity()}

    assert nc.scores(tmp_path, [("p", "s")], timeout=300) == [0.5]
    assert nc.scores(tmp_path, [("p", "s")], timeout=601) is None
    assert nc.entails(tmp_path, [("p", "s")], calibration=cal, timeout=120) is True
    assert nc.entails(tmp_path, [("p", "s")], calibration=cal, timeout=121) is False


# --- fail-closed edges of the adapter --------------------------------------------------------------------------------------------------


def test_a_non_finite_score_is_unavailable_not_a_pass():
    doc, candidate = tna.control()

    codes, _ = na.verdict(na.score_candidate(candidate, doc, cache="c", scorer=tna.Scorer(math.nan)), tna.good_calibration())

    assert codes == ["NLI.unavailable"]


def test_an_exception_in_the_scorer_becomes_unavailable_and_never_propagates():
    doc, candidate = tna.control()

    def boom(*a, **k):
        raise RuntimeError("worker exploded with a secret sk-123")

    codes, detail = na.make_gate(cache="c", calibration=tna.good_calibration(), scorer=boom)(candidate, doc)

    assert codes == ["NLI.unavailable"] and detail == []


def test_a_gate_that_raises_inside_the_cascade_falls_back_to_rules_in_one_call(parts, monkeypatch):
    monkeypatch.setattr(wc, "rules_length", lambda report: wc.report_length(parts[3]))
    fake = tlw.Fake(tlw.answer(parts[3]), tlw.answer(parts[3]))

    def explode(candidate, doc):
        raise RuntimeError("secret sk-123")

    result = tna.go(parts, fake, explode)

    assert result.path == "rules" and result.failures == ["NLI.unavailable"] and len(fake.calls) == 1 and "sk-123" not in json.dumps(result.attempts)


def test_only_watch_lines_are_skipped_not_any_sentence_that_starts_with_watch():
    doc, candidate = tna.control()
    candidate["headline"]["text"] = "Watch how Kyle Freeland and José Soriano start this game."

    entries = na.plan_pairs(candidate, doc)

    assert any(e["text"].startswith("Watch how Kyle Freeland and") for e in entries)  # the headline is a factual sentence and is checked
