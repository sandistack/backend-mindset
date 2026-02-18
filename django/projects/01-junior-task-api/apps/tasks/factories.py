"""
Factory classes for creating test data
"""
import factory
from factory.django import DjangoModelFactory
from faker import Faker
from django.utils import timezone
from apps.authentication.models import User
from apps.tasks.models import Task, Category

fake = Faker()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances"""
    
    class Meta:
        model = User
        django_get_or_create = ('email',)
    
    email = factory.LazyAttribute(lambda _: fake.unique.email())
    name = factory.LazyAttribute(lambda _: fake.name())
    is_active = True
    is_staff = False
    
    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Set password after instance creation"""
        if not create:
            return
        
        if extracted:
            self.set_password(extracted)
        else:
            self.set_password('TestPass123!')
        self.save()


class CategoryFactory(DjangoModelFactory):
    """Factory for creating Category instances"""
    
    class Meta:
        model = Category
    
    name = factory.LazyAttribute(lambda _: fake.word().capitalize())
    color = '#3B82F6'
    user = factory.SubFactory(UserFactory)


class TaskFactory(DjangoModelFactory):
    """Factory for creating Task instances"""
    
    class Meta:
        model = Task
    
    title = factory.LazyAttribute(lambda _: fake.sentence(nb_words=5)[:-1])  # Remove period
    description = factory.LazyAttribute(lambda _: fake.paragraph(nb_sentences=3))
    priority = 'medium'
    status = 'pending'
    user = factory.SubFactory(UserFactory)
    category = factory.SubFactory(CategoryFactory, user=factory.SelfAttribute('..user'))
    is_deleted = False
    
    # Optional due_date (None by default)
    due_date = None
    
    @factory.lazy_attribute
    def completed_at(self):
        """Set completed_at only if status is 'done'"""
        if self.status == 'done':
            return timezone.now()
        return None
