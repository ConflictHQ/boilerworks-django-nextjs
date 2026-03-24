import sys
from collections import defaultdict

import pydash


def r2tensor() -> defaultdict[
    str,
    defaultdict[str, str]
]:
    return defaultdict(
        lambda: defaultdict(
            lambda: None
        )
    )


def r3tensor() -> defaultdict[
    str,
    defaultdict[
        str,
        defaultdict[str, str]
    ]
]:
    return defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(
                lambda: None
            )
        )
    )


def r4tensor() -> defaultdict[
    str, defaultdict[
        str,
        defaultdict[
            str,
            defaultdict[str, str]
        ]
    ]
]:
    return defaultdict(
        lambda: defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(
                    lambda: None
                )
            )
        )
    )


def main(*args, **kwargs):
    tree = r4tensor()
    functor = r2tensor()

    functor["email"]["header"] = "email_header_template"
    functor["email"]["body"] = "email_body_template"

    functor["android"]["header"] = "android_push_header_template"
    functor["android"]["body"] = "android_push_body_template"

    functor["ios"]["body"] = "ios_push_header_template"
    functor["ios"]["header"] = "ios_push_body_template"

    functor["webapp"]["body"] = "webapp_header_template"
    functor["webapp"]["header"] = "webapp_body_template"

    functor["sms"]["header"] = "sms_header_template"
    functor["sms"]["body"] = "sms_body_template"

    for line in sys.stdin:
        line: str = line.strip()
        category, notification, filename = line.split('/')
        delivery_method, section, extension = filename.split('.')
        tree[category][notification][delivery_method][section] = line

    print("class NotificationResources(EmbeddedResource):")
    for category, notifications in tree.items():
        for notification, delivery_methods in notifications.items():
            for delivery_method, sections in delivery_methods.items():
                for section, line in sections.items():
                    indentation = ' ' * 4
                    member_name = pydash.snake_case(line).upper()
                    literal = repr(line)
                    print(f"{indentation}{member_name} = {literal}")
    print("")
    print("")
    print("class Notifications(BaseNotification):")
    for category, notifications in tree.items():
        for notification, delivery_methods in notifications.items():
            templates = {
                field: delivery_methods[delivery_method][section]
                for delivery_method, sections in functor.items()
                for section, field in sections.items()
            }
            print(f"""{' ' * 4}{category.upper()}_{notification.upper()} = NotificationDefinition(""")
            print(f"""{' ' * 8}identifier = '{category}/{notification}',""")
            for filed, value in templates.items():
                print(f"""{' ' * 8}{filed} = NotificationResources.{pydash.snake_case(value).upper()},""")
            print(f"""{' ' * 4})""")
            print()


if __name__ == '__main__':
    main(*sys.argv)
