import logging
from config.env_vars import load_config

load_config()

class ColoredFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    blue = "\x1b[34;20m"
    cyan = "\x1b[36;20m"
    reset = "\x1b[0m"

    def format(self, record):
        # ensure class_name is always present to avoid KeyError in formatting
        if not hasattr(record, "class_name"):
            record.class_name = ""

        # Select color for level
        if record.levelno == logging.DEBUG:
            level_color = self.blue
        elif record.levelno == logging.INFO:
            level_color = self.green
        elif record.levelno == logging.WARNING:
            level_color = self.yellow
        elif record.levelno == logging.ERROR:
            level_color = self.red
        elif record.levelno == logging.CRITICAL:
            level_color = self.bold_red
        else:
            level_color = self.grey

        # Format time
        record.asctime = self.formatTime(record, self.datefmt)

        # Build the log string
        # Time | Level | File:Line | [Class] | Message
        
        log_str = f"{self.grey}{record.asctime}{self.reset} | "
        log_str += f"{level_color}{record.levelname:<8}{self.reset} | "
        log_str += f"{self.cyan}{record.filename}:{record.lineno}{self.reset} | "
        
        if record.class_name:
             log_str += f"[{record.class_name}] "
        
        log_str += f"{record.getMessage()}"

        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        
        if record.exc_text:
            log_str += f"\n{record.exc_text}"
            
        return log_str

class ContextLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = self.extra.copy()
        extra.update(kwargs.get("extra", {}))
        kwargs["extra"] = extra
        return msg, kwargs

def get_logger(name: str, class_name: str | None = None):
    logger = logging.getLogger(name)
    # avoid adding multiple handlers when called repeatedly
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(ColoredFormatter(datefmt="%Y-%m-%d %H:%M:%S"))
        logger.addHandler(ch)
    return ContextLoggerAdapter(logger, {"class_name": class_name or ""})

# convenience module-level logger (no class_name)
my_logger = get_logger(__name__)