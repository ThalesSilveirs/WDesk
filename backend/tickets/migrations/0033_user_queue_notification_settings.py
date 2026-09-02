from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0032_user_notification_settings'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='notify_queue_delay',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='queue_delay_minutes',
            field=models.IntegerField(default=5),
        ),
    ]
