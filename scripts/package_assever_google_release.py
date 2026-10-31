"""Create a credential-free cloud handoff; preserve earlier release archives."""
import importlib.util
import json
import shutil
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/01a18ed2-2209-7780-8a49-0f2b07180b67/Assever_Google_Release'


def main():
    spec=importlib.util.spec_from_file_location('archive_helpers',ROOT/'scripts/package_assever_release.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    OUT.mkdir(parents=True,exist_ok=True)
    result=json.loads((OUT/'Measured_Results.json').read_text())
    for name in ('Assever_Google_Architecture.svg','Assever_Google_Architecture.png','Assever_Google_Architecture.html'):
        shutil.copy2(ROOT/'docs/assever/integrated-design'/name,OUT/name)
    readme=f'''# Assever 1.2.4 — Google Cloud release

Live product: {result['url']}

The original Abide product is renamed and extended in place. Its console, gateway, Core, SDK, work orders, business policies, original office/support workflows and integration boundaries remain intact. The private Google runtime runs these existing Docker services behind a Cloud Run HTTPS transport. Purchase planning uses Google Gen AI SDK 2.34.0 with Vertex Gemini; original multi-agent tasks use Google ADK 2.12.0. Model Armor, Secret Manager and BigQuery are connected using workload identity. No Ollama service runs in this deployment.

## Verified delivery

{result['foundation_tests']} original-system tests pass (one optional LangChain skip), {result['purchase_tests']} product tests pass and eight console tests pass. The deployed authored conformance campaign has 720 cells. The frozen Gemini cohort has 240 workflow attempts, {result['offline']['captured_vertex_responses']} captured responses and {result['live']['errors']} retained errors; {result['live']['controls']['adaptive']['completed_tasks']} tasks finish and no adaptive unsafe effects occur. Both controls are safe on the captured Gemini proposals. The authored campaign and compromised-agent journeys isolate enforcement behavior. Four live Google ADK journeys pass and complete useful work. Independent reconstruction checks every final saved effect bundle.

Core admission p95 is {result['performance']['summary']['core_admission_ms']['p95']} ms in the twenty-client test on the configured 4-vCPU/8-GB Google host. The earlier timing run is retained. Cloud backup/restore matches {result['backup_tables']} tables. See GOOGLE_CLOUD_VALIDATION.md for denominators, source hashes, availability errors and remaining scope boundaries.

## Files and reproduction

- Assever_Source_v1.2.4.zip: existing-product source, Docker build, package locks, original and new tests, SDK, Google provisioning/operations scripts, documentation, attribution and licenses. Extract into a fresh directory and run `docker compose -f compose.integrated.yml up --build --wait -d` for local conformance. Google inference requires an authorized project/runtime identity; no private credentials are included.
- Assever_Evidence_v1.2.4.zip: final cloud campaign and Gemini cohort, actual Google requests/responses/versions, ADK journeys, provider effects, source manifests, qualification and backup proof, browser artifacts and retained earlier diagnostics. Extract at the source root and run `python scripts/verify_assever_google_exports.py` with the Python standard library. The executed v5 runner is archived with its hash. The current v6 runner fixes null-plan reference handling for future cohorts; historical data remains unchanged.
- Assever_Report_Draft.pdf: seven-page template-aligned submission draft, with mandatory owner facts/consents explicitly pending.
- Assever_Backlog.xlsx / JSON / CSV: stable original IDs and estimates, updated deployment and measured evidence, owner-dependent statuses preserved.
- INTEGRATED_PRD.md, GOOGLE_CLOUD_OPERATIONS.md and the as-built diagram: product scope, runtime boundaries, operation/recovery and reproducibility.

## Remaining owner-controlled work

Registered team/contact details, accurate participation/development declarations and individual permissions require the owner. Public source publication, demo video and form submission remain separate from this deployment request. The public app and SDK download are verified; remaining owner links are tracked. P3P account/UAT and full external interoperability are not implied by synthetic testing. The report must be personalized and renamed to the registered TeamName_Report.pdf before submission.

The deployment uses one persistent private runtime; it is not a multi-node availability or India-only data-residency qualification. All commerce data and funds are synthetic. Runtime hashes are tamper evidence rather than provider signatures. Keep all LICENSE/NOTICE and attribution files. The Compute runtime remains running for review.

Archives exclude environment files, resolved cloud configuration, database dumps, service-account/ADC credentials, browser storage, model weights and installed dependencies. FILE_SHA256.json verifies every archived source/evidence file; Release_Manifest.json records archive hashes. No Git commit or signed provenance is invented. Earlier local/standalone release packages remain separate historical artifacts.
'''
    (OUT/'README.md').write_text(readme,encoding='utf-8')
    source=[]
    for folder in ('services/gateway','packages','apps/console','config','policies','eval','tests','examples','docs','deploy','.github/workflows'):
        source.extend((ROOT/folder).rglob('*'))
    source.extend(p for p in ROOT.iterdir() if p.is_file() and p.name!='compose.assever.yml')
    source.extend((ROOT/'scripts').glob('*.py'))
    source=[p for p in source if p.name not in ('integrate_purchase_modules.py','build_purchase_router.py')]
    evidence=list((ROOT/'outputs/assever-google-evidence').rglob('*.json'))
    evidence.extend((ROOT/'outputs/assever-google-evidence').rglob('*.log'))
    evidence.extend((ROOT/'outputs/assever-google-evidence').rglob('*.py'))
    evidence.extend(p for p in (ROOT/'outputs').glob('assever-google-*') if p.suffix in ('.txt','.log'))
    evidence.extend((ROOT/'output/playwright').glob('*google*'))
    records=[helper.archive(OUT/'Assever_Source_v1.2.4.zip',source),helper.archive(OUT/'Assever_Evidence_v1.2.4.zip',evidence)]
    (OUT/'Release_Manifest.json').write_text(json.dumps({'version':'1.2.4-google','application_url':result['url'],'runtime_image':result['image'],'archives':records,'verification':'ZIP integrity and every file SHA-256 verified'},indent=2))
    master=OUT/'Assever_Google_Implementation_Pack_v1.2.4.zip'
    with zipfile.ZipFile(master,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in OUT.iterdir():
            if p.is_file() and p!=master and not p.name.startswith('Previous_') and p.suffix in ('.zip','.md','.pdf','.xlsx','.csv','.json','.svg','.html','.png'):
                z.write(p,'Assever_Google_Release/'+p.name)
    with zipfile.ZipFile(master) as z:assert z.testzip() is None
    print(json.dumps({'archives':records,'pack':str(master),'bytes':master.stat().st_size},indent=2))


if __name__=='__main__':main()
