"""PST5 administrative utilities: repeat-safe file logging and timestamped backups."""
import logging
import shutil
from datetime import datetime
from pathlib import Path


def init_logger(log_file='msms.log'):
    """Attach one UTF-8 file handler per path, without duplicating on GUI reruns."""
    path = Path(log_file).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(path) for h in logger.handlers):
        handler = logging.FileHandler(path, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger


def backup_data(data_path='data/msms.json', backup_dir='data/backups'):
    """Copy data to a unique timestamped file; return False on filesystem failure."""
    try:
        destination = Path(backup_dir)
        destination.mkdir(parents=True, exist_ok=True)
        name = f'msms_backup_{datetime.now():%Y-%m-%d_%H-%M-%S_%f}.json'
        shutil.copy2(data_path, destination / name)
        logging.info('Data backup created: %s', name)
        return True
    except OSError as error:
        logging.error('Data backup failed: %s', error)
        return False
