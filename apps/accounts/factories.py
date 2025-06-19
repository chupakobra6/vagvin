import factory
from factory.django import DjangoModelFactory
from apps.accounts.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    email = factory.Faker("email")
    username = factory.LazyAttribute(lambda o: o.email.split("@")[0])

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.set_password(extracted)
        else:
            self.set_password("password123")

    @factory.post_generation
    def is_superuser(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.is_superuser = extracted
            self.is_staff = extracted
