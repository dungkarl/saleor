# Generated by Django 3.2.12 on 2022-04-20 08:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0118_alter_order_requested_shipment_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='is_preorder',
            field=models.BooleanField(default=False),
        ),
    ]
