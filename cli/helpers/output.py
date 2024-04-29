# Logger for pretty printing and for redirecting log output if needed.  A pretty CLI is always a nice plus.
# We can also put logic here that may be needed to format for sponge or other log aggregators.
import logging
import os
from datetime import datetime

# ANSI escape codes for colors
ANSI_COLORS = {
    'DEBUG': '\033[94m',  # Blue
    'INFO': '\033[92m',   # Green
    'WARNING': '\033[93m', # Yellow
    'ERROR': '\033[91m',  # Red
    'CRITICAL': '\033[95m', # Magenta
    'RESET': '\033[0m'
}

class OutputFormatter(logging.Formatter):
    def format(self, record):
        color = ANSI_COLORS.get(record.levelname, '')
        reset = ANSI_COLORS['RESET']
        # For clarity in pass through messages we do not label info statements as INFO
        if record.levelno == logging.INFO:
            formatter = logging.Formatter("%(asctime)s - %(message)s")
        else:
            formatter = logging.Formatter(f"%(asctime)s - {color}%(levelname)s{reset} - %(message)s")
        return formatter.format(record)

def configure_logger(logger: logging.Logger, min_level='INFO', file_path=None):
    logger.setLevel(min_level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(OutputFormatter())
    logger.addHandler(console_handler)

    # Optional file handler
    if file_path:
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(file_handler)

# Example usage
# my_logger = create_logger('my_app', min_level='DEBUG', file_path='app.log')

# my_logger.debug("Debug message")
# my_logger.info("Informational message")
# my_logger.warning("Warning message")
# my_logger.error("Error message")
# my_logger.critical("Critical message")
