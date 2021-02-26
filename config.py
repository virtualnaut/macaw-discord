import configparser


# 
# Base config class.
#
class Config:
    def __init__(self):
        self._parser = configparser.ConfigParser()
    
    def _parse(self, file: str) -> None:
        self._parser.read(file)


#
# Class for various credentials configuration.
#
class CredentialsConfig(Config):
    def __init__(self):
        super().__init__()

        self._parse('./config/credentials.ini')

        self.aws_access_key_id = self._parser['default']['aws_access_key_id']
        self.aws_secret_access_key = self._parser['default']['aws_secret_access_key']
        self.discord_bot_token = self._parser['default']['discord_bot_token']
        self.macaw_key = self._parser['default']['macaw_key']

#
# Class for non-credential AWS config.
#
class AWSConfig(Config):
    def __init__(self):
        super().__init__()

        self._parse('./config/aws_config.ini')

        self.region = self._parser['default']['region']
        self.instance = self._parser['default']['instance']

#
# Class for other settings.
#
class SettingsConfig(Config):
    def __init__(self):
        super().__init__()

        self._parse('./config/settings.ini')

        self.check_delay = int(self._parser['default']['check_delay'])