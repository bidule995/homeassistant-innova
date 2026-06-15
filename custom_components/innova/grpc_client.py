"""gRPC client for Solution Tech DiffusApp devices."""
from __future__ import annotations

from typing import Any

import grpc
from google.protobuf import empty_pb2

try:
    from .proto import controls_pb2, controls_pb2_grpc
except ImportError:  # pragma: no cover - used by direct unit-test loading
    import importlib.util
    import sys
    from pathlib import Path

    proto_dir = Path(__file__).resolve().parent / "proto"

    def _load_proto_module(name: str):
        module_name = f"innova_test_proto.{name}"
        package = sys.modules.setdefault(
            "innova_test_proto",
            type(sys)("innova_test_proto"),
        )
        package.__path__ = [str(proto_dir)]
        spec = importlib.util.spec_from_file_location(
            module_name, proto_dir / f"{name}.py"
        )
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    controls_pb2 = _load_proto_module("controls_pb2")
    controls_pb2_grpc = _load_proto_module("controls_pb2_grpc")

GRPC_HOST = "grpc.innova.solutiontech.tech:443"


class DiffusAppGrpcClient:
    """Async wrapper around the device_controls.Controls gRPC service."""

    def __init__(
        self,
        *,
        token: str,
        mac_address: str,
        channel: grpc.aio.Channel | None = None,
        stub: Any | None = None,
    ) -> None:
        self._token = token
        self._mac_address = mac_address
        if stub is not None:
            self._channel = channel
            self._stub = stub
        else:
            self._channel = channel or grpc.aio.secure_channel(
                GRPC_HOST, grpc.ssl_channel_credentials()
            )
            self._stub = controls_pb2_grpc.ControlsStub(self._channel)

    @property
    def metadata(self) -> tuple[tuple[str, str], tuple[str, str]]:
        return (
            ("authorization", f"Bearer {self._token}"),
            ("mac_address", self._mac_address),
        )

    async def get_device_status(self):
        return await self._stub.GetDeviceStatus(empty_pb2.Empty(), metadata=self.metadata)

    async def set_device_value(self, value_type: int, value: int) -> None:
        request = controls_pb2.SetDeviceValueRequest(type=value_type, value=value)
        await self._stub.SetDeviceValue(request, metadata=self.metadata)

    async def close(self) -> None:
        if self._channel is not None and hasattr(self._channel, "close"):
            await self._channel.close()
