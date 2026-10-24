# CV extraction benchmark: OpenRouter `z-ai/glm-5.3-flashx`

Run on 2026-10-25 against a local backend (`CATALOG_MODE=cached`, `MATCHING_MODE=hussain`, `LLM_PROVIDER=openrouter`, `LLM_BASE_URL=https://openrouter.ai/api/v1`, `LLM_MODEL=z-ai/glm-5.3-flashx`, `LLM_API_KEY` from the environment). Every request went through `POST /api/v1/cv/parse`, the real endpoint the UI calls.

## Model check

`GET https://openrouter.ai/api/v1/models` lists `z-ai/glm-5.3-flashx` ("Z.ai: GLM 5.3 FlashX"), with `response_format` among its `supported_parameters`. It has one provider endpoint (Z.AI, fp8). Price: $0.37 per million input tokens and $1.25 per million output tokens.

## Request settings (openrouter path)

`temperature 0`, `response_format {"type": "json_object"}`, `reasoning {"effort": "low"}`, `max_tokens 2500`, timeout `LLM_TIMEOUT_SECONDS` (default 60 s). There is no `reasoning_effort` key; that one is sent only on the RunPod path.

Why reasoning control and a larger budget: the model always reasons before answering. With the original `max_tokens 1200` and no reasoning control, 1,112–1,184 of the 1,200 tokens went on reasoning, the reply stopped with `finish_reason: "length"`, and the JSON was cut off. Two direct calls both truncated, and one of the first two benchmark uploads fell back to manual review. With `reasoning.effort` low, one call used 79 reasoning tokens and finished in 3.0 s (`finish_reason: "stop"`). `reasoning {"enabled": false}` is rejected by the provider (HTTP 400). The backend now logs `GLM reply was cut off at max_tokens` whenever a reply stops at the limit.

## Test CVs

Five fictional people, each a one-page text PDF.

| CV | Field | Expected catalogue skills | Listed skills that are not in the catalogue |
|---|---|---|---|
| cv1_cs_data | Computer science / data | python, sql (PostgreSQL), data_visualization (Tableau), git (GitHub), javascript, excel (Microsoft Excel) | Docker |
| cv2_finance | Accounting / finance | excel (Advanced Excel), accounting_software (QuickBooks), vba, financial_analysis_software (Oracle Hyperion Financial Management), analytical_scientific_software (SAS), attention_to_detail | IFRS reporting |
| cv3_mech_cad | Mechanical / CAD | cad_software (SolidWorks, AutoCAD), matlab, python | Finite Element Analysis (ANSYS) |
| cv4_env_gis | Environmental / GIS | gis (ArcGIS, QGIS), python, excel, analytical_scientific_software (SPSS), science (Scientific Methods) | Remote sensing |
| cv5_short | Short retail CV | excel (Microsoft Excel) | customer service, teamwork |

## Results (3 runs per CV, 15 calls)

| CV | Latency min / median / max | Status | Truncated | Mapped (all runs) | Unmapped | Needs review | Missed | Wrong |
|---|---|---|---|---|---|---|---|---|
| cv1_cs_data | 1.77 / 2.46 / 2.80 s | 3/3 ok | 0 | python, sql, data_visualization, git, javascript, excel | Docker | none | 0 | 0 |
| cv2_finance | 2.25 / 2.31 / 11.67 s | 3/3 ok | 0 | excel, accounting_software, vba, financial_analysis_software, analytical_scientific_software, attention_to_detail | IFRS reporting | none | 0 | 0 |
| cv3_mech_cad | 2.10 / 2.14 / 2.25 s | 3/3 ok | 0 | cad_software, matlab, python | Finite Element Analysis (ANSYS) | none | 0 | 0 |
| cv4_env_gis | 2.01 / 2.25 / 2.61 s | 3/3 ok | 0 | gis, python, excel, analytical_scientific_software, science | Remote sensing | none | 0 | 0 |
| cv5_short | 1.37 / 1.53 / 1.69 s | 3/3 ok | 0 | excel | customer service, teamwork | none | 0 | 0 |

All 15 calls returned `ok`, with no truncation. Every expected skill was mapped in every run, no wrong skill was mapped, each non-catalogue skill landed in `unmapped_skills`, and the person's name was extracted every time. The runs gave identical results. Across all 15 calls the median latency was about 2.2 s; one outlier took 11.7 s.

**Confirm → match** (the first draft of each CV, with a level of study set, sent to `/profile/analyze` and then `/careers/match`): all returned 200 with `data_mode: "cached"`.

| CV | Top 3 matches |
|---|---|
| cv1_cs_data | software_developer 54, web_developer 53, computer_systems_analyst 49 |
| cv2_finance | financial_risk_specialist 65, financial_analyst 63, actuary 41 |
| cv3_mech_cad | mechanical_engineer 49, aerospace_engineer 45, electrical_engineer 45 |
| cv4_env_gis | environmental_scientist 55, public_health_analyst 51, hydrologist 50 |
| cv5_short | financial_analyst 13, financial_risk_specialist 13, logistician 12 |

## Failure cases

| Case | Result |
|---|---|
| `LLM_TIMEOUT_SECONDS=1` | `manual_review` after 1.04 s with the generic message and a 500-character text preview. Log: `GLM request timed out after 1s`. |
| Invalid `LLM_API_KEY` | HTTP 401 from OpenRouter → `manual_review` in 0.05 s. Log: `GLM request rejected: HTTP 401 (check LLM_API_KEY)`. The key value is not logged. |

No server log from these runs contains the API key.

## Provider data policy

From the Z.AI endpoint's `dataPolicy` embedded in https://openrouter.ai/z-ai/glm-5.3-flashx (fetched 2026-10-25): `training: false`, `trainingOpenRouter: false`, `retainsPrompts: false`, `canPublish: false`, `safetyRetention: false`. Provider headquarters and datacenter: Singapore. Provider terms: https://chat.z.ai/legal-agreement/terms-of-service. Privacy policy: https://chat.z.ai/legal-agreement/privacy-policy. CV text sent for extraction is therefore processed by Z.AI in Singapore. OpenRouter's own prompt-logging default comes from its account privacy settings and was not checked here.

## Cost

Total for this benchmark, including the diagnostic calls: $0.019 (from the key's usage counter). One CV extraction costs roughly $0.0007–0.0016.
