import pydash
from django.db.migrations.operations.base import Operation


class LibraryMkDir(Operation):
    # If this is False, it means that this operation will be ignored by
    # sqlmigrate; if true, it will be run and the SQL collected for its output.
    reduces_to_sql = False

    # If this is False, Django will refuse to reverse past this operation.
    reversible = True

    # This categorizes the operation. The corresponding symbol will be
    # displayed by the makemigrations command.
    # TODO: Add this line when we migrate to Django 5.1
    # category = OperationCategory.ADDITION

    def __init__(self, path, name, hidden=False):
        # Operations are usually instantiated with arguments in migration
        # files. Store the values of them on self for later use.
        self.path = path
        self.name = name
        self.hidden = hidden

    def state_forwards(self, app_label, state):
        # The Operation should take the 'state' parameter (an instance of
        # django.db.migrations.state.ProjectState) and mutate it to match
        # any schema changes that have occurred.
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        # The Operation should use schema_editor to apply any changes it
        # wants to make to the database.
        SharedDirectory = from_state.apps.get_model('core', 'SharedDirectory')
        SharedDirectory.objects.mkdir(self.path, self.name, hidden=self.hidden)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        # If reversible is True, this is called when the operation is reversed.
        pass

    def describe(self):
        # This is used to describe what the operation does.
        return f"library: mkdir {repr(self.path)}"

    @property
    def migration_name_fragment(self):
        return pydash.snake_case(self.describe())


class LibraryInit(Operation):
    # If this is False, it means that this operation will be ignored by
    # sqlmigrate; if true, it will be run and the SQL collected for its output.
    reduces_to_sql = False

    # If this is False, Django will refuse to reverse past this operation.
    reversible = True

    # This categorizes the operation. The corresponding symbol will be
    # displayed by the makemigrations command.
    # TODO: Add this line when we migrate to Django 5.1
    # category = OperationCategory.ADDITION

    def __init__(self):
        # Operations are usually instantiated with arguments in migration
        # files. Store the values of them on self for later use.
        pass

    def state_forwards(self, app_label, state):
        # The Operation should take the 'state' parameter (an instance of
        # django.db.migrations.state.ProjectState) and mutate it to match
        # any schema changes that have occurred.
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        # The Operation should use schema_editor to apply any changes it
        # wants to make to the database.
        SharedDirectory = from_state.apps.get_model('core', 'SharedDirectory')
        SharedDirectory.objects.init()

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        # If reversible is True, this is called when the operation is reversed.
        pass

    def describe(self):
        # This is used to describe what the operation does.
        return f"library: init {repr(self.path)}"

    @property
    def migration_name_fragment(self):
        return pydash.snake_case(self.describe())


__all__ = [
    'LibraryMkDir',
    'LibraryInit'
]
