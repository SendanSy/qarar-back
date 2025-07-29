from django.core.management.base import BaseCommand
from django.db import transaction
from apps.content.models import Category, SubCategory, PostType
from apps.geographics.models import Country, State, City
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Seeds the database with reference data for categories, post types, and geographic locations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            if options['clear']:
                self.stdout.write('Clearing existing data...')
                self.clear_data()
            
            self.stdout.write('Seeding categories and subcategories...')
            self.seed_categories()
            
            self.stdout.write('Seeding post types...')
            self.seed_post_types()
            
            self.stdout.write('Seeding geographic data...')
            self.seed_geographic_data()
            
            self.stdout.write(self.style.SUCCESS('Successfully seeded reference data'))

    def clear_data(self):
        """Clear existing reference data"""
        SubCategory.objects.all().delete()
        Category.objects.all().delete()
        PostType.objects.all().delete()
        City.objects.all().delete()
        State.objects.all().delete()
        Country.objects.filter(code='SYR').delete()

    def seed_categories(self):
        """Seed categories and subcategories"""
        # Use the base manager to avoid the GROUP BY issue
        from django.db import models
        
        categories_data = [
            {
                'name': 'Law',
                'name_ar': 'القانون',
                'description': "The legal system governing Syria's civil, criminal, and administrative matters.",
                'description_ar': 'النظام القانوني الذي يحكم الشؤون المدنية والجنائية والإدارية في سوريا.',
                'subcategories': [
                    {
                        'name': 'Civil Law',
                        'name_ar': 'القانون المدني',
                        'description': 'Legal framework governing personal rights, contracts, and property disputes between individuals.',
                        'description_ar': 'الإطار القانوني الذي يحكم الحقوق الشخصية والعقود والنزاعات العقارية بين الأفراد.'
                    },
                    {
                        'name': 'Criminal Law',
                        'name_ar': 'القانون الجنائي',
                        'description': 'Legal system addressing crimes, punishments, and prosecution of criminal offenses.',
                        'description_ar': 'النظام القانوني الذي يتناول الجرائم والعقوبات ومحاكمة الجرائم الجنائية.'
                    }
                ]
            },
            {
                'name': 'Education',
                'name_ar': 'التعليم',
                'description': 'The educational system providing learning opportunities from elementary through higher education.',
                'description_ar': 'النظام التعليمي الذي يوفر فرص التعلم من المرحلة الابتدائية حتى التعليم العالي.',
                'subcategories': [
                    {
                        'name': 'Primary Education',
                        'name_ar': 'التعليم الابتدائي',
                        'description': 'Basic education for children typically ages 6-12 covering fundamental subjects.',
                        'description_ar': 'التعليم الأساسي للأطفال عادة من سن 6-12 يغطي المواد الأساسية.'
                    },
                    {
                        'name': 'Higher Education',
                        'name_ar': 'التعليم العالي',
                        'description': 'University-level education including undergraduate and graduate degree programs.',
                        'description_ar': 'التعليم على مستوى الجامعة بما في ذلك برامج البكالوريوس والدراسات العليا.'
                    }
                ]
            },
            {
                'name': 'Healthcare',
                'name_ar': 'الرعاية الصحية',
                'description': "Medical services and public health systems serving the population's health needs.",
                'description_ar': 'الخدمات الطبية وأنظمة الصحة العامة التي تلبي احتياجات السكان الصحية.',
                'subcategories': [
                    {
                        'name': 'Public Health',
                        'name_ar': 'الصحة العامة',
                        'description': 'Government-provided healthcare services and disease prevention programs.',
                        'description_ar': 'الخدمات الصحية المقدمة من الحكومة وبرامج الوقاية من الأمراض.'
                    },
                    {
                        'name': 'Private Healthcare',
                        'name_ar': 'الرعاية الصحية الخاصة',
                        'description': 'Medical services provided by private hospitals and clinics.',
                        'description_ar': 'الخدمات الطبية المقدمة من المستشفيات والعيادات الخاصة.'
                    }
                ]
            },
            {
                'name': 'Economy',
                'name_ar': 'الاقتصاد',
                'description': "The country's financial system, trade, and economic activities.",
                'description_ar': 'النظام المالي للبلاد والتجارة والأنشطة الاقتصادية.',
                'subcategories': [
                    {
                        'name': 'Agriculture',
                        'name_ar': 'الزراعة',
                        'description': 'Farming and agricultural production including crops and livestock.',
                        'description_ar': 'الزراعة والإنتاج الزراعي بما في ذلك المحاصيل والثروة الحيوانية.'
                    },
                    {
                        'name': 'Industry',
                        'name_ar': 'الصناعة',
                        'description': 'Manufacturing and industrial production sectors.',
                        'description_ar': 'قطاعات التصنيع والإنتاج الصناعي.'
                    }
                ]
            },
            {
                'name': 'Infrastructure',
                'name_ar': 'البنية التحتية',
                'description': "Basic physical systems supporting the country's development and daily operations.",
                'description_ar': 'الأنظمة الفيزيائية الأساسية التي تدعم تنمية البلاد والعمليات اليومية.',
                'subcategories': [
                    {
                        'name': 'Transportation',
                        'name_ar': 'النقل',
                        'description': 'Road, rail, and air transport systems connecting different regions.',
                        'description_ar': 'أنظمة النقل البري والسكك الحديدية والجوية التي تربط المناطق المختلفة.'
                    },
                    {
                        'name': 'Utilities',
                        'name_ar': 'المرافق العامة',
                        'description': 'Essential services including electricity, water, and telecommunications.',
                        'description_ar': 'الخدمات الأساسية بما في ذلك الكهرباء والمياه والاتصالات.'
                    }
                ]
            },
            {
                'name': 'Culture',
                'name_ar': 'الثقافة',
                'description': "The country's traditions, arts, and cultural heritage.",
                'description_ar': 'تقاليد البلاد والفنون والتراث الثقافي.',
                'subcategories': [
                    {
                        'name': 'Arts',
                        'name_ar': 'الفنون',
                        'description': 'Creative expressions including music, literature, and visual arts.',
                        'description_ar': 'التعبيرات الإبداعية بما في ذلك الموسيقى والأدب والفنون البصرية.'
                    },
                    {
                        'name': 'Heritage',
                        'name_ar': 'التراث',
                        'description': 'Historical sites, monuments, and traditional practices.',
                        'description_ar': 'المواقع التاريخية والآثار والممارسات التقليدية.'
                    }
                ]
            },
            {
                'name': 'Security',
                'name_ar': 'الأمن',
                'description': 'National defense and internal security systems protecting the country.',
                'description_ar': 'الدفاع الوطني وأنظمة الأمن الداخلي التي تحمي البلاد.',
                'subcategories': [
                    {
                        'name': 'National Defense',
                        'name_ar': 'الدفاع الوطني',
                        'description': 'Military forces protecting against external threats.',
                        'description_ar': 'القوات العسكرية التي تحمي من التهديدات الخارجية.'
                    },
                    {
                        'name': 'Internal Security',
                        'name_ar': 'الأمن الداخلي',
                        'description': 'Police and security forces maintaining law and order.',
                        'description_ar': 'قوات الشرطة والأمن التي تحافظ على القانون والنظام.'
                    }
                ]
            },
            {
                'name': 'Environment',
                'name_ar': 'البيئة',
                'description': 'Natural resources and environmental protection efforts.',
                'description_ar': 'الموارد الطبيعية وجهود حماية البيئة.',
                'subcategories': [
                    {
                        'name': 'Natural Resources',
                        'name_ar': 'الموارد الطبيعية',
                        'description': 'Oil, gas, minerals, and other natural assets.',
                        'description_ar': 'النفط والغاز والمعادن وغيرها من الأصول الطبيعية.'
                    },
                    {
                        'name': 'Conservation',
                        'name_ar': 'المحافظة على البيئة',
                        'description': 'Environmental protection and sustainability initiatives.',
                        'description_ar': 'مبادرات حماية البيئة والاستدامة.'
                    }
                ]
            },
            {
                'name': 'Social Services',
                'name_ar': 'الخدمات الاجتماعية',
                'description': 'Government programs supporting citizen welfare and social needs.',
                'description_ar': 'البرامج الحكومية التي تدعم رفاهية المواطنين والاحتياجات الاجتماعية.',
                'subcategories': [
                    {
                        'name': 'Social Welfare',
                        'name_ar': 'الرعاية الاجتماعية',
                        'description': 'Government assistance programs for vulnerable populations.',
                        'description_ar': 'برامج المساعدة الحكومية للفئات الضعيفة.'
                    },
                    {
                        'name': 'Housing',
                        'name_ar': 'الإسكان',
                        'description': 'Public and private housing development and policies.',
                        'description_ar': 'تطوير الإسكان العام والخاص والسياسات.'
                    }
                ]
            },
            {
                'name': 'Technology',
                'name_ar': 'التكنولوجيا',
                'description': 'Information technology and digital infrastructure development.',
                'description_ar': 'تكنولوجيا المعلومات وتطوير البنية التحتية الرقمية.',
                'subcategories': [
                    {
                        'name': 'Information Technology',
                        'name_ar': 'تكنولوجيا المعلومات',
                        'description': 'Computer systems, software, and digital services.',
                        'description_ar': 'أنظمة الكمبيوتر والبرمجيات والخدمات الرقمية.'
                    },
                    {
                        'name': 'Telecommunications',
                        'name_ar': 'الاتصالات',
                        'description': 'Phone, internet, and communication network systems.',
                        'description_ar': 'أنظمة الهاتف والإنترنت وشبكات الاتصال.'
                    }
                ]
            },
            {
                'name': 'Media',
                'name_ar': 'الإعلام',
                'description': 'Mass communication channels and information dissemination systems serving the public.',
                'description_ar': 'قنوات الاتصال الجماهيري وأنظمة نشر المعلومات التي تخدم الجمهور.',
                'subcategories': [
                    {
                        'name': 'Traditional Media',
                        'name_ar': 'الإعلام التقليدي',
                        'description': 'Television, radio, and print newspapers providing news and entertainment.',
                        'description_ar': 'التلفزيون والراديو والصحف المطبوعة التي توفر الأخبار والترفيه.'
                    },
                    {
                        'name': 'Digital Media',
                        'name_ar': 'الإعلام الرقمي',
                        'description': 'Online platforms, social media, and internet-based news sources.',
                        'description_ar': 'المنصات الإلكترونية ووسائل التواصل الاجتماعي ومصادر الأخبار عبر الإنترنت.'
                    }
                ]
            }
        ]

        for idx, cat_data in enumerate(categories_data):
            # Use a simpler approach to avoid GROUP BY issue with CategoryManager
            try:
                # Check if category exists using a simple filter
                category = Category.objects.filter(name=cat_data['name']).first()
                if category:
                    # Update existing category
                    category.name_ar = cat_data['name_ar']
                    category.description = cat_data['description']
                    category.description_ar = cat_data['description_ar']
                    category.slug = slugify(cat_data['name'])
                    category.order = idx + 1
                    category.is_active = True
                    category.is_deleted = False
                    category.save()
                    created = False
                else:
                    # Create new category
                    category = Category(
                        name=cat_data['name'],
                        name_ar=cat_data['name_ar'],
                        description=cat_data['description'],
                        description_ar=cat_data['description_ar'],
                        slug=slugify(cat_data['name']),
                        order=idx + 1,
                        is_active=True
                    )
                    category.save()
                    created = True
                
                if created:
                    self.stdout.write(f"Created category: {category.name}")
                else:
                    self.stdout.write(f"Updated category: {category.name}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error with category {cat_data['name']}: {str(e)}"))
            
            # Create subcategories
            for sub_idx, sub_data in enumerate(cat_data.get('subcategories', [])):
                try:
                    subcategory = SubCategory.objects.filter(
                        category=category,
                        name=sub_data['name']
                    ).first()
                    
                    if subcategory:
                        # Update existing subcategory
                        subcategory.name_ar = sub_data['name_ar']
                        subcategory.description = sub_data['description']
                        subcategory.description_ar = sub_data['description_ar']
                        subcategory.slug = slugify(sub_data['name'])
                        subcategory.order = sub_idx + 1
                        subcategory.is_active = True
                        subcategory.is_deleted = False
                        subcategory.save()
                        sub_created = False
                    else:
                        # Create new subcategory
                        subcategory = SubCategory(
                            category=category,
                            name=sub_data['name'],
                            name_ar=sub_data['name_ar'],
                            description=sub_data['description'],
                            description_ar=sub_data['description_ar'],
                            slug=slugify(sub_data['name']),
                            order=sub_idx + 1,
                            is_active=True
                        )
                        subcategory.save()
                        sub_created = True
                    
                    if sub_created:
                        self.stdout.write(f"  Created subcategory: {subcategory.name}")
                    else:
                        self.stdout.write(f"  Updated subcategory: {subcategory.name}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error with subcategory {sub_data['name']}: {str(e)}"))

    def seed_post_types(self):
        """Seed post types"""
        post_types_data = [
            {
                'name': 'Decision',
                'name_ar': 'قرار',
                'description': 'Official ruling or judgment made by an authority.',
                'description_ar': 'قرار أو حكم رسمي صادر عن سلطة مختصة.'
            },
            {
                'name': 'Circular',
                'name_ar': 'تعميم',
                'description': 'Internal communication distributed to multiple recipients.',
                'description_ar': 'تواصل داخلي يُوزع على عدة مستلمين.'
            },
            {
                'name': 'Announcement',
                'name_ar': 'إعلان',
                'description': 'Public notice or proclamation for general information.',
                'description_ar': 'إشعار عام أو إعلان لنشر معلومات عامة.'
            },
            {
                'name': 'Statement',
                'name_ar': 'بيان',
                'description': 'Official declaration or position on a matter.',
                'description_ar': 'إعلان رسمي أو موقف بشأن قضية معينة.'
            },
            {
                'name': 'Administrative Order',
                'name_ar': 'أمر إداري',
                'description': 'Administrative directive from management.',
                'description_ar': 'توجيه إداري صادر عن الإدارة.'
            },
            {
                'name': 'Mission Order',
                'name_ar': 'أمر مهمة',
                'description': 'Task assignment or mission directive.',
                'description_ar': 'تكليف بمهمة أو توجيه خاص بمهمة محددة.'
            },
            {
                'name': 'Judicial Order',
                'name_ar': 'أمر قضائي',
                'description': 'Court order or judicial directive.',
                'description_ar': 'أمر محكمة أو توجيه قضائي.'
            },
            {
                'name': 'Court Ruling',
                'name_ar': 'حكم قضائي',
                'description': 'Final judicial decision or verdict.',
                'description_ar': 'قرار قضائي نهائي أو حكم.'
            },
            {
                'name': 'Request',
                'name_ar': 'طلب',
                'description': 'Formal application or petition for something.',
                'description_ar': 'طلب رسمي أو التماس للحصول على شيء ما.'
            },
            {
                'name': 'Decree',
                'name_ar': 'مرسوم',
                'description': 'Executive decree issued by high authority.',
                'description_ar': 'مرسوم تنفيذي صادر عن سلطة عليا.'
            },
            {
                'name': 'Notice',
                'name_ar': 'بلاغ',
                'description': 'Official notification or advisory message.',
                'description_ar': 'إشعار رسمي أو رسالة إعلامية.'
            },
            {
                'name': 'Letter',
                'name_ar': 'كتاب',
                'description': 'Formal correspondence or official letter.',
                'description_ar': 'مراسلة رسمية أو كتاب رسمي.'
            },
            {
                'name': 'Referral',
                'name_ar': 'إحالة',
                'description': 'Transfer of case or matter to another authority.',
                'description_ar': 'نقل قضية أو أمر إلى سلطة أخرى.'
            },
            {
                'name': 'Reference',
                'name_ar': 'إشارة',
                'description': 'Citation or reference to existing documents.',
                'description_ar': 'استشهاد أو إشارة إلى وثائق موجودة.'
            },
            {
                'name': 'Recommendation',
                'name_ar': 'توصية',
                'description': 'Formal suggestion or advisory proposal.',
                'description_ar': 'اقتراح رسمي أو توصية استشارية.'
            },
            {
                'name': 'Minutes',
                'name_ar': 'محضر',
                'description': 'Official record of meeting proceedings.',
                'description_ar': 'سجل رسمي لوقائع اجتماع.'
            },
            {
                'name': 'Permit',
                'name_ar': 'إذن',
                'description': 'Authorization or license for specific activity.',
                'description_ar': 'تصريح أو ترخيص لنشاط محدد.'
            },
            {
                'name': 'Warning',
                'name_ar': 'إنذار',
                'description': 'Official warning or cautionary notice.',
                'description_ar': 'تحذير رسمي أو إشعار تحذيري.'
            },
            {
                'name': 'Agreement',
                'name_ar': 'اتفاقية',
                'description': 'Formal contract or treaty between parties.',
                'description_ar': 'عقد رسمي أو معاهدة بين أطراف.'
            },
            {
                'name': 'Report',
                'name_ar': 'تقرير',
                'description': 'Detailed account or analysis document.',
                'description_ar': 'حساب مفصل أو وثيقة تحليلية.'
            },
            {
                'name': 'Memorandum',
                'name_ar': 'مذكرة',
                'description': 'Internal note or briefing document.',
                'description_ar': 'مذكرة داخلية أو وثيقة إحاطة.'
            },
            {
                'name': 'Assignment',
                'name_ar': 'تكليف',
                'description': 'Official delegation of responsibility or task.',
                'description_ar': 'تفويض رسمي بمسؤولية أو مهمة.'
            },
            {
                'name': 'Other',
                'name_ar': 'أخرى',
                'description': 'Miscellaneous or unspecified document type.',
                'description_ar': 'نوع وثيقة متنوعة أو غير محددة.'
            },
            {
                'name': 'Property Document',
                'name_ar': 'وثيقة عقارية',
                'description': 'Real estate or property-related document.',
                'description_ar': 'وثيقة متعلقة بالعقارات أو الممتلكات.'
            },
            {
                'name': 'Administrative Document',
                'name_ar': 'وثيقة إدارية',
                'description': 'General administrative paperwork.',
                'description_ar': 'أوراق إدارية عامة.'
            }
        ]

        for post_type_data in post_types_data:
            post_type, created = PostType.objects.update_or_create(
                name=post_type_data['name'],
                defaults={
                    'name_ar': post_type_data['name_ar'],
                    'description': post_type_data['description'],
                    'description_ar': post_type_data['description_ar'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f"Created post type: {post_type.name}")
            else:
                self.stdout.write(f"Updated post type: {post_type.name}")

    def seed_geographic_data(self):
        """Seed geographic data for Syria"""
        # Create Syria country
        syria, created = Country.objects.update_or_create(
            code='SYR',
            defaults={
                'name': 'Syria',
                'is_active': True
            }
        )
        
        if created:
            self.stdout.write('Created country: Syria')
        else:
            self.stdout.write('Updated country: Syria')

        # Governorates and cities data
        governorates_data = [
            {
                'name': 'Damascus Governorate',
                'name_ar': 'محافظة دمشق',
                'code': 'DM',
                'cities': [
                    {'name': 'Damascus', 'name_ar': 'دمشق', 'code': 'DM-01'},
                    {'name': 'Douma', 'name_ar': 'دوما', 'code': 'DM-02'},
                    {'name': 'Harasta', 'name_ar': 'حرستا', 'code': 'DM-03'},
                    {'name': 'Daraya', 'name_ar': 'داريا', 'code': 'DM-04'}
                ]
            },
            {
                'name': 'Aleppo Governorate',
                'name_ar': 'محافظة حلب',
                'code': 'HL',
                'cities': [
                    {'name': 'Aleppo', 'name_ar': 'حلب', 'code': 'HL-01'},
                    {'name': 'Azaz', 'name_ar': 'أعزاز', 'code': 'HL-02'},
                    {'name': 'Al-Bab', 'name_ar': 'الباب', 'code': 'HL-03'},
                    {'name': 'Afrin', 'name_ar': 'عفرين', 'code': 'HL-04'}
                ]
            },
            {
                'name': 'Homs Governorate',
                'name_ar': 'محافظة حمص',
                'code': 'HM',
                'cities': [
                    {'name': 'Homs', 'name_ar': 'حمص', 'code': 'HM-01'},
                    {'name': 'Palmyra', 'name_ar': 'تدمر', 'code': 'HM-02'},
                    {'name': 'Al-Qusayr', 'name_ar': 'القصير', 'code': 'HM-03'},
                    {'name': 'Rastan', 'name_ar': 'الرستن', 'code': 'HM-04'}
                ]
            },
            {
                'name': 'Hama Governorate',
                'name_ar': 'محافظة حماة',
                'code': 'HI',
                'cities': [
                    {'name': 'Hama', 'name_ar': 'حماة', 'code': 'HI-01'},
                    {'name': 'Salamiyah', 'name_ar': 'سلمية', 'code': 'HI-02'},
                    {'name': 'Suran', 'name_ar': 'صوران', 'code': 'HI-03'},
                    {'name': 'Masyaf', 'name_ar': 'مصياف', 'code': 'HI-04'}
                ]
            },
            {
                'name': 'Latakia Governorate',
                'name_ar': 'محافظة اللاذقية',
                'code': 'LA',
                'cities': [
                    {'name': 'Latakia', 'name_ar': 'اللاذقية', 'code': 'LA-01'},
                    {'name': 'Jableh', 'name_ar': 'جبلة', 'code': 'LA-02'},
                    {'name': 'Qardaha', 'name_ar': 'القرداحة', 'code': 'LA-03'},
                    {'name': 'Al-Haffah', 'name_ar': 'الحفة', 'code': 'LA-04'}
                ]
            },
            {
                'name': 'Tartus Governorate',
                'name_ar': 'محافظة طرطوس',
                'code': 'TA',
                'cities': [
                    {'name': 'Tartus', 'name_ar': 'طرطوس', 'code': 'TA-01'},
                    {'name': 'Banias', 'name_ar': 'بانياس', 'code': 'TA-02'},
                    {'name': 'Safita', 'name_ar': 'صافيتا', 'code': 'TA-03'},
                    {'name': 'Dreikish', 'name_ar': 'دريكيش', 'code': 'TA-04'}
                ]
            },
            {
                'name': 'Idlib Governorate',
                'name_ar': 'محافظة إدلب',
                'code': 'ID',
                'cities': [
                    {'name': 'Idlib', 'name_ar': 'إدلب', 'code': 'ID-01'},
                    {'name': 'Jisr al-Shughur', 'name_ar': 'جسر الشغور', 'code': 'ID-02'},
                    {'name': 'Maarat al-Numan', 'name_ar': 'معرة النعمان', 'code': 'ID-03'},
                    {'name': 'Saraqib', 'name_ar': 'سراقب', 'code': 'ID-04'}
                ]
            },
            {
                'name': 'Daraa Governorate',
                'name_ar': 'محافظة درعا',
                'code': 'DR',
                'cities': [
                    {'name': 'Daraa', 'name_ar': 'درعا', 'code': 'DR-01'},
                    {'name': 'Bosra', 'name_ar': 'بصرى', 'code': 'DR-02'},
                    {'name': 'Al-Sanamayn', 'name_ar': 'الصنمين', 'code': 'DR-03'},
                    {'name': 'Nawa', 'name_ar': 'نوى', 'code': 'DR-04'}
                ]
            },
            {
                'name': 'As-Suwayda Governorate',
                'name_ar': 'محافظة السويداء',
                'code': 'SU',
                'cities': [
                    {'name': 'As-Suwayda', 'name_ar': 'السويداء', 'code': 'SU-01'},
                    {'name': 'Salkhad', 'name_ar': 'صلخد', 'code': 'SU-02'},
                    {'name': 'Shahba', 'name_ar': 'شهبا', 'code': 'SU-03'},
                    {'name': 'Qanawat', 'name_ar': 'قنوات', 'code': 'SU-04'}
                ]
            },
            {
                'name': 'Quneitra Governorate',
                'name_ar': 'محافظة القنيطرة',
                'code': 'QU',
                'cities': [
                    {'name': 'Quneitra', 'name_ar': 'القنيطرة', 'code': 'QU-01'},
                    {'name': 'Khan Arnabah', 'name_ar': 'خان أرنبة', 'code': 'QU-02'},
                    {'name': 'Fiq', 'name_ar': 'فيق', 'code': 'QU-03'},
                    {'name': 'Jubata al-Khashab', 'name_ar': 'جباتا الخشب', 'code': 'QU-04'}
                ]
            },
            {
                'name': 'Deir ez-Zor Governorate',
                'name_ar': 'محافظة دير الزور',
                'code': 'DZ',
                'cities': [
                    {'name': 'Deir ez-Zor', 'name_ar': 'دير الزور', 'code': 'DZ-01'},
                    {'name': 'Al-Mayadin', 'name_ar': 'الميادين', 'code': 'DZ-02'},
                    {'name': 'Al-Bukamal', 'name_ar': 'البوكمال', 'code': 'DZ-03'},
                    {'name': 'Al-Ashara', 'name_ar': 'العشارة', 'code': 'DZ-04'}
                ]
            },
            {
                'name': 'Ar-Raqqa Governorate',
                'name_ar': 'محافظة الرقة',
                'code': 'RA',
                'cities': [
                    {'name': 'Ar-Raqqa', 'name_ar': 'الرقة', 'code': 'RA-01'},
                    {'name': 'Tell Abiad', 'name_ar': 'تل أبيض', 'code': 'RA-02'},
                    {'name': 'Tabqa', 'name_ar': 'الطبقة', 'code': 'RA-03'},
                    {'name': 'Suluk', 'name_ar': 'سلوك', 'code': 'RA-04'}
                ]
            },
            {
                'name': 'Al-Hasakah Governorate',
                'name_ar': 'محافظة الحسكة',
                'code': 'HA',
                'cities': [
                    {'name': 'Al-Hasakah', 'name_ar': 'الحسكة', 'code': 'HA-01'},
                    {'name': 'Qamishli', 'name_ar': 'القامشلي', 'code': 'HA-02'},
                    {'name': 'Ras al-Ayn', 'name_ar': 'رأس العين', 'code': 'HA-03'},
                    {'name': 'Al-Malikiyah', 'name_ar': 'المالكية', 'code': 'HA-04'}
                ]
            },
            {
                'name': 'Rif Dimashq Governorate',
                'name_ar': 'محافظة ريف دمشق',
                'code': 'RD',
                'cities': [
                    {'name': 'Zabadani', 'name_ar': 'الزبداني', 'code': 'RD-01'},
                    {'name': 'Qalamoun', 'name_ar': 'القلمون', 'code': 'RD-02'},
                    {'name': 'Eastern Ghouta', 'name_ar': 'الغوطة الشرقية', 'code': 'RD-03'},
                    {'name': 'Qudsaya', 'name_ar': 'قدسيا', 'code': 'RD-04'}
                ]
            }
        ]

        for gov_data in governorates_data:
            # Create or update governorate (State model)
            governorate, gov_created = State.objects.update_or_create(
                country=syria,
                code=gov_data['code'],
                defaults={
                    'name': gov_data['name'],
                    'is_active': True
                }
            )
            
            if gov_created:
                self.stdout.write(f"Created governorate: {governorate.name}")
            else:
                self.stdout.write(f"Updated governorate: {governorate.name}")
            
            # Create cities
            for city_data in gov_data['cities']:
                city, city_created = City.objects.update_or_create(
                    state=governorate,
                    code=city_data['code'],
                    defaults={
                        'name': city_data['name'],
                        'is_active': True
                    }
                )
                
                if city_created:
                    self.stdout.write(f"  Created city: {city.name}")
                else:
                    self.stdout.write(f"  Updated city: {city.name}")