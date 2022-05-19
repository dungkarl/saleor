from .. import models


def resolve_request_transfers():
    qs = models.RequestTransferStock.objects.all()
    return qs


def resolve_request_transfer(id):
    return models.RequestTransferStock.objects.get(id)
