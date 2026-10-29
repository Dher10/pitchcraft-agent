# Security design and threat model

Design approved by owner 2026-10-28 with D47 adjustments (Gemini -> rules;
no Mistral). This remains a design, not evidence its runtime controls exist.
P2-SEC implements the internal request/output/cache/log boundaries and site
headers; it does not admit generated prose into schema 0.9.0. The owner also
approved nonce-based CSP, dynamic /quality and style-src-attr on Oct 28,
and the separate local-key route. STOP before P2.1 for owner key setup.
Production environment restrictions are verified read-only; secret storage
remains owner-attested where metadata access returned 403. Rules stay live.

## Assets and actors

Assets: trustworthy reports and provenance/claims; the public site's
integrity; LLM API keys and the separate daily deploy key; the protected
branches/workflows; sealed test labels/results; prompt/evaluator/model
versions; cached responses/model artifacts; safe append-only audit records;
the renewable $0 request allowance and available CPU time.

Actors include the owner, one implementing agent, read-only reviewer,
GitHub/Vercel operators and model/data providers. Treat source text, cached
files, generated reports and judge responses as untrusted even when a
provider/account is legitimate. A compromised contributor, provider or
dependency is in scope; provider internals are not under our control.

## Trust boundaries and data flow

1. Public MLB/Savant responses -> whole-response schemas/cache validation ->
   typed packet. Closed sets/strict patterns, numeric bounds and field length
   limits apply before any prompt. No employer/private data is allowed.
2. Validated packet/catalog facts -> quoted and labelled data inside writer
   and judge requests. Versioned instructions are separate. External text
   never becomes an instruction, tool call, role, URL destination or code.
3. v2/PR/preview/frontend execution -> **no production LLM keys**.
   `pitchcraft-llm-main` contains production Gemini/Groq secrets per owner;
   its main-only deployment policy and absence of reviewers are verified.
   It is separate from `data-publish`. Rehearsals/tests use recorded fixtures.
   No repository secrets, .env, NEXT_PUBLIC or browser credentials. The approved
   owner-PC exception uses separately revocable local keys read explicitly
   from Windows USER variables only by an approved offline runner; no local
   credentialed run until owner key setup and the P2.1 stop are cleared.
4. Provider output -> bounded parse/schema -> plain-text and code checks ->
   sentence/evidence integrity -> local NLI -> retry/rules fallback -> final
   independent publication validation. No writer/judge tools or retrieval.
5. Approved public payload -> React text rendering -> browser. No HTML
   insertion. Headers add defense in depth; output checks do not replace
   React escaping or contract validation.
6. Published report -> one remote monitoring judge call -> safe audit record.
   Judge verdicts cannot gate/undo publication (D17). Offline evaluation uses
   the same frozen judge, with test results sealed from tuning.

Production credentialed jobs, if later approved, use main and its restricted
environment, never a user-supplied ref, pull_request_target or downloaded
untrusted executable with credentials. The owner prefers frequent offline
experiments on the PC without merging each change: `plans/P2.md` records the approved route using
SEPARATE local Gemini/Groq keys, fixed hosts, explicit offline opt-in,
redaction, bounded quotas, restricted caches and no inherited build/test
credentials. The route is approved.
Owner confirmed creation/storage of both separate local keys Oct 28 and
accepted the owner-reported restriction settings the same day; RUNBOOK
records their non-secret inventory. Probes follow the runner commit's green CI.
P2.1's new runner is synthetic/offline only and not wired to publication;
its fixture results never establish account access or full queue capacity.
Windows USER storage persists in the registry, is not encrypted, is readable
by same-user/admin processes and may be inherited; separate keys reduce
revocation impact but not those risks or shared-quota usage.

No workflow patch is approved. Before any later patch, account for daily.yml's
v2 trigger and the three spent D42 rehearsals; no accidental fourth run.
Existing server protections/deploy-key bypass remain unchanged.

## STRIDE threats

| Class | Threat / boundary | Planned control | Residual risk |
|---|---|---|---|
| Spoofing | Source/cache text impersonates system instructions; forged writer/judge identity | Whole-input schemas, prompt field allowlist, explicit data delimiters, no tools; record exact model/route/fingerprint and request digests | A schema-valid name can still resemble instructions; delimiters are not a proof that a model ignores it |
| Tampering | Wrong-owner evidence, poisoned response cache, edited weights or public report | Independent sentence/evidence checks and final gate; ownership/scope checks; complete cache identity; pinned HF revision and SHA-256 manifest; safetensors only | A provider can return plausible wrong content; trusted upstream data can itself be wrong |
| Repudiation | Lost failures or model/version switches make results unauditable | Append-only attempt records, closed safe reasons, input/prompt/guide/model/evaluator digests and usage; frozen-judge rule | Provider fingerprints or historical availability may be incomplete; missing identity/evidence blocks official comparisons |
| Information disclosure | Keys, raw internal prompts or provider exception text reach logs, artifacts or frontend | Main-only environment; minimal API scopes; no secret environment dumps; safe error mapping/redaction; sentinel tests; restricted raw response/label storage | Account/runner/provider compromise remains possible; masking alone is insufficient |
| Denial of service | Oversized text, tokenizer/NLI resource exhaustion, quota loops or outage | Fixed input/sentence/token limits; no silent truncation; CPU/time bounds; cached pinned model; paced/resumable calls and total two writer attempts, then rules | CPU performance and free quotas can still delay work; availability falls back to rules, not a validation pass |
| Elevation of privilege | v2/PR code obtains main keys; generated instructions trigger tools; malicious model loader code | Main branch restrictions plus job conditions; no tools; closed endpoint/provider selection; safetensors, remote code disabled, pinned runtime dependencies; least-privilege workflow | An authorized main workflow/admin can still misuse access; server-side restrictions and owner review remain essential |

## Prompt and output controls

P2-SEC must inventory every prompt-reaching free-text field in the approved
schema: player/team/venue names where needed, abbreviations, series text,
catalog-rendered findings and candidate report sentences. Pitch families,
hands, labels and scopes use closed sets; series text keeps its established
strict patterns. Names need anchored patterns and explicit length limits,
not a generic "is string" test. Exclude bios, recent-form narratives, raw
source errors and any field not required by the packet contract.

The field inventory drives red-team parametrization and is checked for
completeness/nonemptiness, so adding a new text field cannot silently evade
injection coverage. Include payloads that pass the lexical pattern (e.g.
instruction-like words in a name) as well as malformed characters. Rejection
or neutralization must be shown at the real prompt/output boundary, without
asserting that every possible future model will ignore all instructions.

Generated sentences remain data, including when the offline judge sees a
rejected first attempt. They never set judge roles/rubrics. Writer and judge
requests expose no tools, browsing, shell, retrieval or arbitrary callbacks.
Provider hosts and routes are closed/allowlisted; env-based selection is
not permission to send credentials to an arbitrary URL.

Fail closed before public output on HTML tags, markdown syntax, URLs, email
addresses, Unicode control/invisible characters, overlong sentences and a
versioned forbidden-word list covering derogatory language, injuries,
personal life and betting. Proposed fixed sentence cap: **300 Unicode code
points**; enforce model/token bounds separately. Reject rather than silently
strip characters or reword an evidence-bearing sentence. Recognizers must
cover encoded/obfuscated variants, mixed case and Unicode evasions with
valid accented-name/punctuation controls. Lexical policy checks cannot
exhaustively detect all harmful meanings; guide/NLI/adversarial tests and
human audit retain distinct roles.

Schema/contract, G1 entity/number, code R1/L1, policy, coverage and format
checks precede local NLI. Each generated sentence is checked against the
packet's **verified catalog fact sentences**, never raw JSON. Premises must
preserve subject, measurements, flags, scope and time; a number elsewhere
in the packet is not support. Bound each pair/compatible fact group; reject
oversize inputs rather than truncating evidence. Calibrate threshold on dev
human entailment labels with wrong-subject, quantity, causal and unsupported
semantic negatives. A score is not an accuracy/confidence guarantee.

One informed Gemini retry total, then the
independently validated rules writer. Failed rules/final integrity validation
retains the prior public file. No-games days invoke neither writer nor judge.
Post-publication Groq covers G2 residue, L1, R1, S1 and policy only as
monitoring; unavailable/invalid results are not_evaluated, never passes.
Remote judge unavailability never skips the local/code publication gates.

## Local model and supply chain

Pin the NLI repository to an exact immutable Hugging Face revision, with
SHA-256 for weights, tokenizer and config in a reviewed manifest. Use cached
**safetensors only**; reject pickle/.bin alternatives, remote Python and
unlisted files. Disable remote code execution, pin runtime/dependencies,
verify license and CPU compatibility before selection. Model identity,
tokenizer, fact renderer and calibrated threshold are part of run identity.
No model ID/revision/hash is fabricated by this design.

Missing files, hash mismatch, unsupported format, unset threshold, timeout
or model failure rejects the LLM candidate and follows rules fallback. Unit
tests use deterministic local loader/model fakes and fixtures; a real cached
CPU smoke check is separately recorded before enabling the gate. Do not put
weights, response caches, keys or raw private label material in public artifacts.

## Credentials, logs and site headers

Production Free keys without card/trial are owner-reported in the
main-restricted environment; inventory/evidence limits are in RUNBOOK.
Separate local keys are approved but not created/read by the agent. Restrict each key to its API and
smallest available scope/model/project permissions. Verify provider-native
restrictions in P2.1; if a required restriction is unavailable, document the
gap and stop for owner review rather than claiming it exists. Cloudflare
backup credentials, if later provisioned before freeze, get the same isolation.
Owner review Oct 28 (RUNBOOK inventory): both Gemini keys are API-restricted
to the Gemini API with no billing account, but have no application
restriction because the owner's IP is dynamic. Groq offers no per-key
restriction; the local Groq key relies on a Nov 27 expiry, Free plan without
payment method, separation from production and USER-only storage. Accepted
residual risk: a leaked local key can spend the shared Free project/org quota
(and, for Gemini, any Gemini API call) until expiry or revocation.

Only safe closed error codes and validated bounded context reach public
logs/artifacts; no raw provider errors, internal raw prompts, credentials,
authorization headers or environment dumps. Exact new error codes still
need owner approval before implementation. Preserve reproducibility through
versioned templates/digests and approved packet evidence, without dumping
assembled internal requests. Raw failures/responses stay restricted and
sanitized before any public export. Sentinel tests inspect stdout/stderr,
logs, exceptions, generated payloads and artifact/bundle contents.

P2-SEC adds `X-Content-Type-Options: nosniff` and CSP with default self,
`frame-ancestors 'none'`, no object embedding, and only self plus necessary
Vercel Analytics origins for scripts/connections. No wildcard third-party
origins or broad script unsafe-inline/unsafe-eval. The installed analytics
package uses /_vercel/insights/script.js in production; verify actual needed
endpoints at implementation. Handle Next.js bootstrap/style requirements
with reviewed nonce/hash handling or scoped code changes, not a broken page
or an unreviewed CSP relaxation. Exact header policy and compatibility must
be proved against real responses for /, /quality and public assets, plus
legitimate rendering/analytics and blocked external script/frame probes.
Any wider rendering redesign requires scope approval. The owner approved
nonce/dynamic rendering and explicit style-src-attr on Oct 28. `proxy.ts`
generates 192-bit random nonces, overwrites incoming nonce/CSP, sends the
same policy to Next and the browser, and sets private/no-store on documents.
`app/layout.tsx` reads request headers, so /quality and the home page render
dynamically. Script-src is self plus nonce, never unsafe-inline/unsafe-eval,
including development (React development eval features may be blocked).
Style elements use self/nonce; style-src-attr permits existing React/chart
attributes. That exception permits inline style attributes; it grants no
script capability and is not a defense against arbitrary style injection.
`next.config.ts` supplies nosniff/DENY globally and restrictive CSP for data,
static bundles and favicon. No new external origin is permitted. The local
browser check stubs the same-origin Vercel intake, not a real deployment;
production Vercel collection still needs the owner's release smoke check.

Rotation/revocation and incident response: `docs/RUNBOOK.md`.

## Required evidence and limits

Before P2-SEC is complete: evidence v2/PR production-secret absence and main restriction;
every text-field injection/judge-manipulation payload rejected or neutralized;
HTML/markdown/URL/email/Unicode/derogatory output rejection; valid controls;
NLI hash/format/offline/timeout negative tests; safe log/artifact sentinel
tests; and real security-header/compatibility evidence. Tests never fetch
MLB/Savant or call providers. Run the full five suites and clean-context review.

Before generated prose can ship: owner-approved guide and exact schema,
calibrated local boundary, Nov 2 proof checkpoint, all held-out eval gates,
independent Antigravity QA and owner release decision. Neither a small
regression suite, 40-case dataset, NLI score, nor a remote judge is a claim
of perfect safety or accuracy. Free-tier drift, lexical evasions, NLI false
entailment and compromised trusted infrastructure remain residual risks.

## P2-SEC implementation and evidence boundary

- `agents/prompt_boundary.py` delegates to `data_pipeline/prompt_boundary.py`
  (boundary validation, not a display agent). Language-keyed model security
  instructions live in versioned `agents/security_instructions.json`.
  `prepare_request` is the required future
  provider entry point. It independently validates the whole existing
  public payload, then extracts a fresh closed projection and exact complete
  catalog fact keys, with subject, raw sample counts, flags and scopes.
  No whole scout/findings dictionary, bios/recent form, raw errors, critic
  verdicts, titles or standalone formatting fragments reach a request.
  This initial fact projection does not express every raw measurement;
  P2.2 extensions must update the closed schema/injection inventory.
  `SCHEMA` drives `TEXT_FIELDS` and the every-field tests. Lower-level
  `make_messages` validates shape/encoding, not truth; adapters must not
  accept arbitrary caller-constructed facts instead of `prepare_request`.
  Names are at most 100 code points (letters/marks and approved punctuation),
  abbreviations 2-4 ASCII uppercase, counts 0..1M or null (never bool),
  series 1..7 plus existing standing constraints. The dedicated JSON data
  message cannot change fixed roles/instructions; no tool field is emitted.
  A pattern-valid instruction remains untrusted data, not a proven guarantee
  that a future model will ignore it. Independent publication gates remain.
- `agents/security_policy.py` version p2-sec-1: 300-code-point candidate cap,
  2400-code-point internal fact cap; reject markup/URLs/emails/controls/
  invisibles, encoded forms and versioned policy patterns, without changing
  evidence text. Unicode/confusable/leet views broaden lexical matching,
  not an exhaustive semantic policy detector. Offline judge candidates may
  contain rejected policy text as quoted data; publication admission still
  rejects that text. S1/guide, semantic/NLI and humans retain distinct roles.
- `agents/model_transport.py`: fixed Gemini/Groq HTTPS hosts/routes, verified
  TLS, no redirects or tools, no arbitrary endpoint environment variable,
  64K request/128KiB response caps and 60s maximum timeout. Receives a key
  explicitly, reads none. Auth/quota/model IDs/settings/usage pacing still
  require P2.1; tests fake all HTTP, never call a provider.
- `agents/safe_model_log.py`: exact internal event/route fields, existing
  closed error codes, bounded counts and canonical digests only. No raw
  exception/message/prompt/header/context parameter. Sentinels are rejected
  without stdout/stderr/logger leakage. No new public error code or actual
  live-log schema is introduced. Existing source/cache/generator raw local
  diagnostics were inventoried and are unchanged; this is NOT a claim that
  those legacy console paths are globally sanitized. Provider/NLI adapters
  must not route failures into those raw diagnostics.
- `agents/nli_cache.py` and `nli_manifest.json`: exact revision/file set,
  regular files only (no symlinks/reparse points), sizes/SHA-256s, known
  DeBERTa config/labels and bounded safetensors headers before loading.
  No pickle/remote code/download fallback. A disposable isolated worker
  receives no key-bearing environment, checks pinned runtime versions,
  loads explicit built-in classes locally with safetensors, CPU float32,
  one thread, no silent token truncation (512 including specials), at most
  32 bounded pairs and a hard subprocess timeout. Missing/invalid runtime,
  cache/calibration/identity, worker failures or invalid scores reject.
  `entails` is internal and UNWIRED: a fixture threshold is not admission.

NLI metadata provenance (public reads only, Oct 28):
[immutable model card](https://huggingface.co/cross-encoder/nli-deberta-v3-small/blob/fa2804872c3b4bd748f38c0185cc85775361e735/README.md),
[config](https://huggingface.co/cross-encoder/nli-deberta-v3-small/blob/fa2804872c3b4bd748f38c0185cc85775361e735/config.json).
Revision fa2804872c3b4bd748f38c0185cc85775361e735, Apache-2.0, English NLI;
contradiction 0 / entailment 1 / neutral 2. Small tokenizer/config files were
hashed in memory; the 567,605,820-byte weights SHA is from HF LFS metadata,
NOT a downloaded/local hash. No weights were downloaded/executed here.

`requirements-nli-windows.txt` is an OPTIONAL isolated Windows AMD64 CPython
3.14 lock (not 3.14.1, excluded by NetworkX), not installed by normal CI or
the site. Torch CPU wheel is pinned by official SHA, all transitive pins
were checked against versioned PyPI metadata; this is metadata compatibility,
not executed runtime proof. Sources: [official CPU index](https://download.pytorch.org/whl/cpu/torch/),
[Transformers metadata](https://pypi.org/pypi/transformers/5.21.0/json).
Default terminal is Python 3.14.6. Linux production runtime is not verified
by this Windows lock. Before any admission: provision/hash the actual cache,
record a real CPU smoke (and the production platform lock), supply dev HUMAN
calibration bound to model/runtime/fact-renderer identity, and complete
P2.3/P2.6/guide/schema/eval/release gates. Missing any keeps rules; P2-SEC
fixture/metadata evidence never proves the Nov 2 publication boundary.

Verification results, observed red counts, controls, real-response/browser
checks and clean-context review are recorded in STATUS/status-archive.
