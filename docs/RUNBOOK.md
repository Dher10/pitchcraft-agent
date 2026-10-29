# Operations runbook: Phase 2 security

Security design approved 2026-10-28; D47 removes Mistral. Companion to
`SECURITY.md` and `plans/P2.md`. Current production uses rules. Provider
adapters, model gate, rules-only switch and monitoring integration remain
unimplemented. The LOCAL route below is a proposal awaiting owner approval.
No key values, account email or project identifiers belong in this inventory.

## Key and settings inventory (2026-10-28)

Provider/account settings below are owner-reported; GitHub verification and
its limits are recorded separately. Never paste key values into chat, git,
terminal arguments, documents, logs or screenshots. Free only: no billing,
paid upgrade, trial or payment card to unblock access.

| Key | Management / account context | Plan / expiry | Storage and boundary |
|---|---|---|---|
| Gemini **pitchcraft-writer** | [AI Studio API keys](https://aistudio.google.com/api-keys); owner's Google account, project shown there | Free tier, no billing; **never enable Configurar la facturación**; no expiry set | GitHub > Settings > Environments > **pitchcraft-llm-main** > **GEMINI_API_KEY**; main only |
| Groq **pitchcraft-judge** | [Groq keys](https://console.groq.com/keys); Personal organization, Default Project | Free plan; **never Upgrade to Dev Plan**; expires **2026-11-27** | Same environment > **GROQ_API_KEY**; main only |
| Bot **pitchcraft-data-bot** | GitHub > Settings > Deploy keys | Write deploy key; sole main-ruleset bypass per owner setup | Private half only as **DATA_DEPLOY_KEY** in **data-publish**; main only; never copy to LLM/local execution |
| Proposed Gemini **pitchcraft-writer-local** | Same AI Studio management page; create a separate key after approval | Free/no billing; record actual restrictions/expiry at creation | Windows USER **PITCHCRAFT_GEMINI_API_KEY_LOCAL**; explicit approved offline runner only; never production key reuse |
| Proposed Groq **pitchcraft-judge-local** | Same Groq page; record organization/project at creation | Free; record chosen expiry (do not assume Nov 27) | Windows USER **PITCHCRAFT_GROQ_API_KEY_LOCAL**; explicit approved offline runner only |

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

## Proposed local keys: exact owner steps (ONLY after approval)

This implements the preference proposed in `plans/P2.md`; it is **not yet
authorization to create keys or run P2.1**. No production secret is exported.

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
   explicitly; it does not yet exist. Existing processes need no restart
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
