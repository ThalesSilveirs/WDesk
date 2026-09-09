from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0033_user_queue_notification_settings'),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketReminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scheduled_for', models.DateTimeField(db_index=True)),
                ('note', models.TextField(blank=True, null=True)),
                ('is_sent', models.BooleanField(db_index=True, default=False)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ticket_reminders', to='tickets.company')),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reminders', to='tickets.ticket')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ticket_reminders', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['scheduled_for'],
            },
        ),
        migrations.AddIndex(
            model_name='ticketreminder',
            index=models.Index(fields=['is_sent', 'scheduled_for'], name='tickets_tic_is_sent_c653a1_idx'),
        ),
        migrations.AddIndex(
            model_name='ticketreminder',
            index=models.Index(fields=['ticket', 'is_sent'], name='tickets_tic_ticket__3e9112_idx'),
        ),
        migrations.AddIndex(
            model_name='ticketreminder',
            index=models.Index(fields=['company', 'is_sent'], name='tickets_tic_company_07f3b8_idx'),
        ),
        migrations.AddIndex(
            model_name='ticketreminder',
            index=models.Index(fields=['user', 'is_sent'], name='tickets_tic_user_id_45a190_idx'),
        ),
    ]
