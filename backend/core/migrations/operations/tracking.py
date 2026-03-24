import pydash
from core.models import system_user
from django.db import DatabaseError
from django.db.migrations.operations.base import Operation


class SetTrackingUserForModel(Operation):
    # If this is False, it means that this operation will be ignored by
    # sqlmigrate; if true, it will be run and the SQL collected for its output.
    reduces_to_sql = False

    # If this is False, Django will refuse to reverse past this operation.
    reversible = True

    # This categorizes the operation. The corresponding symbol will be
    # displayed by the makemigrations command.
    # TODO: Add this line when we migrate to Django 5.1
    # category = OperationCategory.ADDITION

    def __init__(self, app_label, model_name):
        # Operations are usually instantiated with arguments in migration
        # files. Store the values of them on self for later use.
        self.app_label = app_label
        self.model_name = model_name

    def state_forwards(self, app_label, state):
        # The Operation should take the 'state' parameter (an instance of
        # django.db.migrations.state.ProjectState) and mutate it to match
        # any schema changes that have occurred.
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        # The Operation should use schema_editor to apply any changes it
        # wants to make to the database.
        user_model_class = from_state.apps.get_model('auth', 'user')
        model_class = from_state.apps.get_model(self.app_label, self.model_name)
        user = system_user(user_model_class)
        if user is None:
            raise DatabaseError('Unable to find system user')
        model_class.objects.filter(created_by__isnull=True).update(created_by=user)
        model_class.objects.filter(updated_by__isnull=True).update(updated_by=user)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        # If reversible is True, this is called when the operation is reversed.
        pass

    def describe(self):
        # This is used to describe what the operation does.
        return f"Set Created|Updated by on {self.app_label}.{self.model_name}"

    @property
    def migration_name_fragment(self):
        return pydash.snake_case(self.describe())
