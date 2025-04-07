"""RPG game logging module providing centralized logging functionality."""

import logging
import sys
from pathlib import Path


class RPGLogger:
    """Simple logger for the game that sets up both console and file logging."""

    def __init__(self) -> None:
        """Initialize the logger with console and file handlers.

        Sets up a logger with appropriate handlers for both console and file output.
        The log file is created in the parent directory of the current file.
        """
        # for log files, use the executables directory, not _MEIPASS
        if getattr(sys, "frozen", False):
            # running as bundled exe
            log_dir = Path(sys.executable).parent
        else:
            # running in normal Python environment
            log_dir = Path(__file__).parent.parent

        self.log_path = log_dir / "rpg_game.log"

        # create logger
        self.logger = logging.getLogger("rpg_game")

        # only add handlers if they haven't been added yet
        if not self.logger.handlers:
            # configure console handler
            console_handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # add file handler
            file_handler = logging.FileHandler(self.log_path)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            # set level
            self.logger.setLevel(logging.DEBUG)

    def get_logger(self) -> logging.Logger:
        """Return the configured logger instance."""
        return self.logger


# singleton pattern for easy access
class _LoggerState:
    instance: logging.Logger | None = None


def get_logger() -> logging.Logger:
    """Return the standard logger instance."""
    if _LoggerState.instance is None:
        game_logger = RPGLogger()
        _LoggerState.instance = game_logger.get_logger()
    return _LoggerState.instance