from django.core.management.base import BaseCommand

from apps.accounts.models import UserProfile
from apps.accounts.utils import normalize_phone


class Command(BaseCommand):
    help = 'Нормализует поле phone у всех UserProfile к виду +7XXXXXXXXXX'

    def handle(self, *args, **options):
        updated = 0
        skipped = 0
        for profile in UserProfile.objects.exclude(phone=''):
            normalized = normalize_phone(profile.phone)
            if not normalized:
                skipped += 1
                self.stdout.write(self.style.WARNING(
                    f'Пропущен (невалидный): {profile.user} → "{profile.phone}"'
                ))
                continue
            if normalized != profile.phone:
                profile.phone = normalized
                profile.save(update_fields=['phone'])
                updated += 1
        self.stdout.write(self.style.SUCCESS(
            f'Готово. Нормализовано: {updated}, пропущено невалидных: {skipped}.'
        ))
