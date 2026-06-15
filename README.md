[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)

# homeassistant-innova

Custom Home Assistant integration for EVOLUSION/Innova units that use the newer Solution Tech DiffusApp Wi-Fi module.

This fork keeps the Home Assistant domain as `innova`, but replaces the old local `/api/v/1/status` client with the DiffusApp cloud API:

- REST login and device registration through `https://api.innova.solutiontech.tech/api/`
- gRPC status and control through `grpc.innova.solutiontech.tech:443`
- Cloud polling with a default scan interval of 600 seconds
- One Home Assistant config entry per physical unit

The first DiffusApp cloud version targets Duepuntozero/STG-compatible devices. Other Solution Tech device types are aborted until their command maps are known.

## Installation

### HACS Custom Repository

1. In HACS, add `https://github.com/bidule995/homeassistant-innova` as a custom integration repository.
2. Install the Innova integration from HACS.
3. Restart Home Assistant.
4. Go to **Settings -> Devices & Services -> Add Integration -> Innova**.

### Manual Installation

Copy `custom_components/innova` from this repository into your Home Assistant configuration directory:

```text
config/custom_components/innova
```

Restart Home Assistant after copying the files.

## Configuration

Add each physical air conditioner separately.

1. Sign in with the same email and password used by Diffus'app.
2. Select an existing DiffusApp home. If the account has no homes, the integration creates one named `Home` using the Home Assistant time zone.
3. Select a cloud-listed device, or choose manual import and paste one BLE `device_auth` hex value.

For manual import, the integration extracts the base MAC address from the first 12 hex characters of `device_auth`, registers the device with `POST devices`, verifies it with `GET devices/{macAddress}`, and performs a first gRPC status fetch before creating the entry.

The DiffusApp password and pasted `device_auth` are not stored. Home Assistant stores the DiffusApp email, cloud token, home ID, MAC address, device name, and device type.

## Known Units

The target EVOLUSION STG 12HP units are expected to be added as separate entries:

| Room | MAC address |
| --- | --- |
| Office | `FC:01:2C:FA:13:1C` |
| Bedroom | `FC:01:2C:F8:15:2C` |

## Supported Controls

- Power on/off
- Target temperature in Celsius tenths
- Mode: auto, heat, cool, fan-only, dry
- Fan: auto, low, medium, high
- Flap/swing on/off
- Current room temperature sensor

Scheduling, presets, keyboard lock, Home Assistant Bluetooth provisioning, and gRPC event streaming are intentionally left out of v1.

## Notes

If manual cloud registration succeeds but status verification still fails, the unit may need to re-run the DiffusApp BLE provisioning sequence so the module reconnects to Wi-Fi and the cloud. For the EVOLUSION/STG units, the app instructions were:

1. Maintain power for 10 seconds.
2. Select `uP`.
3. Select `St`.

After the unit appears in the DiffusApp cloud, add it again in Home Assistant.
