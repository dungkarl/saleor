import graphene
from graphene import relay

from ..meta.types import ObjectWithMetadata
from ..order.types import Order
from ...order import models


class PreOrderType(Order):
    requested_shipment_date = graphene.Date()
    is_preorder = graphene.Boolean()

    class Meta:
        description = "Represents an pre-order in the shop."
        interfaces = [relay.Node, ObjectWithMetadata]
        model = models.Order

