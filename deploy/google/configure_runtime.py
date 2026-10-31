"""Runs as root on the owned VM; fetch credentials using its workload identity."""
import base64
import json
import os
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path('/opt/assever')


def request(url, token=None):
    headers = {'Authorization': 'Bearer '+token} if token else {'Metadata-Flavor': 'Google'}
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=40) as response:
        return json.load(response)


def main():
    os.umask(0o077)
    token = request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token')['access_token']
    raw = request('https://secretmanager.googleapis.com/v1/projects/assever/secrets/assever-runtime-config/versions/latest:access', token)
    cfg = json.loads(base64.b64decode(raw['payload']['data']))
    data = json.loads((ROOT/'base-compose.json').read_text())
    services = data['services']
    for name in list(services):
        if name in ('models', 'agents'): del services[name]
    for name,s in services.items():
        if name != 'postgres':
            s['image'] = 'us-central1-docker.pkg.dev/assever/assever/runtime@sha256:7cfb83d1deba3a0b703038c1886bf62b842d9697fbc0d19c3512d85ec7dc574c'
            s.pop('build',None)
        s.pop('profiles',None)
        if name == 'postgres':
            s['environment']['POSTGRES_PASSWORD'] = cfg['db_admin']
            s['volumes'] = ['/srv/assever/postgres:/var/lib/postgresql/data',str(ROOT/'init-purchase.sql')+':/docker-entrypoint-initdb.d/01-purchase.sql:ro']
        if name == 'gateway':
            s['ports'] = ['10.61.0.10:8000:8000']
            s['volumes'] = ['/srv/assever/gateway:/data']
        env = s.get('environment',{})
        for key in ('DATABASE_URL','INTENTSEAL_DATABASE_URL'):
            if key in env:
                env[key] = ('postgresql://purchase_effects:'+cfg['db_effects']+'@postgres:5432/purchase_effects' if name=='effects'
                            else 'postgresql://intentseal_app:'+cfg['db_app']+'@postgres:5432/intentseal')
        for key, value in {'SERVICE_KEY':'service','DISPATCH_KEY':'dispatch','OBSERVER_KEY':'observer','CALLBACK_KEY':'callback','ISSUER_KEY_V1':'issuer','LAB_KEY':'lab'}.items():
            if key in env: env[key] = cfg[value]
        if name in ('gateway','evaluator'):
            env.update({'GOOGLE_CLOUD_PROJECT':'assever','GOOGLE_CLOUD_QUOTA_PROJECT':'assever','GOOGLE_CLOUD_LOCATION':'global','GOOGLE_GENAI_USE_VERTEXAI':'true','INTENTSEAL_DELEGATE_AGENT_MODEL':'gemini-3.5-flash',
                        'INTENTSEAL_MODEL_ARMOR_TEMPLATE':'projects/assever/locations/us-central1/templates/assever',
                        'INTENTSEAL_BIGQUERY_DATASET':'assever_audit'})
        if name=='gateway':
            env.update({'INTENTSEAL_API_KEYS':f"owner:{cfg['project_key']}:project,reviewer:{cfg['admin_key']}:admin,agent:{cfg['agent_key']}:agent",
                        'INTENTSEAL_PUBLIC_KEY':cfg['public_key'],'INTENTSEAL_DELEGATE_SECRET':cfg['handoff'],
                        'INTENTSEAL_TRUSTED_PROXIES':'10.61.0.0/24','INTENTSEAL_TRIAL_PER_HOUR':'500'})
        if name in ('gateway','evaluator'):
            s.setdefault('volumes',[]).append('/srv/assever/evidence:/evidence')
        s.pop('memswap_limit',None)
    data['name']='assever-cloud'
    data.pop('volumes',None)
    for network in data.get('networks',{}).values(): network.pop('name',None)
    (ROOT/'compose.cloud.json').write_text(json.dumps(data,indent=2))
    # The generated SQL contains only random hex passwords. The containing host directory is private.
    sql=(ROOT/'init-template.sql').read_text().replace('synthetic-local-only',cfg['db_app']).replace('synthetic-effects-local-only',cfg['db_effects'])
    (ROOT/'init-purchase.sql').write_text(sql)
    os.chmod(ROOT/'init-purchase.sql',0o644)
    subprocess.run(['docker','login','-u','oauth2accesstoken','--password-stdin','https://us-central1-docker.pkg.dev'],input=token,text=True,check=True,stdout=subprocess.DEVNULL)
    print('Runtime credentials loaded from Secret Manager; no service-account key files.')


if __name__ == '__main__': main()
