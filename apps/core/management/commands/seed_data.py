from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from apps.geographics.models import Country, State, City
from apps.producers.models import Organization
from apps.content.models import (
    PostType,
    Category,
    SubCategory,
    HashTag,
    Post,
    PostAttachment,
    Bookmark
)
import os
from django.core.files import File
from django.utils.text import slugify

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with sample data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-cleanup',
            action='store_true',
            help='Do not cleanup existing data before seeding',
        )

    def cleanup_database(self):
        """Delete all existing data from the database"""
        self.stdout.write('Cleaning up existing data...')
        
        # Delete in reverse order of dependencies
        self.stdout.write('Deleting bookmarks...')
        Bookmark.objects.all().delete()
        
        self.stdout.write('Deleting posts...')
        Post.objects.all().delete()
        
        self.stdout.write('Deleting hashtags...')
        HashTag.objects.all().delete()
        
        self.stdout.write('Deleting subcategories...')
        SubCategory.objects.all().delete()
        
        self.stdout.write('Deleting categories...')
        Category.objects.all().delete()
        
        self.stdout.write('Deleting post types...')
        PostType.objects.all().delete()
        
        self.stdout.write('Deleting organizations...')
        Organization.objects.all().delete()
        
        self.stdout.write('Deleting cities...')
        City.objects.all().delete()
        
        self.stdout.write('Deleting states...')
        State.objects.all().delete()
        
        self.stdout.write('Deleting countries...')
        Country.objects.all().delete()
        
        self.stdout.write('Deleting users...')
        # Delete all users except superuser
        User.objects.exclude(is_superuser=True).delete()
        
        self.stdout.write(self.style.SUCCESS('Database cleanup completed!'))

    @transaction.atomic
    def handle(self, *args, **kwargs):
        try:
            self.stdout.write('Starting database seeding...')
            
            # Cleanup unless --no-cleanup flag is provided
            if not kwargs.get('no_cleanup'):
                self.cleanup_database()
            
            # Create all data in a single transaction
            self.create_users()
            self.create_countries()
            self.create_states()
            self.create_cities()
            self.create_organizations()
            self.create_post_types()
            self.create_categories()
            self.create_subcategories()
            self.create_hashtags()
            self.create_posts()
            self.create_bookmarks()
            
            self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during seeding: {str(e)}'))
            raise

    def create_users(self):
        self.stdout.write('Creating users...')
        user_data = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'password': 'adminpass123',
                'first_name': 'مدير',
                'last_name': 'النظام',
                'is_staff': True,
                'is_superuser': True,
                'user_type': 'admin',
                'is_verified': True,
                'bio': 'مدير النظام مع صلاحيات كاملة',
                'location': 'دمشق، سوريا',
                'website': 'https://admin.example.com',
                'twitter': '@admin',
                'linkedin': 'admin-user'
            },
            {
                'username': 'editor',
                'email': 'editor@example.com',
                'password': 'editorpass123',
                'first_name': 'محرر',
                'last_name': 'المحتوى',
                'user_type': 'editor',
                'is_verified': True,
                'bio': 'محرر المحتوى المسؤول عن المراجعة والنشر',
                'location': 'حلب، سوريا',
                'website': 'https://editor.example.com',
                'twitter': '@editor',
                'linkedin': 'editor-user'
            },
            {
                'username': 'journalist',
                'email': 'journalist@example.com',
                'password': 'journalistpass123',
                'first_name': 'صحفي',
                'last_name': 'ميداني',
                'user_type': 'journalist',
                'is_verified': True,
                'bio': 'صحفي ميداني يغطي آخر الأخبار',
                'location': 'حمص، سوريا',
                'website': 'https://journalist.example.com',
                'twitter': '@journalist',
                'linkedin': 'journalist-user'
            }
        ]
        
        for data in user_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'is_staff': data.get('is_staff', False),
                    'is_superuser': data.get('is_superuser', False),
                    'user_type': data['user_type'],
                    'is_verified': data['is_verified'],
                    'bio': data['bio'],
                    'location': data['location'],
                    'website': data['website'],
                    'twitter': data['twitter'],
                    'linkedin': data['linkedin']
                }
            )
            if created:
                user.set_password(data['password'])
                user.save()
                self.stdout.write(f'Created user: {user.username}')

    def create_countries(self):
        self.stdout.write('Creating countries...')
        countries_data = [
            {'name': 'سوريا', 'code': 'SYR'},
            {'name': 'لبنان', 'code': 'LBN'},
            {'name': 'الأردن', 'code': 'JOR'}
        ]
        
        for data in countries_data:
            country, created = Country.objects.get_or_create(
                code=data['code'],
                defaults={'name': data['name']}
            )
            if created:
                self.stdout.write(f'Created country: {country.name}')

    def create_states(self):
        self.stdout.write('Creating states...')
        syria = Country.objects.get(code='SYR')  # Get Syria as the default country
        states_data = [
            {'name': 'دمشق', 'code': 'DMS', 'country': syria},
            {'name': 'حلب', 'code': 'ALP', 'country': syria},
            {'name': 'حمص', 'code': 'HOM', 'country': syria}
        ]
        
        for data in states_data:
            state, created = State.objects.get_or_create(
                name=data['name'],
                code=data['code'],
                country=data['country'],
                defaults={'is_active': True}
            )
            if created:
                self.stdout.write(f'Created state: {state.name}')

    def create_cities(self):
        self.stdout.write('Creating cities...')
        states = State.objects.all()[:3]  # Get the first three states
        cities_data = [
            {'name': 'مدينة دمشق', 'code': 'DMC', 'state': states[0]},
            {'name': 'مدينة حلب', 'code': 'ALC', 'state': states[1]},
            {'name': 'مدينة حمص', 'code': 'HOC', 'state': states[2]}
        ]
        
        for data in cities_data:
            city, created = City.objects.get_or_create(
                name=data['name'],
                code=data['code'],
                state=data['state'],
                defaults={'is_active': True}
            )
            if created:
                self.stdout.write(f'Created city: {city.name}')

    def create_organizations(self):
        self.stdout.write('Creating organizations...')
        org_data = [
            {
                'name': 'وزارة المالية',
                'name_ar': 'وزارة المالية',
                'code': 'MOF',
                'description': 'تتعامل مع السياسات والأنظمة المالية',
                'description_ar': 'تتعامل مع السياسات والأنظمة المالية'
            },
            {
                'name': 'وزارة الاقتصاد',
                'name_ar': 'وزارة الاقتصاد',
                'code': 'MOE',
                'description': 'تدير السياسات الاقتصادية والتجارة',
                'description_ar': 'تدير السياسات الاقتصادية والتجارة'
            },
            {
                'name': 'المصرف المركزي',
                'name_ar': 'المصرف المركزي',
                'code': 'CBK',
                'description': 'السلطة المصرفية المركزية',
                'description_ar': 'السلطة المصرفية المركزية'
            }
        ]
        
        for data in org_data:
            org, created = Organization.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'name_ar': data['name_ar'],
                    'description': data['description'],
                    'description_ar': data['description_ar']
                }
            )
            if created:
                self.stdout.write(f'Created organization: {org.name}')

    def create_post_types(self):
        self.stdout.write('Creating post types...')
        type_data = [
            {
                'name': 'قرار',
                'name_ar': 'قرار',
                'description': 'القرارات والمراسيم الرسمية الصادرة عن الجهات الحكومية',
                'description_ar': 'القرارات والمراسيم الرسمية الصادرة عن الجهات الحكومية',
                'is_active': True
            },
            {
                'name': 'تعميم',
                'name_ar': 'تعميم',
                'description': 'التعاميم والإعلانات الرسمية للتوعية العامة',
                'description_ar': 'التعاميم والإعلانات الرسمية للتوعية العامة',
                'is_active': True
            },
            {
                'name': 'خبر',
                'name_ar': 'خبر',
                'description': 'آخر الأخبار والتحديثات من مختلف القطاعات',
                'description_ar': 'آخر الأخبار والتحديثات من مختلف القطاعات',
                'is_active': True
            }
        ]
        
        for data in type_data:
            post_type, created = PostType.objects.get_or_create(
                name=data['name'],
                defaults={
                    'name_ar': data['name_ar'],
                    'description': data['description'],
                    'description_ar': data['description_ar'],
                    'is_active': data['is_active']
                }
            )
            if created:
                self.stdout.write(f'Created post type: {post_type.name}')

    def create_categories(self):
        self.stdout.write('Creating categories...')
        category_data = [
            {
                'name': 'اقتصاد',
                'name_ar': 'اقتصاد',
                'description': 'أخبار وسياسات وتحديثات السوق الاقتصادية',
                'description_ar': 'أخبار وسياسات وتحديثات السوق الاقتصادية',
                'slug': 'economy',
                'icon': 'fa-chart-line',
                'is_active': True
            },
            {
                'name': 'مالية',
                'name_ar': 'مالية',
                'description': 'الأنظمة المالية والمصرفية والسياسات النقدية',
                'description_ar': 'الأنظمة المالية والمصرفية والسياسات النقدية',
                'slug': 'finance',
                'icon': 'fa-money-bill',
                'is_active': True
            },
            {
                'name': 'تجارة',
                'name_ar': 'تجارة',
                'description': 'أنظمة التجارة والاستيراد/التصدير والأنشطة التجارية',
                'description_ar': 'أنظمة التجارة والاستيراد/التصدير والأنشطة التجارية',
                'slug': 'trade',
                'icon': 'fa-shopping-cart',
                'is_active': True
            }
        ]
        
        for data in category_data:
            category, created = Category.objects.get_or_create(
                name=data['name'],
                defaults={
                    'name_ar': data['name_ar'],
                    'description': data['description'],
                    'description_ar': data['description_ar'],
                    'slug': data['slug'],
                    'icon': data['icon'],
                    'is_active': data['is_active']
                }
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

    def create_subcategories(self):
        self.stdout.write('Creating subcategories...')
        categories = Category.objects.all()
        
        subcategories_data = {
            'اقتصاد': [
                {
                    'name': 'السياسة النقدية',
                    'name_ar': 'السياسة النقدية',
                    'description': 'قرارات البنك المركزي والسياسات النقدية',
                    'description_ar': 'قرارات البنك المركزي والسياسات النقدية',
                    'slug': 'monetary-policy'
                },
                {
                    'name': 'النمو الاقتصادي',
                    'name_ar': 'النمو الاقتصادي',
                    'description': 'مؤشرات ومبادرات النمو الاقتصادي',
                    'description_ar': 'مؤشرات ومبادرات النمو الاقتصادي',
                    'slug': 'economic-growth'
                },
                {
                    'name': 'تحليل السوق',
                    'name_ar': 'تحليل السوق',
                    'description': 'اتجاهات السوق وتقارير التحليل',
                    'description_ar': 'اتجاهات السوق وتقارير التحليل',
                    'slug': 'market-analysis'
                }
            ],
            'مالية': [
                {
                    'name': 'الخدمات المصرفية',
                    'name_ar': 'الخدمات المصرفية',
                    'description': 'أخبار وتحديثات القطاع المصرفي',
                    'description_ar': 'أخبار وتحديثات القطاع المصرفي',
                    'slug': 'banking'
                },
                {
                    'name': 'الاستثمار',
                    'name_ar': 'الاستثمار',
                    'description': 'فرص وأنظمة الاستثمار',
                    'description_ar': 'فرص وأنظمة الاستثمار',
                    'slug': 'investment'
                },
                {
                    'name': 'التأمين',
                    'name_ar': 'التأمين',
                    'description': 'سياسات وتحديثات قطاع التأمين',
                    'description_ar': 'سياسات وتحديثات قطاع التأمين',
                    'slug': 'insurance'
                }
            ],
            'تجارة': [
                {
                    'name': 'الاستيراد/التصدير',
                    'name_ar': 'الاستيراد/التصدير',
                    'description': 'أنظمة وإجراءات الاستيراد والتصدير',
                    'description_ar': 'أنظمة وإجراءات الاستيراد والتصدير',
                    'slug': 'import-export'
                },
                {
                    'name': 'الاتفاقيات التجارية',
                    'name_ar': 'الاتفاقيات التجارية',
                    'description': 'اتفاقيات التجارة الثنائية ومتعددة الأطراف',
                    'description_ar': 'اتفاقيات التجارة الثنائية ومتعددة الأطراف',
                    'slug': 'trade-agreements'
                },
                {
                    'name': 'الوصول إلى الأسواق',
                    'name_ar': 'الوصول إلى الأسواق',
                    'description': 'شروط ومتطلبات الوصول إلى الأسواق',
                    'description_ar': 'شروط ومتطلبات الوصول إلى الأسواق',
                    'slug': 'market-access'
                }
            ]
        }
        
        for category in categories:
            if category.name in subcategories_data:
                for sub_data in subcategories_data[category.name]:
                    subcategory, created = SubCategory.objects.get_or_create(
                        name=sub_data['name'],
                        category=category,
                        defaults={
                            'name_ar': sub_data['name_ar'],
                            'description': sub_data['description'],
                            'description_ar': sub_data['description_ar'],
                            'slug': sub_data['slug']
                        }
                    )
                    if created:
                        self.stdout.write(f'Created subcategory: {subcategory.name}')

    def create_hashtags(self):
        self.stdout.write('Creating hashtags...')
        hashtag_data = [
            {
                'name': 'اقتصاد_2024',
                'slug': 'economy2024',
                'is_trending': True,
                'post_count': 0,
                'last_used': timezone.now()
            },
            {
                'name': 'تحديثات_مالية',
                'slug': 'financeupdate',
                'is_trending': True,
                'post_count': 0,
                'last_used': timezone.now()
            },
            {
                'name': 'أخبار_التجارة',
                'slug': 'tradenews',
                'is_trending': True,
                'post_count': 0,
                'last_used': timezone.now()
            }
        ]
        
        for data in hashtag_data:
            hashtag, created = HashTag.objects.get_or_create(
                name=data['name'],
                defaults={
                    'slug': data['slug'],
                    'is_trending': data['is_trending'],
                    'post_count': data['post_count'],
                    'last_used': data['last_used']
                }
            )
            if created:
                self.stdout.write(f'Created hashtag: {hashtag.name}')

    def create_post_attachments(self, post, index):
        """Helper method to create attachments for a post"""
        attachment_data = [
            {
                'title': f'وثيقة السياسة {index}',
                'description': 'وثيقة السياسة الرسمية بصيغة PDF',
                'file_type': 'application/pdf',
                'order': 1
            },
            {
                'title': f'رسم توضيحي {index}',
                'description': 'تمثيل مرئي للنقاط الرئيسية',
                'file_type': 'image/jpeg',
                'order': 2
            }
        ]
        
        for data in attachment_data:
            # In a real scenario, you would handle actual file uploads
            # For seeding, we'll just create the database entries
            attachment = PostAttachment.objects.create(
                post=post,
                title=data['title'],
                description=data['description'],
                file_type=data['file_type'],
                order=data['order']
            )
            self.stdout.write(f'Created attachment: {attachment.title} for post: {post.title}')

    def create_posts(self):
        self.stdout.write('Creating posts...')
        users = User.objects.all()
        post_types = PostType.objects.all()
        organizations = Organization.objects.all()
        categories = Category.objects.all()
        hashtags = HashTag.objects.all()
        
        posts_data = [
            {
                'title': 'إطار السياسة الاقتصادية الجديد',
                'title_ar': 'إطار السياسة الاقتصادية الجديد',
                'content': '''
                تعلن وزارة الاقتصاد عن إطار جديد وشامل للسياسة الاقتصادية
                يهدف إلى التنمية المستدامة واستقرار السوق.
                
                النقاط الرئيسية تشمل:
                1. تسهيل الاستثمار
                2. أنظمة السوق
                3. مبادرات النمو الاقتصادي
                ''',
                'content_ar': '''
                تعلن وزارة الاقتصاد عن إطار جديد وشامل للسياسة الاقتصادية
                يهدف إلى التنمية المستدامة واستقرار السوق.
                
                النقاط الرئيسية تشمل:
                1. تسهيل الاستثمار
                2. أنظمة السوق
                3. مبادرات النمو الاقتصادي
                ''',
                'summary': 'إعلان إطار السياسة الاقتصادية الجديد مع المبادرات الرئيسية',
                'summary_ar': 'إعلان إطار السياسة الاقتصادية الجديد مع المبادرات الرئيسية',
                'meta_description': 'إعلان إطار شامل للسياسة الاقتصادية',
                'meta_keywords': 'سياسة اقتصادية، استثمار، استقرار السوق',
                'status': 'published'
            },
            {
                'title': 'تحديثات القطاع المالي 2024',
                'title_ar': 'تحديثات القطاع المالي 2024',
                'content': '''
                يعلن المصرف المركزي عن تحديثات رئيسية للوائح القطاع المالي
                لعام 2024، مع التركيز على التحول الرقمي والشمول المالي.
                
                التحديثات تشمل:
                1. إرشادات الخدمات المصرفية الرقمية
                2. لوائح التكنولوجيا المالية
                3. إصلاحات القطاع المصرفي
                ''',
                'content_ar': '''
                يعلن المصرف المركزي عن تحديثات رئيسية للوائح القطاع المالي
                لعام 2024، مع التركيز على التحول الرقمي والشمول المالي.
                
                التحديثات تشمل:
                1. إرشادات الخدمات المصرفية الرقمية
                2. لوائح التكنولوجيا المالية
                3. إصلاحات القطاع المصرفي
                ''',
                'summary': 'تحديثات رئيسية للقطاع المالي لعام 2024',
                'summary_ar': 'تحديثات رئيسية للقطاع المالي لعام 2024',
                'meta_description': 'تحديثات تنظيمية للقطاع المالي لعام 2024',
                'meta_keywords': 'قطاع مالي، خدمات مصرفية، لوائح تنظيمية',
                'status': 'published'
            },
            {
                'title': 'إعلان اتفاقية تجارية',
                'title_ar': 'إعلان اتفاقية تجارية',
                'content': '''
                تعلن وزارة التجارة عن اتفاقية تجارية ثنائية جديدة
                تهدف إلى تعزيز العلاقات التجارية والتعاون الاقتصادي.
                
                أبرز نقاط الاتفاقية:
                1. تخفيض التعريفات
                2. تسهيل التجارة
                3. الشراكات الاقتصادية
                ''',
                'content_ar': '''
                تعلن وزارة التجارة عن اتفاقية تجارية ثنائية جديدة
                تهدف إلى تعزيز العلاقات التجارية والتعاون الاقتصادي.
                
                أبرز نقاط الاتفاقية:
                1. تخفيض التعريفات
                2. تسهيل التجارة
                3. الشراكات الاقتصادية
                ''',
                'summary': 'إعلان اتفاقية تجارية ثنائية جديدة',
                'summary_ar': 'إعلان اتفاقية تجارية ثنائية جديدة',
                'meta_description': 'إعلان وتفاصيل اتفاقية تجارية جديدة',
                'meta_keywords': 'اتفاقية تجارية، تجارة ثنائية، تعاون اقتصادي',
                'status': 'published'
            }
        ]
        
        for index, data in enumerate(posts_data, 1):
            post = Post.objects.create(
                title=data['title'],
                title_ar=data['title_ar'],
                content=data['content'],
                content_ar=data['content_ar'],
                summary=data['summary'],
                summary_ar=data['summary_ar'],
                meta_description=data['meta_description'],
                meta_keywords=data['meta_keywords'],
                status=data['status'],
                author=users[index % len(users)],
                type=post_types[index % len(post_types)],
                organization=organizations[index % len(organizations)],
                published_at=timezone.now() if data['status'] == 'published' else None
            )
            
            # Add categories and hashtags
            post.categories.add(categories[index % len(categories)])
            post.hashtags.add(hashtags[index % len(hashtags)])
            
            # Create attachments
            self.create_post_attachments(post, index)
            
            self.stdout.write(f'Created post: {post.title}')

    def create_bookmarks(self):
        self.stdout.write('Creating bookmarks...')
        users = User.objects.all()
        posts = Post.objects.all()
        
        for user in users:
            for post in posts:
                bookmark = Bookmark.objects.create(
                    user=user,
                    post=post,
                    notes='ملاحظات المستخدم حول المحتوى'
                )
                self.stdout.write(f'Created bookmark for user {user.username} on post {post.title}') 