"""Real HTTP rehearsals, tenant isolation and twenty-client admission measurements."""
import json
import platform
import os
import statistics
import time
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

BASE=os.environ.get("ASSEVER_BASE_URL","http://localhost:8088")
OUT=Path(os.environ.get("ASSEVER_EVIDENCE_DIR","outputs/assever-evidence"))
OUT.mkdir(parents=True,exist_ok=True)


@contextmanager
def session():
    c=httpx.Client(base_url=BASE,timeout=30,trust_env=False,limits=httpx.Limits(max_connections=30,max_keepalive_connections=30))
    s=c.post("/v1/sessions",json={});s.raise_for_status();c.headers["X-CSRF-Token"]=s.json()["csrf"]
    try:
        yield c
    finally:
        c.close()


def post(c,path,body):
    r=c.post("/v1"+path,json=body);r.raise_for_status();return r.json()


def approved(c):
    d=post(c,"/contracts/drafts",{"request_text":"Buy 1 x 5 kg rice and 2 x 1 L oil up to INR1500"})
    return post(c,f"/contracts/{d['id']}/approve",{"version":1,"hash":d["digest"],"accepted_fields":d["scope"],"human_confirmation_nonce":d["human_confirmation_nonce"]})


def preview(c,d):
    q=post(c,"/quotes",{"root_id":d["id"],"merchant_id":"supplier_a"})
    lines=[{"demand_line_id":next(x["id"] for x in d["demand_lines"] if x["name"]==name),"sku":sku,"quantity":qty,"unit":unit} for name,sku,qty,unit in [("rice","RICE_5KG_A",1,"pack"),("oil","OIL_1L_A",2,"bottle")]]
    p=post(c,"/proposals",{"root_id":d["id"],"merchant_id":"supplier_a","checkout_ref":q["body"]["id"],"lines":lines,"total_paise":70000,"delivery_ref":"shop_01"})
    return post(c,f"/proposals/{p['id']}/prepare",{"expected_contract_version":1,"proposal_digest":p["digest"]})


def main():
    records=[]
    with session() as c:
        for index in range(3):
            d=approved(c)
            post(c,f"/contracts/{d['id']}/agent-purchase",{"root_id":d["id"],"merchant_id":"supplier_a"})
            for _ in range(50):
                state=c.get(f"/v1/contracts/{d['id']}").json()
                if state["money"]["captured"]==70000:break
                time.sleep(.2)
            assert state["money"]["captured"]==70000
            r=c.post(f"/v1/contracts/{d['id']}/agent-purchase",json={"root_id":d["id"],"merchant_id":"supplier_a"})
            assert r.status_code==409 and r.json()["code"]=="DEMAND_ALREADY_ENCUMBERED"
            evidence=c.get(f"/v1/contracts/{d['id']}/evidence").json()
            assert evidence["verification"]["task_complete"] and evidence["verification"]["orders"]==1
            (OUT/f"rehearsal-{index+1}.json").write_text(json.dumps(evidence,indent=2),encoding="utf-8")
            with session() as other:
                for suffix in ("","/evidence","/events"):
                    assert other.get(f"/v1/contracts/{d['id']}"+suffix).status_code==404
            assert c.get("/v1/session").status_code==200
            records.append({"rehearsal":index+1,"root_id":d["id"],"verdict":evidence["verification"],"two_visitor_isolation":True})
    with session() as c:
        items=[preview(c,approved(c)) for _ in range(20)]
        def admission(op):
            started=time.perf_counter()
            r=c.post(f"/v1/operations/{op['id']}/commit",json={"prepared_digest":op["digest"]})
            duration=(time.perf_counter()-started)*1000
            assert r.status_code==202,(r.status_code,r.text)
            return {"http_ms":duration,**r.json().get("timings",{})}
        with ThreadPoolExecutor(max_workers=20) as pool:
            measurements=list(pool.map(admission,items))
    timings=sorted(x["http_ms"] for x in measurements)
    result={"rehearsals":records,"performance":{"clients":20,"requests":20,"mode":"20 independent preprepared roots, concurrent HTTP commits; provider/model execution excluded, readiness included","host":platform.platform(),"docker_host_cpus":8,"docker_host_memory_gib":15.54,"background_campaign":"May be running; record contention rather than infer isolated-host SLA","p50_ms":round(statistics.median(timings),2),"p95_ms":round(timings[18],2),"samples_ms":timings,"prd_target_ms":100,"target_met_this_measurement":timings[18]<=100}}
    for field in ("core_admission_ms","provider_readiness_ms"):
        values=sorted(x[field] for x in measurements if field in x)
        if values:result["performance"][field]={"samples":len(values),"p50":round(statistics.median(values),3),"p95":round(values[18],3)}
    (OUT/"http-rehearsal-performance.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__=="__main__":main()
