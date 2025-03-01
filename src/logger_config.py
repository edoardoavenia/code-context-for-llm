import logging

def setup_logger(name=__name__, level=logging.INFO):
    """
    Sets up and returns a logger with a standardized format.
    Ensures that the logger only adds handlers once.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    return logger
