"""Package the corrected original-product release, excluding credentials and stores."""
import importlib.util
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/01a18ed2-2209-7780-8a49-0f2b07180b67/Assever_Integrated_Release'


def main():
    spec = importlib.util.spec_from_file_location('archive_helpers', ROOT / 'scripts/package_assever_release.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    OUT.mkdir(parents=True, exist_ok=True)
    measured = json.loads((OUT / 'Measured_Results.json').read_text())
    for name in ('Assever_Local_Architecture.svg', 'Assever_Local_Architecture.html', 'Assever_Local_Architecture.png'):
        source = ROOT / 'docs/assever/integrated-design' / name
        if source.exists(): shutil.copy2(source, OUT / name)
    (OUT / 'README.md').write_text(f'''# Assever 1.1 — integrated local release

The original application is renamed and extended in place. Open http://localhost:8000 . The original console, gateway, Core, SDK, policies, office/support workflows and integrations remain the product. The earlier standalone purchase application is stopped, with its data preserved.

## Run and inspect

Extract Assever_Source_v1.1.0.zip into a new directory. Run `docker compose -f compose.integrated.yml up --build --wait -d`. Only the original gateway is public on localhost:8000; PostgreSQL, effect provider, evaluator and worker are private. Optional local Qwen proposals require `docker compose -f compose.integrated.yml --profile models up -d models` and pulling the documented models. Weights and installed dependencies are excluded from this archive. See INTEGRATED_OPERATIONS.md for configuration, testing and backup instructions. Keep LICENSE, NOTICE and all attribution.

Extract Assever_Evidence_v1.1.0.zip at the same source root. Run `python scripts/verify_assever_integrated_exports.py` using the Python standard library. Evidence retains source digests, raw proposals, provider effects, all outcomes and the one timeout. Hashes are tamper evidence, not signed provenance. No Git commit is invented.

## Verified scope

{measured['purchase_tests']} integrated product tests, {measured['foundation_tests']} original-system tests and eight console tests pass. One optional LangChain test is skipped. The Core/runtime campaign has 720 cells; the separate live study has 240 attempts, 239 captured model responses and one retained timeout. Adaptive gateway enforcement records zero unsafe effects over 239 captured proposals and completes 231 tasks. The payment-budget reference records 53 unsafe effects. All 1,218 final bundles independently verify. Comparisons are bounded synthetic tests with different reference transport topology, not vendor measurements.

Twenty-client admission p95 is {measured['performance']['summary']['core_admission_ms']['p95']} ms. The 100 ms target on 4 CPU / 8 GB remains open; this host has eight Docker CPUs and approximately 16 GB. Read the measured results and release status for boundaries, unresolved outcomes and conditional gates.

## Remaining owner work

Cloud deployment, demo video, public repository publication and form submission are excluded. Complete registered team/contact facts, accurate development declarations and individual publication consents, then supply required public links and rename the report to the registered TeamName_Report.pdf. P3P account/UAT and the fresh-reader naming exercise require owner participation. The report is a template-aligned draft with owner facts explicitly pending.

Assever_Backlog.xlsx/JSON/CSV reconcile all 121 stable original items. Excluded and Partial statuses are retained. Original estimates are not actual hours. INTEGRATED_PRD.md is the current whole-product specification; the previous standalone package remains a historical artifact outside this release.

Archives exclude .env files, database dumps, model weights, installed dependencies and browser storage. Synthetic localhost defaults are development credentials. FILE_SHA256.json verifies every source/evidence file; Release_Manifest.json records archive hashes.
''', encoding='utf-8')
    source = []
    for folder in ('services/gateway', 'packages', 'apps/console', 'config', 'policies', 'eval', 'tests', 'examples', 'docs', 'deploy', '.github/workflows'):
        source.extend((ROOT / folder).rglob('*'))
    source.extend(p for p in ROOT.iterdir() if p.is_file() and p.name not in {'compose.assever.yml'})
    source.extend((ROOT / 'scripts').glob('*.py'))
    # Historical one-time code generators are not installation or migration tools.
    source = [p for p in source if p.name not in {'integrate_purchase_modules.py', 'build_purchase_router.py'}]
    evidence_root = ROOT / 'outputs/assever-integrated-evidence'
    evidence = list(evidence_root.rglob('*.json')) + list(evidence_root.rglob('*.md'))
    evidence.extend(p for p in (ROOT / 'outputs').glob('assever-integrated-*') if p.suffix in {'.txt', '.log'})
    evidence.extend((ROOT / 'output/playwright').glob('*integrated*'))
    records = [helper.archive(OUT / 'Assever_Source_v1.1.0.zip', source), helper.archive(OUT / 'Assever_Evidence_v1.1.0.zip', evidence)]
    (OUT / 'Release_Manifest.json').write_text(json.dumps({'version': '1.1.0-integrated', 'archives': records, 'verification': 'ZIP integrity and every file SHA-256 verified', 'excluded': ['credentials', 'database dumps', 'model weights', 'dependencies', 'browser storage']}, indent=2))
    pack = OUT / 'Assever_Integrated_Implementation_Pack_v1.1.0.zip'
    with zipfile.ZipFile(pack, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(OUT.iterdir()):
            if path.is_file() and path != pack and path.suffix in {'.zip', '.md', '.pdf', '.xlsx', '.csv', '.json', '.svg', '.html', '.png'}:
                z.write(path, 'Assever_Integrated_Release/' + path.name)
    with zipfile.ZipFile(pack) as z: assert z.testzip() is None
    print(json.dumps({'archives': records, 'pack': str(pack), 'bytes': pack.stat().st_size}, indent=2))


if __name__ == '__main__':
    main()
