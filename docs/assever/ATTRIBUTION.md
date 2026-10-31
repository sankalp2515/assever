# Attribution and AI assistance

Assever is licensed under the repository's Apache-2.0 LICENSE. Existing NOTICE, copyright statements and internal compatibility identifiers are retained. The local source tree arrived without Git metadata; the evidence records file hashes rather than inventing commit IDs. The owner must verify the precise development dates and any team-specific external-code declaration before submission.

## Application dependencies

The integrated edition retains Assever's Protect AI DeBERTa prompt-injection classifier and RapidOCR/ONNX extraction path. The classifier's upstream model card identifies Apache-2.0 and English-only coverage: https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2 . It is an existing content-screening layer, not the purchase authority. Schibsted Grotesk, Newsreader and Fragment Mono are locally hosted with their upstream SIL OFL licenses in `apps/console/public/fonts`; source URLs accompany the assets. No claim of broad non-English classifier coverage follows from Hindi structured labels.

| Component | Role | License reference |
|---|---|---|
| Python | Runtime | PSF license, https://docs.python.org/3/license.html |
| FastAPI, Starlette, Pydantic | API and strict DTOs | MIT, respective upstream distributions |
| psycopg / psycopg_pool | PostgreSQL transaction/pool driver | LGPL-3.0, https://www.psycopg.org/license/ |
| PostgreSQL 16.4 | Ledger and independent effect storage | PostgreSQL License, https://www.postgresql.org/about/licence/ |
| HTTPX | HTTP clients | BSD-3-Clause, https://github.com/encode/httpx/blob/master/LICENSE.md |
| React, TypeScript, Vite | Console | MIT, upstream distributions |
| pytest | Regression tests | MIT, https://docs.pytest.org/en/stable/license.html |
| PyJWT | Optional offline ES256 envelope fixtures | MIT, https://github.com/jpadilla/pyjwt/blob/master/LICENSE |
| cryptography | P-256 signature verification | Apache-2.0 OR BSD-3-Clause, https://cryptography.io/en/latest/faq/#what-license-is-cryptography-distributed-under |
| Ollama 0.40.13 | Local inference | MIT, https://github.com/ollama/ollama/blob/main/LICENSE |
| Qwen2.5 0.5B / Qwen3 0.6B | Live study proposals | Apache-2.0 distribution pages linked in LOCAL_MODELS.md |
| ReportLab, pypdf, pdfplumber | Local report authoring/QA only | BSD / BSD-3-Clause / MIT, upstream distributions |
| @oai/artifact-tool | Backlog workbook authoring only | Bundled authoring runtime; not shipped as application dependency |

Exact installed Python package/version/license metadata and frontend lockfile records accompany the release evidence. The source archive contains no model weights, paid provider credentials or unlicensed third-party datasets. All commerce records and attack messages are authored synthetic fixtures.

## AI assistance record

Codex (GPT-6 family; the exact serving model identifier is not exposed to this chat) assisted with research synthesis, product planning, implementation, tests, documentation and report/workbook generation. The user supplied earlier ChatGPT-authored planning documents; their exact model versions were not supplied. They are planning inputs, not implemented capabilities or measured results.

The runtime's default three-role planner is deterministic. Actual local Qwen model runs are explicitly labeled, store their exact artifact digests/settings/prompts/responses, and are counted separately from scripted fault injection. Invalid output, inference errors and unsuccessful tasks remain in study denominators. No model output signs or activates human authority. AI-produced claims are checked against executable tests and independent effect records.

## Prior work and contribution

AP2's mandate binding and constraint model, Grantex's shared atomic wallet governance, and literature on capabilities, transactions, idempotency, prompt injection and safe retry are acknowledged antecedents. The contribution is this finite executable purchase profile, integrated durable enforcement, independent effect reconstruction and measured comparison. Authored controls do not establish defects in those products. See the research decision and exact AP2 projection scope for source links and limits.
