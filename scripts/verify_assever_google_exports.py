"""Verify deployed raw evidence with the standalone standard-library checker."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'outputs/assever-google-evidence/deployed'
spec=importlib.util.spec_from_file_location('independent_checker',ROOT/'packages/core/intentseal_core/purchase/checker.py')
checker=importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))


def main():
    campaign=E/'campaign'
    summary,manifest,rows=(read(campaign/n) for n in ('summary.json','manifest.json','results.json'))
    assert checker.hash_json(rows)==summary['rows_digest']
    assert checker.hash_json({k:v for k,v in manifest.items() if k!='digest'})==manifest['digest']==summary['manifest_digest']
    for name,value in manifest['source_snapshot'].items():
        assert hashlib.sha256((ROOT/'packages/core/intentseal_core/purchase'/name).read_bytes()).hexdigest()==value,name
    cells=0
    for p in campaign.glob('run_*.json'):
        r=read(p)['result'];assert checker.verify(r['bundle'])==r['verification'],p.name;cells+=1
    assert cells==720
    folder=E/'gemini-final-study'
    protocol,summary,rows=(read(folder/n) for n in ('protocol.json','summary.json','results.json'))
    assert checker.hash_json({k:v for k,v in protocol.items() if k!='digest'})==protocol['digest']==summary['protocol_digest']
    assert checker.hash_json(rows)==summary['rows_digest']
    for name,value in {**protocol['backend_snapshot'],**protocol['configuration_snapshot']}.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==value,name
    # The executed study runner is archived alongside its evidence, independently of later harness fixes.
    runner=E/'scripts/assever_google_study.py'
    assert hashlib.sha256(runner.read_bytes()).hexdigest()==protocol['study_script_sha256']
    expected=[(m,t[0],s,mode) for m in protocol['models'] for t in protocol['tasks'] for s in protocol['seeds'] for mode in protocol['modes']]
    assert len(rows)==240==len(expected)
    requests,responses,valid,paired,bundles=0,0,0,0,0
    errors=[]
    per_control={}
    for index,(row,wanted) in enumerate(zip(rows,expected),1):
        assert (row['model'],row['task'],row['seed'],row['mode'])==wanted
        r=read(folder/f'modelrun_{index:03}.json')
        invocation=r.get('invocation')
        if invocation:
            requests+=1
            assert invocation['provider']=='vertex' and invocation['sdk']=='google-genai'
            assert checker.hash_json(invocation['request'])==invocation['request_digest']
            assert invocation['request']['options']['seed']==r['seed']
            responses+=bool(invocation.get('raw_response'))
            valid+=isinstance(invocation.get('plan'),dict)
        if r.get('error'):
            errors.append({'index':index,'model':r['model'],'task':r['task'],'mode':r['mode'],'recorded_error':r['error'],
                           'provider_error':(invocation or {}).get('error')})
        controls=r['controls']
        if 'adaptive' in controls and 'payment' in controls:paired+=1
        for name,result in controls.items():
            assert checker.verify(result['bundle'])==result['verification'],(index,name)
            if name=='adaptive':
                assert result['bundle']['manifest']['integrated']
                assert result['bundle']['work_order']['binding']['workflow']==result['workflow_id']
            per_control[name]=per_control.get(name,0)+1;bundles+=1
    assert requests==summary['actual_invocations']
    assert len(errors)==summary['errors']
    assert all(per_control.get(k,0)==v['replays'] for k,v in summary['controls'].items())
    proof={'planned_workflow_attempts':240,'recorded_vertex_requests':requests,'captured_vertex_responses':responses,
           'valid_typed_model_plans':valid,'matched_successful_proposals':paired,'live_effect_bundles':bundles,
           'core_conformance_bundles':cells,'total_verified_bundles':cells+bundles,'source_and_digest_checks':True,
           'all_saved_verdicts_agree':True,'errors_retained':errors,
           'denominator_note':'Failed requests and missing reference replays remain visible; no retries or imputed proposals.'}
    (E.parent/'offline-verification.json').write_text(json.dumps(proof,indent=2))
    print(json.dumps(proof,indent=2))


if __name__=='__main__':main()
