import graphene
from core.utils.api.rocketchat_rest_client import RocketchatRestClient


class GenerateRocketChatTokenMutation(graphene.Mutation):
    token = graphene.String(
        description="The temporary token of the user, ttl must be configured directly in the rocketchat server"
    )

    @classmethod
    def mutate(cls, root, info):
        client = RocketchatRestClient()
        return cls(
            token=client.create_auth_token(info.context.user)
        )
