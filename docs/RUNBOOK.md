# Operations runbook: Phase 2 security

Security design approved 2026-10-28; D47 removes Mistral. Companion to
`SECURITY.md` and `plans/P2.md`. Current production uses rules. Provider
adapters, model gate, rules-only switch and monitoring integration remain
unimplemented. The LOCAL route was approved Oct 28; owner confirmed key setup
on Oct 28 and accepted the owner-reported restriction settings the same day
(inventory below). The two bounded P2.1 probes follow the runner commit's green CI.
No key values, account email or project identifiers belong in this inventory.

## Key and settings inventory (2026-10-28)

Provider/account settings below are owner-reported; GitHub verification and
its limits are recorded separately. Never paste key values into chat, git,
terminal arguments, documents, logs or screenshots. Free only: no billing,
paid upgrade, trial or payment card to unblock access.

| Key | Management / account context | Plan / expiry | Storage and boundary |
|---|---|---|---|
| Gemini **pitchcraft-writer** | [AI Studio API keys](https://aistudio.google.com/api-keys); owner's Google account; one Google Cloud project shared with the local key (identifier withheld per the rule above) | Free tier, no billing account; **never enable Configurar la facturación**; no expiry set; API restriction: Gemini API only; no application restriction | GitHub > Settings > Environments > **pitchcraft-llm-main** > **GEMINI_API_KEY**; main only |
| Groq **pitchcraft-judge** | [Groq keys](https://console.groq.com/keys); Personal organization, Default Project | Free plan; **never Upgrade to Dev Plan**; expires **2026-11-27** | Same environment > **GROQ_API_KEY**; main only |
| Bot **pitchcraft-data-bot** | GitHub > Settings > Deploy keys | Write deploy key; sole main-ruleset bypass per owner setup | Private half only as **DATA_DEPLOY_KEY** in **data-publish**; main only; never copy to LLM/local execution |
| Local Gemini **pitchcraft-writer-local** | Google AI Studio, same Cloud project as production **pitchcraft-writer**; owner created and confirmed Oct 28, then renamed it from the mislabeled "pitchcraft-judge-local" (same key, value unchanged) | Free tier, no billing account; no expiry set; API restriction: Gemini API only; no application restriction (dynamic residential IP) | Windows USER **PITCHCRAFT_GEMINI_API_KEY_LOCAL**, stored by owner using the hidden-input script below; no project file; explicit approved offline runner only |
| Local Groq **pitchcraft-judge-local** | Groq Free, Personal / Default Project; owner created and confirmed Oct 28 | Free plan, no payment method; expires **2026-11-27**; Groq offers no provider-native per-key restriction (see compensating controls below) | Windows USER **PITCHCRAFT_GROQ_API_KEY_LOCAL**, stored by owner using the same hidden-input script; no project file; explicit approved offline runner only |

Owner restriction review, accepted 2026-10-28 (owner-reported settings; the
agent did not inspect either console). Both Gemini keys are in the same Google
Cloud project (shared quota), API-restricted to the Gemini API only, with no billing
account. Neither has an application restriction: the owner's residential IP
is dynamic, so an IP allowlist would break local runs. For Groq
**pitchcraft-judge-local**, Groq offers no provider-native per-key
restriction. Compensating controls: 30-day expiry 2026-11-27, Free plan
with no payment method, a separate key from production **pitchcraft-judge**,
storage only as a Windows USER variable, and never logged. Residual risk:
anyone holding the local Groq key can use the whole organization's Free quota
until expiry or revocation; see `SECURITY.md`.

Security controls: GitHub > Settings > **Advanced Security**: secret
protection/secret scanning, push protection, Dependabot alerts and private
vulnerability reporting enabled. Dependency graph enabled; Dependabot
security updates and automatic dependency submission stay OFF. Rulesets:
GitHub > Settings > **Rules > Rulesets**: main, v2 and tags, active.
Do not disable a ruleset for a release or experiment.

Renewal: **before Opening Day 2027**, create a new Groq key and replace
GROQ_API_KEY in pitchcraft-llm-main, together with the yearly saved MLB
season-calendar refresh (retain prior years/source digests). If an offline
experiment uses the inventoried Nov 27 key after **2026-11-27**, create a
new key first. Proposed offline runs use their separate local key: renew
that key before its own actual expiry too; never borrow production access.
Record non-secret rotation/revocation dates here. No renewal was performed.

## Read-only GitHub evidence and limits

Checked Oct 28 (America/Bogota), with direct **gh api GET** calls only;
no setting or credential was changed. Endpoint paths below are relative
to `repos/Dher10/pitchcraft-agent/`. No key values were requested or read.

| GET | Observed output / conclusion |
|---|---|
| Repository metadata | secret_scanning enabled; secret_scanning_push_protection enabled; dependabot_security_updates disabled |
| environments/pitchcraft-llm-main | custom branch policies; protection_rules only branch_policy, no reviewers |
| environments/pitchcraft-llm-main/deployment-branch-policies | exactly main, type branch |
| environments/pitchcraft-llm-main/secrets (names/timestamps metadata only) | HTTP 403 Resource not accessible by personal access token; key names/presence NOT independently verified; no broader access requested |
| vulnerability-alerts | HTTP 204: Dependabot alerts enabled |
| automated-security-fixes | HTTP 200, enabled=false, paused=false |
| private-vulnerability-reporting | enabled=true |
| code-security-configuration | HTTP 204, no attached configuration; does NOT prove automatic dependency submission state |
| dependency-graph/sbom | SPDX-2.3, 652 packages; dependency graph available |
| rulesets | main, v2, tags all active |
| rulesets/25520388 | main only; exactly one bypass actor, type DeployKey, mode always; actor_id null (API does not resolve its identity) |
| keys (public metadata, title/write flag only) | one key, pitchcraft-data-bot, read_only=false; no private key accessed |
| environments/data-publish and its deployment-branch-policies | main only |

**Owner-reported, not independently established:** names/storage of both
LLM secrets and DATA_DEPLOY_KEY, absence from other storage and automatic dependency submission OFF. The API evidence above
must not be described as verification of those facts. A 204 configuration
response is not a disabled setting. No secrets/permissions need widening
for this task; owner UI evidence can close metadata gaps later.
Previous v2 commit ae743e7: CI 40612968097 success (gh run list).

## Approved local keys: exact owner setup steps (before P2.1)

The owner approved this route in `plans/P2.md` and confirmed setup Oct 28:
both entries were stored with this script and its presence check printed
True for both. The agent repeated only the literal presence command below:
both printed True. No key value was read into tool output or a file, and no
production secret was exported. The remaining restriction/access/capacity
checks are separate from this storage confirmation.

1. At [AI Studio API keys](https://aistudio.google.com/api-keys), select the
   intended no-billing project and create **pitchcraft-writer-local**.
   Keep Free/no billing; never click **Configurar la facturación**. Restrict
   to Gemini API / generativelanguage.googleapis.com using the console's
   API restriction/auth-key controls. If the available controls differ or
   API access requires paid billing, stop for review. Record non-secret
   restriction/expiry evidence; never copy the production key.
2. At [Groq keys](https://console.groq.com/keys), in Personal / Default
   Project (or explicitly record a different local project), create
   **pitchcraft-judge-local**, set/record its expiry and retain Free.
   Never click **Upgrade to Dev Plan**. Verify what scopes Groq actually
   offers in P2.1; do not claim per-model restrictions if absent.
3. Use an ordinary local PowerShell window with no transcript, tracing or
   screen capture. Run the following **literal code**, entering the two
   NEW values only into the hidden prompts. Do not replace code with key
   literals, use setx with a key argument, or save any key to a file/profile.
   Read-Host input is not a command-history entry. Clear the clipboard after
   each entry if copy/paste was used. The script prints no values.

```powershell
function Set-PitchcraftLocalKey {
    param([string]$VariableName)
    $localKeyInput = Read-Host "Enter new $VariableName (hidden)" -AsSecureString
    if ($localKeyInput.Length -eq 0) {
        $localKeyInput.Dispose()
        throw "Empty key input; nothing stored"
    }
    $localKeyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($localKeyInput)
    try {
        [Environment]::SetEnvironmentVariable(
            $VariableName,
            [Runtime.InteropServices.Marshal]::PtrToStringBSTR($localKeyPointer),
            [EnvironmentVariableTarget]::User
        )
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($localKeyPointer)
        $localKeyInput.Dispose()
        Remove-Variable localKeyInput, localKeyPointer -ErrorAction SilentlyContinue
    }
}
Set-PitchcraftLocalKey 'PITCHCRAFT_GEMINI_API_KEY_LOCAL'
Set-PitchcraftLocalKey 'PITCHCRAFT_GROQ_API_KEY_LOCAL'
Remove-Item Function:\Set-PitchcraftLocalKey
```

4. Verify **presence only**, never echo or enumerate environment variables:

```powershell
foreach ($localKeyName in @('PITCHCRAFT_GEMINI_API_KEY_LOCAL', 'PITCHCRAFT_GROQ_API_KEY_LOCAL')) {
    $localKeyPresent = -not [string]::IsNullOrWhiteSpace(
        [Environment]::GetEnvironmentVariable($localKeyName, [EnvironmentVariableTarget]::User)
    )
    Write-Host "$localKeyName configured: $localKeyPresent"
}
Remove-Variable localKeyName, localKeyPresent
```

5. Do not restart a general-purpose IDE/test/build environment just to
   inherit keys. The approved offline runner will read these USER entries
   explicitly, only after an explicit offline invocation. Existing processes need no restart
   for that direct read. New processes after sign-in/restart may inherit
   the values: keep both variables out of frontend/build/test subprocess
   environments. Never dump the registry/environment, enable HTTP debug
   logging, upload memory/crash dumps, or log assembled authenticated calls.
6. Stop after setup. P2.1 still requires completed P2-SEC and the approved
   runner, quota/auth-failure fixtures and safe logging before any probe.

Windows USER variables persist in the user registry, **not encrypted secret
storage**. Same-user software/admins can read them, processes can inherit
them, and values exist in memory. The no-file rule means no key material
written into project files, .env, scripts, history or artifacts; this route
still deliberately uses Windows' persistent environment storage. Separate
keys allow local revocation without touching production but do not isolate
shared project/org quotas. Push protection is a backstop, not the control.
If registry persistence is unacceptable, approve a different storage route
before proceeding; do not silently replace this with .env or a vault.

To revoke: delete/revoke **the local key by its name** at its provider page
above, then remove the USER entries (and any inherited process copies):

```powershell
[Environment]::SetEnvironmentVariable('PITCHCRAFT_GEMINI_API_KEY_LOCAL', $null, [EnvironmentVariableTarget]::User)
[Environment]::SetEnvironmentVariable('PITCHCRAFT_GROQ_API_KEY_LOCAL', $null, [EnvironmentVariableTarget]::User)
Remove-Item Env:\PITCHCRAFT_GEMINI_API_KEY_LOCAL -ErrorAction SilentlyContinue
Remove-Item Env:\PITCHCRAFT_GROQ_API_KEY_LOCAL -ErrorAction SilentlyContinue
```

Close processes that inherited them. Removing variables alone never revokes
provider access. Production revocation uses the separate production key
names and the same provider management pages, followed by replacement of
the corresponding GitHub environment secret.

Provider setup references (reverify exact account entitlement in P2.1):
[Google key/restriction documentation](https://ai.google.dev/gemini-api/docs/api-key),
[Google Free pricing](https://ai.google.dev/gemini-api/docs/pricing),
[Groq key management](https://console.groq.com/keys),
[Groq limits](https://console.groq.com/docs/rate-limits).
These links do not prove access, exact model entitlement or account quotas.

## Credential rotation and revocation

Owner performs provider-console and GitHub environment changes; agents do
not request key values. Rotate on suspected exposure, provider notice or
owner maintenance. For ordinary rotation:

1. Confirm rules-only operation/last known safe deployment is available and
   record non-secret key identity/scope. Do not print the current secret.
2. Create a replacement Free API-restricted key; store it in the same
   main-only environment secret. No temporary repository/local copy of production keys.
3. For production, use only a separately approved main-only minimal canary
   to verify authentication and safe logging. Local-key rotation, if approved,
   uses only the explicit offline runner; ordinary v2 tests replay fixtures. Do not
   dispatch a daily MLB/Savant fetch or spend another D42 rehearsal.
4. Revoke the old key at the provider; prove rejection by its non-secret
   console state or an approved safe check, without logging key values.
5. Record dates, affected provider/key identifier, safe test result and
   revocation evidence. If the replacement fails, keep rules and revoke
   unused/exposed credentials; never enable paid access as a workaround.

For a suspected leak, revoke immediately rather than waiting for a canary.
Removing a key from GitHub does not revoke it at the provider. Treat leaked
tokens as compromised even if logs were later masked/deleted. Retain incident
evidence privately; cleanup/history changes require the owner's separate
decision and never authorize agent force pushes or history rewriting.

## Incident: unsafe report, injection or credential exposure

Owner executes containment; record timestamps and deployment/run IDs only.

1. **Vercel rollback:** restore the last known safe rules-only deployment.
   Verify the public page/data and record the rollback deployment ID. A
   previously unsafe report is not made safe by a successful new judge call.
2. **Disable the daily workflow** in GitHub to stop automated publication
   while containment is in progress. Record the affected workflow/run; do
   not alter rulesets, the deploy-key bypass or branch/history protections.
3. **Revoke affected LLM keys** at Gemini/Groq (and Cloudflare if ever
   provisioned), remove/replace environment secrets and inspect safe usage
   records. Do not paste raw provider errors/prompts or secrets into an issue.
4. **Force the rules writer.** Once implemented, use the P2.3 verified
   rules-only switch; confirm actual writer origin and validated rules output.
   Until that switch exists, the known rules-only rollback is the supported
   control. Removing credentials alone is not proof that a report is safe.
5. Preserve restricted evidence, classify the failure and add a fixture-based
   regression on v2. Prove the failing boundary red then green, all five
   suites and reviewer PASS; owner reviews any scope/schema/code/workflow
   change and accepts independent QA as applicable.
6. Owner releases through the normal v2 -> main PR/Merge path, verifies
   Vercel READY/safe output, then re-enables the workflow after containment
   and safe credential wiring are confirmed. Observe the next approved
   scheduled run; no extra dispatch/rehearsal is implied. LLM enablement
   requires the original eval/QA gates, not merely incident closure.

## Quota, judge and local model failure

- An unavailable writer or failed local/code gate gets at most one informed
  Gemini retry, then validated rules; no other model writer. Final integrity failure keeps
  the previous public file. No-games makes no model call.
- A failed/unavailable post-publication Groq judgment is logged as
  not_evaluated for the affected dimensions. Do not gate or undo publication,
  invent a pass, rerun the writer for a better score or silently use Cloudflare.
- Offline quota pauses resume the identical cached request identity. Never
  switch the frozen judge. Before freeze only, owner-approved Cloudflare
  selection/calibration can use its own budget; after freeze, drift/outage
  stops the experiment or needs an independently approved separate run.
- On local NLI cache hash/format mismatch, missing revision, timeout or
  uncalibrated threshold, reject the LLM candidate and force rules. Never
  load pickle, enable remote code, skip a checksum or download mutable latest
  weights to keep publication moving. Rebuild the verified cache separately.

P2-SEC/P2.3 must demonstrate these procedures with fixtures and safe test
records before calling the controls operational. Actual public data and
live logs remain the deployed bot's responsibility, never a v2 regeneration.

## P2-SEC operator evidence and safe rehearsal

The default pipeline still uses the existing independently validated rules
writer and requires no model keys. Model primitives are not wired into
publication yet. Never assume removing keys alone substitutes for a safe
publication boundary. The runbook's incident actions remain owner actions:
rollback in Vercel, disable the daily workflow, revoke provider key, restore
validated rules. No actual workflow disable/rollback/key revocation was run.

Fixture rehearsals exercise revoked/auth-failure responses, rejection of
raw-error/key sentinels, unavailable NLI/cache/timeouts, and validated rules
operation with no transport calls. They do not prove a provider key was
revoked or a Vercel rollback succeeded. Record real incident operation IDs
and timestamps privately when those actions are actually needed.

To repeat local production header/browser proof (no provider/source calls):
run `npm run build`, start `npm run start -- --hostname 127.0.0.1 --port 3082`,
then in another terminal `node scripts/check_security_headers.mjs http://127.0.0.1:3082`.
Pinned Playwright uses installed Chrome in a new temporary profile. The
script accepts loopback only, aborts external requests, and stubs the
same-origin Vercel script/intake because next start does not host it. It
checks real / and /quality/asset headers, unique nonced bootstrap, hydration,
pitch-control interaction, styles, and blocked script/eval/frame probes.
The eval probe runs from a page script: CDP evaluation itself may bypass CSP.
No production Vercel ingestion claim is made by the local stub.

The setup script creates exactly these Windows USER entries:
**PITCHCRAFT_GEMINI_API_KEY_LOCAL** and **PITCHCRAFT_GROQ_API_KEY_LOCAL**.
It has not been executed by the agent. No runner automatically reads them
in P2-SEC. Do not paste values in chat; confirm setup by names/presence only.

## P2.1 runner checkpoint (2026-10-28; first Gemini probe run, see STATUS)

`evals/local_runner.py` is a synthetic-probe runner, not the writer or
judge queue. Imports/tests/builds make no credential read or provider call.
Only explicit owner-PC offline invocation may read the exact USER entries;
there is no inherited/production-variable fallback or subprocess. The
runner offers no arbitrary prompt, model, endpoint, output path or retry.
The CLI requires a pinned commit and dirty-tree digest. These are operator
inputs, not independently certified by a provider. Record the actual git
HEAD/dirty digest immediately before invocation; do not invent them. The
dirty digest is the SHA-256 of the bytes printed by `git diff HEAD --binary`.
For a clean tree that output is empty, so the digest is
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. Run
probes only from a clean tree: untracked files are not covered by that diff.
Closed probe codes (local ledger and CLI output only; never published):
`key_unavailable` (the USER entry is missing or the loader rejected it; no
request was sent), `connection_failed_timeout` and `connection_failed_other`
(the request was handed to the network but no HTTP status came back: the first
is a timeout, the second a reset, TLS, DNS or any other transport error),
`request_failed` (any other failure, including a non-429 HTTP status, which is
recorded in `http_status`), `budget_spent` (HTTP 429, or the ledger's
per-provider budget is used up) and `malformed_response` (a 200 whose body
fails validation). The first three never carry an HTTP status. Plain
`connection_failed` is the Oct 29 code of generation 2's recorded Gemini row,
kept readable but no longer produced.

Ledger generations are fixed in code; `--ledger-generation` is required and
has no default. Each generation lists the providers it may still reserve.
Generation 1 (`.local/p2-1/`) spent one Gemini probe (`request_failed`,
`http_status` null). Generation 2 (`.local/p2-1-gen2/`) spent one Gemini probe
(`connection_failed`, no status within 30 s) and one Groq probe (HTTP 403).
Both are closed and stay untouched. Generation 3 (`.local/p2-1-gen3/`) was
authorized by the owner on Oct 29 for exactly one further Gemini probe. Across
all generations that is at most Gemini 3 and Groq 1 requests and 16,384
reserved tokens. Any further generation, or any further Groq probe, needs
owner approval and a code change.

Model-version mismatches and truncation are recorded with their usage and
still spend the provider's single probe. Per D48 Gemini runs at its default
temperature (the field is omitted; Google warns that lowering it can make
Gemini 3 loop) with thinking at LOW, the lowest level the chosen model is
known to support (MINIMAL was unsupported on gemini-3.8-flash; D49 now uses gemini-3.5-flash). The API field is
`generationConfig.thinkingConfig.thinkingLevel`, with uppercase enum values
(read from the public API discovery document, not only the guides).

The Groq 403 of Oct 29 was not an access or key problem: Cloudflare in front
of `api.groq.com` rejects Python's default `Python-urllib` agent with error
1010 before authentication, while a custom agent reaches the API (HTTP 401 to
a keyless request). The transport now always sends the fixed agent
`pitchcraft-agent/1.0`. A Groq probe has not yet succeeded; one more needs
owner approval.

Per ledger generation: one synthetic request per provider, two total, with a 1,024 generated-token
cap, 120-second transport timeout (D49; the transport maximum), fixed HTTPS/no redirect and no tools.
Each request reserves 4,096 tokens before key load/network, even on failure
or interruption: at most 8,192 tokens in this ledger. These conservative
debits are not observed usage or evidence of spare shared-account quota.
Requests are at least one minute apart. Rejected/unknown results never
auto-retry; an identical complete accepted result can be reused. Changed
identities cannot bypass the per-provider budget. Do not delete the ledger
or its lock to repeat a request; investigate an interrupted run first.

The fixed local evidence paths are the generation directories under `.local/`, ignored by git and never
served. A protected Windows DACL grants owner/SYSTEM/administrators access;
POSIX fixtures use 0700/0600. ACL failure, symlinks/reparse points, hardlinked
files, unexpected files, a lock or a partial/corrupt ledger fail before key
load. A single-writer, fsynced hash-chain ledger stores reservations and
closed sanitized results, not request headers/prompts/raw errors or raw
reasoning. Only the fixed boolean probe output's digest is retained. All
usage/fingerprint fields absent from the provider remain unavailable.
Fingerprint hashes identify observations without persisting arbitrary
provider text; they do not establish an immutable backend version.

Candidate synthetic IDs/settings: **gemini-3.5-flash** (D49 primary; fallback gemini-3.1-flash-lite, not probed), default temperature,
thinking LOW (D48), JSON schema; **openai/gpt-oss-120b**, temperature 0, reasoning
effort low with `include_reasoning: false`, strict JSON schema. Groq does not
support `reasoning_format` on gpt-oss models. Gemini may attach an opaque
`thoughtSignature` to a text part; the parser accepts it and never stores it. These are not a frozen writer/judge protocol
and no guide/prompt for baseball has been created. The complete probe body,
protocol source, schema, input, placeholder guide/evaluator identity and
commit/dirty digest determine cache identity. Future real-packet/report
queues require their own validated adapters and complete identities.

Current official sources checked Oct 28 (America/Bogota):

- [Gemini key types/restrictions](https://ai.google.dev/gemini-api/docs/api-key):
  new AI Studio keys default to auth keys restricted to Gemini. This is
  documentation, not inspection of this key's actual settings.
- [Gemini deprecations](https://ai.google.dev/gemini-api/docs/deprecations)
  (checked Oct 29): `gemini-3.5-flash` is not shutting down and routes to
  `gemini-3.6-flash`; `gemini-3.1-flash-lite` shuts down May 7, 2027.
  [Pricing](https://ai.google.dev/gemini-api/docs/pricing) lists Free input/output
  for 3.6 Flash and 3.1 Flash-Lite. [2.5 availability](https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash)
  warns of legacy-project access limits; do not assume a new key gets 2.5.
- [Gemini limits](https://ai.google.dev/gemini-api/docs/rate-limits):
  project-shared; exact active limits require AI Studio evidence. No numeric
  account quota has been established here.
- [Groq model permissions](https://console.groq.com/docs/model-permissions):
  organization/project controls; no per-key model scope is claimed. The owner
  reviewed and accepted the missing per-key restriction on Oct 28 (inventory above).
- [Groq limits/headers](https://console.groq.com/docs/rate-limits): Free
  published defaults remain 30 RPM/1,000 RPD/8K TPM/200K TPD for this model,
  organization-shared. Request headers refer to RPD, token headers to TPM;
  they do not independently establish TPD. Exact account limits still pending.
- [Groq API](https://console.groq.com/docs/api-reference) and
  [reasoning](https://console.groq.com/docs/reasoning) document strict JSON
  schema on gpt-oss-120b, low effort and `include_reasoning` (rechecked Oct 28;
  `reasoning_format` is unsupported on gpt-oss). [Gemini thinking](https://ai.google.dev/gemini-api/docs/thinking)
  lists levels per model (none for the D49 names), says the output cap includes thought tokens
  and that signatures can be attached to any part. Synthetic fixtures imitate
  these wire shapes; they are not recordings of successful account access.

The owner's restriction review was recorded Oct 28 (inventory above), which
clears the P2.md gate for the two bounded probes once this runner is
committed. Run Gemini first. If its probe returns 401 or 403, stop and report
to the owner: do not try another variable, key or retry. Never request values
or broaden billing/access. P2.1 remains unchecked; no real usage measurement,
account entitlement, quota acceptance or dataset exists yet.

## D49 writer call policy (Oct 29)

Owner manual tests showed free-tier latency from 4 s to 89 s and 503s, with models.list fine, so earlier probe timeouts were capacity, not the key or Python.
Writer policy (`agents/writer_policy.py`): 120 s timeout; 503, 429 or timeout gets one retry after 3 s, then the fallback model with the same policy, then rules; other 4xx go to rules.
Per call the path and the closed code of each failed attempt are recorded; summaries report LLM coverage and fallback rate. Generation 5 (`.local/p2-1-gen5`) allows exactly one Gemini probe on the primary at 120 s; generation 4 never ran and is closed; generation 5 was accepted (HTTP 200, 4.7 s). Generation 6 (`.local/p2-1-gen6`, owner Oct 29) allows exactly one Groq probe with the user-agent fix; P2.1 closes only after a Groq success.
