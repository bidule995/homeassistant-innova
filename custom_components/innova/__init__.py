"""The Innova component."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .cloud_device import InnovaCloudDevice
from .const import (
    CONF_DEVICE_NAME,
    CONF_DEVICE_TYPE,
    CONF_MAC_ADDRESS,
    CONF_TOKEN,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import InnovaCoordinator
from .grpc_client import DiffusAppGrpcClient

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SENSOR, Platform.SWITCH]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Innova AC from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    api = _device_from_entry(entry)

    # Get the scan interval from options, falling back to the default
    coordinator = await _async_update_coordinator(hass, entry, api)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for changes in options
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.innova.async_close()

    return unload_ok


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    # Reinitialize the coordinator with updated options
    coordinator = hass.data[DOMAIN][entry.entry_id]
    scan_interval_seconds = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)
    scan_interval = timedelta(seconds=scan_interval_seconds)

    # Dynamically update the polling interval
    coordinator.update_interval = scan_interval

    # Trigger an immediate refresh of the entities
    await coordinator.async_refresh()

    # Unload the existing platforms
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Recreate entities by setting up platforms again
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


async def _async_update_coordinator(
    hass: HomeAssistant, entry: ConfigEntry, api: InnovaCloudDevice
) -> InnovaCoordinator:
    """Helper function to update the coordinator."""
    scan_interval_seconds = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)
    scan_interval = timedelta(seconds=scan_interval_seconds)

    coordinator = create_coordinator(hass, api, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    # Save the coordinator in hass.data
    hass.data[DOMAIN][entry.entry_id] = coordinator

    return coordinator


def create_coordinator(
    hass: HomeAssistant, api: InnovaCloudDevice, scan_interval: timedelta
) -> InnovaCoordinator:
    """Create the coordinator with the provided scan interval."""
    coordinator = InnovaCoordinator(
        hass,
        api,
        _LOGGER,
        name=DOMAIN,
        update_interval=scan_interval
    )

    return coordinator


def _device_from_entry(entry: ConfigEntry) -> InnovaCloudDevice:
    """Create the cloud-backed device facade from a config entry."""
    mac_address = entry.data[CONF_MAC_ADDRESS]
    token = entry.data[CONF_TOKEN]
    return InnovaCloudDevice(
        grpc_client=DiffusAppGrpcClient(token=token, mac_address=mac_address),
        mac_address=mac_address,
        name=entry.data[CONF_DEVICE_NAME],
        device_type=entry.data[CONF_DEVICE_TYPE],
    )
