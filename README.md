# Levolor PG3x Plugin

A Universal Devices PG3x plugin for local control and monitoring of compatible Levolor motorized blinds through a MotionBlinds gateway.

The plugin communicates locally with the gateway using the Python `motionblinds` library and exposes discovered blinds as nodes in IoX.

## Features

- Automatic discovery of blinds connected to the MotionBlinds gateway
- Individual IoX node for each discovered blind
- Set blind position from 0–100%
- Report current blind position
- Report battery level
- Report RSSI
- Report blind availability
- Supports IoX programs and other IoX integrations through the normal node interface
- Local communication with the gateway

Discovered blinds are initially assigned generic names such as:

- Levolor 0001
- Levolor 0002
- Levolor 0003

Users may rename the nodes in IoX to match their rooms or windows. The underlying node addresses remain unchanged.

## Requirements

- Universal Devices eisy
- PG3x
- IoX
- Compatible Levolor motorized blinds
- Levolor/MotionBlinds gateway accessible on the local network
- Python 3
- `udi-interface`
- `motionblinds` version 0.6.30

The required Python packages are listed in `requirements.txt`.

## Configuration

After installing the plugin, configure these Custom Parameters in PG3x:

### gateway_ip

The local IPv4 address of the Levolor/MotionBlinds gateway.

Example:

    gateway_ip = 192.168.1.100

It is recommended that the gateway have a DHCP reservation or otherwise maintain a consistent IP address.

### gateway_key

The MotionBlinds API key for the gateway.

Example:

    gateway_key = your-gateway-key

Do not publish or share your actual gateway key.

After entering both parameters, restart the plugin.

The controller should connect to the gateway and automatically discover the associated blinds.

## IoX Nodes

The plugin creates one controller node plus one node for each discovered blind.

Each blind currently exposes:

- Position
- Battery
- RSSI
- Available
- Set Position
- Query

### Position

Position is represented as a percentage from 0–100%.

The position reported by the blind may differ slightly from the requested value after movement. For example, a requested position of 20% may subsequently be reported as 21%.

### Position Updates

Position commands are sent immediately.

Status is refreshed by normal plugin polling. The displayed position therefore may not update immediately after a blind is commanded to move.

This avoids blocking the plugin while a blind is physically traveling.

## Installation

This plugin is currently intended for PG3x on Universal Devices eisy.

For development, the repository may be installed using a PG3x Local Store entry in Developer Mode.

The executable is:

    levolor.py

The plugin profile is contained in:

    profile/

Dependencies are contained in:

    requirements.txt

## Dependencies

This plugin uses the `motionblinds` Python library:

https://github.com/starkillerOG/motion-blinds

`motionblinds` is a separate open-source project and is not included in this repository.

## Security

The gateway IP address and API key are supplied through PG3x Custom Parameters.

Do not hard-code gateway credentials into the plugin source and do not commit gateway keys to a public repository.

## Compatibility

Development and initial testing were performed with:

- PG3x 3.4.x
- IoX 6.x
- Python 3.11
- motionblinds 0.6.30
- Levolor motorized blinds using a compatible MotionBlinds gateway

Other configurations may work but have not necessarily been tested.

## Status

This project is under active development.

Core functionality currently tested includes:

- Gateway connection
- Discovery of multiple blinds
- Position reporting
- Battery reporting
- RSSI reporting
- Availability reporting
- Position control through IoX
- Plugin restart and rediscovery

Please report issues with the relevant PG3x and IoX versions, gateway type, and plugin logs when possible.

## Acknowledgments

This plugin relies on the excellent `motionblinds` Python library developed by starkillerOG and contributors.

MotionBlinds and Levolor product names and trademarks belong to their respective owners.

## License

This project is licensed under the MIT License. See `LICENSE` for details.
