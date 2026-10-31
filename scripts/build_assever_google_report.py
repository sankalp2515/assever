"""Template-aligned seven-page report using measured Google deployment evidence."""
import ast
import importlib.util
import inspect
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/01a18ed2-2209-7780-8a49-0f2b07180b67/Assever_Google_Release'
E=ROOT/'outputs/assever-google-evidence'


def main():
    spec=importlib.util.spec_from_file_location('report_layout',ROOT/'scripts/build_assever_report.py')
    base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
    tree=ast.parse((ROOT/'scripts/build_assever_integrated_report.py').read_text())
    for n in ast.walk(tree):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='update' and isinstance(n.func.value,ast.Attribute) and n.func.value.attr=='TEXT':
            base.TEXT.update(ast.literal_eval(n.args[0]));break
    r=json.loads((E/'release-summary.json').read_text())
    bridge=OUT/'_work/report-data'
    for folder in ('final/campaign','final/live-study'):(bridge/folder).mkdir(parents=True,exist_ok=True)
    live={**r['live'],'per_control':{k:{'unsafe_effects':v['verdicts'].get('FAIL',0),'completed_tasks':v['completed_tasks']} for k,v in r['live']['controls'].items()}}
    for p,d in [('final/campaign/summary.json',r['campaign']),('final/live-study/summary.json',live),('release-summary.json',r),
                ('http-rehearsal-performance.json',{'performance':{**r['performance']['summary'],'p95_ms':r['performance']['summary']['http_ms']['p95']}})]:
        (bridge/p).write_text(json.dumps(d))
    base.OUT=OUT;base.DATA=bridge
    base.TEXT['website']+=' Gemini uses the deployment’s Google identity.'
    base.TEXT['approach']=base.TEXT['approach'].replace('Assever extends the existing Abide console, gateway, Core engine, SDK and business-policy registry.',
        'Assever adds Vertex Gemini through Google Gen AI SDK and Google ADK to its existing console, gateway, Core, SDK and business-policy registry.')
    base.TEXT['evaluation']='We test the deployed application through its public Google Cloud HTTPS endpoint, original identities, approved work orders and private background worker. The original-system suite includes PostgreSQL tests in isolated schemas. Product tests cover exact confirmation, company policy, SDK mediation, parallel admission, recovery, isolation and independent evidence. A separate frozen Core/runtime campaign covers 24 authored families, three provider profiles, two role topologies and five controls: 720 cells. The final live study plans 240 workflow attempts: twelve tasks, two explicit Vertex Gemini model IDs, five seeds and ordinary/attacked modes. Raw Google SDK requests, model versions, responses, token usage and provider errors remain in the denominator. Adaptive execution uses original read screening and Model Armor; successful proposals are matched to an isolated authored payment-budget Core reference. These replays are not independent model samples or commercial-product measurements. Four live Google ADK office/support journeys independently test useful completion under normal and compromised-agent conditions. Source hashes, provider effects, browser checks, twenty-client timing and cloud backup/restore have separate records.'
    base.TEXT['limits']='The commerce profile is finite and synthetic. Its provider atomically commits order, payment and minimum disclosure; independently settling real rails require additional adapter qualification. Opaque outcomes remain unresolved. Hosted model capacity and malformed output can prevent useful completion; failed requests are retained without replacement. Reference execution shares proposals but uses a different transport topology. Provider-reported model versions are not weight checksums; hashes provide tamper evidence rather than provider signatures. Hindi coverage is structured review labels, not multilingual security. The global Vertex endpoint does not establish India-only data residency. The twenty-client timing result is a measured workload, not an availability SLA. The deployment uses one persistent runtime. Full AP2 interoperability, P3P UAT and live payment-network certification remain separate.'
    base.TEXT['adoption']=base.TEXT['adoption'].replace('The owned local environment','The deployed Google environment')
    base.TEXT['reflection']+=' Cloud testing also exposed a task-list race while Gemini drafted a contract. A typed preparing state and owner filtering before pagination preserve the original workflow under concurrent use.'
    code=inspect.getsource(base.main)
    for old,new in {'#143C68':'#1D5E46','#4C647A':'#4A5466','#EDF4FA':'#E5F0EA','#183047':'#101826',
                    'Purchase integrity for AI agents':'Work-order governance and purchase integrity',
                    'Video and deployment are excluded from this implementation request.':'Video and mandatory owner actions remain outside this implementation request.',
                    'Video, deployment and publication are excluded from this request.':'Video and owner-controlled publication remain separate.',
                    'Deliverables: local Docker product;':'Deliverables: Google Cloud deployment of the original integrated product; Vertex Gemini through Google Gen AI SDK and Google ADK; Model Armor and BigQuery; local Docker reproduction;',
                    'Database/process regression:':'Deployed gateway / database / process regression:',
                    'and each browser visitor has a separate tenant.':'and each authenticated owner has isolated work-order scope.',
                    'Docker host: eight CPUs and approximately 16 GB RAM.':'Google runtime: four vCPUs and 8 GB RAM.',
                    'React/TypeScript/Vite and local Ollama 0.40.13.':'React/TypeScript/Vite, Google Gen AI SDK 2.34.0, Google ADK 2.12.0 and Vertex Gemini.',
                    'Testing targets only the owned local simulators and localhost application.':'Testing targets only the owned Google deployment and its synthetic simulators.',
                    'The exact PRD 4-CPU/8-GB host target is not inferred from this larger Docker host.':'The deployed host matches the declared 4-vCPU/8-GB configuration; core admission meets the 100 ms target in this measured run.',
                    'Synthetic purchase-integrity research':'Deployed Google work-order and purchase research',
                    'Actual results: release evidence final/campaign, final/live-study, ablations, test logs and portable checker bundles.':'Actual results: outputs/assever-google-evidence; frozen Gemini cohort, SDK/ADK records, source hashes, independent effects and cloud qualification.',
                    '("Purchase API",182,90)':'("Existing gateway",182,90)',
                    '("Ledger + outbox",356,90)':'("Core ledger + outbox",356,90)',
                   }.items():code=code.replace(old,new)
    old='f"Live protocol v2: {live[\'actual_invocations\']} model invocations; {live[\'errors\']} invocation/execution errors retained. Adaptive replay has {live[\'per_control\'][\'adaptive\'][\'unsafe_effects\']} unsafe-effect verdicts and completes 228/240 tasks: 120/120 ordinary and 108/120 attacked. Payment-only replay produces 67 unsafe outcomes across the same 240 proposals."'
    new='f"Final deployed Gemini cohort: 240 workflow attempts; {release[\'offline\'][\'captured_vertex_responses\']} captured model responses; {live[\'errors\']} errors retained. Adaptive has {live[\'per_control\'][\'adaptive\'][\'unsafe_effects\']} unsafe-effect verdicts and completes {live[\'per_control\'][\'adaptive\'][\'completed_tasks\']}/240 tasks. The matched payment reference produces {live[\'per_control\'][\'payment\'][\'unsafe_effects\']} unsafe outcomes across {release[\'offline\'][\'matched_successful_proposals\']} paired proposals."'
    assert old in code;code=code.replace(old,new)
    code=code.replace('Live and deterministic denominators are separate. The exploratory first live protocol is retained; final results use the revised finite tool schema and a newly frozen seed set.',
        f"Original-system regression: {r['foundation_tests']} passed, one optional LangChain skip; console: eight passed. Four Google ADK journeys pass and finish their useful tasks. Interrupted cohorts and provider errors remain separate.")
    code=code.replace('p("Assever",title);',f'p("Assever",title);p("Live application: {r["url"]}",small);')
    exec(compile(code,'google_report_layout','exec'),base.__dict__);base.main()


if __name__=='__main__':main()
