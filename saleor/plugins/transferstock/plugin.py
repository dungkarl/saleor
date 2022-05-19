import logging
from typing import Any, Optional
from ..base_plugin import BasePlugin


class TransferStockPlugin(BasePlugin):
    PLUGIN_ID = "transferstock.write"
    PLUGIN_NAME = "TransferStock"

    def write_to_db(
            self,
            transferstock: "TransferStock",
            previous_value: Any,
    ) -> Any:
        logging.getLogger().info(transferstock)
        return []
