from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_manifest_uses_homeassistant_core_grpc_constraints() -> None:
    manifest = json.loads(
        (ROOT / "custom_components" / "innova" / "manifest.json").read_text()
    )

    assert manifest["requirements"] == [
        "grpcio==1.78.0",
        "protobuf==6.32.0",
    ]
