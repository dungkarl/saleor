from django.db import models
from saleor.warehouse.models import Warehouse
from saleor.product.models import ProductVariant
from saleor.core.models import ModelWithMetadata
from saleor.account.models import User


class TransferStock(ModelWithMetadata):

    source_warehouse = models.ForeignKey(Warehouse, related_name='source_warehouse', on_delete=models.CASCADE)
    next_warehouse = models.ForeignKey(Warehouse, related_name='next_warehouse', on_delete=models.CASCADE)
    quantity_requested = models.IntegerField(null=True, blank=True)
    product_variant = models.ForeignKey(ProductVariant, related_name='product_variant', on_delete=models.CASCADE)
    status = models.BooleanField(default=False, null=True, blank=True)
    user_request = models.ForeignKey(User, related_name='user_requested', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta(ModelWithMetadata.Meta):
        ordering = ('pk', )
