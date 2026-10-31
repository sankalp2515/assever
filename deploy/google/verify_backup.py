"""Quiesce only the owned cloud stack and compare full restored table fingerprints."""
from datetime import datetime, timezone
import json
import re
import subprocess
from pathlib import Path

BASE=['docker','compose','-f','/opt/assever/compose.cloud.json']
PG='assever-cloud-postgres-1'


def run(args,**kwargs):return subprocess.run(args,check=True,**kwargs)


def query(database,sql):
    return run(['docker','exec',PG,'psql','-U','localdbadmin','-d',database,'-Atc',sql],capture_output=True,text=True).stdout.strip().splitlines()


def main():
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    out=Path('/srv/assever/backups')/stamp
    out.mkdir(parents=True,mode=0o700)
    apps=['gateway','worker','evaluator','effects']
    run(BASE+['stop']+apps)
    proof=[]
    try:
        for database in ('intentseal','purchase_effects'):
            dump=out/(database+'.dump')
            with dump.open('wb') as f:run(['docker','exec',PG,'pg_dump','-U','localdbadmin','-Fc',database],stdout=f)
            restored='verify_'+database+'_'+stamp
            run(['docker','exec',PG,'createdb','-U','localdbadmin',restored])
            with dump.open('rb') as f:run(['docker','exec','-i',PG,'pg_restore','-U','localdbadmin','-d',restored],stdin=f)
            tables=query(database,"SELECT schemaname||'.'||tablename FROM pg_tables WHERE schemaname IN ('public','purchase','purchase_effects') ORDER BY 1")
            assert all(re.fullmatch(r'[a-z_][a-z_0-9]*\.[a-z_][a-z_0-9]*',t) for t in tables)
            sql=' UNION ALL '.join("SELECT '"+t+"',count(*)::text||':'||coalesce(md5(string_agg(row_to_json(t)::text,',' ORDER BY row_to_json(t)::text)),'empty') FROM "+t+' t' for t in tables)
            # UNION ALL does not promise branch order, particularly after restore changes plans.
            source=sorted(query(database,sql));copy=sorted(query(restored,sql))
            if source!=copy:
                Path('/srv/assever/evidence/backup-mismatch-'+stamp+'.json').write_text(
                    json.dumps({'database':database,'source':source,'restored':copy},indent=2))
            assert source==copy
            proof.extend({'database':database,'table':a.split('|')[0],'fingerprint':a.split('|')[1],'match':True} for a in source)
        evidence=Path('/srv/assever/evidence/backup-verification.json')
        evidence.write_text(json.dumps({'timestamp':stamp,'tables':proof,'tables_verified':len(proof),'dump_files_published':False},indent=2))
        print('Cloud backup/restore verified:',len(proof),'tables')
    finally:run(BASE+['up','--wait','--wait-timeout','600','-d']+apps)


if __name__=='__main__':main()
