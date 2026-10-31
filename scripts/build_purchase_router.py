"""Generate explicit adapters into the existing gateway; not a second application."""
import ast
from pathlib import Path

root=Path(__file__).resolve().parents[1]
source=(root/'services/assever/assever/api.py').read_text(encoding='utf-8')
tree=ast.parse(source)
exclude={'draft','approve','list_contracts','get_contract','current','session','create_agent','ready'}
out=['''"""Purchase routes in the existing gateway, using its KeyRing and principals."""
import hashlib
import os
from fastapi import APIRouter, Depends, Request, Header
from intentseal_core.purchase import service as actions
from intentseal_core.purchase.schemas import (ModelPurchase, Approval, Callback, Commit,
    ExceptionDecision, ExceptionRequest, GrantInput, LabInput, Narrow, Prepare,
    Proposal, QuoteInput, Reconcile, Revoke, EditScope)
from .security import Principal, require, human_only

router = APIRouter(tags=['purchase integrity'])

def actor(request: Request, p: Principal = require('project')):
    identity = p.name
    if p.agent:
        token=request.headers.get('x-api-key') or request.headers.get('authorization','')
        identity='agent:'+hashlib.sha256(token.encode()).hexdigest()[:24]
    a={'tenant':p.org,'actor':identity,'role':'agent' if p.agent else 'human', 'principal':p.name}
    request.state.purchase_actor=a
    return a

def human(request: Request, p: Principal = require('project')):
    human_only(p)
    return actor(request,p)

def evaluator(a=Depends(human)):
    actions.require(os.environ.get('LAB_ENABLED')=='1','LAB_DISABLED','The local safety lab is disabled.',403)
    return a

@router.get('/v1/purchases/identity')
def identity(a=Depends(actor)):
    return {'actor_id':a['actor'],'tenant_id':a['tenant'],'role':a['role']}
''']
for node in tree.body:
    if not isinstance(node,ast.FunctionDef) or node.name in exclude:
        continue
    decorators=[d for d in node.decorator_list if isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and isinstance(d.func.value,ast.Name) and d.func.value.id=='app' and d.func.attr in ('post','get')]
    if not decorators:
        continue
    decorator=decorators[0]
    path=decorator.args[0].value
    if path.startswith('/v1/'):
        path='/v1/purchases/'+path[4:]
    else:
        continue
    decorator.func.value.id='router'
    decorator.args[0]=ast.Constant(path)
    node.decorator_list=[decorator]
    args=[ast.Name(a.arg,ast.Load()) for a in node.args.args]
    node.body=[ast.Return(ast.Call(ast.Attribute(ast.Name('actions',ast.Load()),node.name,ast.Load()),args,[]))]
    out.append(ast.unparse(node))
(root/'services/gateway/intentseal_gateway/purchase_api.py').write_text('\n\n'.join(out)+'\n',encoding='utf-8')
print('Generated gateway router; no enrollment or session endpoints.')
