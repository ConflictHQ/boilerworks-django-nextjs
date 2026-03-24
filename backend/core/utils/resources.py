import sys
from enum import Enum
from importlib.resources import files

import pydash


class EmbeddedResource(Enum):
    """
    Base class for embedded resources.
    """

    def __init__(self, resource: str):
        self._value_ = resource

    @property
    def content(self) -> str:
        """
        Returns the string value of the embedded resource.
        """
        package = self.__class__.__module__
        with files(package).joinpath(self.value).open("r") as file:
            return file.read()


if __name__ == "__main__":
    for line in sys.stdin:
        line = line.strip()
        print(f"""   {pydash.snake_case(line).upper()} = {repr(line)}""")
