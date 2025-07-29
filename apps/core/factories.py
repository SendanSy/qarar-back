"""
Model factories for testing using factory_boy.
"""
import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyInteger, FuzzyText, FuzzyDate
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for User model."""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    is_superuser = False
    date_joined = factory.LazyFunction(timezone.now)


class AdminUserFactory(UserFactory):
    """Factory for admin users."""
    
    is_staff = True
    is_superuser = True
    username = factory.Sequence(lambda n: f"admin{n}")


class OrganizationFactory(DjangoModelFactory):
    """Factory for Organization model."""
    
    class Meta:
        model = 'producers.Organization'
    
    name = factory.Faker('company')
    name_ar = factory.Faker('company', locale='ar_SA')
    code = factory.Sequence(lambda n: f"ORG{n:03d}")
    description = factory.Faker('text', max_nb_chars=200)
    description_ar = factory.Faker('text', max_nb_chars=200, locale='ar_SA')
    is_active = True
    website = factory.Faker('url')
    email = factory.Faker('email')
    phone = factory.Faker('phone_number')


class SubsidiaryFactory(DjangoModelFactory):
    """Factory for Subsidiary model."""
    
    class Meta:
        model = 'producers.Subsidiary'
    
    parent_organization = factory.SubFactory(OrganizationFactory)
    name = factory.Faker('company')
    name_ar = factory.Faker('company', locale='ar_SA')
    code = factory.Sequence(lambda n: f"SUB{n:03d}")
    description = factory.Faker('text', max_nb_chars=150)
    description_ar = factory.Faker('text', max_nb_chars=150, locale='ar_SA')
    is_active = True


class CategoryFactory(DjangoModelFactory):
    """Factory for Category model."""
    
    class Meta:
        model = 'content.Category'
    
    name = factory.Sequence(lambda n: f"Category {n}")
    name_ar = factory.Sequence(lambda n: f"فئة {n}")
    description = factory.Faker('text', max_nb_chars=200)
    description_ar = factory.Faker('text', max_nb_chars=200, locale='ar_SA')
    icon = FuzzyChoice(['fas fa-file', 'fas fa-folder', 'fas fa-tag'])
    is_active = True
    order = FuzzyInteger(0, 100)
    post_count = 0


class SubCategoryFactory(DjangoModelFactory):
    """Factory for SubCategory model."""
    
    class Meta:
        model = 'content.SubCategory'
    
    category = factory.SubFactory(CategoryFactory)
    name = factory.Sequence(lambda n: f"SubCategory {n}")
    name_ar = factory.Sequence(lambda n: f"فئة فرعية {n}")
    description = factory.Faker('text', max_nb_chars=150)
    description_ar = factory.Faker('text', max_nb_chars=150, locale='ar_SA')
    is_active = True
    order = FuzzyInteger(0, 100)
    post_count = 0


class HashTagFactory(DjangoModelFactory):
    """Factory for HashTag model."""
    
    class Meta:
        model = 'content.HashTag'
    
    name = factory.LazyFunction(lambda: f"tag{random.randint(1, 1000)}")
    is_active = True
    post_count = 0
    is_trending = False
    order = FuzzyInteger(0, 100)


class PostTypeFactory(DjangoModelFactory):
    """Factory for PostType model."""
    
    class Meta:
        model = 'content.PostType'
    
    name = FuzzyChoice(['Decision', 'Circular', 'Announcement', 'Statement'])
    name_ar = FuzzyChoice(['قرار', 'تعميم', 'إعلان', 'بيان'])
    description = factory.Faker('text', max_nb_chars=200)
    description_ar = factory.Faker('text', max_nb_chars=200, locale='ar_SA')
    is_active = True


class PostFactory(DjangoModelFactory):
    """Factory for Post model."""
    
    class Meta:
        model = 'content.Post'
    
    title = factory.Faker('sentence', nb_words=6)
    title_ar = factory.Faker('sentence', nb_words=6, locale='ar_SA')
    content = factory.Faker('text', max_nb_chars=1000)
    content_ar = factory.Faker('text', max_nb_chars=1000, locale='ar_SA')
    summary = factory.Faker('text', max_nb_chars=200)
    summary_ar = factory.Faker('text', max_nb_chars=200, locale='ar_SA')
    
    author = factory.SubFactory(UserFactory)
    type = factory.SubFactory(PostTypeFactory)
    organization = factory.SubFactory(OrganizationFactory)
    subsidiary = factory.SubFactory(SubsidiaryFactory)
    
    status = 'draft'
    view_count = FuzzyInteger(0, 1000)
    
    created_at = factory.LazyFunction(
        lambda: timezone.now() - timedelta(days=random.randint(0, 365))
    )
    
    @factory.post_generation
    def published_at(self, create, extracted, **kwargs):
        """Set published_at for published posts."""
        if not create:
            return
        
        if self.status == 'published':
            self.published_at = self.created_at + timedelta(hours=random.randint(1, 24))
            self.save()
    
    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        """Add categories to the post."""
        if not create:
            return
        
        if extracted:
            for category in extracted:
                self.categories.add(category)
        else:
            # Add 1-3 random categories
            categories = CategoryFactory.create_batch(random.randint(1, 3))
            self.categories.set(categories)
    
    @factory.post_generation
    def hashtags(self, create, extracted, **kwargs):
        """Add hashtags to the post."""
        if not create:
            return
        
        if extracted:
            for hashtag in extracted:
                self.hashtags.add(hashtag)
        else:
            # Add 0-5 random hashtags
            hashtags = HashTagFactory.create_batch(random.randint(0, 5))
            self.hashtags.set(hashtags)


class PublishedPostFactory(PostFactory):
    """Factory for published posts."""
    
    status = 'published'
    published_at = factory.LazyFunction(
        lambda: timezone.now() - timedelta(days=random.randint(1, 30))
    )


class FeaturedPostFactory(PublishedPostFactory):
    """Factory for featured posts."""
    
    pass


class UrgentPostFactory(PublishedPostFactory):
    """Factory for urgent posts."""
    
    pass


class PostAttachmentFactory(DjangoModelFactory):
    """Factory for PostAttachment model."""
    
    class Meta:
        model = 'content.PostAttachment'
    
    post = factory.SubFactory(PostFactory)
    title = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('text', max_nb_chars=100)
    file_type = FuzzyChoice(['application/pdf', 'image/jpeg', 'text/plain'])
    size = FuzzyInteger(1024, 1024*1024*10)  # 1KB to 10MB
    order = factory.Sequence(lambda n: n)


class BookmarkFactory(DjangoModelFactory):
    """Factory for Bookmark model."""
    
    class Meta:
        model = 'content.Bookmark'
    
    user = factory.SubFactory(UserFactory)
    post = factory.SubFactory(PublishedPostFactory)
    notes = factory.Faker('text', max_nb_chars=200)
    tags = factory.LazyFunction(
        lambda: ', '.join([f"tag{i}" for i in range(random.randint(0, 5))])
    )
    is_private = FuzzyChoice([True, False])


class BookmarkCollectionFactory(DjangoModelFactory):
    """Factory for BookmarkCollection model."""
    
    class Meta:
        model = 'content.BookmarkCollection'
    
    user = factory.SubFactory(UserFactory)
    name = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('text', max_nb_chars=200)
    is_public = FuzzyChoice([True, False])
    color = FuzzyChoice(['#007bff', '#28a745', '#dc3545', '#ffc107', '#6f42c1'])


# Trait classes for common variations
class Traits:
    """Common traits for factories."""
    
    class Arabic:
        """Arabic content trait."""
        title_ar = factory.Faker('sentence', nb_words=6, locale='ar_SA')
        content_ar = factory.Faker('text', max_nb_chars=1000, locale='ar_SA')
    
    class English:
        """English content trait."""
        title = factory.Faker('sentence', nb_words=6, locale='en_US')
        content = factory.Faker('text', max_nb_chars=1000, locale='en_US')
    
    class Recent:
        """Recent content trait."""
        created_at = factory.LazyFunction(
            lambda: timezone.now() - timedelta(days=random.randint(0, 7))
        )
    
    class Old:
        """Old content trait."""
        created_at = factory.LazyFunction(
            lambda: timezone.now() - timedelta(days=random.randint(180, 365))
        )


# Utility functions for creating test data
def create_test_dataset():
    """Create a comprehensive test dataset."""
    
    # Create users
    admin = AdminUserFactory()
    editors = UserFactory.create_batch(3)
    regular_users = UserFactory.create_batch(10)
    
    # Create organizations and subsidiaries
    orgs = OrganizationFactory.create_batch(5)
    subsidiaries = []
    for org in orgs:
        subsidiaries.extend(
            SubsidiaryFactory.create_batch(random.randint(1, 3), organization=org)
        )
    
    # Create categories and subcategories
    categories = CategoryFactory.create_batch(8)
    subcategories = []
    for category in categories:
        subcategories.extend(
            SubCategoryFactory.create_batch(random.randint(2, 5), category=category)
        )
    
    # Create post types
    post_types = PostTypeFactory.create_batch(6)
    
    # Create hashtags
    hashtags = HashTagFactory.create_batch(20)
    
    # Create posts
    posts = []
    
    # Featured posts
    posts.extend(FeaturedPostFactory.create_batch(
        5,
        author=factory.Iterator(editors),
        organization=factory.Iterator(orgs),
        type=factory.Iterator(post_types)
    ))
    
    # Urgent posts
    posts.extend(UrgentPostFactory.create_batch(
        3,
        author=factory.Iterator(editors),
        organization=factory.Iterator(orgs),
        type=factory.Iterator(post_types)
    ))
    
    # Regular published posts
    posts.extend(PublishedPostFactory.create_batch(
        50,
        author=factory.Iterator(editors + [admin]),
        organization=factory.Iterator(orgs),
        type=factory.Iterator(post_types)
    ))
    
    # Draft posts
    posts.extend(PostFactory.create_batch(
        20,
        status='draft',
        author=factory.Iterator(editors),
        organization=factory.Iterator(orgs),
        type=factory.Iterator(post_types)
    ))
    
    # Add attachments to some posts
    for post in random.sample(posts, min(20, len(posts))):
        PostAttachmentFactory.create_batch(
            random.randint(1, 3),
            post=post
        )
    
    # Create bookmarks
    for user in regular_users:
        bookmarked_posts = random.sample(
            [p for p in posts if p.status == 'published'],
            random.randint(0, 10)
        )
        for post in bookmarked_posts:
            BookmarkFactory(user=user, post=post)
    
    # Create bookmark collections
    for user in random.sample(regular_users, 5):
        collections = BookmarkCollectionFactory.create_batch(
            random.randint(1, 3),
            user=user
        )
    
    return {
        'admin': admin,
        'editors': editors,
        'users': regular_users,
        'organizations': orgs,
        'subsidiaries': subsidiaries,
        'categories': categories,
        'subcategories': subcategories,
        'post_types': post_types,
        'hashtags': hashtags,
        'posts': posts
    }


def create_minimal_test_data():
    """Create minimal test data for quick tests."""
    
    user = UserFactory()
    org = OrganizationFactory()
    category = CategoryFactory()
    post_type = PostTypeFactory()
    
    post = PublishedPostFactory(
        author=user,
        organization=org,
        type=post_type,
        categories=[category]
    )
    
    return {
        'user': user,
        'organization': org,
        'category': category,
        'post_type': post_type,
        'post': post
    }