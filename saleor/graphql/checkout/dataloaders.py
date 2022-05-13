from collections import defaultdict

from django.db.models import F
from django.utils.functional import SimpleLazyObject
from promise import Promise

from ...checkout.fetch import (
    CheckoutInfo,
    CheckoutLineInfo,
    get_delivery_method_info,
    get_shipping_method_list_for_checkout_info,
)
from ...checkout.models import Checkout, CheckoutLine
from ...shipping.utils import convert_to_shipping_method_data
from ..account.dataloaders import AddressByIdLoader, UserByUserIdLoader
from ..core.dataloaders import DataLoader
from ..discount.dataloaders import VoucherByCodeLoader
from ..product.dataloaders import (
    CollectionsByVariantIdLoader,
    ProductByVariantIdLoader,
    ProductTypeByVariantIdLoader,
    ProductVariantByIdLoader,
    VariantChannelListingByVariantIdAndChannelIdLoader,
)
from ..shipping.dataloaders import (
    ShippingMethodByIdLoader,
    ShippingMethodChannelListingByChannelSlugLoader,
)


class CheckoutByTokenLoader(DataLoader):
    context_key = "checkout_by_token"

    def batch_load(self, keys):
        checkouts = Checkout.objects.using(self.database_connection_name).in_bulk(keys)
        return [checkouts.get(token) for token in keys]


class CheckoutLinesInfoByCheckoutTokenLoader(DataLoader):
    context_key = "checkoutlinesinfo_by_checkout"

    def batch_load(self, keys):
        def with_checkout_lines(results):
            checkouts, checkout_lines = results
            variants_pks = list(
                {line.variant_id for lines in checkout_lines for line in lines}
            )
            if not variants_pks:
                return [[] for _ in keys]

            channel_pks = [checkout.channel_id for checkout in checkouts]

            def with_variants_products_collections(results):
                (
                    variants,
                    products,
                    product_types,
                    collections,
                    channel_listings,
                ) = results
                variants_map = dict(zip(variants_pks, variants))
                products_map = dict(zip(variants_pks, products))
                product_types_map = dict(zip(variants_pks, product_types))
                collections_map = dict(zip(variants_pks, collections))
                channel_listings_map = dict(
                    zip(variant_ids_channel_ids, channel_listings)
                )

                lines_info_map = defaultdict(list)
                for checkout, lines in zip(checkouts, checkout_lines):
                    lines_info_map[checkout.pk].extend(
                        [
                            CheckoutLineInfo(
                                line=line,
                                variant=variants_map[line.variant_id],
                                channel_listing=channel_listings_map[
                                    (line.variant_id, checkout.channel_id)
                                ],
                                product=products_map[line.variant_id],
                                product_type=product_types_map[line.variant_id],
                                collections=collections_map[line.variant_id],
                            )
                            for line in lines
                        ]
                    )
                return [lines_info_map[key] for key in keys]

            variants = ProductVariantByIdLoader(self.context).load_many(variants_pks)
            products = ProductByVariantIdLoader(self.context).load_many(variants_pks)
            product_types = ProductTypeByVariantIdLoader(self.context).load_many(
                variants_pks
            )
            collections = CollectionsByVariantIdLoader(self.context).load_many(
                variants_pks
            )

            variant_ids_channel_ids = []
            for channel_id, lines in zip(channel_pks, checkout_lines):
                variant_ids_channel_ids.extend(
                    [(line.variant_id, channel_id) for line in lines]
                )

            channel_listings = VariantChannelListingByVariantIdAndChannelIdLoader(
                self.context
            ).load_many(variant_ids_channel_ids)
            return Promise.all(
                [variants, products, product_types, collections, channel_listings]
            ).then(with_variants_products_collections)

        checkouts = CheckoutByTokenLoader(self.context).load_many(keys)
        checkout_lines = CheckoutLinesByCheckoutTokenLoader(self.context).load_many(
            keys
        )
        return Promise.all([checkouts, checkout_lines]).then(with_checkout_lines)


class CheckoutByUserLoader(DataLoader):
    context_key = "checkout_by_user"

    def batch_load(self, keys):
        checkouts = Checkout.objects.using(self.database_connection_name).filter(
            user_id__in=keys, channel__is_active=True
        )
        checkout_by_user_map = defaultdict(list)
        for checkout in checkouts:
            checkout_by_user_map[checkout.user_id].append(checkout)
        return [checkout_by_user_map.get(user_id) for user_id in keys]


class CheckoutByUserAndChannelLoader(DataLoader):
    context_key = "checkout_by_user_and_channel"

    def batch_load(self, keys):
        user_ids = [key[0] for key in keys]
        channel_slugs = [key[1] for key in keys]
        checkouts = (
            Checkout.objects.using(self.database_connection_name)
            .filter(
                user_id__in=user_ids,
                channel__slug__in=channel_slugs,
                channel__is_active=True,
            )
            .annotate(channel_slug=F("channel__slug"))
        )
        checkout_by_user_and_channel_map = defaultdict(list)
        for checkout in checkouts:
            key = (checkout.user_id, checkout.channel_slug)
            checkout_by_user_and_channel_map[key].append(checkout)
        return [checkout_by_user_and_channel_map.get(key) for key in keys]


class CheckoutInfoByCheckoutTokenLoader(DataLoader):
    context_key = "checkoutinfo_by_checkout"

    def batch_load(self, keys):
        def with_checkout(data):
            checkouts, checkout_line_infos = data
            from ..channel.dataloaders import ChannelByIdLoader

            channel_pks = [checkout.channel_id for checkout in checkouts]
            channel_alternative_pks = [checkout.alternative_channel_id for checkout in
                                       checkouts]

            def with_channel(channels, channels_alternative=[]):
                billing_address_ids = {
                    checkout.billing_address_id
                    for checkout in checkouts
                    if checkout.billing_address_id
                }
                shipping_address_ids = {
                    checkout.shipping_address_id
                    for checkout in checkouts
                    if checkout.shipping_address_id
                }
                addresses = AddressByIdLoader(self.context).load_many(
                    billing_address_ids | shipping_address_ids
                )
                users = UserByUserIdLoader(self.context).load_many(
                    [checkout.user_id for checkout in checkouts if checkout.user_id]
                )
                shipping_method_ids = [
                    checkout.shipping_method_id
                    for checkout in checkouts
                    if checkout.shipping_method_id
                ]
                shipping_methods = ShippingMethodByIdLoader(self.context).load_many(
                    shipping_method_ids
                )
                channel_slugs = [channel.slug for channel in channels]
                shipping_method_channel_listings = (
                    ShippingMethodChannelListingByChannelSlugLoader(
                        self.context
                    ).load_many(channel_slugs)
                )
                voucher_codes = {
                    checkout.voucher_code
                    for checkout in checkouts
                    if checkout.voucher_code
                }
                vouchers = VoucherByCodeLoader(self.context).load_many(voucher_codes)

                def with_checkout_info(results):
                    (
                        addresses,
                        users,
                        shipping_methods,
                        listings_for_channels,
                        vouchers,
                    ) = results
                    address_map = {address.id: address for address in addresses}
                    user_map = {user.id: user for user in users}
                    shipping_method_map = {
                        shipping_method.id: shipping_method
                        for shipping_method in shipping_methods
                    }
                    shipping_method_channel_listing_map = {
                        (listing.shipping_method_id, listing.channel_id): listing
                        for channel_listings in listings_for_channels
                        for listing in channel_listings
                        if listing
                    }
                    voucher_map = {voucher.code: voucher for voucher in vouchers}

                    checkout_info_map = {}
                    for key, checkout, channel, alternative_channel, checkout_lines in zip(
                        keys, checkouts, channels, channels_alternative, checkout_line_infos
                    ):
                        shipping_method = shipping_method_map.get(
                            checkout.shipping_method_id
                        )
                        listing = shipping_method_channel_listing_map.get(
                            (checkout.shipping_method_id, channel.id)
                        )
                        delivery_method = None
                        if shipping_method:
                            delivery_method = convert_to_shipping_method_data(
                                shipping_method,
                                listing,
                            )

                        shipping_address = address_map.get(checkout.shipping_address_id)
                        delivery_method_info = get_delivery_method_info(
                            delivery_method, shipping_address
                        )
                        voucher = voucher_map.get(checkout.voucher_code)
                        checkout_info = CheckoutInfo(
                            checkout=checkout,
                            user=user_map.get(checkout.user_id),
                            channel=channel,
                            alternative_channel=alternative_channel,
                            billing_address=address_map.get(
                                checkout.billing_address_id
                            ),
                            shipping_address=address_map.get(
                                checkout.shipping_address_id
                            ),
                            delivery_method_info=delivery_method_info,
                            all_shipping_methods=[],
                            voucher=voucher,
                        )

                        def fetch_valid_shipping_methods():
                            if not shipping_address:
                                return []

                            manager = self.context.plugins
                            discounts = self.context.discounts
                            shipping_method_listings = [
                                listing
                                for channel_listings in listings_for_channels
                                for listing in channel_listings
                                if listing.channel_id == channel.id
                            ]
                            return get_shipping_method_list_for_checkout_info(
                                checkout_info,
                                shipping_address,
                                checkout_lines,
                                discounts,
                                manager,
                                shipping_method_listings,
                            )

                        checkout_info.all_shipping_methods = SimpleLazyObject(
                            fetch_valid_shipping_methods
                        )
                        checkout_info_map[key] = checkout_info

                    return [checkout_info_map[key] for key in keys]

                return Promise.all(
                    [
                        addresses,
                        users,
                        shipping_methods,
                        shipping_method_channel_listings,
                        vouchers,
                    ]
                ).then(with_checkout_info)

            return (
                ChannelByIdLoader(self.context)
                .load_many(channel_pks, channel_alternative_pks)
                .then(with_channel)
            )

        checkouts = CheckoutByTokenLoader(self.context).load_many(keys)
        checkout_line_infos = CheckoutLinesInfoByCheckoutTokenLoader(
            self.context
        ).load_many(keys)
        return Promise.all([checkouts, checkout_line_infos]).then(with_checkout)


class CheckoutLineByIdLoader(DataLoader):
    context_key = "checkout_line_by_id"

    def batch_load(self, keys):
        checkout_lines = CheckoutLine.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [checkout_lines.get(line_id) for line_id in keys]


class CheckoutLinesByCheckoutTokenLoader(DataLoader):
    context_key = "checkoutlines_by_checkout"

    def batch_load(self, keys):
        lines = CheckoutLine.objects.using(self.database_connection_name).filter(
            checkout_id__in=keys
        )
        line_map = defaultdict(list)
        for line in lines.iterator():
            line_map[line.checkout_id].append(line)
        return [line_map.get(checkout_id, []) for checkout_id in keys]
