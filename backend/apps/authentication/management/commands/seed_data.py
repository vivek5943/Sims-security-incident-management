from django.core.management.base import BaseCommand
from django.db import transaction

class Command(BaseCommand):
    help = 'Seed SIMS database: Roles + default admin + demo users'

    def handle(self, *args, **options):
        from apps.authentication.models import Role, User

        self.stdout.write('\n  SIMS Database Seeder')

        with transaction.atomic():
            for role_name in [Role.ANALYST, Role.MANAGER, Role.ADMIN]:
                _, created = Role.objects.get_or_create(role_name=role_name)
                self.stdout.write(f'  Role: {role_name}')

            admin_email = 'admin@sims.local'
            admin_role = Role.objects.get(role_name=Role.ADMIN)

            if not User.objects.filter(email=admin_email).exists():
                user = User(email=admin_email, full_name='SIMS Administrator', role=admin_role)
                user.set_password('Admin@1234')
                user.is_staff = True
                user.is_superuser = True
                user.save()
                self.stdout.write('  Admin created: admin@sims.local / Admin@1234')

            demo_users = [
                {'email': 'manager@sims.local',  'full_name': 'Sarah Chen',   'role': Role.MANAGER, 'pw': 'Manager@1234'},
                {'email': 'analyst1@sims.local',  'full_name': 'Rajesh Kumar', 'role': Role.ANALYST, 'pw': 'Analyst@1234'},
                {'email': 'analyst2@sims.local',  'full_name': 'Priya Sharma', 'role': Role.ANALYST, 'pw': 'Analyst@1234'},
            ]
            for u in demo_users:
                if not User.objects.filter(email=u['email']).exists():
                    role_obj = Role.objects.get(role_name=u['role'])
                    new_user = User(email=u['email'], full_name=u['full_name'], role=role_obj)
                    new_user.set_password(u['pw'])
                    new_user.save()
                    self.stdout.write(f'  User created: {u["email"]}')

        self.stdout.write('  Done!')