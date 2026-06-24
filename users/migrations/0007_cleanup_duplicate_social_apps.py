from django.db import migrations

def cleanup_duplicate_apps(apps, schema_editor):
    try:
        SocialApp = apps.get_model('socialaccount', 'SocialApp')
        
        # 1. Delete all placeholder apps
        SocialApp.objects.filter(client_id__contains='placeholder').delete()
        SocialApp.objects.filter(secret__contains='placeholder').delete()
        
        # 2. Delete all DB-backed apps per provider since they are configured in settings.py
        for provider in ['google', 'github']:
            SocialApp.objects.filter(provider=provider).delete()
    except Exception as e:
        print(f"Error during social app cleanup: {e}")

class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('users', '0006_create_social_apps'),
    ]

    operations = [
        migrations.RunPython(cleanup_duplicate_apps),
    ]
