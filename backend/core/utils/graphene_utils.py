from typing import Dict, List

import pydash
from graphene_django.types import ErrorType


class GrapheneUtils:
    @classmethod
    def unpack_nested_errors(cls, errors: Dict, prefix=None):
        response = []
        for k, v in errors.items():
            if prefix:
                k = f'{prefix}.{k}'
            if isinstance(v, List):
                # Convert ErrorDetail (DRF str subclass) to plain str for consistent serialization
                response.extend(ErrorType.from_errors({k: [str(m) for m in v]}))
            elif isinstance(v, Dict):
                response.extend(cls.unpack_nested_errors(v, prefix=k))
        return response

    @classmethod
    def to_camel_case(cls, text: str):
        """
        Based on  graphene.utils.str_converters.to_camel_case method, extended to cover blank spaces and dashes.
        Any inner whitespace, hyphens or dashes will be removed and the following character capitalized.
        """
        return pydash.camel_case(text)
