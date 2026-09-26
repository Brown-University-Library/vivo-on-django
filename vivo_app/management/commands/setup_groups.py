from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Sets up default user groups and permissions'

    def handle(self, *args, **options):
        # Create groups
        admin_group, _ = Group.objects.get_or_create(name='Administrators')
        editor_group, _ = Group.objects.get_or_create(name='Editors')
        viewer_group, _ = Group.objects.get_or_create(name='Viewers')

        # Get all models to assign view permissions
        for model in apps.get_models():
            content_type = ContentType.objects.get_for_model(model)
            permissions = Permission.objects.filter(content_type=content_type)

            # Add all permissions to admin group
            admin_group.permissions.add(*permissions)

            # Add view permissions to editors and viewers
            view_permission = permissions.filter(codename__startswith='view_')
            editor_group.permissions.add(*view_permission)
            viewer_group.permissions.add(*view_permission)

            # Add add/change/delete permissions to editors
            edit_permissions = permissions.filter(codename__in=['add_', 'change_', 'delete_'], content_type=content_type)
            editor_group.permissions.add(*edit_permissions)

        self.stdout.write(self.style.SUCCESS('Successfully set up default groups and permissions'))
