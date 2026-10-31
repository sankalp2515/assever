# Local model setup

The model-free product does not require this optional inference service. The research study uses two small local models, not a hosted frontier model.

```powershell
docker run -d --name assever-models --network assever_ledger -p 127.0.0.1:11435:11434 -v assever-models:/root/.ollama --memory=3g --cpus=3 --security-opt=no-new-privileges:true ollama/ollama:0.40.13
docker exec assever-models ollama pull qwen2.5:0.5b
docker exec assever-models ollama pull qwen3:0.6b
docker compose -f compose.assever.yml exec -T api python -m assever.live_study --freeze-only --output /tmp/live-study
docker compose -f compose.assever.yml exec -T api python -m assever.live_study --output /tmp/live-study
python scripts/assever_capture.py assever-api-1 /tmp/live-study outputs/assever-evidence/final
```

Create the product stack first, so the `assever_ledger` network exists. If the named model container already exists, start it rather than creating another: `docker start assever-models`. The model service is local inference, not application deployment. Its loopback port is for diagnosis and may be omitted if only the API needs access.

The API uses `http://assever-models:11434`; `OLLAMA_URL` can override that explicitly. The operator can run a chosen model against an approved purchase in Connect an agent. The recorded model plan remains untrusted, and scoped checkout agents still propose through the ledger. A model cannot activate a draft or change approval.

Qwen2.5 0.5B and Qwen3 0.6B distribution pages identify Apache-2.0 model licenses. Exact artifact digests, runtime version, prompts, schemas and settings are captured in study outputs. Sources: https://ollama.com/library/qwen2.5:0.5b and https://ollama.com/library/qwen3:0.6b . API documentation: https://docs.ollama.com/api/chat . Runtime release: https://github.com/ollama/ollama/releases/tag/v0.40.13 .
