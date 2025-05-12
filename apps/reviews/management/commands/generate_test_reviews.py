import logging
import random
from typing import Any, Optional

from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from apps.reviews.models import Review

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generates test review data for development purposes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=15,
            help='Number of reviews to generate (default: 15)'
        )
        
        parser.add_argument(
            '--approved',
            action='store_true',
            help='Generate only approved reviews'
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        count = options['count']
        approved_only = options['approved']
        
        fake = Faker('ru_RU')
        
        admin_responses = [
            "Спасибо за ваш отзыв! Мы рады, что вам понравился наш сервис.",
            "Благодарим за обратную связь! Ваше мнение очень важно для нас.",
            "Спасибо за высокую оценку! Мы стараемся сделать наш сервис еще лучше.",
            "Благодарим за отзыв и высокую оценку нашей работы!",
            None, None, None
        ]
        
        reviews_created = 0
        
        self.stdout.write(self.style.MIGRATE_HEADING(f'Generating {count} test reviews...'))
        
        for _ in range(count):
            rating = random.randint(3, 5)
            
            is_approved = True if approved_only else random.random() < 0.7
            
            admin_response = random.choice(admin_responses) if is_approved and random.random() < 0.6 else None
            
            review = Review(
                name=fake.name(),
                email=fake.email(),
                rating=rating,
                text=fake.paragraph(nb_sentences=random.randint(2, 5)),
                admin_response=admin_response,
                approved=is_approved
            )
            
            review.save()
            reviews_created += 1
            
            if reviews_created % 10 == 0:
                self.stdout.write(f'Created {reviews_created} reviews...')
        
        logger.info(f'Successfully generated {reviews_created} test reviews.')
        self.stdout.write(self.style.SUCCESS(f'Successfully generated {reviews_created} test reviews.'))
        return None 