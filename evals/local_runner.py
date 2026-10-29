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

from agents.model_transport import post_json, ProviderResponse
from evals.local_store import append, locked, read_ledger
from evals.provider_protocol import canonical, MODELS, parse_probe, probe_request, request_identity

KEY_NAMES = {"gemini": "PITCHCRAFT_GEMINI_API_KEY_LOCAL", "groq": "PITCHCRAFT_GROQ_API_KEY_LOCAL"}
ROOT = Path(__file__).resolve().parents[1]


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
                model, body = probe_request(provider)
                try:
                    response = post_json(provider, model, body, api_key=key, timeout=30, with_metadata=True)
                finally:
                    del key
                result = parse_probe(provider, response)
            except Exception:
                result = parse_probe(provider, ProviderResponse(503, {}, None))
                result["http_status"] = None
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
    args = parser.parse_args(argv)
    try:
        verify_checkout(ROOT, args.commit)
        result = run_probe(args.provider, ROOT / ".local/p2-1", args.commit, args.dirty_digest, offline=args.owner_pc_offline)
    except Exception as error:
        code = "budget_spent" if type(error) is ValueError and error.args == ("budget_spent",) else "request_failed"
        print(canonical({"event": "rejected", "code": code}))
        return 1
    print(canonical(result))
    return 0 if result["event"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
