"""One-time source extraction into the existing Core boundary; preserves input files."""
import ast
from pathlib import Path
import shutil

root=Path(__file__).resolve().parents[1]
src=root/'services/assever/assever'
dst=root/'packages/core/intentseal_core/purchase'
dst.mkdir(exist_ok=True)
for name in ('common','runtime','schemas','worker','sink','checker','models','lab','campaign','live_study','ablations','ap2_projection','retention','boundaries'):
    s=(src/f'{name}.py').read_text(encoding='utf-8')
    s=s.replace('from . import api, runtime, worker','from . import service as api, runtime, worker').replace('from . import api','from . import service as api')
    s=s.replace('assever.runtime','intentseal_core.purchase.runtime').replace('assever.worker','intentseal_core.purchase.worker')
    (dst/f'{name}.py').write_text(s,encoding='utf-8')
(dst/'__init__.py').write_text('"""Purchase integrity extensions for the existing delegation system."""\n',encoding='utf-8')
shutil.copytree(root/'services/assever/migrations',dst/'migrations',dirs_exist_ok=True)
source=(src/'api.py').read_text(encoding='utf-8')
tree=ast.parse(source)
names=[]
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.lineno>=246:
        names.append(node.name)
# Select business operations explicitly; no FastAPI app, sessions, auth or static hosting.
names=['create_draft','draft','list_contracts','get_contract','approve','review_nonce','edit_scope','revoke','narrow','grant','quote','propose','prepare','scoped_op','commit','operation','refund_notice','cancel','reconcile','events','evidence','exception_request','exception_decide','exception_review_nonce','callback','agent_purchase','ready','metrics','lab_run','lab_runs','lab_result','manifest','model_purchase','model_run_history']
header='''"""Application operations using Core's ledger; identity is supplied by the existing gateway.

No HTTP application, enrollment, cookies or parallel authentication system lives here.
"""
import hashlib
import hmac
import os
import re
import secrets
import time
import httpx
from .common import CATALOG, MERCHANTS, db, default_scope, digest, jsonb, now, uid
from .runtime import Refusal, active, event, grant_signature, projection, require, reserve, root, snapshot, validate_scope
from .schemas import (EditScope, ModelPurchase, Approval, Callback, Commit, Draft, ExceptionDecision,
    ExceptionRequest, GrantInput, LabInput, Narrow, Prepare, Proposal, QuoteInput, Reconcile, Revoke)
from .worker import provider, reconcile_one

def create_agent(a):
    # Ephemeral role identities share the existing authenticated delegation owner;
    # they are never enrolled as a second browser or API session.
    return {"actor_id": uid("role")}

'''
body=[]
for node in tree.body:
    if isinstance(node,ast.FunctionDef) and node.name in names:
        node.decorator_list=[]
        for i,default in enumerate(node.args.defaults):
            if isinstance(default,ast.Call) and isinstance(default.func,ast.Name) and default.func.id in ('Depends','Header'):
                node.args.defaults[i]=ast.Constant(None if default.func.id=='Depends' else '')
        body.append(ast.unparse(node))
(dst/'service.py').write_text(header+'\n\n'.join(body)+'\n',encoding='utf-8')
print('Extracted Core operations; standalone source preserved.')
