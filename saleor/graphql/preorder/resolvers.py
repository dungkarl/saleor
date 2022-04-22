from ...order import models


def resolve_preorders(_info, **_kwargs):
    return models.Order.objects.filter(is_preorder=True).order_by("-id")
