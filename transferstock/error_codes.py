from enum import Enum


class TransferStockErrorCode(str, Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    STOCK_NOT_ENOUGH = "stock_not_enough"
    STOCK_INVALID = "stock_invalid"
