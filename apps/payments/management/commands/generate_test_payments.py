import logging
import random
from decimal import Decimal
from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from apps.payments.models import Payment

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Generates test payment data for development purposes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of payments to generate (default: 20)'
        )

        parser.add_argument(
            '--user',
            type=str,
            help='Username to generate payments for (default: random users)'
        )

        parser.add_argument(
            '--success-rate',
            type=float,
            default=0.7,
            help='Percentage of successful payments (default: 0.7)'
        )

        parser.add_argument(
            '--provider',
            type=str,
            choices=['all', 'robokassa', 'yookassa', 'heleket', 'internal'],
            default='all',
            help='Payment provider to use (default: all)'
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        count = options['count']
        username = options['user']
        success_rate = options['success_rate']
        provider_choice = options['provider']

        fake = Faker('ru_RU')

        # Get or create user(s)
        if username:
            try:
                users = [User.objects.get(username=username)]
                self.stdout.write(f'Using existing user: {username}')
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'User {username} not found. Creating new user.'))
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@example.com",
                    password="password123"
                )
                users = [user]
        else:
            # Get existing users or create some if needed
            users = list(User.objects.all()[:5])
            if not users:
                self.stdout.write('No users found. Creating test users.')
                for i in range(3):
                    username = f"testuser{i}"
                    user = User.objects.create_user(
                        username=username,
                        email=f"{username}@example.com",
                        password="password123"
                    )
                    users.append(user)

        # Define payment providers
        if provider_choice == 'all':
            providers = ['robokassa', 'yookassa', 'heleket', 'internal']
        else:
            providers = [provider_choice]

        # Generate payments
        payments_created = 0

        self.stdout.write(self.style.MIGRATE_HEADING(f'Generating {count} test payments...'))

        for _ in range(count):
            user = random.choice(users)

            # Generate random payment data
            provider = random.choice(providers)
            amount = Decimal(str(round(random.uniform(10, 1000), 2)))
            commission_rate = random.choice([0.05, 0.07, 0.1, 0.12])
            total_amount = round(float(amount) * (1 + commission_rate), 2)

            # Generate status based on success rate
            status = random.choices(
                ['success', 'failed', 'pending'],
                weights=[success_rate, (1 - success_rate) / 2, (1 - success_rate) / 2],
                k=1
            )[0]

            invoice_id = f"{provider}_{fake.uuid4()}"

            # Create the payment
            payment = Payment.objects.create(
                user=user,
                provider=provider,
                amount=amount,
                total_amount=total_amount,
                invoice_id=invoice_id,
                status=status
            )

            # If successful payment, update user's balance
            if status == 'success':
                try:
                    user.balance = Decimal(user.balance) + amount
                    user.save(update_fields=['balance'])
                except Exception:
                    logger.exception("Failed to update balance for user")

            payments_created += 1

            if payments_created % 10 == 0:
                self.stdout.write(f'Created {payments_created} payments...')

        logger.info(f'Successfully generated {payments_created} test payments.')
        self.stdout.write(self.style.SUCCESS(f'Successfully generated {payments_created} test payments.'))
        return None
