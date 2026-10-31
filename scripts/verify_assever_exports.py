"""Recompute every saved conformance verdict using the offline checker."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("offline_checker",ROOT/"services/assever/assever/checker.py")
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)


def main():
    folder=ROOT/"outputs/assever-evidence/final/campaign"
    summary=json.loads((folder/"summary.json").read_text())
    manifest=json.loads((folder/"manifest.json").read_text())
    rows=json.loads((folder/"results.json").read_text())
    assert checker.hash_json(rows)==summary["rows_digest"]
    assert checker.hash_json({k:v for k,v in manifest.items() if k!="digest"})==manifest["digest"]==summary["manifest_digest"]
    for file,expected in manifest["source_snapshot"].items():
        assert hashlib.sha256((ROOT/"services/assever/assever"/file).read_bytes()).hexdigest()==expected,file
    count=0
    for source in folder.glob("run_*.json"):
        result=json.loads(source.read_text())["result"]
        computed=checker.verify(result["bundle"])
        assert computed==result["verification"],(source.name,computed,result["verification"])
        if result["checks"] and any("rehashed_omission_verdict" in x for x in result["checks"]):
            assert all(x["rehashed_omission_verdict"]["verdict"]=="FAIL" for x in result["checks"] if "rehashed_omission_verdict" in x)
        count+=1
    assert count==summary["cells"]==720
    live_folder=ROOT/"outputs/assever-evidence/final/live-study"
    live_count=0
    if live_folder.exists():
        live_summary=json.loads((live_folder/"summary.json").read_text())
        live_rows=json.loads((live_folder/"results.json").read_text())
        assert checker.hash_json(live_rows)==live_summary["rows_digest"]
        for source in live_folder.glob("modelrun_*.json"):
            entry=json.loads(source.read_text())
            invocation=entry.get("invocation")
            if invocation:
                assert checker.hash_json(invocation["request"])==invocation["request_digest"]
                assert invocation["request"]["options"]["seed"]==entry["seed"]
            for replay in entry["controls"].values():
                assert checker.verify(replay["bundle"])==replay["verification"],source.name
                live_count+=1
        assert live_count==480
    ablation_count=0
    for source in (ROOT/"outputs/assever-evidence/final/ablations").glob("*-*.json"):
        entry=json.loads(source.read_text())
        result=entry["run"]["result"]
        assert checker.verify(result["bundle"])==result["verification"]
        ablation_count+=1
    assert ablation_count==20
    result={"exports_rechecked":count+live_count+ablation_count,"conformance":count,"live_matched_replays":live_count,"instrumented_ablations":ablation_count,"all_verdicts_agree":True,"source_snapshot_agrees":True,"row_and_manifest_digests_agree":True,"checker_dependencies":"Python standard library only"}
    (ROOT/"outputs/assever-evidence/offline-verification.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result))


if __name__=="__main__":main()
