import requests
from requests.exceptions import Timeout
import config

from aws_actions import InstanceState

credentials = config.CredentialsConfig()


class MacawState:
    instance_stopped = 0
    stopped = 1
    starting = 2
    running = 3
    stopping = 4
    macaw_starting = 5
    macaw_stopping = 6
    macaw_stopped = 7


JSON_REPONSE_MAP = {
    'stopped': MacawState.stopped,
    'starting': MacawState.starting,
    'running': MacawState.running,
    'stopping': MacawState.stopping,
}


class MacawManager:
    def __init__(self, aws_manager):
        self._aws_manager = aws_manager

    def get_state(self, starting=True) -> int:
        # Check that the instance is running.
        if self._aws_manager.get_state() == InstanceState.running:
            try:
                res = requests.get('https://{}:8080/status?key={}'.format(self._aws_manager.get_public_ip(),
                                   credentials.macaw_key), timeout=3,
                                   verify=False)
            except Timeout:
                if starting:
                    return MacawState.macaw_starting
                else:
                    return MacawState.macaw_stopped
            except:
                if starting:
                    return MacawState.macaw_starting
                else:
                    return MacawState.macaw_stopping

            json = res.json()

            return JSON_REPONSE_MAP[json['status']]
        return MacawState.instance_stopped

    def shutdown(self):
        # Check that the instance is running.
        if self._aws_manager.get_state() == InstanceState.running:
            try:
                res = requests.get('https://{}:8080/kill?key={}'.format(self._aws_manager.get_public_ip(),
                                   credentials.macaw_key), timeout=3,
                                   verify=False)
                return True, 'Shutting system down...'
            except Timeout:
                return False, 'Failed to contact the Macaw server.'

        return False, 'The instance is not running!'

    def issue(self, command: str) -> tuple:
        # Check that the instance is running.
        if self._aws_manager.get_state() == InstanceState.running:
            try:
                res = requests.post(
                    'https://{}:8080/issue?key={}'.format(self._aws_manager.get_public_ip(), credentials.macaw_key),
                    json={'command': command},
                    timeout=3,
                    verify=False)
            except Timeout:
                return False, 'Macaw server is not running.'

            status = res.status_code

            if status == 401:
                return False, 'The Macaw API key is not correct, check the config.'
            elif status == 503:
                return False, 'The Minecraft server is not running yet.'
            else:
                return True, 'Command issued!'

        return False, 'Instance is not running.'

    def get_online_players(self) -> tuple:
        # Check that the instance is running.
        if self._aws_manager.get_state() == InstanceState.running:
            try:
                res = requests.get('https://{}:8080/status?key={}'.format(self._aws_manager.get_public_ip(),
                                   credentials.macaw_key), timeout=3,
                                   verify=False)
            except:
                return False, 'Macaw server is not running.'

            status = res.status_code
            json = res.json()

            if status == 401:
                return False, 'The Macaw API key is not correct, check the config.'
            else:
                players = json['players']
                if len(players) < 1:
                    return True, 'No-one is online :('
                else:
                    return True, '\n'.join(players)
        return False, 'Instance is not running.'