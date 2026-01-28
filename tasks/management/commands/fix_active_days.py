from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tasks.models import Day
from django.db import transaction


class Command(BaseCommand):
    help = 'Fix users with multiple active days - keeps only the most recent one active'

    def handle(self, *args, **options):
        fixed_count = 0
        
        # Get all users
        users = User.objects.all()
        
        for user in users:
            # Find all active days for this user
            active_days = Day.objects.filter(user=user, is_active=True).order_by('-date')
            
            if active_days.count() > 1:
                self.stdout.write(
                    self.style.WARNING(
                        f'User "{user.username}" has {active_days.count()} active days!'
                    )
                )
                
                # Keep the first one (most recent), deactivate the rest
                with transaction.atomic():
                    for i, day in enumerate(active_days):
                        if i == 0:
                            # Keep this one active
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✓ Keeping {day.date} as active'
                                )
                            )
                        else:
                            # Deactivate this one
                            day.is_active = False
                            day.save(update_fields=['is_active'])
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'  ✗ Deactivated {day.date}'
                                )
                            )
                            fixed_count += 1
        
        if fixed_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Fixed {fixed_count} duplicate active days!'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    '\n✅ No issues found - all users have at most one active day!'
                )
            )
