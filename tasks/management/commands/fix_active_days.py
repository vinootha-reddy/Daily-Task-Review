from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tasks.models import Day

User = get_user_model()


class Command(BaseCommand):
    help = 'Fix users with multiple active days - keeps only the most recent OPEN day as active'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made\n'))
        
        users = User.objects.all()
        fixed_count = 0
        total_deactivated = 0
        
        for user in users:
            # Get all active days for this user
            active_days = Day.objects.filter(user=user, is_active=True).order_by('-date')
            
            if active_days.count() > 1:
                self.stdout.write(
                    self.style.WARNING(
                        f'\nUser {user.username} has {active_days.count()} active days:'
                    )
                )
                
                for day in active_days:
                    status_color = self.style.SUCCESS if day.status == 'OPEN' else self.style.ERROR
                    self.stdout.write(f'  - {day.date} (Status: {status_color(day.status)})')
                
                # Keep the most recent OPEN day active, or if none are OPEN, keep the most recent one
                open_days = active_days.filter(status='OPEN')
                
                if open_days.exists():
                    keep_active = open_days.first()
                else:
                    keep_active = active_days.first()
                
                self.stdout.write(
                    self.style.SUCCESS(f'  → Keeping {keep_active.date} as active')
                )
                
                # Deactivate all others
                days_to_deactivate = active_days.exclude(id=keep_active.id)
                deactivate_count = days_to_deactivate.count()
                
                if not dry_run:
                    days_to_deactivate.update(is_active=False)
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Deactivated {deactivate_count} days')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  [DRY RUN] Would deactivate {deactivate_count} days')
                    )
                
                fixed_count += 1
                total_deactivated += deactivate_count
            
            elif active_days.count() == 0:
                # User has no active day - this is also a problem
                self.stdout.write(
                    self.style.WARNING(f'\nUser {user.username} has NO active days')
                )
                
                # Find the most recent OPEN day
                open_day = Day.objects.filter(user=user, status='OPEN').order_by('-date').first()
                
                if open_day:
                    self.stdout.write(f'  → Setting {open_day.date} as active')
                    if not dry_run:
                        open_day.is_active = True
                        open_day.save(update_fields=['is_active'])
                        self.stdout.write(self.style.SUCCESS('  ✓ Fixed'))
                    else:
                        self.stdout.write(self.style.WARNING('  [DRY RUN] Would set as active'))
                    fixed_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR('  ✗ No OPEN days found - needs manual attention')
                    )
        
        # Summary
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN COMPLETE: Would fix {fixed_count} users, '
                    f'deactivating {total_deactivated} days'
                )
            )
            self.stdout.write('\nRun without --dry-run to apply changes')
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Fixed {fixed_count} users, deactivated {total_deactivated} days'
                )
            )
