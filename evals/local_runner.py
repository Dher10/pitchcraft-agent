"""Explicit owner-PC synthetic probes only. No import-time key/network access.

No arbitrary model, prompt, endpoint, output path, retry, or paid fallback.
The CLI is gated separately from fixture execution and never publishes.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import time

from agents.model_transport import ConnectionFailed, ConnectionTimeout, post_json, ProviderResponse
from evals.local_store import append, locked, read_ledger
from evals.provider_protocol import canonical, MODELS, parse_probe, probe_request, request_identity

KEY_NAMES = {"gemini": "PITCHCRAFT_GEMINI_API_KEY_LOCAL", "groq": "PITCHCRAFT_GROQ_API_KEY_LOCAL"}
ROOT = Path(__file__).resolve().parents[1]
PROBE_TIMEOUT = 60  # the transport's maximum
# Fixed ledger generations and the providers each may still reserve. Generation 1
# spent one Gemini probe (Oct 28); generation 2 spent one Gemini and one Groq
# probe (Oct 29). Both are closed so no provider is probed more often than
# authorized. Generation 3 is the owner's single further Gemini probe (Oct 29).
# A new generation or provider needs owner approval.
LEDGERS = {"1": (".local/p2-1", frozenset()),
           "2": (".local/p2-1-gen2", frozenset()),
           "3": (".local/p2-1-gen3", frozenset({"gemini"}))}


def verify_checkout(root, commit):
    """Read only the local v2 ref; never invoke git or another subprocess."""
    try:
        gitdir = Path(root) / ".git"
        if not re.fullmatch(r"[0-9a-f]{40}", commit) or (gitdir / "HEAD").read_text().strip() != "ref: refs/heads/v2":
            raise ValueError("request_failed")
        ref = gitdir / "refs/heads/v2"
        if ref.exists():
            actual = ref.read_text().strip()
        else:
            lines = (gitdir / "packed-refs").read_text().splitlines()
            actual = next(line.split(" ")[0] for line in lines if line.endswith(" refs/heads/v2"))
        if actual != commit:
            raise ValueError("request_failed")
    except Exception:
        raise ValueError("request_failed") from None


def _local_key(name):
    # Only this explicit runner reads USER storage, never inherited/prod keys.
    try:
        if os.name != "nt" or name not in KEY_NAMES.values():
            raise ValueError("request_failed")
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ) as handle:
            value, kind = winreg.QueryValueEx(handle, name)
        if kind != winreg.REG_SZ or type(value) is not str or not 1 <= len(value) <= 512 or any(ord(c) < 33 or ord(c) > 126 for c in value):
            raise ValueError("request_failed")
        return value
    except Exception:
        raise ValueError("request_failed") from None


def _no_status(provider, code):
    result = parse_probe(provider, ProviderResponse(503, {}, None))
    result.update(http_status=None, code=code)
    return result


def run_probe(provider, directory, commit, dirty_digest, *, offline=False):
    """One call/provider for this P2.1 ledger, 4096 reserved tokens each.

    Reservation precedes key load/network; failures/crashes never auto-resubmit.
    The 8192-token envelope is a conservative shared-account debit, not proof
    of spare account capacity. Account restrictions/entitlement are owner gates.
    """
    if offline is not True or provider not in MODELS:
        raise ValueError("request_failed")
    identity = request_identity(provider, commit, dirty_digest)
    try:
        with locked(directory) as ledger:
            rows = read_ledger(ledger)
            for row in rows:
                if row["identity"] == identity:
                    matches = [r for r in rows if r["identity"] == identity and r["kind"] == "result"]
                    if matches and matches[0]["result"]["event"] == "accepted":
                        return matches[0]["result"]
                    raise ValueError("request_failed")
            reservations = [r for r in rows if r["kind"] == "reserve"]
            now = time.time()
            if any(r["identity"]["provider"] == provider for r in reservations) or len(reservations) >= 2 or (rows and (rows[-1]["kind"] == "reserve" or now - rows[-1]["at"] < 60)):
                raise ValueError("budget_spent")
            append(ledger, rows, "reserve", identity, now)
            try:
                key = _local_key(KEY_NAMES[provider])
            except Exception:
                result = _no_status(provider, "key_unavailable")
            else:
                try:
                    model, body = probe_request(provider)
                    result = parse_probe(provider, post_json(provider, model, body, api_key=key,
                                                             timeout=PROBE_TIMEOUT, with_metadata=True))
                except ConnectionTimeout:
                    result = _no_status(provider, "connection_failed_timeout")
                except ConnectionFailed:
                    result = _no_status(provider, "connection_failed_other")
                except Exception:
                    result = _no_status(provider, "request_failed")
                finally:
                    del key
            append(ledger, rows, "result", identity, time.time(), result)
            return result
    except Exception as error:
        code = "budget_spent" if type(error) is ValueError and error.args == ("budget_spent",) else "request_failed"
        raise ValueError(code) from None


def main(argv=None):
    parser = argparse.ArgumentParser(description="P2.1 synthetic owner-PC offline access probe")
    parser.add_argument("--owner-pc-offline", action="store_true", required=True)
    parser.add_argument("--provider", choices=tuple(MODELS), required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--dirty-digest", required=True)
    parser.add_argument("--ledger-generation", choices=tuple(LEDGERS), required=True)
    args = parser.parse_args(argv)
    try:
        path, open_providers = LEDGERS[args.ledger_generation]
        if args.provider not in open_providers:
            raise ValueError("budget_spent")
        verify_checkout(ROOT, args.commit)
        result = run_probe(args.provider, ROOT / path, args.commit, args.dirty_digest, offline=args.owner_pc_offline)
    except Exception as error:
        code = "budget_spent" if type(error) is ValueError and error.args == ("budget_spent",) else "request_failed"
        print(canonical({"event": "rejected", "code": code}))
        return 1
    print(canonical(result))
    return 0 if result["event"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
