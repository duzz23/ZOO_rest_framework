from django.core.management.base import BaseCommand, CommandError
from userapp.models import MyUser
from django.db.utils import IntegrityError


class Command(BaseCommand):
    help = "Fill db with test data"

    def handle(self, *args, **options):
        try:
            MyUser.objects.create_user('user', 'user@admin.com', 'user')
        except IntegrityError:
            self.stdout.write(
                self.style.SUCCESS('Already Exists')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Done')
            )

        try:
            MyUser.objects.create_user('food_master', 'food_master@admin.com', 'food_master')
        except IntegrityError:
            self.stdout.write(
                self.style.SUCCESS('Already Exists')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Done')
            )

        try:
            MyUser.objects.create_user('user3', 'user3@admin.com', 'user3')
        except IntegrityError:
            self.stdout.write(
                self.style.SUCCESS('Already Exists')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Done')
            )

        # MyUser.objects.create_superuser('admin', 'admin@admin.com', 'admin')
