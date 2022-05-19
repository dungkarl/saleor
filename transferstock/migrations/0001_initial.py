# Generated by Django 3.2.12 on 2022-05-19 04:30

from django.conf import settings
import django.contrib.postgres.indexes
from django.db import migrations, models
import django.db.models.deletion
import saleor.core.utils.json_serializer


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('warehouse', '0016_stock_quantity_allocated'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('product', '0151_productchannellisting_product_pro_discoun_3145f3_btree'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransferStock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('private_metadata', models.JSONField(blank=True, default=dict, encoder=saleor.core.utils.json_serializer.CustomJsonEncoder, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict, encoder=saleor.core.utils.json_serializer.CustomJsonEncoder, null=True)),
                ('quantity_requested', models.IntegerField(blank=True, null=True)),
                ('status', models.BooleanField(blank=True, default=False, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('next_warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='next_warehouse', to='warehouse.warehouse')),
                ('product_variant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='product_variant', to='product.productvariant')),
                ('source_warehouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='source_warehouse', to='warehouse.warehouse')),
                ('user_request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_requested', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('pk',),
                'abstract': False,
            },
        ),
        migrations.AddIndex(
            model_name='transferstock',
            index=django.contrib.postgres.indexes.GinIndex(fields=['private_metadata'], name='transferstock_p_meta_idx'),
        ),
        migrations.AddIndex(
            model_name='transferstock',
            index=django.contrib.postgres.indexes.GinIndex(fields=['metadata'], name='transferstock_meta_idx'),
        ),
    ]