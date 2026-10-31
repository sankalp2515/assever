"""Standard-library-only verification of the integrated release's frozen evidence."""

from pathlib import Path
import hashlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "outputs/assever-integrated-evidence"
spec = importlib.util.spec_from_file_location("independent_checker", ROOT / "packages/core/intentseal_core/purchase/checker.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    folder = EVIDENCE / "final/integrated-campaign"
    summary, manifest, rows = (read(folder / name) for name in ["summary.json", "manifest.json", "results.json"])
    assert checker.hash_json(rows) == summary["rows_digest"]
    assert (
        checker.hash_json({k: v for k, v in manifest.items() if k != "digest"})
        == manifest["digest"]
        == summary["manifest_digest"]
    )
    for name, digest in manifest["source_snapshot"].items():
        assert hashlib.sha256((ROOT / "packages/core/intentseal_core/purchase" / name).read_bytes()).hexdigest() == digest, name
    count = 0
    for file in folder.glob("run_*.json"):
        result = read(file)["result"]
        assert checker.verify(result["bundle"]) == result["verification"], file.name
        count += 1
    assert count == 720
    ablations = 0
    for file in (EVIDENCE / "final/ablations").glob("*-*.json"):
        record = read(file)["run"]["result"]
        assert checker.verify(record["bundle"]) == record["verification"], file.name
        ablations += 1
    assert ablations == 20
    live = EVIDENCE / "final/integrated-live-study"
    actual, replays, linked = 0, 0, 0
    if live.exists():
        protocol, live_summary, live_rows = (read(live / name) for name in ["protocol.json", "summary.json", "results.json"])
        assert (
            checker.hash_json({k: v for k, v in protocol.items() if k != "digest"})
            == protocol["digest"]
            == live_summary["protocol_digest"]
        )
        assert checker.hash_json(live_rows) == live_summary["rows_digest"]
        for name, expected in {**protocol["backend_snapshot"], **protocol["configuration_snapshot"]}.items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
        assert (
            hashlib.sha256((ROOT / "scripts/assever_integrated_study.py").read_bytes()).hexdigest()
            == protocol["study_script_sha256"]
        )
        for file in live.glob("modelrun_*.json"):
            record = read(file)
            invocation = record.get("invocation")
            if invocation:
                actual += 1
                assert checker.hash_json(invocation["request"]) == invocation["request_digest"]
                assert invocation["request"]["options"]["seed"] == record["seed"]
            for control, result in record["controls"].items():
                assert checker.verify(result["bundle"]) == result["verification"], file.name
                if control == "adaptive":
                    assert (
                        result["bundle"]["manifest"]["integrated"]
                        and result["bundle"]["work_order"]["binding"]["workflow"] == result["workflow_id"]
                    )
                    linked += 1
                replays += 1
        assert actual == live_summary["actual_invocations"]
        assert len(live_rows) == live_summary["rows"] == 240
        assert linked == live_summary["controls"]["adaptive"]["replays"]
        assert replays == sum(r["replays"] for r in live_summary["controls"].values())
        assert actual + live_summary["errors"] == 240
    result = {
        "conformance_bundles": count,
        "instrumented_ablation_bundles": ablations,
        "actual_live_model_invocations": actual,
        "matched_live_replay_bundles": replays,
        "gateway_workflow_bundles": linked,
        "total_bundles": count + ablations + replays,
        "source_and_manifest_hashes_agree": True,
        "all_saved_verdicts_agree": True,
        "checker_dependencies": "Python standard library only",
        "full_live_study_present": live.exists(),
    }
    (EVIDENCE / "offline-verification.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
