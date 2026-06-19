from django.db import migrations

def create_social_apps(apps, schema_editor):
    try:
        Site = apps.get_model('sites', 'Site')
        SocialApp = apps.get_model('socialaccount', 'SocialApp')
        
        site = Site.objects.get_or_create(id=1, defaults={'domain': 'example.com', 'name': 'example.com'})[0]
        
        # Create Google App if not exists
        google_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': 'placeholder-google-client-id',
                'secret': 'placeholder-google-secret',
            }
        )
        if created:
            google_app.sites.add(site)
            
        # Create GitHub App if not exists
        github_app, created = SocialApp.objects.get_or_create(
            provider='github',
            defaults={
                'name': 'GitHub',
                'client_id': 'placeholder-github-client-id',
                'secret': 'placeholder-github-secret',
            }
        )
        if created:
            github_app.sites.add(site)
    except Exception as e:
        print(f"Error seeding social apps: {e}")

class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('users', '0005_userprofile_interest_tags'),
        ('socialaccount', '0001_initial'),
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_social_apps),
    ]
