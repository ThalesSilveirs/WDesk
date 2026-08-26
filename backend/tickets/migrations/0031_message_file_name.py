# Generated manually on 2026-08-26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0030_remove_ticket_tickets_tic_company_a1e5b3_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='file_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
