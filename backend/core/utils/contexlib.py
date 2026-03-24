import logging


class on_error_continue:
    """
    Enables to log an error and continue
    """

    def __init__(self, logger: logging.Logger, message: str):
        self.logger = logger
        self.message = message

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            logging.exception(self.message)
