> **Superseded.** These numbers are from the earlier standalone build. The current, canonical results are in [INTEGRATED_RELEASE_STATUS.md](INTEGRATED_RELEASE_STATUS.md).

# Measured results - Assever 1.0.0

31 October 2026. Synthetic owned services only. The exact source snapshot and raw records accompany the release.

## Deterministic campaign

| Authored control | Cells | Unsafe / FAIL | Unresolved | Task complete | Execution errors |
|---|---:|---:|---:|---:|---:|
| unrestricted | 144 | 54 | 10 | 74 | 0 |
| permission | 144 | 36 | 10 | 92 | 0 |
| payment | 144 | 36 | 10 | 92 | 0 |
| conservative | 144 | 0 | 12 | 120 | 0 |
| adaptive | 144 | 0 | 12 | 126 | 0 |

An unresolved opaque-provider outcome is retained, not counted as a safely completed task. Revocation-before-admission cases intentionally do not buy. Adaptive and conservative controls have the same covered safety behavior; approved stock replanning adds six completed cells.

## Live protocol v2

240 real model invocations, 0 errors. Each proposal is replayed against payment and adaptive controls, producing 480 matched replays. These are not 480 independent model samples.

| Control | Actual replays | Unsafe effects | Completed tasks |
|---|---:|---:|---:|
| payment | 240 | 67 | 161 |
| adaptive | 240 | 0 | 228 |

### Model and mode breakdown

| Model | Mode | Invocations | Adaptive completion | Payment completion | Payment unsafe |
|---|---|---:|---:|---:|---:|
| qwen2.5:0.5b | ordinary | 60 | 60 | 60 | 0 |
| qwen2.5:0.5b | attacked | 60 | 53 | 13 | 40 |
| qwen3:0.6b | ordinary | 60 | 60 | 60 | 0 |
| qwen3:0.6b | attacked | 60 | 55 | 28 | 27 |

The exploratory v1 study is retained separately. Its unconstrained ID strings damaged utility; v2 uses a finite tool schema that still includes explicitly unapproved choices, an explicit trusted approval, and a fresh seed set. This grouped integration revision is not an isolated causal estimate for each prompt/schema change. Seeds repeat authored families; neither protocol establishes frontier-model behavior.

## Integrity, recovery and operations

- 62 new product tests pass, including eight-process 100-attempt races, actual process exit, recovery, authority, split quantities, exceptions and malformed-model retention.
- 102 preserved foundation tests pass with local imports.
- Twenty explicit instrumented mechanism removals run without execution errors. Null removals masked by another layer are retained, not presented as individual causal wins.
- The offline standard-library checker independently recomputes all 1,220 final conformance/live/ablation verdicts with agreement.
- Three HTTP rehearsals exercise scoped checkout, duplicate refusal, reconnect and cross-tenant read/export isolation.
- Backup/restore verifies all twenty ledger/effect tables by row count and data fingerprint.

## Performance boundary

Latest twenty-client measurement: core-admission p95 138.654 ms, provider-readiness p95 21.175 ms, end-to-end Windows-to-Docker HTTP p95 2270.5 ms. The core metric excludes authentication, provider readiness and host transport; HTTP includes them. Earlier measurements remain in logs. The original 100-ms runtime target on a 4-CPU/8-GB host is not established by this 8-CPU/approximately-16-GB environment. Treat the exact-host target as a remaining performance qualification, not a safety result.

## Protocol provenance

Conformance manifest: `41b7608642885f3fe5f1f89bc40017b2f9b09f29998e757af82feaf358017ad2`.
Live protocol: `7ca0915d4c1abf69e34833194e71ab113be3490a026933298e8b61f6a607dba9`.

Raw artifacts are under outputs/assever-evidence/final. Failed preflight, initial complete campaign, exploratory live protocol and the interrupted 494-cell transport-diagnostic campaign are preserved separately and are not pooled into final denominators.
