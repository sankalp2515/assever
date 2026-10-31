"""Recover lost client responses from durable model/effect records, never re-infer.

Original per-attempt files and transport failures remain immutable. A separately
identified capture addendum supplies recoverable invocation/output/effect records.
Any matched payment reference missing because the HTTP response was lost runs
once against that recorded proposal. This is post-collection evidence recovery,
not an extra model invocation or replacement of an unsuccessful model response.
"""
from pathlib import Path
from collections import Counter
import argparse
import json
import shutil
from intentseal_core.purchase.common import db, digest, now, uid
from intentseal_core.purchase import service
from intentseal_core.purchase.live_study import execute_plan
from intentseal_core.purchase.checker import verify


def read(path):return json.loads(path.read_text())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--directory',default='/tmp/integrated-live-study');args=parser.parse_args()
    folder=Path(args.directory)
    raw=sorted(folder.glob('modelrun_*.json'))
    assert len(raw)==240,'Finish all scheduled attempts before capture recovery'
    entries=[read(p) for p in raw]
    first=next(e for e in entries if 'adaptive' in e['controls'])['controls']['adaptive']['bundle']['contract']
    owner={'tenant':first['tenant'],'actor':first['owner'],'role':'human','allow_lab':False}
    with db() as c:
        workflows=c.execute('''SELECT w.id,b.root FROM public.delegate_workflows w
            JOIN public.delegate_principals p ON p.workflow_id=w.id
            JOIN workflow_bindings b ON b.workflow=w.id
            WHERE p.principal=%s ORDER BY w.created,w.id''',(owner['actor'],)).fetchall()
    assert len(workflows)==240,'The study owner must have exactly the frozen 240 workflows'
    for entry,workflow in zip(entries,workflows):
        if 'adaptive' in entry['controls']:
            assert entry['controls']['adaptive']['workflow_id']==workflow['id']
    recovery=folder/'capture-recovery';recovery.mkdir(exist_ok=True)
    captured=[]
    for entry,workflow in zip(entries,workflows):
        if entry.get('invocation') and len(entry['controls'])==2:continue
        target=recovery/f"recovered_{entry['index']:03}.json"
        if target.exists():
            supplemental=read(target)
        else:
            with db() as c:
                runs=c.execute("SELECT * FROM model_runs WHERE tenant=%s AND manifest->>'root_id'=%s ORDER BY created",(owner['tenant'],workflow['root'])).fetchall()
            if len(runs)!=1 or not runs[0]['result'].get('invocation',{}).get('plan'):
                continue  # Missing or failed inference remains missing/failed, never guessed.
            run=runs[0];invocation=run['result']['invocation']
            assert run['manifest']['model_id']==entry['model'] and run['manifest']['seed']==entry['seed']
            assert invocation['request_digest']==digest(invocation['request'])
            adaptive=service.evidence(workflow['root'],owner)
            assert verify(adaptive['bundle'])==adaptive['verification']
            reference_owner={'tenant':uid('capture-reference'),'actor':uid('capture-reference-owner'),'role':'human'}
            payment=execute_plan(invocation,reference_owner,'payment')
            supplemental={'index':entry['index'],'original_transport_error':entry['error'],'runtime_model_record':run,
                          'invocation':invocation,'captured_at':now(),'new_model_invocations':0,
                          'controls':{'adaptive':{'workflow_id':workflow['id'],**adaptive},'payment':payment},
                          'method':'Join the sequential frozen study owner workflows; validate all successful original workflow IDs, exact model/seed/root and request digest. Recover the already persisted output and original effect evidence. Run the missing authored payment replay once on that saved plan.'}
            target.write_text(json.dumps(supplemental,indent=2))
        captured.append(supplemental)
    for name in ('summary.json','results.json'):
        prior=folder/('before_capture_recovery_'+name)
        if not prior.exists():shutil.copy2(folder/name,prior)
    rows=read(folder/'before_capture_recovery_results.json')
    mapped={e['index']:e for e in captured}
    for row in rows:
        supplemental=mapped.get(row['index'])
        if supplemental:
            row['capture_recovery']=f"capture-recovery/recovered_{row['index']:03}.json"
            row['controls']={key:{'verification':value['verification']} for key,value in supplemental['controls'].items()}
            # The error field is deliberately retained.
    summary=read(folder/'before_capture_recovery_summary.json')
    summary['actual_invocations']=sum(bool(e.get('invocation')) for e in entries)+sum(not entries[e['index']-1].get('invocation') for e in captured)
    summary['transport_errors_retained']=sum(bool(e['error']) for e in entries)
    summary['recovered_transport_captures']=len(captured)
    summary['capture_recovery_new_model_invocations']=0
    summary['capture_note']='Original failed transport records remain. Durable server outputs/effects and separately labeled missing reference replays were recovered without another model call.'
    summary['controls']={}
    for control in ('payment','adaptive'):
        records=[r['controls'][control]['verification'] for r in rows if control in r['controls']]
        summary['controls'][control]={'replays':len(records),'verdicts':dict(Counter(v['verdict'] for v in records)),
                                     'completed_tasks':sum(v['task_complete'] for v in records)}
    summary['rows_digest']=digest(rows)
    (folder/'results.json').write_text(json.dumps(rows,indent=2))
    (folder/'summary.json').write_text(json.dumps(summary,indent=2))
    (recovery/'ADDENDUM.json').write_text(json.dumps({'recovered_cases':list(mapped),'new_model_invocations':0,'original_errors_retained':True,
        'method':'Post-collection durable-output/effect capture. Not preplanned replacement sampling. Original protocol/attempts remain intact.',
        'supplemental_files':[f"recovered_{i:03}.json" for i in mapped]},indent=2))
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
