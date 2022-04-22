import graphene
from ...core.permissions import OrderPermissions
from ..decorators import permission_required
from ...order.models import Order

from .resolvers import (
    resolve_preorders
)
from ..core.fields import FilterInputConnectionField, PrefetchingConnectionField
from ..order.sorters import OrderSortingInput
from ..order.schema import OrderFilterInput, OrderQueries
from .types import PreOrderType
from ..checkout.schema import CheckoutMutations
from .mutaions import PreOrderCreate, PreOrderComplete
from ..order.types import Order


class PreOrderQueries(OrderQueries):
    preorders = FilterInputConnectionField(
        PreOrderType,
        sort_by=OrderSortingInput(description="Sort orders."),
        filter=OrderFilterInput(description="Filtering options for orders."),
        channel=graphene.String(
            description="Slug of a channel for which the data should be returned."
        ),
        description="List of pre orders.",
    )

    @permission_required(OrderPermissions.MANAGE_ORDERS)
    def resolve_preorders(self, info, **_kwargs):
        return resolve_preorders(info)


class PreOrderMutations(CheckoutMutations):

    preorder_create = PreOrderCreate.Field()
    preorder_complete_create = PreOrderComplete.Field()
