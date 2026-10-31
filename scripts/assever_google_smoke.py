"""Real HTTPS -> Vertex SDK -> original work order -> worker -> effect evidence."""
import json
import time
from pathlib import Path
import httpx
from intentseal_core.purchase.checker import verify

BASE='https://assever-872171487489.us-central1.run.app'
OUT=Path(__file__).resolve().parents[1]/'outputs/assever-google-evidence/smoke'


def checked(r):
    assert r.status_code in (200,201,202),(r.status_code,r.text[:500])
    return r.json()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    with httpx.Client(base_url=BASE,timeout=240) as c:
        checked(c.get('/readyz'))
        c.headers['Authorization']='Bearer '+checked(c.post('/v1/trial-keys'))['key']
        for model in ('gemini-3.5-flash','gemini-3.1-flash-lite'):
            wf=checked(c.post('/v1/delegations',json={'request':'Buy 1 x 5 kg rice and 2 x 1 L oil up to INR 1500, from supplier A or B; share only shop name and delivery address.','workspace':'kirana','owner':'Google deployment evaluator'}))['workflow']['id']
            d=checked(c.post(f'/v1/delegations/{wf}/purchase'))
            checked(c.post(f"/v1/purchases/contracts/{d['id']}/approve",json={'version':d['version'],'hash':d['digest'],'accepted_fields':d['scope'],'human_confirmation_nonce':d['human_confirmation_nonce']}))
            run=checked(c.post(f"/v1/purchases/contracts/{d['id']}/model-purchase",json={'model_id':model,'seller_text':'Supplier A has the approved basket in stock; deliver exactly once to shop_01.','seed':101}))
            (OUT/(model+'-invocation.json')).write_text(json.dumps(run,indent=2))
            assert not run['result']['error'],run['result']['error']
            invocation=run['result']['invocation']
            assert invocation['provider']=='vertex' and invocation['sdk']=='google-genai'
            end=time.monotonic()+45
            while time.monotonic()<end:
                state=checked(c.get(f"/v1/purchases/contracts/{d['id']}"))
                if not any(o['state'] in ('RESERVED','DISPATCHING') for o in state['operations']):break
                time.sleep(.2)
            bundle=checked(c.get(f"/v1/purchases/contracts/{d['id']}/evidence"))
            (OUT/(model+'-evidence.json')).write_text(json.dumps(bundle,indent=2))
            verdict=verify(bundle['bundle'])
            assert verdict==bundle['verification'] and verdict['verdict']=='PASS' and verdict['task_complete'],verdict
            report=checked(c.get(f'/v1/delegations/{wf}/report'))
            assert report['chain_ok']
            (OUT/(model+'-report.json')).write_text(json.dumps(report,indent=2))
            print(json.dumps({'model':model,'version':invocation['model_version'],'sdk_version':invocation['sdk_version'],'workflow':wf,'verification':verdict}),flush=True)


if __name__=='__main__':main()
