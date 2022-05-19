from .TransferErrorCodes import TransferErrorCode
import graphene
from saleor.graphql.warehouse.types import Warehouse
from saleor.graphql.core.mutations import ModelMutation
from .. import models
from .types import TransferStockRequest
from saleor.warehouse.models import Stock


def check_stock_product_variant_available(source_warehouse, quantity_requested, product_variant):
    warehouse_stock_source = Stock.objects.filter(warehouse=source_warehouse,
                                            product_variant=product_variant).first()
    if warehouse_stock_source.annotate_available_quantity() < quantity_requested:
        raise TransferErrorCode


class TransferStockRequestInput(graphene.InputObjectType):
    source_warehouse_id = graphene.ID(
        required=True,
        description="Source warehouse send product"
    )
    next_warehouse_id = graphene.ID(
        required=True,
        description="Next warehouse send product"
    )

    variant_id = graphene.ID(
        required=True,
        description="Product Variant for transfer"
    )
    quantity = graphene.Int(
        required=True,
        description="quantity of product variant"
    )


class TransferStockApproveRequestInput(graphene.InputObjectType):
    transferstock_request_id = graphene.ID(
        description=(
            "Request ID."
        ),
        required=True
    )


class TransferStockRequestCreate(ModelMutation):
    class Arguments:
        input = TransferStockRequestInput(
            required=True, description="Fields required to create a gift card."
        )

    class Meta:
        description = "Creates a new request stock transfer"
        model = models.TransferStock
        return_field_name = "stock_transfer_request"
        error_type_class = TransferErrorCode
        error_type_field = "stock_transfer_request_errors"

    @classmethod
    def get_type_for_model(cls):
        return TransferStockRequest


class TransferStockApproveCreate(ModelMutation):
    class Arguments:
        input = TransferStockApproveRequestInput(
            required=True, description="Fields required to create a gift card."
        )

    class Meta:
        description = "Creates a new request stock transfer"
        model = models.TransferStock
        return_field_name = "stock_transfer_request"
        error_type_class = TransferErrorCode
        error_type_field = "stock_transfer_request_errors"
