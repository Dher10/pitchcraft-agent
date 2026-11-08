"""The NLI cache provisioner keeps a file only when it equals the manifest; it never touches the network in tests."""

from __future__ import annotations

import hashlib
import io

import pytest

from agents import nli_cache
from evals import provision_nli_cache as pv


class Opener:
    def __init__(self, bodies):
        self.bodies, self.requested = bodies, []

    def open(self, request, timeout=None):
        self.requested.append(request.full_url)
        name = request.full_url.rsplit("/", 1)[1]
        return io.BytesIO(self.bodies[name])


def expected_for(body):
    return {"size": len(body), "sha256": hashlib.sha256(body).hexdigest()}


def test_urls_are_the_pinned_revision_over_https_on_hugging_face_hosts_only():
    url = pv.file_url("config.json")

    assert url == f"https://huggingface.co/{nli_cache.MANIFEST['repository']}/resolve/{nli_cache.MANIFEST['revision']}/config.json"
    pv._check_url(url)
    pv._check_url("https://cas-bridge.xethub.hf.co/x/y")
    for bad in ("http://huggingface.co/x", "https://evilhuggingface.co/x", "https://huggingface.co.evil.com/x", "https://example.com/x", "ftp://huggingface.co/x"):
        with pytest.raises(pv.Refused):
            pv._check_url(bad)


def test_a_file_that_equals_the_manifest_is_kept(tmp_path):
    body = b"hello"
    opener = Opener({"config.json": body})

    pv.fetch_one("config.json", expected_for(body), tmp_path, opener)

    assert (tmp_path / "config.json").read_bytes() == body and not list(tmp_path.glob("*.part"))


@pytest.mark.parametrize("body", [b"hellO", b"hello world", b"hell"])
def test_a_file_with_another_hash_or_size_is_deleted_and_refused(tmp_path, body):
    opener = Opener({"config.json": body})

    with pytest.raises(pv.Refused):
        pv.fetch_one("config.json", expected_for(b"hello"), tmp_path, opener)

    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("name", ["pytorch_model.bin", "modeling.py", "weights.pkl", "../x.json", "a/b.json"])
def test_pickle_code_and_path_names_are_refused_before_any_request(tmp_path, name):
    opener = Opener({})

    with pytest.raises(pv.Refused):
        pv.fetch_one(name, {"size": 1, "sha256": "0" * 64}, tmp_path, opener)

    assert opener.requested == []


def test_an_unlisted_file_in_the_cache_directory_is_refused(tmp_path):
    (tmp_path / "extra.bin").write_bytes(b"x")

    with pytest.raises(pv.Refused):
        pv.provision(tmp_path, Opener({}))
