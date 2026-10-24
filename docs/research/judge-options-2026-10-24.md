# $0 judge options for PitchCraft

Researched October 24, 2026, America/Bogota. Research only: no account,
key, inference request, code, workflow, schema or decision was changed.
Sources are provider documentation, provider/model-author publications and
research papers. All linked pages were checked on this date. A page with
no publication/update date is identified as undated; access date does not
establish how long its terms have held.

## Recommendation for the owner's decision

Calibrate **Cloudflare Workers AI `@cf/zai-org/glm-4.7-flash` first**, with
**`@cf/qwen/qwen3-30b-a3b-fp8` as the selection/calibration backup**. Both
have a published renewable allowance that fits the budget below without
paid activation. Both are outside the Gemini family. These are relatively
small MoE models, approximately 30B total/3B active, with no demonstrated
PitchCraft judge-human agreement yet. This recommendation prioritizes
verifiable capacity, output controls and data terms; it does not establish
that either is the strongest judge in quality. The exact hosted-model
controls are documented in [Cloudflare's GLM page](https://developers.cloudflare.com/workers-ai/models/glm-4.7-flash/)
and [Qwen page](https://developers.cloudflare.com/workers-ai/models/qwen3-30b-a3b-fp8/).

The backup shares Cloudflare's quota and outage risk. It is not a second
independent provider allowance. **Neither is selected or approved by this
report.** If neither reaches 85% agreement separately for G2/L1/U1/R1/S1,
keep rules live and report the experiment honestly. Do not lower the bar
to obtain a $0 deployment.

GPT-OSS-120B is a stronger candidate to investigate on judge-specific
evidence, but Groq's published free token limit makes this workload take
roughly a month. Larger Mistral models have promising capabilities but no
publicly verifiable Free-mode capacity/entitlement for this run. These
constraints, rather than an unsupported quality ranking, drive the choice.

## 1. Exact request ledger and bounded token budget

### What can and cannot be exact today

The counts below implement the owner's requested research envelope:
**40 cases for each of A/B1/B2**, four separately judged report dimensions,
and both U1 presentation orders. This is larger than the minimum P2 plan,
which requires B2 on 20 held-out cases and previously budgeted one
randomized U1 order. Budgeting the larger envelope does not change
`eval-spec.md`, authorize B2 tuning on test or complete any P2 task.

**Actual token volume cannot yet be measured.** There is no `evals/data/`,
approved writer guide, judge prompt or B1/B2 output. Token counts also
depend on the selected tokenizer and generated reasoning. Any purported
exact observed token total now would be invented. This report gives exact
request counts under explicit execution assumptions and exact arithmetic
for a declared token envelope; actual tokenization must replace it before
the eventual run is authorized.

Counting assumptions:

- One call per report for each of G2, L1, R1 and S1. Code evaluators cost
  zero judge calls. S1 returns the binary vector for all guide rules in
  **one** call, not one call per rule.
- Three total dev judge-prompt versions/passes, including the final one;
  calibration uses the 20 dev cases for A/B1 only. B2 does not exist until
  after the judge/B2-change stages, so it cannot be a calibration dependency.
- Each dev pass also judges B1 versus A in both presentation orders.
- The frozen official run evaluates A/B1/B2 on all 40 cases, with U1
  comparing each B version against A in both orders. B2 dev results are
  evaluated by the already-frozen judge, not used to retune it.
- Both U1 orders are budgeted as position controls. Their aggregation and
  disagreement handling must be declared before the freeze; this research
  does not choose a new scoring rule.
- Request counts exclude writer generation/retries, access probes, provider
  errors and extra candidate-model calibration. Those are separate budgets.

| Work | Formula | Single-report calls | Pairwise calls | Total |
|---|---|---:|---:|---:|
| Official G2/L1/R1/S1 | 40 cases × 3 systems × 4 dimensions | 480 | 0 | 480 |
| Official U1 | 40 × 2 B-vs-A comparisons × 2 orders | 0 | 160 | 160 |
| One dev calibration pass | 20 × 2 systems × 4 dimensions, plus 20 × 2 orders | 160 | 40 | 200 |
| Three dev calibration passes | 3 × preceding row | 480 | 120 | 600 |
| **Conservative total before reuse/retries** | 640 + 600 | **960** | **280** | **1,240** |
| Reuse final dev A/B1 responses | subtract identical final-pass calls | −160 | −40 | −200 |
| **New requests with that reuse** | 1,240 − 200 | **800** | **240** | **1,040** |

Final-dev reuse is legitimate only when packet, report, ordered pair,
dimension/rubric, guide, judge model/endpoint, all generation settings and
prompt/schema versions are identical. Cache complete validated responses
locally by these hashes. Changing a prompt or model invalidates reuse.
No guaranteed provider prompt-cache hit is assumed here.

If “three iterations” means three revisions *after* an initial version,
add another 200 calls. Running S1 separately for each of `m` guide rules
would add `240 × (m − 1)` calls to the conservative ledger; that is not the
design counted here. Bundling all four dimensions into one request would
instead produce 520 calls before reuse or 440 after reuse, but changes the
judge protocol and couples the verdicts. Do not adopt bundling merely to
make a provider fit without calibration and owner agreement.

### Token envelope, including prompt and schema overhead

| Request class | Input budget | Total generated-token budget | Total/call |
|---|---:|---:|---:|
| Single report/dimension | 4,000 | 500 | 4,500 |
| U1 ordered pair | 5,500 | 500 | 6,000 |
| Daily G2, same single-report envelope | 4,000 | 500 | 4,500 |

Input includes the instructions, packet/evidence, report(s), guide material
needed by that dimension and output schema. The 500 generated tokens
include reasoning where the service counts it, not just final JSON.
These are planning caps, not measured averages or promises that S1 fits.
An output truncated by the cap is an invalid/missing evaluation, never a
pass. Do not truncate evidence to force a quota fit.

| Work | Input tokens | Generated tokens | Total tokens |
|---|---:|---:|---:|
| Official 640 calls | 2,800,000 | 320,000 | 3,120,000 |
| Three calibration passes, 600 calls | 2,580,000 | 300,000 | 2,880,000 |
| **1,240-call envelope** | **5,380,000** | **620,000** | **6,000,000** |
| **1,040 new calls after final-dev reuse** | **4,520,000** | **520,000** | **5,040,000** |
| Ten daily G2 calls | 40,000/day | 5,000/day | 45,000/day |
| Ten days of daily G2 | 400,000 | 50,000 | 450,000 |
| Conservative offline + ten monitoring days | 5,780,000 | 670,000 | 6,450,000 |

Formula for actual usage: sum the selected tokenizer's input count and
all generated tokens over each distinct report/dimension/prompt-version
and ordered-pair request. The eventual manifest must record measured
input/output/reasoning usage and retry counts. No inference/tokenizer API
was called for this research.

A 20% retry/invalid-output allowance makes the conservative offline budget
**1,488 attempts / 7.2M tokens**, plus monitoring. One retry for every call
would be 2,480 attempts / 12M tokens. These are capacity scenarios, not a
new judge-retry policy. D2's existing writer retry is a separate concern.
First-attempt scores remain the primary comparison; additional attempts
must not become a best-of selection that inflates the reported result.

Daily monitoring remains **G2 only** by judge under the approved eval plan;
judged R1/S1 and U1 remain offline. Ten calls/day is the owner's conservative
capacity allowance, not a claim that today's capped pipeline emits ten
reports. A no-games day invokes no judge. D17 records unavailable G2 as
`not_evaluated`; it cannot turn missing offline evidence into a pass.

## 2. Current quotas and capacity verdicts

`NR` means no public numeric promise found, not unlimited. `K/M` are
decimal quota units unless a model card explicitly says otherwise.
Account/organization quotas can be lower and shared with unrelated use.
“Fits” below concerns the declared envelope, not verified account access,
latency, uptime or judge quality.

| Provider / mechanism | RPM | RPD | TPM | TPD / other allowance | Verdict for ~10 days |
|---|---:|---:|---:|---|---|
| Cloudflare Workers Free, selected GLM/Qwen | 300 ordinary text; REST additionally 1,200 requests/5 min | NR | NR | 10,000 shared neurons/day, reset 00:00 UTC (19:00 Bogotá) | Both fit paced envelopes below |
| Groq Free, GPT-OSS120B/20B/Qwen3.8-27B | 30 | 1,000 | 8,000 combined; account may add separate input/output limits | 200,000 tokens/day | Fails 6M/5.04M offline token budget |
| OpenRouter free, no purchase | 20 | 50 across free models | NR; upstream limits also apply | NR | Fails 1,240/1,040 calls; daily ten fits |
| Mistral Free mode | RPS enforced, number NR | NR | Enforced, number NR; input + output | Monthly shared allowance, amount NR; per-org/model limits in account | Capacity/large-model entitlement unproven |
| Cerebras Free Trial | 5 | NR | 30,000 uncached / 90,000 total | 1M tokens/hour and 1M/day; $5 once, 30-day expiry, verified card | Can fit trial; fails renewable-$0 requirement |
| Hugging Face Inference Providers, Free user | NR | NR | NR | **No included monthly credits in current pricing page** | No verified $0 routed API budget |
| Z.ai direct `glm-4.7-flash` | NR, account page only | NR | NR | Token price Free; quantitative capacity NR | Promising pricing, 10-day fit unproven |
| NVIDIA hosted NIM prototype endpoint | NR | NR | NR | Trial API credits; current public numeric grant/renewal NR | No verified renewable budget/production entitlement |

Sources: [Cloudflare limits, updated Sep 17](https://developers.cloudflare.com/workers-ai/platform/limits/),
[REST limit, Aug 25](https://developers.cloudflare.com/fundamentals/api/reference/limits/),
[Cloudflare pricing, Oct 20](https://developers.cloudflare.com/workers-ai/platform/pricing/),
[Groq limits, undated](https://console.groq.com/docs/rate-limits),
[OpenRouter limits, undated](https://openrouter.ai/docs/api_reference/limits),
[Mistral usage/limits, undated](https://docs.mistral.ai/admin/billing-usage/usage-limits),
[Cerebras limits, undated](https://inference-docs.cerebras.ai/support/rate-limits),
[HF current pricing, undated](https://huggingface.co/docs/inference-providers/en/pricing),
[Z.ai pricing, undated](https://docs.z.ai/guides/overview/pricing),
[Z.ai account-limit FAQ, undated](https://docs.z.ai/help/faq),
[NVIDIA FAQ, updated approximately July 2026](https://docs.api.nvidia.com/nim/docs/faq).

### Cloudflare: practical $0 candidates

The two selected IDs are Cloudflare-hosted. Free operations stop at the
allocation; extra consumption requires changing to paid billing. Avoid
Paid activation and prepaid AI Gateway credits for this proposal.
Frontier Kimi K2.6/K2.7, GLM-5.2/5.3 and listed DeepSeek-V4 endpoints require
paid billing despite appearing in the catalog. The
[July 28 changelog](https://developers.cloudflare.com/changelog/post/2026-07-28-models-require-workers-paid/)
explicitly retains GLM-4.7-Flash on Free; current pricing identifies the
expanded paid-only list. Catalog presence alone is not proof of free access.

### Groq: good daily candidate, token-limited offline

At 200K TPD, 6M tokens require **30 quota-days**, or **39** when reserving
45K/day for ten G2 calls. Final-dev reuse reduces these to **26 / 33**.
A 4.5K/6K request fits individually inside 8K TPM; approximately one request
per minute is conservative. Cache hits may reduce rate usage, but exact
prefix matching/expiry and post-processing deduction make guaranteed
savings unsafe. Organization/project limits apply; use actual reset and
retry headers after owner-approved access. [Prompt caching](https://console.groq.com/docs/prompt-caching),
[projects](https://console.groq.com/docs/projects).

### OpenRouter: free daily monitoring, insufficient offline calls

The lower bounds are **25 days raw / 21 after reuse**, or **31 / 26** with
ten daily calls reserved. A $10 lifetime-credit purchase unlocks a higher
advertised daily quota but violates strict $0. Failed requests can consume
quota. Do not use `openrouter/free`: it selects models dynamically.
Pin model and upstream route; require supported parameters, otherwise
routing may ignore unsupported requirements.
[Free router](https://openrouter.ai/openrouter/free),
[provider selection](https://openrouter.ai/docs/guides/routing/provider-selection).

### Mistral: strongest-model possibility, missing capacity proof

Free mode explicitly enables API access without a card. However, the
largest model's free entitlement and actual monthly/per-model quotas are
not published. “1B/month”, “1 RPS” or unrestricted model access cannot be
assumed from old posts. New-account access would have to be approved and
inspected before a fit claim. Free use is shared across API/Studio/Vibe;
unused monthly capacity is not independently reserved for this evaluation.
[Activation guide](https://docs.mistral.ai/getting-started/quickstarts/studio/activate-and-generate-api-key),
[subscriptions](https://docs.mistral.ai/admin/billing-usage/subscriptions).

### Cerebras: trial fits, ongoing $0 does not

The current service explicitly says there is no automatically renewing
free allowance. Under GPT-OSS pricing $0.35/M input and $0.75/M output,
the conservative offline envelope costs **$2.348**; plus ten monitoring
days, **$2.5255**. Reuse costs **$1.972 / $2.1495**. These can fit the $5
trial, assuming *all* reasoning fits the output envelope, but access ends
after credit exhaustion/30 days without purchase. No card/account was
created. It is not the recommended primary or ongoing backup.
[Billing](https://inference-docs.cerebras.ai/console/account-billing),
[pricing](https://www.cerebras.ai/pricing).

### Hugging Face: stale free-tier claims rejected

The current fetched pricing table says **Free Users: None** for monthly
credits, with purchase or PRO required. Older indexed snippets still say
$0.10/month. This report uses the current page, not those snippets.
Even the older $0.10 would not fund the workload: 620K generated tokens
at DeepInfra GPT-OSS120B's $0.17/M output rate alone cost $0.1054, before
input. BYOK uses another provider's quota; it creates no new HF free tier.
[Current pricing](https://huggingface.co/docs/inference-providers/en/pricing),
[DeepInfra model price](https://deepinfra.com/openai/gpt-oss-120b).

### Additional verified leads: Z.ai and NVIDIA

Z.ai lists `glm-4.7-flash` and `glm-4.5-flash` at zero input/output price.
Its limit page redirects to the account console; public docs do not establish
RPM/RPD/TPM/TPD, model entitlement from Colombia or no-payment activation.
General chat docs omit Flash in the current model enum even while pricing
lists it: endpoint compatibility needs a later authorized check. Do not
mistake a GLM Coding Plan subscription or daily coding trial for this API.
[Pricing](https://docs.z.ai/guides/overview/pricing),
[chat reference](https://docs.z.ai/api-reference/llm/chat-completion).

NVIDIA's current `nvidia/nemotron-3-ultra-550b-a55b` page explicitly has an
available free prototype endpoint, 1M context. Its FAQ still describes
remote inference as consuming trial credits, without a current public
renewal or numeric grant. Older 2024 staff posts described 1,000 initial
credits/extra trial credits; that is historical, not today's entitlement.
GPT-OSS120B and Llama3.3-70B pages now mark their free endpoints deprecated.
This is a useful lead for model quality, not a certified recurring quota.
[Current Nemotron endpoint](https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b),
[current GPT-OSS endpoint](https://build.nvidia.com/openai/gpt-oss-120b),
[historical credit explanation, Sep 16, 2024](https://forums.developer.nvidia.com/t/api-credits-for-build-nvidia-com/306633).

## 3. Exact candidate IDs and output controls

Context is the hosted limit where published, not a model-family maximum.
Output maxima marked NR must be checked later; sample/default `max_tokens`
values are not hard maxima. Accepting temperature zero does not guarantee
determinism, and schema support does not establish factual correctness.

| Provider and exact ID | Family / scale | Context; max output | JSON / structured output; temperature zero |
|---|---|---|---|
| Cloudflare `@cf/zai-org/glm-4.7-flash` | Z.ai GLM; 30B/A3B MoE, smaller judge | 131,072; hosted hard output max NR | Object and schema; official schema has `strict`; temperature 0–2. Hard `enable_thinking:false` documented. |
| Cloudflare `@cf/qwen/qwen3-30b-a3b-fp8` | Alibaba Qwen3; 30B/~3B active, FP8, smaller judge | 32,768; hard output max NR, 2,000 is only default | Object/schema; separate strict switch NR; temperature 0–5. Host has no published hard thinking-off switch. |
| Groq `openai/gpt-oss-120b` | OpenAI GPT-OSS; 120B | 131,072; 65,536 | Strict schema/object supported; 0 converted to 1e-8. Reasoning low/medium/high, cannot assume it is disabled. |
| Groq `openai/gpt-oss-20b`; `qwen/qwen3.8-27b` | Smaller OpenAI 20B / Qwen 27B Preview | GPT 131,072/65,536; Qwen 131,072/16,384 | Strict schema/object; same zero conversion, same free token limits. No demonstrated judge upgrade. |
| OpenRouter `nvidia/nemotron-3.5-super-vl:free` | NVIDIA Nemotron3.5, MoE | 1,000,000; 131,072 | `response_format`/schema and temperature supported; zero within routing API range. Pin supporting upstream. |
| OpenRouter `nvidia/nemotron-3-ultra-550b-a55b:free` | NVIDIA Nemotron3 Ultra; ~550B/A55B, substantially larger | 1,000,000; 65,536 | Explicitly no `response_format`; temperature accepted. Weak fit for native structured judging. |
| Mistral `mistral-large-4` | Mistral Large4; 1.05T/A52B, Public Preview Oct 6 | 1M; output max NR | Structured schema/object published, zero supported; **Free entitlement unverified**. |
| Mistral `mistral-large-2512`; `mistral-medium-3-5` | Mistral GA alternatives; Large3 675B/A41B | 256K; output max NR | Structured schema/object, zero supported; Free entitlement/quota unverified. |
| Cerebras `gpt-oss-120b`; `qwen-3.8-27b` | OpenAI120B / smaller Qwen27B | Trial GPT65K/Qwen64K; max output NR | Object/strict schema; zero accepted (0–2). GPT reasoning cannot be disabled. Trial-only. |
| HF `moonshotai/Kimi-K3`; `zai-org/GLM-5.3`; `deepseek-ai/DeepSeek-V4-Pro` | Moonshot / Z.ai / DeepSeek frontier candidates | DeepInfra catalog routes 1,048,576; max output NR | Schema on particular routes; HF zero range 0–2, compatibility depends on route. **No included free credits.** |
| Z.ai direct `glm-4.7-flash` | Same GLM family/model class as primary, different hosting | Publisher 131,072; hosted Flash max unverified | General API object JSON, zero accepted; strict hosted Flash schema unverified. Not certified by generic GLM5 docs. |
| NVIDIA `nvidia/nemotron-3-ultra-550b-a55b` | NVIDIA Nemotron3 Ultra | Hosted catalog 1M; hard output max NR | Hosted strict-schema/zero guarantees unverified; examples use 1.0 and show thinking-off. Do not substitute self-hosted capabilities. |

Capability sources, all accessed Oct 24:
[Cloudflare GLM schema](https://raw.githubusercontent.com/cloudflare/cloudflare-docs/production/src/content/workers-ai-models/glm-4.7-flash.json),
[Cloudflare Qwen schema](https://raw.githubusercontent.com/cloudflare/cloudflare-docs/production/src/content/workers-ai-models/qwen3-30b-a3b-fp8.json),
[Groq model](https://console.groq.com/docs/model/openai/gpt-oss-120b),
[Groq Qwen](https://console.groq.com/docs/model/qwen/qwen3.8-27b),
[Groq structured output](https://console.groq.com/docs/structured-outputs),
[Groq zero conversion](https://console.groq.com/docs/openai),
[OpenRouter Super VL](https://openrouter.ai/nvidia/nemotron-3.5-super-vl:free/),
[OpenRouter Ultra](https://openrouter.ai/nvidia/nemotron-3-ultra-550b-a55b:free),
[OpenRouter parameters](https://openrouter.ai/docs/api_reference/parameters),
[Mistral Large4](https://docs.mistral.ai/models/mistral-large-4-0),
[Large3](https://docs.mistral.ai/models/mistral-large-3-25-12),
[Medium3.5](https://docs.mistral.ai/models/mistral-medium-3-5-26-04),
[Mistral structured output](https://docs.mistral.ai/studio/conversations/structured-output/custom),
[Cerebras catalog](https://inference-docs.cerebras.ai/models/overview),
[Cerebras schema](https://inference-docs.cerebras.ai/capabilities/structured-outputs),
[Cerebras API](https://inference-docs.cerebras.ai/api-reference/chat-completions),
[HF model routes](https://huggingface.co/inference/models),
[HF output guide](https://huggingface.co/docs/inference-providers/en/guides/structured-output),
[Z.ai API](https://docs.z.ai/api-reference/llm/chat-completion),
[NVIDIA model documentation](https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3-ultra-550b-a55b).

Cloudflare documentation has an inconsistency: the generic JSON-mode page
lists an older subset, while its model schemas and Oct 21 SDK guide expose
GLM schema outputs. Treat this as documented support requiring a later
small authorized probe, not a tested guarantee. JSON mode should be
non-streaming. Qwen's publisher warns against greedy decoding in thinking
mode; `/no_think` is a soft instruction, not an equivalent hard API switch.
Calibrate the exact settings to be frozen.
[JSON-mode guide, Sep 14](https://developers.cloudflare.com/workers-ai/features/json-mode/),
[SDK guide, Oct 21](https://developers.cloudflare.com/workers-ai/configuration/ai-sdk/),
[Qwen FP8 publisher card](https://huggingface.co/Qwen/Qwen3-30B-A3B-FP8).

## 4. Submitted-text terms and account/region restrictions

These are summaries of published terms, not a legal clearance. Account
signup from Colombia was not tested. No reviewed provider supplies a
general guarantee of Colombian free access; absence of an explicit
prohibition is not proof of eligibility. Export/sanctions and provider
acceptable-use rules still apply. Public MLB material remains subject to
D16; no employer/private data belongs in a request.

| Provider | Training, retention and relevant controls | Signup/region facts and unresolved limits |
|---|---|---|
| Cloudflare Workers AI | No Customer Content training. Standard stateless content retained only as needed to process/deliver; metadata and legal/security exceptions remain. Storage, batch/stateful features, app logs and AI Gateway logging/cache can retain content. No Free exception published. | Email/password and email verification documented; official workshop says no card for Free; phone step not listed. No Colombia-specific allowlist found. Account+authorized Cloudflare token needed later; no Z.ai/Qwen-provider key. |
| Groq | Services Agreement forbids training/fine-tuning without permission/instruction. Normally no retained inference content; abuse/reliability exceptions up to30 days or legal necessity. ZDR available to all orgs, with metadata retained. Provider prompt-cache policy remains separate. | Age18+; payment for upgrades. Explicit no-card/phone-free signup promise not found. Actual Colombia access untested; org/project quotas may differ. |
| OpenRouter + upstream | Router content logging/improvement is opt-in, with metadata/classification; upstream terms still apply. NVIDIA free banners permit security/product-improvement logging and prohibit confidential/personal content. Privacy filters may eliminate the free route. | No-card Free documented in official tutorial; phone verification NR; age18+, registration and upstream regional restrictions. Do not pay $10 to obtain a higher “free” quota under this proposal. |
| Mistral | Free GA data may train unless opted out in Admin Privacy. **Preview/Labs, including Large4, can train even when other opt-out/ZDR settings are enabled.** ZDR is PAYG-only; ordinary API abuse retention is described as30 rolling days, subject to applicable terms. | No card for Free documented. Phone and Colombia-specific eligibility NR. Studio/API terms differ from consumer chat; preview access is professional/commercial-customer only. EU default hosting is not a Colombia signup guarantee. |
| Cerebras | Terms exclude inference-content training; docs say request/response not retained. Usage/account/security records remain; no numeric general metadata retention maximum found. No trial training exception identified. | Verified payment method mandatory for trial access; accepted Colombian payment instruments NR. No renewable allowance after30 days; access stops without purchase. |
| HF routed inference | HF says no request/response content storage or training; debugging metadata up to30 days. Each downstream provider has separate terms; route must be pinned. | Free signup does not include current inference credit. Identity/account and provider/model licenses/regions apply; phone and Colombia access not verified. BYOK shifts payment/quota to another provider. |
| Z.ai direct | API DPA says request/generated content is processed in real time without server storage; other customer data may persist and generally processes in Singapore. Consumer improvement/training policy is different; do not apply it as the API policy. Exact free-API training assurance/eligibility needs confirmation. FAQ acknowledges prompt caching. | Pricing is Free for named Flash models, but new-account activation, phone/card and Colombia availability unverified. Quantitative quotas require account access; no account created. |
| NVIDIA NIM hosted | General terms grant content use for service/security/product improvement and restrict confidential, personal/sensitive and third-party-rights content. No numeric hosted-inference retention/opt-out promise verified here. Do not equate self-hosting control with hosted privacy. | Prototype/developer signup and API credits; no verified recurring quota, phone/card rule or Colombian eligibility. Do not assume current free prototype endpoint includes ongoing published-product use. |

Policy/access sources and published dates:

- Cloudflare [data policy, updated Oct 16, 2026](https://developers.cloudflare.com/workers-ai/platform/data-usage/),
  [signup, Sep 17](https://developers.cloudflare.com/fundamentals/account/create-account/),
  [official no-card workshop, undated](https://developers.cloudflare.com/labs/workers),
  [REST guide, Sep 15](https://developers.cloudflare.com/workers-ai/get-started/rest-api/),
  [agreement, current undated version](https://www.cloudflare.com/terms/).
- Groq [Services Agreement, June 22, 2026](https://console.groq.com/docs/legal/services-agreement),
  [data controls, undated](https://console.groq.com/docs/your-data).
- OpenRouter [data collection](https://openrouter.ai/docs/guides/privacy/data-collection),
  [upstream logging/training controls](https://openrouter.ai/docs/guides/privacy/provider-logging),
  [official Free/no-card tutorial](https://openrouter.ai/blog/tutorials/image-generation-models/),
  [terms, Aug 31, 2026](https://openrouter.ai/terms); model banners linked above.
- Mistral [Free training policy](https://help.mistral.ai/en/articles/347617-do-you-use-my-user-data-to-train-your-artificial-intelligence-models),
  [opt-out, Sep 3, 2026](https://help.mistral.ai/en/articles/455207-can-i-opt-out-of-my-input-or-output-data-being-used-for-training),
  [Commercial Terms §§4.2-4.3, Sep 25](https://legal.mistral.ai/terms/commercial-terms-of-service/),
  [ZDR, Aug 12](https://help.mistral.ai/en/articles/347612-can-i-activate-zero-data-retention-zdr),
  [privacy, Sep 3](https://legal.mistral.ai/terms/privacy-policy/),
  [hosting, Aug 12](https://help.mistral.ai/en/articles/347629-where-do-you-store-my-data-or-my-organization-s-data).
- Cerebras [terms, Aug 27, 2024](https://www.cerebras.ai/terms-of-service),
  [privacy, same date](https://www.cerebras.ai/privacy-policy),
  [retention support, undated](https://support.cerebras.net/articles/1811589793-does-cerebras-retain-my-data).
- HF [routing security](https://huggingface.co/docs/inference-providers/en/security),
  [account terms](https://huggingface.co/terms-of-service),
  [example downstream DeepInfra privacy](https://docs.deepinfra.com/account/data-privacy).
- Z.ai [API DPA/privacy, Sep 29, 2025](https://docs.z.ai/legal-agreement/privacy-policy),
  [terms/additional API terms, Apr 14, 2026](https://docs.z.ai/legal-agreement/terms-of-use),
  [cache/limits FAQ, undated](https://docs.z.ai/help/faq).
- NVIDIA [developer terms, updated Aug 20, 2026](https://developer.nvidia.com/legal/terms),
  [privacy](https://www.nvidia.com/en-us/about-nvidia/privacy-policy/),
  [current prototype/credit FAQ](https://docs.api.nvidia.com/nim/docs/faq).

## 5. Judge quality: evidence and limits

**GPT-OSS120B has direct public evaluator evidence.** AgentJudgeBench,
submitted Aug 27, 2026, tests structured tool workflows and reports it as
the most human-aligned judge in its human study. The same paper finds
hard settings without ground truth cluster around 77-82% across judges.
This is a different domain/protocol, not a forecast of PitchCraft agreement.
[Paper](https://arxiv.org/abs/2608.26623).
NVIDIA's Nemotron-Cascade research also uses GPT-OSS120B for answer
extraction/correctness judging; that is evidence of use, not validation of
fan prose or an 85% guarantee.
[Research report](https://research.nvidia.com/labs/nemotron/files/Nemotron-Cascade-2.pdf).

**The capacity-feasible candidates have weaker judge-specific evidence.**
The GLM publisher reports general reasoning/agent benchmarks for its
30B-A3B model; those do not test R1 or first-use jargon. The Qwen card
describes a 30B/~3B-active MoE; its size does not establish judge quality.
FP8 and the
Cloudflare-hosted context/settings also matter. No credible public
human-agreement result for these exact hosted endpoints on PitchCraft-like
grounding/style tasks was established by this survey.
[GLM publisher card](https://huggingface.co/zai-org/GLM-4.7-Flash),
[Qwen FP8 card](https://huggingface.co/Qwen/Qwen3-30B-A3B-FP8).

Judge-tuned derivatives of the Qwen30B base exist, but they are different
models, with specialized supervision and domain-specific limitations.
Their reported results cannot be attributed to the stock Cloudflare model.
[Example primary author card](https://huggingface.co/agcbench-2026/AGC-Judge).

Mistral Large4 is much larger and has strong publisher capability claims,
but its Oct 6 announcement is not judge-specific human calibration and
does not establish Free entitlement. Nemotron Ultra is also substantially
larger, but quota/output-format constraints remain.
[Large4 announcement](https://mistral.ai/news/mistral-large-4/),
[Nemotron technical report, June 4, 2026](https://research.nvidia.com/labs/nemotron/files/NVIDIA-Nemotron-3-Ultra-Technical-Report.pdf).

There is no defensible universal strongest-free-judge ranking in this
evidence. Prefer GPT-OSS120B if the owner later relaxes the time/token
constraint or verifies materially different free limits. Under the current
constraints, start with GLM because its documented strict schema and hard
thinking switch reduce operational uncertainty, then compare Qwen on dev
human labels if needed. This is an engineering judgment, not a benchmark
claim that GLM beats every alternative.

Calibration must include real semantic negatives: invented but plausible
injury/award/history, correct entity with unsupported claim, wrong starter's
evidence, omitted limitation, irrelevant true statement, unexplained jargon,
and asymmetric U1 position controls. Measure agreement/TPR/TNR separately
by dimension and S1 rule; do not substitute schema success or mostly-pass
class agreement for human trust. Do not use test examples to select a judge.

## 6. Pacing, completion time and the actual calendar

### Cloudflare arithmetic

Use the published neuron coefficients, not rounded displayed dollar
prices: GLM input/output **5,500/36,400 per million tokens**; Qwen
**4,625/30,475**. `neurons = input_tokens × input_coefficient / 1M +
generated_tokens × output_coefficient / 1M`.
[Official coefficients](https://developers.cloudflare.com/workers-ai/platform/pricing/).

| Item, exact under the token envelope | GLM-4.7-Flash | Qwen3-30B-A3B-FP8 |
|---|---:|---:|
| Single report | 40.2 neurons | 33.7375 neurons |
| U1 ordered pair | 48.45 | 40.675 |
| Conservative offline, 1,240 calls | 52,158 | 43,777 |
| Final-dev reuse, 1,040 new calls | 43,788 | 36,752 |
| Ten daily G2 calls | 402/day | 337.375/day |
| Conservative offline /10 + daily G2 | 5,617.8/day | 4,715.075/day |
| Offline with 20% attempt overhead /10 + G2 | 6,660.96/day | 5,590.615/day |

Both stay below 10,000/day when spread across ten available quota windows,
even with 20% overhead, assuming this envelope and no other account use.
Duplicating the baseline on both models consumes **10,332.875/day** with
monitoring and does not fit: they share one allocation.

For comparison, Cloudflare GPT-OSS120B's coefficients 31,818/68,182 produce
213,453.68 neurons for the conservative offline workload. With daily G2
reserved, that needs at least 26 quota windows, despite its larger size.
It is not a hidden ten-day alternative.

| Lower bound in quota windows, reserving ten G2/day | GLM | Qwen |
|---|---:|---:|
| Raw 1,240 calls, use full available 10K | 6 | 5 |
| Raw 1,240, voluntary 8K/day total operational cap | 7 | 6 |
| Reuse 1,040, full 10K | 5 | 4 |
| Raw plus 20% attempts, full 10K | 7 | 6 |
| Raw plus 20%, voluntary 8K cap | 9 | 7 |
| Reuse plus 20%, voluntary 8K cap | 7 | 6 |

These are resource lower bounds, not elapsed-time promises. At a deliberately
conservative one call/minute, raw inference requests take 20h40m of dispatch
slots; reuse 17h20m, plus latency/backoff. This is compatible with spreading
work across quota windows. A one/minute proposal is far below published
request ceilings, but throughput/availability has not been measured.

### Five late windows are tighter than a ten-day budget

The P2 calendar has labels Nov 4-6, judge freeze Nov 6 and B2 Nov 7-8.
Unspent October/early-November daily allocation cannot be banked. Assume
one 200-call dev pass on each of Nov 4/5/6, final-dev reuse, then the remaining
official 440 calls on Nov 7/8, only after the required freezes.

This is an optimistic quota illustration, **not a booked labeling schedule**:
the owner has not confirmed hours or that all 20 dev labels will be ready
on Nov 4. A judge pass may be captured before labels, but agreement cannot
be assessed and the next prompt chosen without the relevant human labels.

| Phase | GLM with G2 reserve | Qwen with G2 reserve |
|---|---:|---:|
| One dev pass/day, Nov 4-6 | 8,772/day | 7,362.375/day |
| Remaining official work /2 days, Nov 7-8 | 9,741/day | 8,175.875/day |
| Same official phase with 20% attempt overhead | 11,608.8/day: does not fit | 9,743.575/day: fits, little headroom |

GLM can meet Nov 8 at the baseline with final-dev reuse, but has little room
for retries and competing usage. Reserve Nov 9-10 contingency for a credible
primary schedule. Under an 8K/day total operational cap, reuse plus 20%
overhead needs roughly seven GLM quota windows or six Qwen windows after
usable labels begin. Human-label availability or writer delays can extend
that further; do not move the Nov 2 prose-boundary checkpoint silently.

If the complete calibration labels arrive only on Nov 6, the conservative
schedule changes materially. With exact-response reuse, 20% attempt
overhead, ten daily G2 calls and the proposed 8K total/day cap:

| First usable full-label window: Nov 6 | GLM | Qwen |
|---|---|---|
| Three total calibration versions + remaining official work | 7 quota windows, through Nov 12 | 6 quota windows, through Nov 11 |
| Two versions, only if agreement already meets every target | 6 quota windows, through Nov 11 | 5 quota windows, through Nov 10 |

Thus a late-label, three-version GLM run **misses the Nov 11 evidence cutoff**
at the proposed safety cap. Do not promise Nov 8 or use pre-label quota
as if it could be banked. If the third version is unnecessary because all
calibration targets are already met, omitting that optional pass saves
200 calls / 8,370 GLM or 7,025 Qwen neurons before retry overhead.
Otherwise the owner must accept a schedule change, consider the backup
before freezing, or explicitly authorize using more of the published
10K/day allowance: GLM reuse plus 20% needs six windows at that harder
ceiling, with less headroom. No option waives calibration or permits a
switch after test inspection. Writer/B2 preparation and human review take
additional time; these dates are quota lower bounds, not guaranteed delivery.

Doubling both input and generated-token sizes makes the raw GLM workload
plus daily G2 need at least 12 full quota windows. A retry for every call
needs at least 11 GLM windows under the original envelope. This is why
actual token measurement and a daily usage ledger are release prerequisites.

Proposed pacing after owner approval: one in-flight request, maximum one
dispatch/minute initially, local durable response cache, exact per-call
usage accounting, an 8K/day operational stop and explicit next-window resume
at 19:00 Bogotá. Schedule calibration before frozen test work, keep test
outputs sealed, and count failed attempts/selection probes/backup calls.
Pause on truncation, quota exhaustion, unexpected tokenizer growth or
model drift; never silently change models or strip evidence to resume.
No pacing code or account setting was implemented here.

## 7. Stability evidence and the frozen-judge rule

| Service | Dated official evidence | What it establishes |
|---|---|---|
| Cloudflare | [GA, Apr2,2024](https://blog.cloudflare.com/workers-ai-ga-huggingface-loras-python-support/); [model-access change, Jul28,2026](https://developers.cloudflare.com/changelog/post/2026-07-28-models-require-workers-paid/); current pricing Oct20 | Recurring allocation has historical precedent; model eligibility changes. Selected GLM remained Free in July, not a permanence guarantee. |
| Groq | [GPT-OSS launch, Aug5,2025, in changelog](https://console.groq.com/docs/changelog); current free table | Model history and current availability, not proof of uninterrupted quotas. |
| OpenRouter | [free-provider changes, Jul10,2025, updated Jun11,2026](https://openrouter.ai/blog/announcements/updates-to-our-free-tier-sustaining-accessible-ai-for-everyone/) | Provider subsidies/routes and free-model availability have changed. |
| Cerebras | [trial change Jul16,2026](https://inference-docs.cerebras.ai/support/change-log); [2026 deprecations](https://inference-docs.cerebras.ai/support/deprecation) | Earlier “free tier” advice is no longer current; trial/availability changed. |
| Mistral | [Devstral2 paid transition Jan27,2026, changelog](https://docs.mistral.ai/resources/changelogs); [lifecycle policy](https://docs.mistral.ai/inference/model-lifecycle) | Free/preview access and aliases can change; static-looking names are not an SLA. |
| HF | [current pricing and official document history](https://github.com/huggingface/hub-docs/commits/main/docs/inference-providers/pricing.md) | Old free-credit/search results conflict with current None. Exact removal date was not established here. |
| Z.ai / NVIDIA | Current zero-price/prototype pages; older trial-credit material | Present lead only; uninterrupted renewable capacity was not established. |

GitHub Models is the concrete warning for this project: its
[July30,2026 retirement](https://github.blog/changelog/2026-07-30-github-models-is-now-retired/)
removed inference, catalog, playground and BYOK for existing users as well.
D9/D17 are not edited by research. No provider promises permanent free
capacity, immutable hosted weights or an SLA established by this report.

The judge is frozen **before test inspection**: exact provider/route,
model ID, available version/fingerprint, quantization when disclosed,
temperature, thinking settings, prompt/schema/guide/evaluator versions,
and canonical inputs. Keep the same judge for all official A/B1/B2 scores.
Do not use the backup after seeing held-out failures to rescue the outcome.
If the hosted version becomes unavailable or changes materially, stop;
resumption as the same experiment requires evidence that the frozen
identity/settings remain valid, otherwise a separately approved new run.

Backup use is limited to selection/calibration **before** the freeze or
separately identified daily monitoring after owner approval. New-provider
calibration spends additional calls beyond the single-candidate ledger.
Never pool the backup's daily results into the frozen offline comparison;
log actual model/prompt/evaluator versions. D17 still means an unavailable
daily judge is `not_evaluated`, with code gates continuing publication.

## 8. Owner decision requested; implementation remains stopped

Approve or reject the proposed Cloudflare primary/backup for subsequent
access verification and dev calibration. Approval should explicitly accept
the smaller-model quality risk, shared quota/outage risk, stateless data
policy, token envelope pending measurement and the late-label schedule
risk above (a three-version GLM run at the 8K cap can extend to Nov 12).
Alternatively, authorize investigating Mistral's actual Free entitlement or
a longer GPT-OSS schedule. None of those actions is authorized by this report.

Only after a provider/model decision and credentials confirmation should
P2.1 perform its small access probes and exact quota/model checks. P2.4
remains unstarted. No account, key or provider change is made; no live data
or workflow is touched. The guide, actual packet sizes, judge calibration
and exact runtime configuration remain their later approved tasks.
