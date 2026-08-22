#!/usr/bin/env python3

import sys
import hashlib
import os
import markdown2
import udi_interface
from motionblinds import MotionGateway

LOGGER = udi_interface.LOGGER

polyglot = udi_interface.Interface([])
controller = None


class BlindNode(udi_interface.Node):
    id = 'levolorblind'

    drivers = [
        {'driver': 'ST',  'value': 0, 'uom': 51},
        {'driver': 'GV1', 'value': 0, 'uom': 51},
        {'driver': 'GV2', 'value': 0, 'uom': 56},
        {'driver': 'GV3', 'value': 0, 'uom': 2},
    ]

    def __init__(self, polyglot, primary, address, name, blind):
        super().__init__(polyglot, primary, address, name)
        self.blind = blind

    def update_status(self):
        try:
            self.blind.Update()

            if self.blind.position is not None:
                self.setDriver('ST', self.blind.position)

            if self.blind.battery_level is not None:
                self.setDriver('GV1', self.blind.battery_level)

            if self.blind.RSSI is not None:
                self.setDriver('GV2', self.blind.RSSI)

            self.setDriver('GV3', 1 if self.blind.available else 0)

        except Exception as err:
            LOGGER.error(f'Error updating {self.name}: {err}')

    def set_position(self, command):
        try:
            query = command.get('query', {})

            raw_value = (
                query.get('value.uom51')
                or query.get('value')
                or command.get('value')
            )

            if raw_value is None:
                LOGGER.error(f'No position value in command: {command}')
                return

            value = int(float(raw_value))
            value = max(0, min(100, value))

            LOGGER.info(f'Setting {self.name} to {value}%')

            self.blind.Set_position(value)

        except Exception as err:
            LOGGER.error(f'Error setting {self.name}: {err}')


    def open_blind(self, command=None):
        try:
            LOGGER.info(f'Opening {self.name}')
            self.blind.Open()
        except Exception as err:
            LOGGER.error(f'Error opening {self.name}: {err}')

    def close_blind(self, command=None):
        try:
            LOGGER.info(f'Closing {self.name}')
            self.blind.Close()
        except Exception as err:
            LOGGER.error(f'Error closing {self.name}: {err}')

    def stop_blind(self, command=None):
        try:
            LOGGER.info(f'Stopping {self.name}')
            self.blind.Stop()
        except Exception as err:
            LOGGER.error(f'Error stopping {self.name}: {err}')

    def query(self, command=None):
        self.update_status()

    commands = {
        'OPEN': open_blind,
        'CLOSE': close_blind,
        'STOP': stop_blind,
        'SET_POS': set_position,
        'QUERY': query,
    }


class Controller(udi_interface.Node):
    id = 'levolorctrl'

    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 2},
    ]

    def __init__(self, polyglot, primary, address, name):
        super().__init__(polyglot, primary, address, name)

        self.gateway = None
        self.blinds = {}
        self.gateway_ip = None
        self.gateway_key = None

    def configure(self, params):
        self.gateway_ip = params.get('gateway_ip')
        self.gateway_key = params.get('gateway_key')

        if not self.gateway_ip or not self.gateway_key:
            LOGGER.warning(
                'Please configure gateway_ip and gateway_key in PG3x.'
            )
            self.setDriver('ST', 0)
            return

        self.connect_gateway()

    def connect_gateway(self):
        try:
            LOGGER.info(
                f'Connecting to Levolor gateway at {self.gateway_ip}'
            )

            self.gateway = MotionGateway(
                ip=self.gateway_ip,
                key=self.gateway_key
            )

            self.gateway.GetDeviceList()
            self.gateway.Update()

            LOGGER.info(
                f'Found {len(self.gateway.device_list)} blind(s)'
            )

            self.discover_blinds()
            self.setDriver('ST', 1)
        except Exception as err:
            LOGGER.error(f'Gateway connection failed: {err}')
            self.setDriver('ST', 0)

    def discover_blinds(self):
        for mac, blind in self.gateway.device_list.items():

            address = 'b' + hashlib.md5(
                mac.encode()
            ).hexdigest()[:10]

            name = f'Levolor {mac[-4:]}'

            if address in self.blinds:
                continue

            node = BlindNode(
                polyglot,
                self.address,
                address,
                name,
                blind
            )

            self.blinds[address] = node
            polyglot.addNode(node)

            LOGGER.info(
                f'Added blind {name} ({mac}) as {address}'
            )

    def query(self, command=None):
        for node in self.blinds.values():
            node.update_status()

    commands = {
        'QUERY': query,
    }



def custom_params_handler(params):
    global controller

    LOGGER.info('Received custom parameters')

    if controller is None:
        controller = Controller(
            polyglot,
            'controller',
            'controller',
            'Levolor Controller'
        )

        polyglot.addNode(controller)

    controller.configure(params)


def poll_handler(poll_type):
    if controller is None:
        return

    if poll_type == 'shortPoll':
        controller.query()


def stop_handler():
    LOGGER.info('Levolor plugin stopping')
    polyglot.stop()


if __name__ == '__main__':
    try:
        polyglot.start()

        polyglot.subscribe(
            polyglot.CUSTOMPARAMS,
            custom_params_handler
        )

        polyglot.subscribe(
            polyglot.POLL,
            poll_handler
        )

        polyglot.subscribe(
            polyglot.STOP,
            stop_handler
        )

        configuration_help = './configdoc.md'
        if os.path.isfile(configuration_help):
            cfgdoc = markdown2.markdown_path(configuration_help)
            polyglot.setCustomParamsDoc(cfgdoc)

        polyglot.ready()
        polyglot.updateProfile()

        polyglot.runForever()

    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)

    except Exception:
        LOGGER.exception('Unhandled exception')
        polyglot.stop()
        sys.exit(1)
