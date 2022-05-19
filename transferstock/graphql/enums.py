import graphene
from transferstock import error_codes as transfer_error_codes

TransferErrorCode = graphene.Enum.from_enum(transfer_error_codes.TransferStockErrorCode)
