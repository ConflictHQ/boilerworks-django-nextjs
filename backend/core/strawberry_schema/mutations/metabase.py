"""Metabase mutations migrated from Graphene to Strawberry."""
from __future__ import annotations

import strawberry
from strawberry.types import Info

from core.serializers.metabase import MetabaseChartSerializer
from core.strawberry_schema.common import GlobalIDUtils, MutationResult


@strawberry.type
class MetabaseMutations:

    @strawberry.mutation(description="Create or update a Metabase chart via MetabaseChartSerializer.")
    def metabase_chart(self, info: Info, input: strawberry.scalars.JSON) -> MutationResult:
        from core.models import MetabaseChart

        # Resolve global ID to PK if present (mirrors RestrictedSerializerMutation)
        instance_id = input.pop('id', None)
        instance = None
        if instance_id:
            pk = GlobalIDUtils.get_pk_flexible(instance_id)
            if pk:
                instance = MetabaseChart.objects.filter(pk=pk).first()

        # Permission check (mirrors RestrictedSerializerMutation.has_model_permissions)
        user = info.context.user
        if instance:
            MetabaseChart.p('model').change.check(user)
        else:
            MetabaseChart.p('model').add.check(user)

        kwargs = {
            'data': input,
            'partial': True,
        }
        if instance is not None:
            kwargs['instance'] = instance

        serializer = MetabaseChartSerializer(**kwargs)
        if serializer.is_valid():
            serializer.save()
            return MutationResult.success()
        else:
            return MutationResult.from_serializer_errors(serializer.errors)
