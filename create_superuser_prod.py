import os
import django

def create_initial_superuser():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "capstone.settings")
    django.setup()

    from django.contrib.auth import get_user_model

    User = get_user_model()
    
    # Get credentials from environment variables or use safe defaults/placeholders
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

    if username and password:
        if not User.objects.filter(username=username).exists():
            print(f"Creating superuser: {username}")
            User.objects.create_superuser(username=username, email=email, password=password)
        else:
            print(f"Superuser '{username}' already exists.")
    else:
        print("Skipping superuser creation: DJANGO_SUPERUSER_USERNAME or DJANGO_SUPERUSER_PASSWORD not set.")

if __name__ == "__main__":
    create_initial_superuser()
