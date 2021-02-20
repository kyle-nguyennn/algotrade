import json
import logging
import os
from utils import get_project_root, get_logger

logger = get_logger(__name__, logging.INFO)

class Setting:
    """
    A singleton that contains the process's settings, being initialized at process startup
        sender_email: str
            Sender email address used for reporting
        sender_email_password: str
            Password to sender email
        account_config_path: str
            Path to configuration file for account
        graph_file_extension: str
            File extension for picture of graphs
    """
    setting = None
    @classmethod
    def get(cls):
        if cls.setting:
            logger.info(f"Accessing setting {cls.setting}")
            return cls.setting
        else:
            cls.setting = Setting()
            cls.__populateSetting()
            return cls.setting
    @classmethod
    def __populateSetting(cls):
        rootDir = get_project_root()
        path = os.path.join(rootDir, 'settings.json')
        envDict = json.loads(open(path).read())
        for k, v in envDict.items():
            setattr(cls.setting, k, v)