"""Provision the explicitly authorized assever project; never print secret values."""
import json
import secrets
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GCLOUD = shutil.which('gcloud.cmd') or shutil.which('gcloud')
PROJECT, REGION, ZONE = 'assever', 'us-central1', 'us-central1-a'


def gc(*args, data=None, capture=False):
    p = subprocess.run([GCLOUD, *args, '--project='+PROJECT, '--quiet'], input=data,
                       text=True, capture_output=True)
    if p.returncode:
        raise RuntimeError('gcloud '+args[0]+' '+args[1]+': '+p.stderr[:1800])
    if not capture and p.stderr: print(p.stderr.strip(), flush=True)
    return p.stdout.strip()


def exists(*args):
    return bool(gc(*args, '--format=value(name)', capture=True))


def main():
    for account in ('assever-runtime', 'assever-edge'):
        if not exists('iam','service-accounts','list','--filter=email:'+account+'@'):
            gc('iam','service-accounts','create',account,'--display-name='+account)
    runtime = 'assever-runtime@assever.iam.gserviceaccount.com'
    for role in ('roles/aiplatform.user', 'roles/modelarmor.user', 'roles/logging.logWriter', 'roles/monitoring.metricWriter'):
        gc('projects','add-iam-policy-binding',PROJECT,'--member=serviceAccount:'+runtime,'--role='+role,'--condition=None')
    if not exists('artifacts','repositories','list','--location='+REGION,'--filter=name:assever'):
        gc('artifacts','repositories','create','assever','--repository-format=docker','--location='+REGION)
    gc('artifacts','repositories','add-iam-policy-binding','assever','--location='+REGION,
       '--member=serviceAccount:'+runtime,'--role=roles/artifactregistry.reader')
    if not exists('secrets','list','--filter=name:assever-runtime-config'):
        cfg = {k: secrets.token_hex(32) for k in ('db_admin','db_app','db_effects','service','dispatch','observer','callback','issuer','lab','handoff','project_key','agent_key','admin_key')}
        cfg['public_key'] = 'assever-public-readonly'
        gc('secrets','create','assever-runtime-config','--replication-policy=automatic','--data-file=-',data=json.dumps(cfg))
    gc('secrets','add-iam-policy-binding','assever-runtime-config','--member=serviceAccount:'+runtime,'--role=roles/secretmanager.secretAccessor')
    if not exists('compute','networks','list','--filter=name=assever'):
        gc('compute','networks','create','assever','--subnet-mode=custom')
    if not exists('compute','networks','subnets','list','--filter=name=assever-runtime'):
        gc('compute','networks','subnets','create','assever-runtime','--network=assever','--region='+REGION,'--range=10.61.0.0/24','--enable-private-ip-google-access')
    for name, source, port in [('assever-iap-ssh','35.235.240.0/20','22'),('assever-private-gateway','10.61.0.0/24','8000')]:
        if not exists('compute','firewall-rules','list','--filter=name='+name):
            gc('compute','firewall-rules','create',name,'--network=assever','--allow=tcp:'+port,'--source-ranges='+source,'--target-tags=assever-runtime')
    if not exists('compute','disks','list','--filter=name=assever-data'):
        gc('compute','disks','create','assever-data','--zone='+ZONE,'--type=pd-balanced','--size=30GB')
    if not exists('compute','instances','list','--filter=name=assever-runtime'):
        gc('compute','instances','create','assever-runtime','--zone='+ZONE,'--machine-type=e2-custom-4-8192',
           '--image-family=debian-12','--image-project=debian-cloud','--boot-disk-size=50GB','--boot-disk-type=pd-balanced',
           '--network=assever','--subnet=assever-runtime','--private-network-ip=10.61.0.10','--tags=assever-runtime',
           '--service-account='+runtime,'--scopes=cloud-platform',
           '--disk=name=assever-data,device-name=assever-data,mode=rw,boot=no,auto-delete=no',
           '--metadata=enable-oslogin=TRUE,block-project-ssh-keys=TRUE',
           '--metadata-from-file=startup-script='+str(ROOT/'deploy/google/startup.sh'))
    out = ROOT/'outputs/assever-google-evidence'
    out.mkdir(parents=True,exist_ok=True)
    (out/'provisioned.json').write_text(json.dumps({'project':PROJECT,'region':REGION,'zone':ZONE,'runtime_service_account':runtime,'machine':'e2-custom-4-8192','private_ip':'10.61.0.10','database':'PostgreSQL on dedicated persistent disk; separate non-superuser application/effect roles','public_endpoint':'Cloud Run HTTPS edge; private runtime gateway'},indent=2))
    print('Google runtime provisioned; secret values were not printed.',flush=True)


if __name__ == '__main__': main()
