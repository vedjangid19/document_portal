import logging
import os
from datetime import datetime
import structlog


# class CustomLogger:
#     def __init__(self, log_dir="logs"):
#         # Create log directory if it doesn't exist
#         self.log_dir = os.path.join(os.getcwd(), log_dir)
#         os.makedirs(self.log_dir, exist_ok=True)

#         # Set up logging configuration
#         log_file = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
#         log_file_path = os.path.join(self.log_dir, log_file)

#         # Configure logging
#         logging.basicConfig(
#             filename=log_file_path,
#             level=logging.INFO,
#             format="[ %(asctime)s ] %(levelname)s %(name)s (line:%(lineno)d) - %(message)s",
#         )

#     def get_logger(self, name=__file__):
#         return logging.getLogger(name)
    
# if __name__ == "__main__":
#     custom_logger = CustomLogger()
#     logger = custom_logger.get_logger()
#     logger.info("Custom logger initialized successfully.")



# class CustomLogger:
#     def __init__(self, log_dir="logs"):
#         # Create log directory if it doesn't exist
#         self.log_dir = os.path.join(os.getcwd(), log_dir)
#         os.makedirs(self.log_dir, exist_ok=True)

#         # Set up logging configuration
#         log_file = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
#         self.log_file_path = os.path.join(self.log_dir, log_file)

#     def get_logger(self, name=__file__):

#         logger_name = os.path.basename(name)
#         logger = logging.getLogger(logger_name)
#         logger.setLevel(logging.INFO)

#         #formatter for both file and console handlers
#         file_formatter = logging.Formatter("[ %(asctime)s ] %(levelname)s %(name)s (line:%(lineno)d) - %(message)s")
#         console_formatter = logging.Formatter("[ %(levelname)s ] %(message)s")

#         # File handler
#         file_handler = logging.FileHandler(self.log_file_path)
#         file_handler.setFormatter(file_formatter)

#         # Console handler
#         console_handler = logging.StreamHandler()
#         console_handler.setFormatter(console_formatter)

#         if not logger.hasHandlers():
#             logger.addHandler(file_handler)
#             logger.addHandler(console_handler)

#         return logger
    
# if __name__ == "__main__":
#     custom_logger = CustomLogger()
#     logger = custom_logger.get_logger()
#     logger.info("Custom logger initialized successfully.")

        

class CustomLogger:

    def __init__(self, log_dir="logs"):
        # Create log directory if it doesn't exist
        self.log_dir = os.path.join(os.getcwd(), log_dir)
        os.makedirs(self.log_dir, exist_ok=True)

        # time format for log file name
        log_file = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        self.log_file_path = os.path.join(self.log_dir, log_file)

    def get_logger(self, name=__file__):

        logger_name = os.path.basename(name)

        # File handler

        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter("%(message)s")
        )

        # console handler

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(
            logging.Formatter("[ %(levelname)s ] %(message)s")
        )

        # logigng configuration
        logging.basicConfig(
            format="%(message)s",
            handlers=[file_handler, console_handler],
            level=logging.INFO,
        )

        # structlog configuration
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="ISO", utc=True, key="timestamp"),
                structlog.processors.add_log_level,
                structlog.processors.EventRenamer(to="event"),
                structlog.processors.JSONRenderer()
                ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        return structlog.get_logger(logger_name)
    

if __name__ == "__main__":
    custom_logger = CustomLogger()
    logger = custom_logger.get_logger()
    logger.info("Custom logger initialized successfully.")
    logger.info("user upload a file.", filename="test.pdf", user="ved", event_type="file_upload")

    logger.error("failed to process pdffile.", filename="test1.pdf", user="ved", event_type="file_error", error ="File not found")
