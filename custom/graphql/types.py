import graphene
from custom import models
from saleor.graphql.core.connection import CountableDjangoObjectType


class Custom(CountableDjangoObjectType):
    id = graphene.GlobalID(required=True)
    name = graphene.String()

    class Meta:
        model = models.Custom
