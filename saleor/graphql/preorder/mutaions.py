from typing import Tuple, List

import graphene

from django.core.exceptions import ValidationError

from ..checkout.types import Checkout
from ..core.scalars import UUID
from ..core.types.common import CheckoutError
from ..core.validators import validate_variants_available_in_channel
from ..order.mutations import orders
from ..order.mutations import draft_orders
from django.contrib.auth.models import AnonymousUser
from ...product import models as product_models

from ..checkout.mutations import CheckoutCreate, CheckoutCreateInput, \
    validate_variants_available_for_purchase, validate_variants_are_published, \
    check_lines_quantity, CheckoutComplete, get_checkout_by_token
from ..utils import get_user_or_app_from_context
from ...checkout import models as checkout_models
from ...checkout.complete_checkout import complete_checkout
from ...checkout.error_codes import CheckoutErrorCode
from ...checkout.fetch import fetch_checkout_lines, fetch_checkout_info
from ...core import analytics
from ...core.permissions import AccountPermissions
from ...core.transactions import transaction_with_commit_on_errors
from ..product.types import ProductVariant
from ..core.validators import (
    validate_one_of_args_is_in_mutation,
    validate_variants_available_in_channel,
)
from ...order.models import Order


# class PreOrderCreateInput(CheckoutCreateInput):
#     requested_shipment_date = graphene.Date()
#     is_preorder = graphene.Boolean()
#

class PreOrderCreate(CheckoutCreate):
    class Arguments:
        input = CheckoutCreateInput(
            required=True, description="Fields required to create preorder checkout."
        )

    class Meta:
        description = "Create a new checkout."
        model = checkout_models.Checkout
        return_field_name = "checkout"
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def clean_checkout_lines(
            cls, lines, country, channel
    ) -> Tuple[List[product_models.ProductVariant], List[int]]:
        variant_ids = [line["variant_id"] for line in lines]
        variants = cls.get_nodes_or_error(
            variant_ids,
            "variant_id",
            ProductVariant,
            qs=product_models.ProductVariant.objects.prefetch_related(
                "product__product_type"
            ),
        )

        quantities = [line["quantity"] for line in lines]
        variant_db_ids = {variant.id for variant in variants}
        validate_variants_available_for_purchase(variant_db_ids, channel.id)
        validate_variants_available_in_channel(
            variant_db_ids, channel.id, CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL
        )
        validate_variants_are_published(variant_db_ids, channel.id)
        try:
            check_lines_quantity(variants, quantities, country, channel.slug)
        except ValidationError as e:
            if not e.error_dict.get('quantity', False):
                raise e
        return variants, quantities


class PreOrderComplete(CheckoutComplete):

    class Arguments:
        checkout_id = graphene.ID(
            description=(
                "Checkout ID."
                "DEPRECATED: Will be removed in Saleor 4.0. Use token instead."
            ),
            required=False,
        )
        token = UUID(description="Checkout token.", required=False)
        store_source = graphene.Boolean(
            default_value=False,
            description=(
                "Determines whether to store the payment source for future usage."
            ),
        )
        redirect_url = graphene.String(
            required=False,
            description=(
                "URL of a view where users should be redirected to "
                "see the order details. URL in RFC 1808 format."
            ),
        )
        payment_data = graphene.JSONString(
            required=False,
            description=(
                "Client-side generated data required to finalize the payment."
            ),
        )
        requested_shipment_date = graphene.Date(required=True)
        is_preorder = graphene.Boolean(required=True)

    class Meta:
        description = (
            "Completes the checkout. As a result a new order is created and "
            "a payment charge is made. This action requires a successful "
            "payment before it can be performed. "
            "In case additional confirmation step as 3D secure is required "
            "confirmationNeeded flag will be set to True and no order created "
            "until payment is confirmed with second call of this mutation."
        )
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(
        cls, _root, info, store_source, checkout_id=None, token=None, **data
    ):
        #DEPRECATED
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "checkout_id", checkout_id, "token", token
        )

        tracking_code = analytics.get_client_id(info.context)
        with transaction_with_commit_on_errors():
            try:
                if token:
                    checkout = get_checkout_by_token(token)
                # DEPRECATED
                else:
                    checkout = cls.get_node_or_error(
                        info,
                        checkout_id or token,
                        only_type=Checkout,
                        field="checkout_id",
                    )
            except ValidationError as e:
                # DEPRECATED
                if checkout_id:
                    token = cls.get_global_id_or_error(
                        checkout_id, only_type=Checkout, field="checkout_id"
                    )

                order = Order.objects.get_by_checkout_token(token)
                if order:
                    if not order.channel.is_active:
                        raise ValidationError(
                            {
                                "channel": ValidationError(
                                    "Cannot complete checkout with inactive channel.",
                                    code=CheckoutErrorCode.CHANNEL_INACTIVE.value,
                                )
                            }
                        )
                    # The order is already created. We return it as a success
                    # checkoutComplete response. Order is anonymized for not logged in
                    # user
                    return CheckoutComplete(
                        order=order, confirmation_needed=False, confirmation_data={}
                    )
                raise e

            manager = info.context.plugins
            lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
            if unavailable_variant_pks:
                not_available_variants_ids = {
                    graphene.Node.to_global_id("ProductVariant", pk)
                    for pk in unavailable_variant_pks
                }
                raise ValidationError(
                    {
                        "lines": ValidationError(
                            "Some of the checkout lines variants are unavailable.",
                            code=CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.value,
                            params={"variants": not_available_variants_ids},
                        )
                    }
                )
            if not lines:
                raise ValidationError(
                    {
                        "lines": ValidationError(
                            "Cannot complete checkout without lines.",
                            code=CheckoutErrorCode.NO_LINES.value,
                        )
                    }
                )
            checkout_info = fetch_checkout_info(
                checkout, lines, info.context.discounts, manager
            )

            requestor = get_user_or_app_from_context(info.context)
            if requestor.has_perm(AccountPermissions.IMPERSONATE_USER):
                # Allow impersonating user and process a checkout by using user details
                # assigned to checkout.
                customer = checkout.user or AnonymousUser()
            else:
                customer = info.context.user
            requested_shipment_date = data.get('requested_shipment_date')
            is_preorder = data.get('is_preorder')
            if requested_shipment_date and is_preorder:
                checkout_info.checkout.metadata['requested_shipment_date'] = \
                    requested_shipment_date
                checkout_info.checkout.metadata['is_preorder'] = is_preorder

            order, action_required, action_data = complete_checkout(
                manager=manager,
                checkout_info=checkout_info,
                lines=lines,
                payment_data=data.get("payment_data", {}),
                store_source=store_source,
                discounts=info.context.discounts,
                user=customer,
                app=info.context.app,
                site_settings=info.context.site.settings,
                tracking_code=tracking_code,
                redirect_url=data.get("redirect_url"),
            )
        # If gateway returns information that additional steps are required we need
        # to inform the frontend and pass all required data
        return CheckoutComplete(
            order=order,
            confirmation_needed=action_required,
            confirmation_data=action_data,
        )
