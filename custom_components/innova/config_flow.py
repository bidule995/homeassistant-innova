"""Config flow for the Innova DiffusApp cloud integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .cloud_api import (
    DiffusAppApiError,
    DiffusAppCloudApi,
    UnauthorizedError,
    clean_device_auth,
    parse_device_auth_mac,
)
from .cloud_device import InnovaCloudDevice
from .const import (
    CONF_DEVICE_AUTH,
    CONF_DEVICE_NAME,
    CONF_DEVICE_SOURCE,
    CONF_DEVICE_TYPE,
    CONF_EMAIL,
    CONF_HOME_ID,
    CONF_MAC_ADDRESS,
    CONF_TOKEN,
    DEVICE_SOURCE_MANUAL,
    DEVICE_TYPE_DUEPUNTOZERO,
    DOMAIN,
)
from .grpc_client import DiffusAppGrpcClient
from .options_flow import InnovaOptionsFlowHandler

_LOGGER = logging.getLogger(__name__)

SUPPORTED_DEVICE_TYPES = {
    DEVICE_TYPE_DUEPUNTOZERO.casefold(),
    "0",
}

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


def _item_id(item: dict[str, Any]) -> str:
    return str(item.get("id") or item.get("homeId") or item.get("uuid") or "")


def _item_name(item: dict[str, Any], fallback: str) -> str:
    return str(item.get("name") or item.get("label") or fallback)


def _device_mac(device: dict[str, Any]) -> str:
    return str(
        device.get("macAddress")
        or device.get("mac_address")
        or device.get("uid")
        or ""
    ).upper()


def _device_type(device: dict[str, Any]) -> str:
    raw_type = (
        device.get("deviceType") or device.get("device_type") or device.get("type")
    )
    if isinstance(raw_type, dict):
        raw_type = raw_type.get("name") or raw_type.get("id") or raw_type.get("value")
    return str(raw_type or DEVICE_TYPE_DUEPUNTOZERO)


def _is_supported_device_type(device_type: str) -> bool:
    return device_type.casefold() in SUPPORTED_DEVICE_TYPES


def _device_selection_schema(device_options: dict[str, str]) -> vol.Schema:
    return vol.Schema({vol.Required(CONF_DEVICE_SOURCE): vol.In(device_options)})


async def _verify_device(
    token: str, mac_address: str, name: str, device_type: str
) -> None:
    device = InnovaCloudDevice(
        grpc_client=DiffusAppGrpcClient(token=token, mac_address=mac_address),
        mac_address=mac_address,
        name=name,
        device_type=device_type,
    )
    try:
        await device.async_update()
    finally:
        await device.async_close()


class InnovaCreateFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Innova DiffusApp cloud devices."""

    VERSION = 2

    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        self._email = ""
        self._token = ""
        self._homes: list[dict[str, Any]] = []
        self._home_id = ""
        self._devices: list[dict[str, Any]] = []

    @property
    def _api(self) -> DiffusAppCloudApi:
        session = async_get_clientsession(self.hass)
        return DiffusAppCloudApi(session)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Authenticate with the Solution Tech cloud."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors: dict[str, str] = {}
        try:
            login = await self._api.login(
                user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
            )
            self._email = user_input[CONF_EMAIL]
            self._token = str(login["token"])
            self._homes = await self._api.get_homes(self._token)
            if not self._homes:
                home = await self._api.create_home(
                    self._token,
                    "Home",
                    self.hass.config.time_zone,
                )
                self._homes = [home]
            return await self.async_step_home()
        except UnauthorizedError:
            errors["base"] = "invalid_auth"
        except DiffusAppApiError:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected DiffusApp login error")
            errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_home(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select the Solution Tech home."""
        homes = {
            _item_id(home): _item_name(home, "Home")
            for home in self._homes
            if _item_id(home)
        }
        if user_input is None:
            if len(homes) == 1:
                self._home_id = next(iter(homes))
                return await self.async_step_device()
            return self.async_show_form(
                step_id="home",
                data_schema=vol.Schema({vol.Required(CONF_HOME_ID): vol.In(homes)}),
            )

        self._home_id = user_input[CONF_HOME_ID]
        return await self.async_step_device()

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select an existing cloud device or choose manual auth import."""
        selected_home = next(
            (home for home in self._homes if _item_id(home) == self._home_id),
            {},
        )
        self._devices = [
            device
            for device in selected_home.get("devices", [])
            if isinstance(device, dict) and _device_mac(device)
        ]
        device_options = {
            DEVICE_SOURCE_MANUAL: "Manual device_auth import",
            **{
                _device_mac(device): _item_name(device, _device_mac(device))
                for device in self._devices
            },
        }

        if user_input is None:
            return self.async_show_form(
                step_id="device",
                data_schema=_device_selection_schema(device_options),
            )

        selected = user_input[CONF_DEVICE_SOURCE]
        if selected == DEVICE_SOURCE_MANUAL:
            return await self.async_step_manual()

        device = next(item for item in self._devices if _device_mac(item) == selected)
        try:
            return await self._create_cloud_entry(
                mac_address=_device_mac(device),
                name=_item_name(device, _device_mac(device)),
                device_type=_device_type(device),
            )
        except CannotConnect:
            return self.async_show_form(
                step_id="device",
                data_schema=_device_selection_schema(device_options),
                errors={"base": "cannot_connect"},
            )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Register a BLE-authenticated device with the cloud."""
        data_schema = vol.Schema({vol.Required(CONF_DEVICE_AUTH): str})
        if user_input is None:
            return self.async_show_form(step_id="manual", data_schema=data_schema)

        try:
            device_auth = user_input[CONF_DEVICE_AUTH]
            mac_address = parse_device_auth_mac(device_auth)
            normalized_device_auth = clean_device_auth(device_auth)
        except ValueError:
            return self.async_show_form(
                step_id="manual",
                data_schema=data_schema,
                errors={"base": "invalid_auth"},
            )

        await self.async_set_unique_id(mac_address)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}
        try:
            await self._api.create_device(
                self._token, self._home_id, normalized_device_auth
            )
            device_info = await self._api.get_device_info(self._token, mac_address)
            return await self._create_cloud_entry(
                mac_address=mac_address,
                name=_item_name(device_info, mac_address),
                device_type=_device_type(device_info),
            )
        except UnauthorizedError:
            errors["base"] = "invalid_auth"
        except DiffusAppApiError:
            errors["base"] = "cannot_connect"
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected manual device import error")
            errors["base"] = "unknown"

        return self.async_show_form(
            step_id="manual", data_schema=data_schema, errors=errors
        )

    async def _create_cloud_entry(
        self, *, mac_address: str, name: str, device_type: str
    ) -> FlowResult:
        if not _is_supported_device_type(device_type):
            return self.async_abort(reason="unsupported_device")

        await self.async_set_unique_id(mac_address)
        self._abort_if_unique_id_configured()
        try:
            await _verify_device(self._token, mac_address, name, device_type)
        except Exception as err:  # pylint: disable=broad-except
            raise CannotConnect from err
        return self.async_create_entry(
            title=name,
            data={
                CONF_EMAIL: self._email,
                CONF_TOKEN: self._token,
                CONF_HOME_ID: self._home_id,
                CONF_MAC_ADDRESS: mac_address,
                CONF_DEVICE_NAME: name,
                CONF_DEVICE_TYPE: device_type,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return InnovaOptionsFlowHandler(config_entry)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
