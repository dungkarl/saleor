from saleor.graphql.core.types.common import Error
from .enums import TransferErrorCode


class TransferError(Error):
    code = TransferErrorCode(description="The error code.", required=True)
