# Generated migration for BarSchedule model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bar_app', '0003_transaction_payment_method'),
    ]

    operations = [
        migrations.CreateModel(
            name='BarSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_of_week', models.IntegerField(choices=[(0, 'Segunda-feira'), (1, 'Terça-feira'), (2, 'Quarta-feira'), (3, 'Quinta-feira'), (4, 'Sexta-feira'), (5, 'Sábado'), (6, 'Domingo')], unique=True)),
                ('is_open', models.BooleanField(default=True, help_text='O bar está aberto neste dia?')),
                ('opening_time', models.TimeField(default='07:00', help_text='Hora de abertura')),
                ('closing_time', models.TimeField(default='19:00', help_text='Hora de encerramento')),
            ],
            options={
                'verbose_name': 'Horário de Funcionamento',
                'verbose_name_plural': 'Horários de Funcionamento',
            },
        ),
    ]
