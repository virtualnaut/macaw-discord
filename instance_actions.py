import boto3
import config

credentials = config.CredentialsConfig()
aws_config = config.AWSConfig()


class InstanceState:
    pending = 0
    running = 16
    shutting_down = 32
    terminated = 48
    stopping = 64
    stopped = 80


class AWSManager:
    def __init__(self):
        self._session = boto3.Session(
            aws_access_key_id=credentials.aws_access_key_id,
            aws_secret_access_key=credentials.aws_secret_access_key,
            region_name=aws_config.region
        )
        self._ec2 = self._session.resource('ec2')
        self._instance = self._ec2.Instance(aws_config.instance)

    def start(self) -> tuple:
        self._refresh()
        state = self._instance.state['Code']
        if state == InstanceState.stopped:
            self._instance.start()
            return (True, 'Starting instance...')
        elif state == InstanceState.running:
            return (False, 'The instance is already running.')
        elif state == InstanceState.pending:
            return (False, 'The instance is already starting.')
        elif state == InstanceState.stopping:
            return (False, 'The instance is stopping, please wait a few moments before trying again.')
        else:
            return (False, 'The instance cannot be started from it\'s current state')

    def stop(self):
        self._refresh()
        state = self._instance.state['Code']
        if state == InstanceState.running:
            self._instance.stop()
            return (True, 'Stopping instance...')
        elif state == InstanceState.stopping:
            return (False, 'The instance is already stopping.')
        elif state == InstanceState.stopped:
            return (False, 'The instance is already stopped.')
        elif state == InstanceState.pending:
            return (False, 'The instance is starting, please wait a few moments before trying again.')
        else:
            return (False, 'The instance cannot be stopped from it\'s current state.')

    def get_status(self) -> tuple:
        self._refresh()
        return (
            aws_config.instance,
            self._instance.state['Code'],
            self._instance.state['Name'],
            self._instance.state_transition_reason
        )

    def _refresh(self):
        self._instance = self._ec2.Instance(aws_config.instance)