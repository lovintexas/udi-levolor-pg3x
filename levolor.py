#!/usr/bin/env python3

import sys
import hashlib
import threading
import os
import markdown2
import udi_interface
from motionblinds import MotionGateway

LOGGER = udi_interface.LOGGER
VERSION = "1.0.4"

polyglot = udi_interface.Interface([])
controller = None
poll_lock = threading.Lock()
gateway_update_lock = threading.Lock()

rapid_poll_state_lock = threading.Lock()
active_rapid_polls = 0


class BlindNode(udi_interface.Node):
    id = 'levolorblind'

    drivers = [
        {'driver': 'GV4', 'value': 0, 'uom': 51},
        {'driver': 'GV1', 'value': 0, 'uom': 51},
        {'driver': 'GV2', 'value': 0, 'uom': 56},
        {'driver': 'GV3', 'value': 0, 'uom': 2},
    ]

    def __init__(self, polyglot, primary, address, name, blind):
        super().__init__(polyglot, primary, address, name)
        self.blind = blind
        self._rapid_poll_generation = 0
        self._rapid_poll_lock = threading.Lock()

    def update_status(self):
        try:
            with gateway_update_lock:
                self.blind.Update()

            if self.blind.position is not None:
                self.setDriver('GV4', self.blind.position)

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

            with gateway_update_lock:
                self.blind.Set_position(value)
            self.rapid_poll(value)

        except Exception as err:
            LOGGER.error(f'Error setting {self.name}: {err}')


    def rapid_poll(self, target):
        # A new movement command invalidates any previous rapid poll
        # for this same blind.
        with self._rapid_poll_lock:
            self._rapid_poll_generation += 1
            generation = self._rapid_poll_generation

        def worker():
            global active_rapid_polls

            with rapid_poll_state_lock:
                active_rapid_polls += 1

            try:
                # Poll immediately, then every 10 seconds
                # for up to 3 minutes.
                for attempt in range(19):

                    # Stop if another movement command has since
                    # been issued to this same blind.
                    with self._rapid_poll_lock:
                        if generation != self._rapid_poll_generation:
                            LOGGER.info(
                                f'Rapid polling superseded for {self.name}'
                            )
                            return

                    try:
                        self.update_status()

                        if self.blind.position is not None:
                            position = int(self.blind.position)

                            LOGGER.info(
                                f'Rapid poll {self.name}: '
                                f'position={position}%, target={target}%'
                            )

                            if position == target:
                                LOGGER.info(
                                    f'{self.name} reached target {target}%'
                                )
                                return

                    except Exception as err:
                        LOGGER.error(
                            f'Rapid poll error for {self.name}: {err}'
                        )

                    if attempt < 18:
                        threading.Event().wait(10)

                LOGGER.info(
                    f'Rapid polling ended for {self.name}; '
                    f'target {target}% not yet confirmed'
                )

            finally:
                with rapid_poll_state_lock:
                    active_rapid_polls -= 1

        threading.Thread(
            target=worker,
            daemon=True,
            name=f'RapidPoll-{self.address}'
        ).start()

    def open_blind(self, command=None):
        try:
            LOGGER.info(f'Opening {self.name}')
            with gateway_update_lock:
                self.blind.Open()
            self.rapid_poll(0)
        except Exception as err:
            LOGGER.error(f'Error opening {self.name}: {err}')

    def close_blind(self, command=None):
        try:
            LOGGER.info(f'Closing {self.name}')
            with gateway_update_lock:
                self.blind.Close()
            self.rapid_poll(100)
        except Exception as err:
            LOGGER.error(f'Error closing {self.name}: {err}')

    def stop_blind(self, command=None):
        try:
            LOGGER.info(f'Stopping {self.name}')
            with gateway_update_lock:
                self.blind.Stop()

            # Cancel rapid polling for the previous movement target.
            with self._rapid_poll_lock:
                self._rapid_poll_generation += 1
        except Exception as err:
            LOGGER.error(f'Error stopping {self.name}: {err}')

    def query(self, command=None):
        self.update_status()

    commands = {
        'STOP': stop_blind,
        'DON': close_blind,
        'DOF': open_blind,
        'SET_POS': set_position,
        'QUERY': query,
    }


class Controller(udi_interface.Node):
    id = 'levolorctrl'

    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 25},
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

    if poll_type != 'shortPoll':
        return

    with rapid_poll_state_lock:
        if active_rapid_polls > 0:
            LOGGER.debug(
                f'Skipping normal shortPoll; '
                f'{active_rapid_polls} rapid poll(s) active'
            )
            return

    if not poll_lock.acquire(blocking=False):
        LOGGER.warning('Previous blind poll still running; skipping this poll')
        return

    try:
        controller.query()
    finally:
        poll_lock.release()


def stop_handler():
    LOGGER.info('Levolor plugin stopping')
    polyglot.stop()


if __name__ == '__main__':
    try:
        polyglot.start(VERSION)

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
