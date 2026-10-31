"""Operational controls on the owned VM; no secrets are included in output."""
import json
import subprocess
import sys
import zipfile
from pathlib import Path

BASE=['docker','compose','-f','/opt/assever/compose.cloud.json']
E=Path('/srv/assever/evidence')


def run(args, **kwargs):
    return subprocess.run(args,check=True,**kwargs)


def main():
    action=sys.argv[1]
    if action=='stop-study':
        code="""import os,signal
for p in os.listdir('/proc'):
 if p.isdigit() and int(p)!=os.getpid():
  try:
   cmd=open('/proc/'+p+'/cmdline','rb').read()
   if b'/evidence/scripts/assever_google_study.py' in cmd and b'python' in cmd: os.kill(int(p),signal.SIGINT)
  except (OSError,ProcessLookupError):pass
"""
        run(BASE+['exec','-T','evaluator','python','-c',code])
    elif action=='progress':
        for folder in ('gemini-live-study','campaign','gemini-final-study','campaign-final'):
            p=E/folder
            if not p.exists():continue
            summary=p/'summary.json'
            print(folder,summary.read_text() if summary.exists() else json.dumps({'saved_models':len(list(p.glob('modelrun_*.json'))),'saved_cells':len(list(p.glob('run_*.json')))}))
    elif action=='start-study':
        with (E/'gemini-final-study.log').open('wb') as stream:
            p=subprocess.Popen(BASE+['exec','-T','-e','INTEGRATED_URL=https://assever-872171487489.us-central1.run.app','evaluator','python','/evidence/scripts/assever_google_study.py','--output','/evidence/gemini-final-study'],stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        print('Frozen Gemini study launched; host process',p.pid)
    elif action=='capture':
        target=Path('/tmp/assever-google-evidence.zip')
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in E.rglob('*'):
                if p.is_file() and p.suffix not in ('.dump','.pyc') and '__pycache__' not in p.parts:
                    z.write(p,p.relative_to(E))
        print('Evidence archive bytes',target.stat().st_size)
    elif action=='upgrade':
        before=E/'performance-before-task-list-fix'
        if (E/'google-performance').exists() and not before.exists():
            (E/'google-performance').rename(before)
            for label in ('qualification.json','foundation-final.log','purchase-final.log','performance-final.log'):
                item=E/label
                if item.exists():item.rename(E/('before-task-list-fix-'+label))
        path=Path('/opt/assever/compose.cloud.json')
        cfg=json.loads(path.read_text())
        image='us-central1-docker.pkg.dev/assever/assever/runtime@sha256:7cfb83d1deba3a0b703038c1886bf62b842d9697fbc0d19c3512d85ec7dc574c'
        for name in ('gateway','worker','effects','evaluator'):cfg['services'][name]['image']=image
        path.write_text(json.dumps(cfg,indent=2))
        run(BASE+['pull'])
        run(BASE+['up','--wait','--wait-timeout','600','-d'])
        (E/'runtime-image.json').write_text(json.dumps({'image':image,'release':'1.2.4'},indent=2))
    else:raise ValueError('Unknown operation')


if __name__=='__main__':main()
