import enum
from typing import Optional

from tea import errors


class ConsoleTeaError(errors.TeaError):
    pass


class InvalidConfiguration(ConsoleTeaError):
    class Op(str, enum.Enum):
        get = "getting"
        set = "setting"
        load = "loading"
        save = "saving"

    def __init__(
        self,
        message: Optional[str] = None,
        key: Optional[str] = None,
        value: Optional[str] = None,
        error: Optional[Exception] = None,
        operation: Op = Op.get,
    ):
        self.message = message
        self.key = key
        self.value = value
        self.error = error
        self.operation = operation
        if message is not None:
            super().__init__(message=message)
        else:
            error_msg = "" if error is None else f" {error}"
            if key is None:
                if value is None:
                    message = f"Configuration {operation} error.{error_msg}"
                else:
                    message = (
                        f"Invalid {operation} value '{value}'.{error_msg}"
                    )
            else:
                if value is None:
                    message = f"Error {operation} key='{key}'.{error_msg}"
                else:
                    message = (
                        f"Error {operation} key='{key}' value='{value}'."
                        f"{error_msg}"
                    )
            super().__init__(message=message)
