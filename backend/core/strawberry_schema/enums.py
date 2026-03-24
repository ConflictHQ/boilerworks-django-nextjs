import strawberry

from core.models import NotificationStatus, Profile


CoreProfileDocumentOptionChoices = strawberry.enum(
    Profile.DocumentOptions,
    name="CoreProfileDocumentOptionChoices",
    description="Profile document option choices.",
)

EnumNotificationStatus = strawberry.enum(
    NotificationStatus,
    name="EnumNotificationStatus",
    description="Notification status values.",
)
