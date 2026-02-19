import sys
import traceback
from logger.custom_logger import CustomLogger

logger = CustomLogger().get_logger(__file__)


class DocumentPortalException(Exception):
    """Custom Exception class for Document Portal application."""

    def __init__(self, error_message, error_details=sys) -> None:
        # def __init__(self, error_message, error_detail: sys):
        print(error_details.exc_info())
        # _, _, exc_tb = error_detail.exc_info()
        # self.filename = exc_tb.tb_frame.f_code.co_filename
        # self.line_number = exc_tb.tb_lineno
        # self.error_message = str(error_message)
        # self.traceback_str = ''.join(traceback.format_exception(*error_detail.exc_info()))
        _,_,exc_tb = error_details.exc_info()
        self.filename = exc_tb.tb_frame.f_code.co_filename
        self.line_number = exc_tb.tb_lineno
        self.error_message = str(error_message)
        self.traceback_str = ''.join(traceback.format_exception(*error_details.exc_info()))

    def __str__(self) -> str:

        return f"""
        Exception occurred in file: {self.filename} at line: {self.line_number} 
        with message: {self.error_message}
        Traceback:\n{self.traceback_str}
        """



if __name__ == "__main__":
    try:
        a = 1 / 0
    except Exception as e:
        app_exc = DocumentPortalException(e)
        logger.error(app_exc)
        raise app_exc