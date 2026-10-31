"""Run final deployed suites in order; preserve every log and stop on failure."""
import json
import subprocess
from pathlib import Path

BASE=['docker','compose','-f','/opt/assever/compose.cloud.json']
OUT=Path('/srv/assever/evidence')
URL='https://assever-872171487489.us-central1.run.app'


def main():
    original="""import os
os.environ['INTENTSEAL_TEST_DATABASE_URL']=os.environ['DATABASE_URL']
os.environ.update(PURCHASE_ENABLED='0',INTENTSEAL_DATABASE_URL='',INTENTSEAL_DB_PATH=':memory:',INTENTSEAL_STORE_PREVIEWS='1',GOOGLE_CLOUD_PROJECT='',GOOGLE_GENAI_USE_VERTEXAI='0')
import pytest
raise SystemExit(pytest.main(['tests','--ignore=tests/purchase','-q','-p','no:cacheprovider']))
"""
    commands=[('foundation-final',BASE+['exec','-T','gateway','python','-c',original]),
              ('purchase-final',BASE+['exec','-T','-e','INTEGRATED_URL='+URL,'evaluator','python','-m','pytest','tests/purchase','-q','-p','no:cacheprovider']),
              ('performance-final',BASE+['exec','-T','-e','INTEGRATED_URL='+URL,'evaluator','python','/evidence/scripts/assever_google_performance.py'])]
    proof=[]
    for label,args in commands:
        with (OUT/(label+'.log')).open('wb') as stream:
            p=subprocess.run(args,stdout=stream,stderr=subprocess.STDOUT)
        proof.append({'step':label,'exit_code':p.returncode,'log':label+'.log'})
        (OUT/'qualification.json').write_text(json.dumps(proof,indent=2))
        if p.returncode:raise SystemExit(p.returncode)
    print('Deployed regression, integration and timing qualification completed.')


if __name__=='__main__':main()
