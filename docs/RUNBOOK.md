# Operations runbook: Phase 2 security

Draft for owner approval, 2026-10-27. Companion to `SECURITY.md` and
`plans/P2.md`. Current production uses rules; the LLM environment, provider
adapters, rules-only switch and monitoring integration described below are
planned, not implemented by this document. No operational action is run here.

## Owner setup before implementation

1. Create a Google AI Studio Free key, a Groq Free key and a Mistral Free
   key, with no card, billing upgrade or trial. If a provider requires those,
   stop; do not pay to unblock the plan. Never paste values into chat, git,
   terminal arguments, documents or logs.
2. Create a new GitHub environment (proposed `pitchcraft-llm-main`) and
   configure deployment branches to allow **only main**. Keep the existing
   daily deploy-key environment separate. Store GEMINI_API_KEY, GROQ_API_KEY
   and MISTRAL_API_KEY only in this environment, not repository secrets,
   local .env files or frontend variables. Do not grant v2/PR/fork access.
3. Restrict keys to the corresponding API/minimal scope/project/model
   permissions. Keep a non-secret inventory: provider, secret name, purpose,
   creation/rotation/revocation date and restriction evidence, never value.
   Missing provider-native restrictions require owner review in P2.1.
4. Enable GitHub secret scanning and push protection. Owner confirms these
   controls and approves SECURITY/plan before the agent starts P2-SEC or P2.1.
   No workflow wiring/dispatch is part of this setup message or this session.

Provider setup references (reverify in P2.1):
[Google keys](https://ai.google.dev/gemini-api/docs/api-key),
[Google Free pricing](https://ai.google.dev/gemini-api/docs/pricing),
[Groq keys](https://console.groq.com/keys),
[Groq limits](https://console.groq.com/docs/rate-limits),
[Mistral Free activation](https://docs.mistral.ai/getting-started/quickstarts/studio/activate-and-generate-api-key).
These links do not prove account access, exact model entitlement or quotas.

## Credential rotation and revocation

Owner performs provider-console and GitHub environment changes; agents do
not request key values. Rotate on suspected exposure, provider notice or
owner maintenance. For ordinary rotation:

1. Confirm rules-only operation/last known safe deployment is available and
   record non-secret key identity/scope. Do not print the current secret.
2. Create a replacement Free API-restricted key; store it in the same
   main-only environment secret. No temporary repository/local copy.
3. Use only a separately approved main-only minimal probe/canary to verify
   authentication and safe logging. v2 continues recorded fixtures. Do not
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
3. **Revoke affected LLM keys** at Gemini/Groq/Mistral (and Cloudflare if ever
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
  retry across providers, then validated rules. Final integrity failure keeps
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
