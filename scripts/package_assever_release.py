"""Create reviewable source/evidence archives without local credentials or stores."""
import hashlib
import json
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/01a18ed2-2209-7780-8a49-0f2b07180b67/Assever_Release'
PLAN = OUT.parent / 'Assever'
BLOCKED = {'.git', '.venv', 'node_modules', '__pycache__', '.pytest_cache', '.ruff_cache', 'dist', '.next', 'data', '.playwright-cli', '_work'}
PATTERNS = {'google_api_key': r'(?<![A-Za-z0-9_-])AIza[0-9A-Za-z_-]{35}', 'github_token': r'(?<![A-Za-z0-9_-])gh[pousr]_[A-Za-z0-9]{30,}', 'openai_key': r'(?<![A-Za-z0-9_-])sk-(?:proj-)?[A-Za-z0-9_-]{40,}'}


def allowed(path):
    return not any(p in BLOCKED for p in path.parts) and not path.name.startswith('.env') and path.suffix not in {'.pyc', '.pyo', '.dump', '.db', '.sqlite', '.tar', '.tsbuildinfo'}


def archive(target, paths):
    manifest = {}
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(set(paths)):
            if not path.is_file() or not allowed(path.relative_to(ROOT)):
                continue
            name = path.relative_to(ROOT).as_posix()
            raw = path.read_bytes()
            for label, pattern in PATTERNS.items():
                if re.search(pattern.encode(), raw):
                    raise ValueError(f'Credential-like content requires review: {name} ({label})')
            z.writestr(name, raw)
            manifest[name] = hashlib.sha256(raw).hexdigest()
        z.writestr('FILE_SHA256.json', json.dumps(manifest, indent=2))
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for name, digest in manifest.items():
            assert hashlib.sha256(z.read(name)).hexdigest() == digest
    return {'file': target.name, 'entries': len(manifest), 'bytes': target.stat().st_size, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name in ('Assever_Backlog.json', 'Assever_Backlog.csv'):
        shutil.copy2(PLAN / name, OUT / name)
    for name in ('Assever_PRD.md', 'Assever_PRD.pdf', 'Assever_Naming_Decision.md'):
        shutil.copy2(ROOT / 'prd_outputs/Assever' / name, OUT / name)
    readme = '''# Assever 1.0.0 — local implementation release

Open http://localhost:8088 on this workstation. The API, worker, independent synthetic effect service and PostgreSQL are running in Docker; optional local Qwen models are installed.

## Contents

- Assever_Source_v1.0.0.zip: executable source, locks, Docker configuration, tests, SDK, documentation and attribution. Extract into a new directory and run `docker compose -f compose.assever.yml up --build --wait -d` from its root. Docker must have available memory and nonconflicting configured subnets.
- Assever_Evidence_v1.0.0.zip: raw frozen final campaign, real local-model invocations and matched replays, ablations, earlier exploratory runs, independent verification, test logs and browser evidence. Extract at the source root to restore `outputs/assever-evidence`; run `python scripts/verify_assever_exports.py` using the standard library. Browser images are review artifacts, not a demo video.
- Assever_Report_Draft.pdf: seven-page template-aligned report; owner fields are explicitly pending.
- Assever_Backlog.xlsx / JSON / CSV: all 121 original items reconciled: 107 Done, 11 Excluded, 3 Partial. Evidence links use source-root paths. Original estimates are not elapsed hours.
- Assever_PRD.* and naming decision: planning baseline. Current implementation scope and measured behavior are defined by docs/assever/SCOPE_AMENDMENT.md, RELEASE_STATUS.md, RESULTS.md and KNOWN_BOUNDARIES.md in the source archive.

## Verified release

62 purchase-product tests, 102 foundation regression tests and 8 console tests pass. The authored conformance campaign contains 720 cells. The live study contains 240 actual model invocations and 480 matched control replays; adaptive enforcement has zero unsafe-effect verdicts and completes 228/240 tasks. All 1,220 final evidence bundles agree with the independent checker. These are bounded synthetic evaluations; unresolved outcomes and exploratory failures remain in the evidence.

The latest twenty-client core-admission p95 is 138.654 ms, measured separately from provider readiness and HTTP transport. Exact qualification on the PRD's 4-CPU/8-GB target remains open; this workstation's Docker host has 8 CPUs and approximately 16 GB RAM. See RESULTS.md for denominators and measurement boundaries.

## Owner completion and excluded work

No public deployment, demo-video work, public repository publication or form submission was performed. Complete registered team/contact details, factual development declarations and each member's individual publication permissions; supply owner-controlled public links if submitting. Personalize the report and rename it TeamName_Report.pdf. The three-fresh-reader naming exercise and P3P account/UAT work remain owner-dependent. No permissions or identities have been inferred. All independent local deliverables are ready.

Default Compose keys are explicitly synthetic localhost credentials. The archive excludes .env files, database dumps, browser session storage, downloaded model weights and installed dependencies. Keep LICENSE/NOTICE and attribution. Source/evidence archives contain per-file SHA-256 manifests; Release_Manifest.json records archive hashes. No Git commit or signed provenance is invented.
'''
    (OUT / 'README.md').write_text(readme, encoding='utf-8')
    source = []
    for folder in ('services', 'packages', 'apps/console', 'config', 'policies', 'eval', 'tests', 'examples', 'docs', 'deploy'):
        source.extend((ROOT / folder).rglob('*'))
    source.extend(p for p in ROOT.iterdir() if p.is_file() and p.name not in {'docker-compose.google.yml'})
    source.extend((ROOT / 'scripts').glob('*assever*'))
    source.append(ROOT / 'scripts/verify_local_imports.py')
    source.append(ROOT / '.github/workflows/assever.yml')
    source.extend((ROOT / 'prd_outputs/Assever').glob('*.md'))
    source.extend(PLAN / name for name in ('Assever_Backlog.json', 'Assever_Backlog.csv', 'Assever_Backlog.xlsx'))
    evidence = list((ROOT / 'outputs/assever-evidence').rglob('*.json'))
    evidence.extend((ROOT / 'outputs/assever-evidence').rglob('*.md'))
    evidence.extend((ROOT / 'outputs/assever-evidence/source-initial').rglob('*.py'))
    evidence.extend(p for p in (ROOT / 'outputs').glob('assever*') if p.suffix in {'.txt', '.log'} and 'model-qwen' not in p.name)
    evidence.extend((ROOT / 'output/playwright').glob('assever-final*'))
    evidence.extend((ROOT / 'output/playwright').glob('assever-*-metrics.txt'))
    records = [archive(OUT / 'Assever_Source_v1.0.0.zip', source), archive(OUT / 'Assever_Evidence_v1.0.0.zip', evidence)]
    (OUT / 'Release_Manifest.json').write_text(json.dumps({'version':'1.0.0', 'archives':records, 'excludes':['credentials','database dumps','model weights','installed dependencies','browser storage'], 'verification':'ZIP integrity and each file hash verified'}, indent=2), encoding='utf-8')
    master = OUT / 'Assever_Implementation_Pack_v1.0.0.zip'
    with zipfile.ZipFile(master, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(OUT.iterdir()):
            if path.is_file() and path != master and path.suffix in {'.zip', '.md', '.pdf', '.xlsx', '.csv', '.json'}:
                z.write(path, 'Assever_Release/' + path.name)
    with zipfile.ZipFile(master) as z:
        assert z.testzip() is None
    print(json.dumps({'archives':records, 'pack':str(master), 'pack_bytes':master.stat().st_size}, indent=2))


if __name__ == '__main__':
    main()
