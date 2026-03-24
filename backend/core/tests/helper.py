from random import Random

from core.tests.utils.core_gql import CoreGQL
from core.tests.utils.gql_helper import JObject
from django.contrib.auth.models import User


class CoreGQLTestHelper:

    def __init__(self):
        self.next_user = _next_user()
        self.core_gql = CoreGQL.instance()

    def create_random_user(self, context=None) -> JObject:
        return self.create_user(self.next_user(), context)

    def create_user(self, user_data, context=None) -> JObject:
        # users are created at login time, so we need to create the user first
        User.objects.get_or_create(username=user_data['username'], email=user_data['email'])
        context = self.core_gql.context(username=user_data['username'])

        return self.core_gql.exec('upsertUser', context, **user_data)

    def create_index_user(self, index, postfix='', context=None) -> JObject:
        return self.create_user(_user(index), context).first('instance')

    def get_assignable_permissions(self, module, assignable) -> JObject:
        return self.core_gql.exec('assignablePermissions', module=module, assignable=assignable)


random = Random()
random.seed(0)  # sets the sequences always equal


def next_index(max_index):
    index = -1
    postfix = ''

    def next_index():
        nonlocal index
        nonlocal postfix

        if index >= max_index:
            index = 0
            postfix += '1'
        else:
            index += 1

        return index, postfix

    return next_index


names = ['Christopher Kelly', 'Caitlin Branch', 'Anthony Potter', 'Perry Holmes',
         'Rachael Horn', 'Gene Martinez', 'Jacob Smith', 'Emily Anderson',
         'Jason Miller', 'Jo Rodriguez', 'Marc Gonzalez', 'Sara Conley', 'Jerome Krause',
         'Charles Robinson', 'Christina Daniel', 'Donna Smith', 'Rhonda Martin', 'Alexander Robinson',
         'Timothy Bailey', 'Jennifer Armstrong', 'Tammy Liu', 'John Woodward',
         'Donald Hale', 'Veronica Rodriguez', 'David Shaw', 'Jeffrey James', 'David Smith',
         'Michelle Merritt', 'Justin Clark', 'Erik Allen', 'Rachel Adams', 'Andrea Orr',
         'Katherine Valdez', 'Tina Russell', 'Marie Bauer', 'Michael Schroeder', 'Dorothy Morales',
         'Christie Strong', 'Candice King', 'Cynthia Murphy']


def _next_user():
    next_idx = next_index(len(names))

    def next_user():
        index, postfix = next_idx()
        return _user(index, postfix)

    return next_user


def _user(index, postfix=''):
    first_name, last_name = names[index].split(' ')
    first_name = f'{first_name}{postfix}'
    email = f'{first_name}@{last_name}.com'

    return {
        'username': email,
        'email': email,
        'firstName': first_name,
        'lastName': last_name,
        'phoneNumber': '+1 3141 5926',
        'avatar': f'https://i.pravatar.cc/50?u={index}100{postfix}',
    }


def default_prepare(data, prefix, index):
    return data


class Generator:

    def __init__(self, array_data, prepare=default_prepare):
        self.array_data = array_data
        self.prepare = prepare
        self.index = -1
        self.postfix = ''

    def next(self):
        self.index += 1
        if self.index >= len(self.array_data):
            self.index = 0
            self.postfix += '1'

        return self.instance(index=self.index, postfix=self.postfix)

    def random(self):
        idx = random.randint(0, len(self.array_data))
        return self.instance(idx, str(idx))

    def instance(self, index, postfix=''):
        data = self.array_data[index]
        if hasattr(data, 'copy'):
            data = data.copy()
        return self.prepare(data, postfix, index)
