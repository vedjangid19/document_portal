import sys
import traceback
from logger.custom_logger import CustomLogger
from typing import Optional, cast


logger = CustomLogger().get_logger(__file__)


class DocumentPortalException(Exception):
    """Custom Exception class for Document Portal application."""

    def __init__(self, error_message, error_details:Optional[object] = None):
        # Normalize message
        if isinstance(error_message, BaseException):
            normalized_message = f"{type(error_message).__name__}: {str(error_message)}"
        else:
            normalized_message = str(error_message)

        exc_type, exc_value, exc_tb = None, None, None

        # Resolve exc_info (supports: sys module, Exception object, or current context)
        if error_details is None:
            exc_type, exc_value, exc_tb = sys.exc_info()
        else:
            if hasattr(error_details, 'exc_info'):
                exc_info_obj = cast(sys, error_details)
                exc_type, exc_value, exc_tb = exc_info_obj.exc_info()

            elif isinstance(error_details, BaseException):
                exc_type, exc_value, exc_tb = type(error_details), error_details, error_details.__traceback__
            else:
                exc_type, exc_value, exc_tb = sys.exc_info()

        # Walk to the last frame to report the most relevant location
        last_tb = exc_tb

        while last_tb and last_tb.tb_next:
            last_tb = last_tb.tb_next
        
        self.filename = last_tb.tb_frame.f_code.co_filename if last_tb else "<unknown>"
        self.lineno = last_tb.tb_lineno if last_tb else -1
        self.error_message = normalized_message

        # Full pretty traceback (if available)
        if exc_type and exc_tb:
            self.traceback_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        else:
            self.traceback_str = ""

        super().__init__(self.__str__())


    def __str__(self) -> str:
        # Compact, logger-friendly message (no leading spaces)
        base = f"Error in [{self.filename}] at line[{self.lineno}] | Message: {self.error_message}"

        if self.traceback_str:
            return f"{base}\nTraceback:\n{self.traceback_str}"
        
        return base
        

    def __repr__(self):
        return f"DocumentPortalException(file={self.filename!r}, line={self.lineno}, message={self.error_message!r})"



if __name__ == "__main__":
    try:
        a = 1 / 0
    except Exception as e:
        raise DocumentPortalException("Division Failed", e) from e
        # logger.error(app_exc)
        # raise app_exc