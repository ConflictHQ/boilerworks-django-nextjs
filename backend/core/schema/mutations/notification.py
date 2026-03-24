import graphene
from core.serializers.notification import NotificationSerializer
from django.utils import timezone
from graphene_django.rest_framework.mutation import SerializerMutation


class NotificationMutation(SerializerMutation):

    class Meta:
        serializer_class = NotificationSerializer
        lookup_field = 'guid'
        fields = "__all__"


class NotificationReadMutation(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        gid = graphene.ID(description='Notification Global ID')

    @classmethod
    def mutate(cls, root, info, gid):
        from core.models import NotificationStatus
        from core.schema import NotificationType

        notification = NotificationType.get_object(info, gid, raise_not_found=True)
        if notification.user != info.context.user:
            raise ValueError('Notification does not belong to user')

        notification.status = NotificationStatus.READ
        notification.status_date = timezone.now()
        notification.save()

        return cls(ok=True)
