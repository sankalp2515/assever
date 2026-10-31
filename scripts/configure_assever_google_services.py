"""Configure owned Google screening/audit resources without exposing tokens."""
import ast
import json
import shutil
import subprocess
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[1]


def main():
    gc=shutil.which('gcloud.cmd') or shutil.which('gcloud')
    token=subprocess.run([gc,'auth','print-access-token','--project=assever'],capture_output=True,text=True,check=True).stdout.strip()
    headers={'Authorization':'Bearer '+token,'x-goog-user-project':'assever'}
    proof={}
    with httpx.Client(headers=headers,timeout=90) as c:
        base='https://modelarmor.us-central1.rep.googleapis.com/v1/projects/assever/locations/us-central1/templates'
        r=c.get(base+'/assever')
        if r.status_code==404:
            r=c.post(base,params={'templateId':'assever'},json={'filterConfig':{
                'piAndJailbreakFilterSettings':{'filterEnforcement':'ENABLED','confidenceLevel':'MEDIUM_AND_ABOVE'},
                'maliciousUriFilterSettings':{'filterEnforcement':'ENABLED'},
                'sdpSettings':{'basicConfig':{'filterEnforcement':'ENABLED'}}}})
        if r.status_code>=400: raise RuntimeError('Model Armor '+str(r.status_code)+' '+r.text[:1200])
        proof['model_armor']=r.json()['name']
        bq='https://bigquery.googleapis.com/bigquery/v2/projects/assever/datasets'
        r=c.get(bq+'/assever_audit')
        if r.status_code==404:
            r=c.post(bq,json={'datasetReference':{'projectId':'assever','datasetId':'assever_audit'},'location':'US',
                             'access':[{'role':'OWNER','specialGroup':'projectOwners'},
                                       {'role':'WRITER','userByEmail':'assever-runtime@assever.iam.gserviceaccount.com'}]})
        if r.status_code>=400: raise RuntimeError('BigQuery dataset '+str(r.status_code)+' '+r.text[:1000])
        tree=ast.parse((ROOT/'packages/core/intentseal_core/delegate/bigquery.py').read_text())
        schema=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SCHEMA' for t in n.targets))
        tables=bq+'/assever_audit/tables'
        r=c.get(tables+'/receipts')
        if r.status_code==404:
            r=c.post(tables,json={'tableReference':{'projectId':'assever','datasetId':'assever_audit','tableId':'receipts'},
                'schema':{'fields':[{'name':n,'type':t} for n,t in schema]},'timePartitioning':{'type':'DAY','field':'created'},
                'clustering':{'fields':['principal','decision']}})
        if r.status_code>=400: raise RuntimeError('BigQuery table '+str(r.status_code)+' '+r.text[:1000])
        proof['bigquery']='assever.assever_audit.receipts'
    subprocess.run([gc,'projects','add-iam-policy-binding','assever','--project=assever',
        '--member=serviceAccount:assever-runtime@assever.iam.gserviceaccount.com','--role=roles/bigquery.jobUser','--condition=None','--quiet'],capture_output=True,text=True,check=True)
    out=ROOT/'outputs/assever-google-evidence';out.mkdir(exist_ok=True,parents=True)
    (out/'google-services.json').write_text(json.dumps(proof,indent=2))
    print(json.dumps(proof))


if __name__=='__main__':main()
