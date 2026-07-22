import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0026_message_tickets_mes_ticket__810624_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pendency',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='created_pendencies',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
