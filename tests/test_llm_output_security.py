"""P2-SEC lexical boundary; these tests do not claim semantic safety."""
import importlib

import pytest


BAD = (
    "<b>Fastball</b>", "&lt;script&gt;alert(1)&lt;/script&gt;",
    "%3Cscript%3Ealert(1)%3C/script%3E", r"\u003cscript\u003e",
    "**Fastball**", "[read](https://bad.invalid)", "# Headline", "`code`",
    "Visit https://bad.invalid", "Visit example.com", "Mail a@b.test",
    "Fast\u200bball", "Fast\u202eball", "Fast\x00ball", "Fast\nball", "Fast\u00a0ball",
    "He is an IDIOT.", "He is a l0ser.", "He is injured.", "His wife says so.",
    "Bet on him.", "The odds favor him.", "Try b.e.t.t.i.n.g.",
    "Try b\u0435tting.", "He will win.", "x" * 301,
    "%62et on him.", "&#98;et on him.", "%00ball",
    "Fast\u034fball", "Fast\u3164ball", "Fast\ufe0fball",
    "\uff1cscript\uff1e", "- bullet", "1. bullet", "~~Fastball~~", "Visit ftp://bad.invalid", "Visit bad.invalid",
)


@pytest.mark.parametrize("text", BAD)
def test_rejects_output_without_silently_sanitizing(text):
    policy = importlib.import_module("agents.security_policy")
    with pytest.raises(policy.ModelRejected, match="^malformed_response$"):
        policy.validate_sentence(text)


@pytest.mark.parametrize("text", (
    "Jos\u00e9 Berr\u00edos has 0 home runs allowed in this sample.",
    "O'Neill throws a four-seam fastball.",
    "Pitch data is not available for this starter.", "x" * 300,
))
def test_control_plain_text_accents_zero_punctuation_and_exact_cap(text):
    policy = importlib.import_module("agents.security_policy")
    assert policy.validate_sentence(text) == text


@pytest.mark.parametrize("value", (None, 0, True, [], ""))
def test_non_string_or_empty_output_fails_closed(value):
    policy = importlib.import_module("agents.security_policy")
    with pytest.raises(policy.ModelRejected):
        policy.validate_sentence(value)
