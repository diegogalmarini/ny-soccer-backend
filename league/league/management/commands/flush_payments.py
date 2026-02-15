from django.core.management.base import BaseCommand, CommandError
from league.models import PaymentPlaceholder

class Command(BaseCommand):
    help = "Flush expired payments."
    
    def handle(self, *args, **options):
        PaymentPlaceholder.purge_outdated()
