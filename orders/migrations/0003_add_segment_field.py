# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_alter_order_discount_amount_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='segment',
            field=models.CharField(
                max_length=10,
                choices=[
                    ('FBA', 'Fulfillment by Amazon'),
                    ('FBM', 'Fulfillment by Merchant'),
                ],
                null=True,
                blank=True,
                verbose_name='Fulfillment Tipi'
            ),
        ),
    ]