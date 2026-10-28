# Security design and threat model

Draft for owner approval, 2026-10-27. Required by kickoff step 3 and P2-SEC
in `docs/plans/P2.md`. This is a design, not a claim that its new controls
exist. No credentials, environment, workflow, model loader or security
headers are changed by this documentation task. Rules remain the live writer.

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
3. v2/PR/local/preview execution -> **no LLM keys**. Rehearsals replay recorded
   fixtures. A proposed new environment, `pitchcraft-llm-main`, is restricted
   to main and holds Gemini/Groq/Mistral keys. It is separate from the current
   publication deploy-key environment. Merely naming an environment is not a
   branch check: GitHub deployment-branch restrictions and job conditions
   must both be proved before wiring it. No secrets in repository/global
   variables, local .env, NEXT_PUBLIC variables or browser bundles.
4. Provider output -> bounded parse/schema -> plain-text and code checks ->
   sentence/evidence integrity -> local NLI -> retry/rules fallback -> final
   independent publication validation. No writer/judge tools or retrieval.
5. Approved public payload -> React text rendering -> browser. No HTML
   insertion. Headers add defense in depth; output checks do not replace
   React escaping or contract validation.
6. Published report -> one remote monitoring judge call -> safe audit record.
   Judge verdicts cannot gate/undo publication (D17). Offline evaluation uses
   the same frozen judge, with test results sealed from tuning.

Credentialed probes and offline model runs must execute in a separately
approved main-only job using the new environment; "offline" does not mean
local key storage. That job checks out the trusted main commit, never a
user-supplied ref or PR/v2 code; do not use privileged pull_request_target
execution or execute downloaded/untrusted artifacts with credentials.
No workflow patch is approved in this document. Before
any later patch, account for daily.yml's v2 push trigger and all three spent
D42 rehearsals: no accidental fourth fetch/run. Existing server protections
and the deploy key are not modified here.

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

One informed retry total, optionally using Mistral after Gemini, then the
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

Owner creates recurring Free keys without card/trial and stores them only
in the new main-restricted environment. Restrict each key to its API and
smallest available scope/model/project permissions. Verify provider-native
restrictions in P2.1; if a required restriction is unavailable, document the
gap and stop for owner review rather than claiming it exists. Cloudflare
backup credentials, if later provisioned before freeze, get the same isolation.

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
Any wider rendering redesign requires scope approval.

Rotation/revocation and incident response: `docs/RUNBOOK.md`.

## Required evidence and limits

Before P2-SEC is complete: show v2/PR secret absence and main restriction;
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
