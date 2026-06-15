from __future__ import annotations

import pytest

from helpers import load_innova_module

cloud_device = load_innova_module("cloud_device")
grpc_client = load_innova_module("grpc_client")
FanSpeed = cloud_device.FanSpeed
InnovaCloudDevice = cloud_device.InnovaCloudDevice
Mode = cloud_device.Mode
parse_duepuntozero_status = cloud_device.parse_duepuntozero_status


class FakeGrpcClient:
    def __init__(self) -> None:
        self.commands: list[tuple[int, int]] = []

    async def set_device_value(self, value_type: int, value: int) -> None:
        self.commands.append((value_type, value))


@pytest.mark.asyncio
async def test_cloud_device_maps_climate_commands_to_duepuntozero_values() -> None:
    grpc = FakeGrpcClient()
    device = InnovaCloudDevice(
        grpc_client=grpc,
        mac_address="FC:01:2C:FA:13:1C",
        name="Office",
    )

    await device.power_on()
    await device.set_temperature(21.5)
    await device.set_cooling()
    await device.set_fan_speed(FanSpeed.HIGH)
    await device.rotation_on()

    assert grpc.commands == [
        (1, 1),
        (2, 215),
        (3, 2),
        (4, 3),
        (5, 1),
    ]
    assert device.power is True
    assert device.target_temperature == 21.5
    assert device.mode == Mode.COOL
    assert device.fan_speed == FanSpeed.HIGH
    assert device.rotation is True


def test_cloud_device_supported_capabilities_match_v1_scope() -> None:
    device = InnovaCloudDevice(
        grpc_client=FakeGrpcClient(),
        mac_address="FC:01:2C:F8:15:2C",
        name="Bedroom",
    )

    assert device.uid == "FC:01:2C:F8:15:2C"
    assert device.serial == ""
    assert device.supports_target_temp is True
    assert device.supports_fan is True
    assert device.supports_swing is True
    assert device.supports_preset is False
    assert device.supports_keyboard_lock is False


def test_parse_duepuntozero_status_maps_cloud_response_fields() -> None:
    response = grpc_client.controls_pb2.GetDeviceStatusResponse()
    response.iot_status.fw_version = 104
    response.main_status.duepuntozero_status.power_state = True
    response.main_status.duepuntozero_status.temperature_setpoint.value = 215
    response.main_status.duepuntozero_status.temperature_setpoint.min = 160
    response.main_status.duepuntozero_status.temperature_setpoint.max = 310
    response.main_status.duepuntozero_status.temperature_setpoint.step = 5
    response.main_status.duepuntozero_status.room_temperature = 198
    response.main_status.duepuntozero_status.operation_mode = 1
    response.main_status.duepuntozero_status.fan_speed = 2
    response.main_status.duepuntozero_status.flap = True

    status = parse_duepuntozero_status(response)

    assert status.power is True
    assert status.target_temperature == 21.5
    assert status.min_temperature == 16.0
    assert status.max_temperature == 31.0
    assert status.temperature_step == 0.5
    assert status.ambient_temp == 19.8
    assert status.mode == Mode.HEAT
    assert status.fan_speed == FanSpeed.MEDIUM
    assert status.rotation is True
    assert status.software_version == "104"
