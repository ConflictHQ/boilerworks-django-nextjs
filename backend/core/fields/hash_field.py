import binascii

from django.db import models


class HashField(models.BigIntegerField):
    description = ('HashField is related to some other field in a model and'
                   'stores its hashed value for better indexing performance.')

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('db_index', True)
        kwargs.setdefault('editable', False)
        kwargs.setdefault('default', 0)
        super(HashField, self).__init__(*args, **kwargs)

    @classmethod
    def hash(cls, obj) -> int:
        match obj:
            case int():
                return obj
            case str():
                return binascii.crc32(obj.encode('utf8'))
            case list():
                result = 0
                for value in obj:
                    result ^= cls.hash(value)
                return result
            case frozenset() | set():
                result = 0
                for value in sorted(obj):
                    result ^= cls.hash(value)
                return result
            case dict():
                result = 0
                for key, value in sorted(obj.items()):
                    result ^= cls.hash(key)
                    result ^= cls.hash(value)
                return result
            case _:
                raise ValueError(f'Not supported object {obj}')
