import graphene

from saleor.graphql.core.types.common import StockError
from saleor.graphql.warehouse.types import Warehouse
from saleor.warehouse import models
from saleor.graphql.core.mutations import ModelMutation
from .. import models
from ..error_codes import TransferStockError
from saleor.warehouse.models import Stock


def check_stock_product_variant_available(source, quantity_requested, product_variant):
    warehouse_stock_source = Stock.objects.filter(warehouse=source,
                                            product_variant=product_variant).first()
    if warehouse_stock_source.annotate_available_quantity() < quantity_requested:
        raise TransferStockError


class CreateTransferStockInput(graphene.InputObjectType):
    source_warehouse_id = graphene.ID(
        required=True,
        description="Warehouse send product"
    )
    next_warehouse_id = graphene.ID(
        required=True,
        description="Warehouse recipe product")
    product_variant = graphene.ID(
        required=True,
        description="Product variant sent"
    )
    quantity_request = graphene.Int(
        required=True,
        description="Quantity of product sent"
    )


class ApprovedTransferStockInput(graphene.InputObjectType):
    requested_id = graphene.ID(
        description="Transfer stock ID",
        required=True
    )


class CreateTransferStock(ModelMutation):
    created = graphene.Field(
        graphene.Boolean,
        description=(
            "Whether the transfer stock was created or the current active one was returned. "
        ),
    )

    class Arguments:
        input = CreateTransferStockInput(
            required=True, description="Fields required to create transfer stock."
        )

    class Meta:
        description = "Creates new transfer stock."
        model = models.StockNotify
        # permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = StockError
        error_type_field = "transfer_stock_error"

    @classmethod
    # @traced_atomic_transaction()
    def save(cls, info, instance, cleaned_input):

        # Create the checkout object
        instance.save()

    @classmethod
    def get_instance(cls, info, **data):
        instance = super().get_instance(info, **data)
        user = info.context.user
        if user.is_authenticated:
            instance.user = user
        return instance

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        user = info.context.user

        pass

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        source_warehouse_id = data.get("source_warehouse_id")
        next_warehouse_id = data.get("next_warehouse_id")
        source_warehouse = cls.get_node_or_error(info, source_warehouse_id, only_type=Warehouse)
        next_warehouse = cls.get_node_or_error(info, next_warehouse_id,
                                                 only_type=Warehouse)

        res = super().perform_mutation(_root, info, **data)
        return res


class ApprovedTransferStockCreate(ModelMutation):
    created = graphene.Field(
        graphene.Boolean,
        description=(
            "Whether the approved transfer stock was created or the current active one was returned. "
        ),
    )

    class Arguments:
        input = ApprovedTransferStockInput(
            required=True, description="Fields required to create transfer stock."
        )

    class Meta:
        description = "Approve transfer stock by admin"
        model = models.StockNotify
        # permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = StockError
        error_type_field = "transfer_stock_error"
