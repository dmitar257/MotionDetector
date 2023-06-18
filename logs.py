import logging
import os

LOG_FILE_NAME = 'logs/logfile.log'

def setup_logging() -> None:
    log_dir = os.path.dirname(LOG_FILE_NAME)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    formatter = logging.Formatter(
        fmt = "%(asctime)s.%(msecs)03d %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_FILE_NAME)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logging.getLogger().setLevel(logging.INFO)
    logging.getLogger().addHandler(console_handler)
    logging.getLogger().addHandler(file_handler)
