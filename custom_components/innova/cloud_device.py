"""Home Assistant-facing facade for DiffusApp cloud devices."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

VALUE_POWER = 1
VALUE_SETPOINT = 2
VALUE_MODE = 3
VALUE_FAN_SPEED = 4
VALUE_FLAP = 5


class FanSpeed(Enum):
    AUTO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Mode(Enum):
    AUTO = 0
    HEAT = 1
    COOL = 2
    FAN_ONLY = 3
    DRY = 4

    @property
    def is_auto(self) -> bool:
        return self is Mode.AUTO

    @property
    def is_heating(self) -> bool:
        return self is Mode.HEAT

    @property
    def is_cooling(self) -> bool:
        return self is Mode.COOL

    @property
    def is_fan_only(self) -> bool:
        return self is Mode.FAN_ONLY

    @property
    def is_dehumidifying(self) -> bool:
        return self is Mode.DRY


@dataclass(slots=True)
class DiffusAppStatus:
    power: bool
    target_temperature: float
    min_temperature: float
    max_temperature: float
    temperature_step: float
    ambient_temp: float
    mode: Mode
    fan_speed: FanSpeed
    rotation: bool
    software_version: str = ""


def _tenths(value: int | float | None, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value) / 10.0


def _enum_or_default(enum_cls, value, default):
    try:
        return enum_cls(value)
    except ValueError:
        return default


def parse_duepuntozero_status(response) -> DiffusAppStatus:
    """Map a gRPC GetDeviceStatusResponse into the facade status shape."""
    main = response.main_status
    status = main.duepuntozero_status
    setpoint = status.temperature_setpoint
    return DiffusAppStatus(
        power=bool(status.power_state),
        target_temperature=_tenths(setpoint.value, 20.0),
        min_temperature=_tenths(setpoint.min, 16.0),
        max_temperature=_tenths(setpoint.max, 31.0),
        temperature_step=_tenths(setpoint.step, 0.5),
        ambient_temp=_tenths(status.room_temperature, 0.0),
        mode=_enum_or_default(Mode, status.operation_mode, Mode.AUTO),
        fan_speed=_enum_or_default(FanSpeed, status.fan_speed, FanSpeed.AUTO),
        rotation=bool(status.flap),
        software_version=str(response.iot_status.fw_version or ""),
    )


class InnovaCloudDevice:
    """Drop-in-enough replacement for the old innova-controls object."""

    def __init__(
        self,
        *,
        grpc_client,
        mac_address: str,
        name: str,
        device_type: str = "Duepuntozero",
    ) -> None:
        self._grpc = grpc_client
        self._mac_address = mac_address
        self._name = name
        self._device_type = device_type
        self._status = DiffusAppStatus(
            power=False,
            target_temperature=20.0,
            min_temperature=16.0,
            max_temperature=31.0,
            temperature_step=0.5,
            ambient_temp=0.0,
            mode=Mode.AUTO,
            fan_speed=FanSpeed.AUTO,
            rotation=False,
        )

    async def async_update(self) -> bool:
        response = await self._grpc.get_device_status()
        if isinstance(response, dict):
            return bool(response.get("ok", True))
        self._status = parse_duepuntozero_status(response)
        return True

    async def async_close(self) -> None:
        close = getattr(self._grpc, "close", None)
        if close is not None:
            await close()

    @property
    def ambient_temp(self) -> float:
        return self._status.ambient_temp

    @property
    def water_temp(self) -> None:
        return None

    @property
    def target_temperature(self) -> float:
        return self._status.target_temperature

    @property
    def temperature_step(self) -> float:
        return self._status.temperature_step

    @property
    def min_temperature(self) -> float:
        return self._status.min_temperature

    @property
    def max_temperature(self) -> float:
        return self._status.max_temperature

    @property
    def power(self) -> bool:
        return self._status.power

    @property
    def mode(self) -> Mode:
        return self._status.mode

    @property
    def supported_modes(self) -> list[Mode]:
        return [Mode.AUTO, Mode.HEAT, Mode.COOL, Mode.FAN_ONLY, Mode.DRY]

    @property
    def rotation(self) -> bool:
        return self._status.rotation

    @property
    def fan_speed(self) -> FanSpeed:
        return self._status.fan_speed

    @property
    def supported_fan_speeds(self) -> list[FanSpeed]:
        return [FanSpeed.AUTO, FanSpeed.LOW, FanSpeed.MEDIUM, FanSpeed.HIGH]

    @property
    def night_mode(self) -> None:
        return None

    @property
    def scheduling_mode(self) -> None:
        return None

    @property
    def keyboard_locked(self) -> None:
        return None

    @property
    def model(self) -> str:
        return self._device_type

    @property
    def name(self) -> str:
        return self._name

    @property
    def serial(self) -> str:
        return ""

    @property
    def uid(self) -> str:
        return self._mac_address

    @property
    def software_version(self) -> str:
        return self._status.software_version

    @property
    def ip_address(self) -> str:
        return ""

    async def power_on(self) -> bool:
        await self._set_bool(VALUE_POWER, True)
        self._status.power = True
        return True

    async def power_off(self) -> bool:
        await self._set_bool(VALUE_POWER, False)
        self._status.power = False
        return True

    async def rotation_on(self) -> bool:
        await self._set_bool(VALUE_FLAP, True)
        self._status.rotation = True
        return True

    async def rotation_off(self) -> bool:
        await self._set_bool(VALUE_FLAP, False)
        self._status.rotation = False
        return True

    async def night_mode_on(self) -> bool:
        return False

    async def night_mode_off(self) -> bool:
        return False

    async def set_temperature(self, temperature: float) -> bool:
        await self._grpc.set_device_value(VALUE_SETPOINT, round(temperature * 10))
        self._status.target_temperature = temperature
        return True

    async def set_fan_speed(self, speed: FanSpeed) -> bool:
        await self._grpc.set_device_value(VALUE_FAN_SPEED, speed.value)
        self._status.fan_speed = speed
        return True

    async def set_scheduling_on(self) -> bool:
        return False

    async def set_scheduling_off(self) -> bool:
        return False

    async def lock_keyboard(self) -> bool:
        return False

    async def unlock_keyboard(self) -> bool:
        return False

    async def set_heating(self) -> bool:
        return await self._set_mode(Mode.HEAT)

    async def set_cooling(self) -> bool:
        return await self._set_mode(Mode.COOL)

    async def set_dehumidifying(self) -> bool:
        return await self._set_mode(Mode.DRY)

    async def set_fan_only(self) -> bool:
        return await self._set_mode(Mode.FAN_ONLY)

    async def set_auto(self) -> bool:
        return await self._set_mode(Mode.AUTO)

    @property
    def supports_target_temp(self) -> bool:
        return True

    @property
    def supports_water_temp(self) -> bool:
        return False

    @property
    def supports_swing(self) -> bool:
        return True

    @property
    def supports_fan(self) -> bool:
        return True

    @property
    def supports_preset(self) -> bool:
        return False

    @property
    def supports_scheduling(self) -> bool:
        return False

    @property
    def supports_keyboard_lock(self) -> bool:
        return False

    async def _set_bool(self, value_type: int, enabled: bool) -> None:
        await self._grpc.set_device_value(value_type, 1 if enabled else 0)

    async def _set_mode(self, mode: Mode) -> bool:
        await self._grpc.set_device_value(VALUE_MODE, mode.value)
        self._status.mode = mode
        self._status.power = True
        return True
