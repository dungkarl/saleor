
import graphene
from saleor.graphql.core.connection import CountableDjangoObjectType
from saleor.graphql.account.types import User
from saleor.graphql.warehouse.types import Warehouse
from saleor.graphql.product.types import ProductVariant
from .. import models


class TransferStockRequest(CountableDjangoObjectType):
    user_requested = graphene.Field(
        User,
        description="User send request for transfer"
    )

    source_warehouse = graphene.Field(
        Warehouse,
        description="Source warehouse for transfer"
    )

    next_warehouse = graphene.Field(
        Warehouse,
        description="Source warehouse for transfer"
    )

    quantity = graphene.Int(
        description="Quantity for transfer"
    )
    product_variant = graphene.Field(
        ProductVariant,
        description="Product variant transfer"
    )

    status = graphene.Boolean(
        description="status of transfer requeted"
    )

    class Meta:
        only_fields = ["id",
                       "quantity",
                       "product_variant",
                       "source_warehouse",
                       "next_warehouse"
                       ]
        description = "Represents an item in the request transfer stock."
        interfaces = [graphene.relay.Node]
        model = models.TransferStock
        filter_fields = ["id"]
