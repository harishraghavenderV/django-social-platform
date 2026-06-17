from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('users', '0002_badge_userprofile_is_verified_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstagramAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ig_user_id', models.CharField(help_text='Instagram user ID returned by Graph API', max_length=100)),
                ('ig_username', models.CharField(help_text='Instagram @handle', max_length=100)),
                ('access_token', models.TextField(help_text='Long-lived Instagram access token (60 days)')),
                ('token_expires_at', models.DateTimeField(blank=True, help_text='Expiry timestamp for the long-lived token', null=True)),
                ('last_synced', models.DateTimeField(blank=True, help_text='Last time media was synced from Instagram', null=True)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this connection is active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='instagram_account',
                    to='auth.user',
                )),
            ],
            options={
                'verbose_name': 'Instagram Account',
                'verbose_name_plural': 'Instagram Accounts',
            },
        ),
    ]
