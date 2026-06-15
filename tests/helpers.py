from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]


def load_innova_module(name: str) -> ModuleType:
    path = ROOT / "custom_components" / "innova" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"innova_test_{name}", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
