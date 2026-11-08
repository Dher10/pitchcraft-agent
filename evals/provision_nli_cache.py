"""Provision the pinned NLI model cache (docs/SECURITY.md, "Local model and supply chain").

Downloads exactly the files listed in agents/nli_manifest.json from the pinned immutable revision, over HTTPS only, from
Hugging Face hosts only, and keeps a file only if its size and SHA-256 equal the manifest. Anything else is deleted. No pickle,
no remote code, no file outside the manifest. The result is then checked by `agents.nli_cache.verify_cache`.

Run explicitly (it makes network requests): python -m evals.provision_nli_cache --dir .local/nli-cache
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
import urllib.error
import urllib.request

from agents import nli_cache

HOST_SUFFIXES = ("huggingface.co", ".hf.co")  # the pinned repository and its content delivery hosts
CHUNK = 1_048_576


class Refused(ValueError):
    """A download did not match the manifest, or went somewhere it must not."""


class _HttpsHostsOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _check_url(url: str) -> None:
    from urllib.parse import urlsplit

    parts = urlsplit(url)
    host = parts.hostname or ""
    if parts.scheme != "https" or not any(host == s.lstrip(".") or host.endswith(s if s.startswith(".") else "." + s) for s in HOST_SUFFIXES):
        raise Refused("url not allowed")


def file_url(name: str) -> str:
    manifest = nli_cache.MANIFEST
    return f"https://huggingface.co/{manifest['repository']}/resolve/{manifest['revision']}/{name}"


def fetch_one(name: str, expected: dict, directory: Path, opener=None) -> None:
    """Download `name` to `directory`; keep it only if size and SHA-256 match the manifest."""

    if name != Path(name).name or name.endswith((".bin", ".py", ".pkl")):
        raise Refused("file name not allowed")
    url = file_url(name)
    _check_url(url)
    opener = opener or urllib.request.build_opener(_HttpsHostsOnly())
    part = directory / (name + ".part")
    digest, size = hashlib.sha256(), 0
    try:
        with opener.open(urllib.request.Request(url, headers={"User-Agent": "pitchcraft-agent/1.0"}), timeout=120) as response, part.open("wb") as handle:
            for chunk in iter(lambda: response.read(CHUNK), b""):
                size += len(chunk)
                if size > expected["size"]:
                    raise Refused("larger than the manifest")
                digest.update(chunk)
                handle.write(chunk)
        if size != expected["size"] or digest.hexdigest() != expected["sha256"]:
            raise Refused("size or SHA-256 differs from the manifest")
        part.replace(directory / name)
    except (urllib.error.URLError, OSError) as error:
        raise Refused("download failed") from error
    finally:
        part.unlink(missing_ok=True)


def provision(directory, opener=None) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    files = nli_cache.MANIFEST["files"]
    for stale in directory.glob("*.part"):
        stale.unlink()  # left by a killed run; never a kept file
    for existing in directory.iterdir():
        if existing.name not in files:
            raise Refused("unlisted file in the cache directory")
    for name, expected in files.items():
        target = directory / name
        if target.exists():
            try:
                nli_cache_file_ok(target, expected)
                continue
            except Refused:
                target.unlink()
        fetch_one(name, expected, directory, opener)
    return nli_cache.verify_cache(directory)


def nli_cache_file_ok(path: Path, expected: dict) -> None:
    if path.stat().st_size != expected["size"]:
        raise Refused("size differs")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected["sha256"]:
        raise Refused("SHA-256 differs")


def main(argv=None) -> int:  # pragma: no cover - the network entry point
    parser = argparse.ArgumentParser(description="provision the pinned NLI model cache")
    parser.add_argument("--dir", required=True)
    args = parser.parse_args(argv)
    try:
        path = provision(args.dir)
    except Exception as error:
        print(f"refused: {type(error).__name__}")
        return 1
    print(f"cache verified: {path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
