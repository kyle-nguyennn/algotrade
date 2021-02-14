from pathlib import Path
import logging
import os
import tempfile

def get_project_root() -> Path:
    return Path(__file__).parent

def get_logger(name, level=None):
    logging.basicConfig(format=
    '%(asctime)s | %(name)s at line %(lineno)s | p %(processName)s | t %(threadName)s | %(levelname)s | %(message)s')
    logger = logging.getLogger(name)
    if level: logger.setLevel(level)
    return logger

def get_temp_path():
    return os.path.join(get_project_root(), 'tmp')

if __name__=='__main__':
    print(get_project_root())
    logger = get_logger(__name__, logging.DEBUG)
    logger.debug("Test debug")
    logger.info("Test info")
    logger.warning("Test warning")
    logger.error("Test error")
    logger.critical("Test critical")