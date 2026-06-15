from __future__ import annotations

import pytest

from helpers import load_innova_module

grpc_client = load_innova_module("grpc_client")
DiffusAppGrpcClient = grpc_client.DiffusAppGrpcClient


class FakeStub:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object, list[tuple[str, str]]]] = []

    async def SetDeviceValue(self, request, metadata):
        self.calls.append(("SetDeviceValue", request, list(metadata)))

    async def GetDeviceStatus(self, request, metadata):
        self.calls.append(("GetDeviceStatus", request, list(metadata)))
        return {"ok": True}


def test_grpc_metadata_contains_bearer_token_and_mac() -> None:
    client = DiffusAppGrpcClient(
        token="abc123",
        mac_address="FC:01:2C:FA:13:1C",
        stub=FakeStub(),
    )

    assert client.metadata == (
        ("authorization", "Bearer abc123"),
        ("mac_address", "FC:01:2C:FA:13:1C"),
    )


@pytest.mark.asyncio
async def test_set_device_value_sends_type_and_value() -> None:
    stub = FakeStub()
    client = DiffusAppGrpcClient(
        token="abc123",
        mac_address="FC:01:2C:FA:13:1C",
        stub=stub,
    )

    await client.set_device_value(3, 2)

    name, request, metadata = stub.calls[0]
    assert name == "SetDeviceValue"
    assert request.type == 3
    assert request.value == 2
    assert metadata == [
        ("authorization", "Bearer abc123"),
        ("mac_address", "FC:01:2C:FA:13:1C"),
    ]
