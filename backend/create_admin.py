import os
import django
import sys

# Configurar ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tickets.models import Company, User

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Create a default company and admin user.')
    parser.add_argument('--username', default='admin', help='Admin username')
    parser.add_argument('--password', default='admin123', help='Admin password')
    parser.add_argument('--company', default='WDesk', help='Company name')
    args = parser.parse_args()

    company, created = Company.objects.get_or_create(name=args.company)
    if created:
        print(f"Company '{args.company}' created with ID: {company.id}")
    else:
        print(f"Company '{args.company}' already exists with ID: {company.id}")

    if User.objects.filter(username=args.username).exists():
        print(f"User '{args.username}' already exists.")
    else:
        user = User.objects.create_superuser(
            username=args.username,
            password=args.password,
            email=f"{args.username}@wdesk.com",
            role='admin',
            company=company
        )
        print(f"Admin user '{args.username}' created successfully!")

if __name__ == '__main__':
    main()
