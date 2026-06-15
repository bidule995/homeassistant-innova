# Generated-compatible gRPC stubs for device_controls.Controls.
from __future__ import annotations

import grpc
from google.protobuf import empty_pb2

from . import controls_pb2 as device__controls_dot_controls__pb2


class ControlsStub:
    """Client stub for the Solution Tech device controls service."""

    def __init__(self, channel) -> None:
        self.GetDeviceStatus = channel.unary_unary(
            "/device_controls.Controls/GetDeviceStatus",
            request_serializer=empty_pb2.Empty.SerializeToString,
            response_deserializer=(
                device__controls_dot_controls__pb2.GetDeviceStatusResponse.FromString
            ),
        )
        self.SetDeviceValue = channel.unary_unary(
            "/device_controls.Controls/SetDeviceValue",
            request_serializer=(
                device__controls_dot_controls__pb2.SetDeviceValueRequest.SerializeToString
            ),
            response_deserializer=empty_pb2.Empty.FromString,
        )
        self.SubscribeToDeviceEvents = channel.unary_stream(
            "/device_controls.Controls/SubscribeToDeviceEvents",
            request_serializer=empty_pb2.Empty.SerializeToString,
            response_deserializer=device__controls_dot_controls__pb2.Event.FromString,
        )
