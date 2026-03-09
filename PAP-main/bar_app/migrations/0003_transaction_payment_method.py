# Generated migration for adding payment_method field to Transaction

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bar_app', '0002_alter_category_options_alter_order_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='payment_method',
            field=models.CharField(blank=True, choices=[('card', 'Cartão Escolar'), ('atm', 'Multibanco')], default='card', max_length=10),
        ),
    ]
