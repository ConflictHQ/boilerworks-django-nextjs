from django.utils.functional import classproperty


class cached_classproperty(classproperty):
    def __init__(self, method=None):
        self.fget = method

    def get_result_field_name(self):
        return self.fget.__name__ + "_property_result" if self.fget else None

    def __get__(self, instance, cls=None):
        result_field_name = self.get_result_field_name()

        if hasattr(cls, result_field_name):
            return getattr(cls, result_field_name)

        if not cls or not result_field_name:
            return self.fget(cls)

        setattr(cls, result_field_name, self.fget(cls))
        return getattr(cls, result_field_name)

    def getter(self, method):
        self.fget = method
        return self
