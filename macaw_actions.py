import requests
from requests.exceptions import Timeout
import config

from instance_actions import InstanceState

credentials = config.CredentialsConfig()


class MacawState:
    instance_stopped = 0
    stopped = 1
    starting = 2
    running = 3
    stopping = 4
    macaw_starting = 5

JSON_REPONSE_MAP = {
    'stopped': MacawState.stopped,
    'starting': MacawState.starting,
    'running': MacawState.running,
    'stopping': MacawState.stopping,
}


class MacawManager:
    def __init__(self, aws_manager):
        self._aws_manager = aws_manager

    def get_state(self) -> int:
        # Check that the instance is running.
        if self._aws_manager.get_state == InstanceState.running:
            print('https://{}:8080/status?key={}'.format(self._aws_manager.get_public_ip(), config.macaw_key))
            try:
                res = requests.get('https://{}:8080/status?key={}'.format(self._aws_manager.get_public_ip(), config.macaw_key), timeout=3)
            except Timeout:
                return MacawState.macaw_starting

            json = res.json()

            return JSON_REPONSE_MAP[json['status']]
        return MacawState.instance_stopped
