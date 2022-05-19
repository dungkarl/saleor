import graphene

from saleor.graphql.core.fields import FilterInputConnectionField
from .mutations import (
    TransferStockRequestCreate,
    TransferStockApproveCreate
)
from .types import TransferStockRequest
from .resolves import (
    resolve_request_transfers,
    resolve_request_transfer
)


class TransferStockQueries(graphene.ObjectType):
    request_transfer_stocks = FilterInputConnectionField(
        TransferStockRequest,
        description="List of transfer stock requested"
    )

    def request_transfer_stocks(self, info, **kwargs):
        return resolve_request_transfers


class TransferStockMutations(graphene.ObjectType):
    transfer_stock_request_create = TransferStockRequestCreate.Field()
    transfer_stock_approve_create = TransferStockApproveCreate.Field()
