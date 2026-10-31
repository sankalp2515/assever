import json
import time
from pathlib import Path

import httpx
from assever.client import AgentClient
from assever_http_smoke import session,approved,post


def main():
    with session() as human:
        contract=approved(human)
        agent=post(human,"/agents",{})
        grant=post(human,"/grants",{"root_id":contract["id"],"actor_id":agent["actor_id"],"demand_lines":[x["id"] for x in contract["demand_lines"]],"operations":["propose","commit"],"expires_at":time.time()+3600})
        client=AgentClient("http://localhost:8088",agent["agent_token"])
        try:
            r=client.http.post(f"/v1/contracts/{contract['id']}/revoke",json={"expected_epoch":1,"reason":"synthetic agent self-approval test"})
            assert r.status_code==403
            operation=client.purchase(contract["id"],grant["id"])
            for _ in range(50):
                state=client.call("GET","/operations/"+operation["id"])
                if state["state"]=="CONFIRMED":break
                time.sleep(.2)
            assert state["state"]=="CONFIRMED"
            try:
                client.purchase(contract["id"],grant["id"])
                raise AssertionError("Duplicate basket was admitted")
            except httpx.HTTPStatusError as exc:
                assert exc.response.status_code==409
            evidence=human.get(f"/v1/contracts/{contract['id']}/evidence").json()
            assert evidence["verification"]["task_complete"]
            result={"external_agent_client":True,"agent_cannot_revoke":True,"duplicate_refused":True,"verification":evidence["verification"],"root_id":contract["id"],"operation_id":operation["id"]}
            Path("outputs/assever-evidence/sdk-integration.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
            print(json.dumps(result))
        finally:client.close()


if __name__=="__main__":main()
