from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0031_message_file_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='notification_time',
            field=models.TimeField(default='08:00'),
        ),
        migrations.AddField(
            model_name='user',
            name='notify_daily_pendencies',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='user',
            name='notify_daily_open_tickets',
            field=models.BooleanField(default=True),
        ),
    ]
