"""Fail before regression tests if a copied editable install resolves another checkout."""
import importlib
from pathlib import Path
import sys

root=Path(__file__).resolve().parents[1]
for part in ("packages/core","packages/sdk","services/gateway","eval","services/assever"):
    sys.path.insert(0,str(root/part))
for module in ("intentseal_core","intentseal_gateway","intentseal_eval","assever"):
    path=Path(importlib.import_module(module).__file__).resolve()
    assert root in path.parents,(module,path)
    print(module,path)
