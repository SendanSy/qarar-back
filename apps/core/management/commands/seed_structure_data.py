"""
Management command to seed geographic, category, and producer data
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.geographics.models import Country, State, City
from apps.content.models.classification import Category, SubCategory
from apps.content.models.post import PostType
from apps.producers.models import Organization, Subsidiary, Department


class Command(BaseCommand):
    help = 'Seeds the database with geographic, category, and producer data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-geographic',
            action='store_true',
            help='Skip geographic data seeding'
        )
        parser.add_argument(
            '--skip-categories',
            action='store_true',
            help='Skip category data seeding'
        )
        parser.add_argument(
            '--skip-producers',
            action='store_true',
            help='Skip producer data seeding'
        )
        parser.add_argument(
            '--skip-post-types',
            action='store_true',
            help='Skip post type data seeding'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean all seeded data instead of seeding'
        )

    def handle(self, *args, **kwargs):
        if kwargs.get('clean'):
            self.stdout.write(self.style.WARNING('Starting data cleaning...'))
            self.clean_all_data()
            return
            
        self.stdout.write(self.style.NOTICE('Starting data seeding...'))
        
        # Seed geographic data
        if not kwargs.get('skip_geographic'):
            self.seed_geographics()
        
        # Seed category data
        if not kwargs.get('skip_categories'):
            self.seed_categories()
        
        # Seed producer data
        if not kwargs.get('skip_producers'):
            self.seed_producers()
        
        # Seed post type data
        if not kwargs.get('skip_post_types'):
            self.seed_post_types()
        
        self.stdout.write(self.style.SUCCESS('Data seeding completed successfully!'))

    @transaction.atomic
    def seed_geographics(self):
        """Seed geographic data (countries, states, cities)"""
        self.stdout.write(self.style.NOTICE('Seeding geographic data...'))
        
        # Geographic data
        geo_data = {
            "country": {
                "name": "سوريا",
                "code": "SYR",
                "is_active": True
            },
            "states": [
                {"name": "دمشق", "code": "DM", "country_code": "SYR", "is_active": True},
                {"name": "ريف دمشق", "code": "RD", "country_code": "SYR", "is_active": True},
                {"name": "حلب", "code": "AL", "country_code": "SYR", "is_active": True},
                {"name": "حمص", "code": "HM", "country_code": "SYR", "is_active": True},
                {"name": "حماة", "code": "HA", "country_code": "SYR", "is_active": True},
                {"name": "اللاذقية", "code": "LA", "country_code": "SYR", "is_active": True},
                {"name": "إدلب", "code": "ID", "country_code": "SYR", "is_active": True},
                {"name": "طرطوس", "code": "TA", "country_code": "SYR", "is_active": True},
                {"name": "السويداء", "code": "SW", "country_code": "SYR", "is_active": True},
                {"name": "درعا", "code": "DR", "country_code": "SYR", "is_active": True},
                {"name": "القنيطرة", "code": "QU", "country_code": "SYR", "is_active": True},
                {"name": "دير الزور", "code": "DZ", "country_code": "SYR", "is_active": True},
                {"name": "الحسكة", "code": "HS", "country_code": "SYR", "is_active": True},
                {"name": "الرقة", "code": "RQ", "country_code": "SYR", "is_active": True}
            ],
            "cities": [
                # Damascus cities
                {"name": "دمشق", "code": "DM01", "state_code": "DM", "is_active": True},
                {"name": "دمشق القديمة", "code": "DM02", "state_code": "DM", "is_active": True},
                {"name": "المزة", "code": "DM03", "state_code": "DM", "is_active": True},
                {"name": "كفر سوسة", "code": "DM04", "state_code": "DM", "is_active": True},
                {"name": "المالكي", "code": "DM05", "state_code": "DM", "is_active": True},
                {"name": "الشعلان", "code": "DM06", "state_code": "DM", "is_active": True},
                {"name": "المهاجرين", "code": "DM07", "state_code": "DM", "is_active": True},
                {"name": "القصاع", "code": "DM08", "state_code": "DM", "is_active": True},
                {"name": "باب توما", "code": "DM09", "state_code": "DM", "is_active": True},
                {"name": "القيمرية", "code": "DM10", "state_code": "DM", "is_active": True},
                
                # Rural Damascus cities
                {"name": "دوما", "code": "RD01", "state_code": "RD", "is_active": True},
                {"name": "حرستا", "code": "RD02", "state_code": "RD", "is_active": True},
                {"name": "داريا", "code": "RD03", "state_code": "RD", "is_active": True},
                {"name": "سقبا", "code": "RD04", "state_code": "RD", "is_active": True},
                {"name": "زملكا", "code": "RD05", "state_code": "RD", "is_active": True},
                {"name": "عين ترما", "code": "RD06", "state_code": "RD", "is_active": True},
                {"name": "الزبداني", "code": "RD07", "state_code": "RD", "is_active": True},
                {"name": "مضايا", "code": "RD08", "state_code": "RD", "is_active": True},
                {"name": "قطنا", "code": "RD09", "state_code": "RD", "is_active": True},
                {"name": "صحنايا", "code": "RD10", "state_code": "RD", "is_active": True},
                {"name": "جرمانا", "code": "RD11", "state_code": "RD", "is_active": True},
                {"name": "مليحة", "code": "RD12", "state_code": "RD", "is_active": True},
                {"name": "التل", "code": "RD13", "state_code": "RD", "is_active": True},
                {"name": "يبرود", "code": "RD14", "state_code": "RD", "is_active": True},
                {"name": "النبك", "code": "RD15", "state_code": "RD", "is_active": True},
                
                # Aleppo cities
                {"name": "حلب", "code": "AL01", "state_code": "AL", "is_active": True},
                {"name": "حلب القديمة", "code": "AL02", "state_code": "AL", "is_active": True},
                {"name": "صلاح الدين", "code": "AL03", "state_code": "AL", "is_active": True},
                {"name": "السكري", "code": "AL04", "state_code": "AL", "is_active": True},
                {"name": "أعزاز", "code": "AL05", "state_code": "AL", "is_active": True},
                {"name": "الباب", "code": "AL06", "state_code": "AL", "is_active": True},
                {"name": "منبج", "code": "AL07", "state_code": "AL", "is_active": True},
                {"name": "عفرين", "code": "AL08", "state_code": "AL", "is_active": True},
                {"name": "جرابلس", "code": "AL09", "state_code": "AL", "is_active": True},
                {"name": "عين العرب", "code": "AL10", "state_code": "AL", "is_active": True},
                {"name": "السفيرة", "code": "AL11", "state_code": "AL", "is_active": True},
                {"name": "مارع", "code": "AL12", "state_code": "AL", "is_active": True},
                {"name": "تل رفعت", "code": "AL13", "state_code": "AL", "is_active": True},
                {"name": "الأتارب", "code": "AL14", "state_code": "AL", "is_active": True},
                
                # Homs cities
                {"name": "حمص", "code": "HM01", "state_code": "HM", "is_active": True},
                {"name": "حمص القديمة", "code": "HM02", "state_code": "HM", "is_active": True},
                {"name": "الخالدية", "code": "HM03", "state_code": "HM", "is_active": True},
                {"name": "تدمر", "code": "HM04", "state_code": "HM", "is_active": True},
                {"name": "القصير", "code": "HM05", "state_code": "HM", "is_active": True},
                {"name": "الرستن", "code": "HM06", "state_code": "HM", "is_active": True},
                {"name": "تلبيسة", "code": "HM07", "state_code": "HM", "is_active": True},
                {"name": "المخرم", "code": "HM08", "state_code": "HM", "is_active": True},
                {"name": "تلكلخ", "code": "HM09", "state_code": "HM", "is_active": True},
                {"name": "الفرقلس", "code": "HM10", "state_code": "HM", "is_active": True},
                {"name": "صدد", "code": "HM11", "state_code": "HM", "is_active": True},
                
                # Hama cities
                {"name": "حماة", "code": "HA01", "state_code": "HA", "is_active": True},
                {"name": "حماة القديمة", "code": "HA02", "state_code": "HA", "is_active": True},
                {"name": "سلمية", "code": "HA03", "state_code": "HA", "is_active": True},
                {"name": "صوران", "code": "HA04", "state_code": "HA", "is_active": True},
                {"name": "كفر زيتا", "code": "HA05", "state_code": "HA", "is_active": True},
                {"name": "محردة", "code": "HA06", "state_code": "HA", "is_active": True},
                {"name": "مصياف", "code": "HA07", "state_code": "HA", "is_active": True},
                {"name": "الغاب", "code": "HA08", "state_code": "HA", "is_active": True},
                {"name": "السقيلبية", "code": "HA09", "state_code": "HA", "is_active": True},
                {"name": "خناصر", "code": "HA10", "state_code": "HA", "is_active": True},
                
                # Latakia cities
                {"name": "اللاذقية", "code": "LA01", "state_code": "LA", "is_active": True},
                {"name": "جبلة", "code": "LA02", "state_code": "LA", "is_active": True},
                {"name": "القرداحة", "code": "LA03", "state_code": "LA", "is_active": True},
                {"name": "الحفة", "code": "LA04", "state_code": "LA", "is_active": True},
                {"name": "صلنفة", "code": "LA05", "state_code": "LA", "is_active": True},
                {"name": "كسب", "code": "LA06", "state_code": "LA", "is_active": True},
                {"name": "القطيلبية", "code": "LA07", "state_code": "LA", "is_active": True},
                {"name": "عين البيضا", "code": "LA08", "state_code": "LA", "is_active": True},
                
                # Idlib cities
                {"name": "إدلب", "code": "ID01", "state_code": "ID", "is_active": True},
                {"name": "جسر الشغور", "code": "ID02", "state_code": "ID", "is_active": True},
                {"name": "أريحا", "code": "ID03", "state_code": "ID", "is_active": True},
                {"name": "سراقب", "code": "ID04", "state_code": "ID", "is_active": True},
                {"name": "معرة النعمان", "code": "ID05", "state_code": "ID", "is_active": True},
                {"name": "خان شيخون", "code": "ID06", "state_code": "ID", "is_active": True},
                {"name": "بنش", "code": "ID07", "state_code": "ID", "is_active": True},
                {"name": "سلقين", "code": "ID08", "state_code": "ID", "is_active": True},
                {"name": "حارم", "code": "ID09", "state_code": "ID", "is_active": True},
                {"name": "كفر تخاريم", "code": "ID10", "state_code": "ID", "is_active": True},
                
                # Tartus cities
                {"name": "طرطوس", "code": "TA01", "state_code": "TA", "is_active": True},
                {"name": "بانياس", "code": "TA02", "state_code": "TA", "is_active": True},
                {"name": "صافيتا", "code": "TA03", "state_code": "TA", "is_active": True},
                {"name": "دريكيش", "code": "TA04", "state_code": "TA", "is_active": True},
                {"name": "الشيخ بدر", "code": "TA05", "state_code": "TA", "is_active": True},
                {"name": "القدموس", "code": "TA06", "state_code": "TA", "is_active": True},
                {"name": "مشتى الحلو", "code": "TA07", "state_code": "TA", "is_active": True},
                
                # As-Suwayda cities
                {"name": "السويداء", "code": "SW01", "state_code": "SW", "is_active": True},
                {"name": "صلخد", "code": "SW02", "state_code": "SW", "is_active": True},
                {"name": "شهبا", "code": "SW03", "state_code": "SW", "is_active": True},
                {"name": "القريا", "code": "SW04", "state_code": "SW", "is_active": True},
                {"name": "عرمان", "code": "SW05", "state_code": "SW", "is_active": True},
                {"name": "الكفر", "code": "SW06", "state_code": "SW", "is_active": True},
                {"name": "المزرعة", "code": "SW07", "state_code": "SW", "is_active": True},
                
                # Daraa cities
                {"name": "درعا", "code": "DR01", "state_code": "DR", "is_active": True},
                {"name": "إزرع", "code": "DR02", "state_code": "DR", "is_active": True},
                {"name": "الصنمين", "code": "DR03", "state_code": "DR", "is_active": True},
                {"name": "نوى", "code": "DR04", "state_code": "DR", "is_active": True},
                {"name": "جاسم", "code": "DR05", "state_code": "DR", "is_active": True},
                {"name": "الشيخ مسكين", "code": "DR06", "state_code": "DR", "is_active": True},
                {"name": "طفس", "code": "DR07", "state_code": "DR", "is_active": True},
                {"name": "المسيفرة", "code": "DR08", "state_code": "DR", "is_active": True},
                
                # Quneitra cities
                {"name": "القنيطرة", "code": "QU01", "state_code": "QU", "is_active": True},
                {"name": "فيق", "code": "QU02", "state_code": "QU", "is_active": True},
                {"name": "خان أرنبة", "code": "QU03", "state_code": "QU", "is_active": True},
                {"name": "مسعدة", "code": "QU04", "state_code": "QU", "is_active": True},
                {"name": "عين زيوان", "code": "QU05", "state_code": "QU", "is_active": True},
                
                # Deir ez-Zor cities
                {"name": "دير الزور", "code": "DZ01", "state_code": "DZ", "is_active": True},
                {"name": "الميادين", "code": "DZ02", "state_code": "DZ", "is_active": True},
                {"name": "البوكمال", "code": "DZ03", "state_code": "DZ", "is_active": True},
                {"name": "الأشارة", "code": "DZ04", "state_code": "DZ", "is_active": True},
                {"name": "الباغوز", "code": "DZ05", "state_code": "DZ", "is_active": True},
                {"name": "الصور", "code": "DZ06", "state_code": "DZ", "is_active": True},
                
                # Al-Hasakah cities
                {"name": "الحسكة", "code": "HS01", "state_code": "HS", "is_active": True},
                {"name": "القامشلي", "code": "HS02", "state_code": "HS", "is_active": True},
                {"name": "رأس العين", "code": "HS03", "state_code": "HS", "is_active": True},
                {"name": "المالكية", "code": "HS04", "state_code": "HS", "is_active": True},
                {"name": "عامودا", "code": "HS05", "state_code": "HS", "is_active": True},
                {"name": "الدرباسية", "code": "HS06", "state_code": "HS", "is_active": True},
                {"name": "تل حميس", "code": "HS07", "state_code": "HS", "is_active": True},
                {"name": "الشدادي", "code": "HS08", "state_code": "HS", "is_active": True},
                
                # Ar-Raqqah cities
                {"name": "الرقة", "code": "RQ01", "state_code": "RQ", "is_active": True},
                {"name": "تل أبيض", "code": "RQ02", "state_code": "RQ", "is_active": True},
                {"name": "ثوار", "code": "RQ03", "state_code": "RQ", "is_active": True},
                {"name": "السلوك", "code": "RQ04", "state_code": "RQ", "is_active": True},
                {"name": "الكرامة", "code": "RQ05", "state_code": "RQ", "is_active": True},
                {"name": "معدان", "code": "RQ06", "state_code": "RQ", "is_active": True}
            ]
        }
        
        # Create or update country
        country_data = geo_data["country"]
        country, created = Country.objects.update_or_create(
            code=country_data["code"],
            defaults={
                "name": country_data["name"],
                "is_active": country_data["is_active"]
            }
        )
        if created:
            self.stdout.write(f"  Created country: {country.name}")
        else:
            self.stdout.write(f"  Updated country: {country.name}")
        
        # Create or update states
        state_map = {}  # Map state codes to state objects for city creation
        states_created = 0
        states_updated = 0
        
        for state_data in geo_data["states"]:
            state, created = State.objects.update_or_create(
                code=state_data["code"],
                country=country,
                defaults={
                    "name": state_data["name"],
                    "is_active": state_data["is_active"]
                }
            )
            state_map[state_data["code"]] = state
            if created:
                states_created += 1
            else:
                states_updated += 1
        
        self.stdout.write(f"  Created {states_created} states, updated {states_updated} states")
        
        # Create or update cities
        cities_created = 0
        cities_updated = 0
        
        for city_data in geo_data["cities"]:
            state = state_map.get(city_data["state_code"])
            if not state:
                self.stdout.write(self.style.WARNING(f"    Warning: State code {city_data['state_code']} not found for city {city_data['name']}"))
                continue
            
            city, created = City.objects.update_or_create(
                code=city_data["code"],
                state=state,
                defaults={
                    "name": city_data["name"],
                    "is_active": city_data["is_active"]
                }
            )
            if created:
                cities_created += 1
            else:
                cities_updated += 1
        
        self.stdout.write(f"  Created {cities_created} cities, updated {cities_updated} cities")
        self.stdout.write(self.style.SUCCESS("Geographic data seeded successfully!"))
    
    @transaction.atomic
    def seed_categories(self):
        """Seed category data"""
        self.stdout.write(self.style.NOTICE('Seeding category data...'))
        
        # Category data
        category_data = {
            "categories": [
                {"name": "السياسة", "name_en": "Politics", "slug": "politics", "description": "الأخبار والقرارات السياسية المحلية والدولية", "description_en": "Local and international political news and decisions", "color": "#DC2626", "icon": "government", "is_active": True},
                {"name": "الاقتصاد", "name_en": "Economy", "slug": "economy", "description": "الأخبار والقرارات الاقتصادية والمالية", "description_en": "Economic and financial news and decisions", "color": "#059669", "icon": "economy", "is_active": True},
                {"name": "الصحة", "name_en": "Health", "slug": "health", "description": "الأخبار والقرارات الصحية والطبية", "description_en": "Health and medical news and decisions", "color": "#DC2626", "icon": "health", "is_active": True},
                {"name": "التعليم", "name_en": "Education", "slug": "education", "description": "الأخبار والقرارات التعليمية والأكاديمية", "description_en": "Educational and academic news and decisions", "color": "#7C3AED", "icon": "education", "is_active": True},
                {"name": "التكنولوجيا", "name_en": "Technology", "slug": "technology", "description": "الأخبار والقرارات التقنية والرقمية", "description_en": "Technology and digital news and decisions", "color": "#2563EB", "icon": "technology", "is_active": True},
                {"name": "الرياضة", "name_en": "Sports", "slug": "sports", "description": "الأخبار والقرارات الرياضية", "description_en": "Sports news and decisions", "color": "#EA580C", "icon": "sports", "is_active": True},
                {"name": "الثقافة", "name_en": "Culture", "slug": "culture", "description": "الأخبار والقرارات الثقافية والفنية", "description_en": "Cultural and artistic news and decisions", "color": "#DB2777", "icon": "culture", "is_active": True},
                {"name": "السياحة", "name_en": "Tourism", "slug": "tourism", "description": "الأخبار والقرارات السياحية والسفر", "description_en": "Tourism and travel news and decisions", "color": "#0891B2", "icon": "tourism", "is_active": True},
                {"name": "البيئة", "name_en": "Environment", "slug": "environment", "description": "الأخبار والقرارات البيئية والمناخية", "description_en": "Environmental and climate news and decisions", "color": "#10B981", "icon": "environment", "is_active": True},
                {"name": "المواصلات", "name_en": "Transportation", "slug": "transportation", "description": "الأخبار والقرارات المتعلقة بالنقل والمواصلات", "description_en": "Transportation and transit news and decisions", "color": "#6366F1", "icon": "transportation", "is_active": True},
                {"name": "الطاقة", "name_en": "Energy", "slug": "energy", "description": "الأخبار والقرارات المتعلقة بالطاقة والكهرباء", "description_en": "Energy and electricity news and decisions", "color": "#F59E0B", "icon": "energy", "is_active": True},
                {"name": "الزراعة", "name_en": "Agriculture", "slug": "agriculture", "description": "الأخبار والقرارات الزراعية والغذائية", "description_en": "Agricultural and food news and decisions", "color": "#84CC16", "icon": "agriculture", "is_active": True},
                {"name": "العدل", "name_en": "Justice", "slug": "justice", "description": "الأخبار والقرارات القضائية والقانونية", "description_en": "Judicial and legal news and decisions", "color": "#1F2937", "icon": "justice", "is_active": True},
                {"name": "الأمن", "name_en": "Security", "slug": "security", "description": "الأخبار والقرارات الأمنية والعسكرية", "description_en": "Security and military news and decisions", "color": "#991B1B", "icon": "security", "is_active": True},
                {"name": "الإسكان", "name_en": "Housing", "slug": "housing", "description": "الأخبار والقرارات المتعلقة بالإسكان والعقارات", "description_en": "Housing and real estate news and decisions", "color": "#92400E", "icon": "housing", "is_active": True},
                {"name": "الشؤون الاجتماعية", "name_en": "Social Affairs", "slug": "social-affairs", "description": "الأخبار والقرارات الاجتماعية والإنسانية", "description_en": "Social and humanitarian news and decisions", "color": "#BE185D", "icon": "social", "is_active": True},
                {"name": "التجارة", "name_en": "Commerce", "slug": "commerce", "description": "الأخبار والقرارات التجارية والأعمال", "description_en": "Commercial and business news and decisions", "color": "#0369A1", "icon": "commerce", "is_active": True},
                {"name": "الصناعة", "name_en": "Industry", "slug": "industry", "description": "الأخبار والقرارات الصناعية والإنتاجية", "description_en": "Industrial and production news and decisions", "color": "#475569", "icon": "industry", "is_active": True},
                {"name": "الاتصالات", "name_en": "Communications", "slug": "communications", "description": "الأخبار والقرارات المتعلقة بالاتصالات والإعلام", "description_en": "Communications and media news and decisions", "color": "#7C2D12", "icon": "communications", "is_active": True},
                {"name": "المياه", "name_en": "Water", "slug": "water", "description": "الأخبار والقرارات المتعلقة بالموارد المائية", "description_en": "Water resources news and decisions", "color": "#1E40AF", "icon": "water", "is_active": True}
            ],
            "subcategories": [
                {"name": "السياسة الداخلية", "name_en": "Domestic Politics", "slug": "domestic-politics", "category_slug": "politics", "description": "القرارات والأخبار السياسية المحلية", "description_en": "Local political decisions and news", "is_active": True},
                {"name": "السياسة الخارجية", "name_en": "Foreign Politics", "slug": "foreign-politics", "category_slug": "politics", "description": "العلاقات الدولية والدبلوماسية", "description_en": "International relations and diplomacy", "is_active": True},
                {"name": "القرارات الحكومية", "name_en": "Government Decisions", "slug": "government-decisions", "category_slug": "politics", "description": "القرارات الرسمية الحكومية", "description_en": "Official government decisions", "is_active": True},
                {"name": "الانتخابات", "name_en": "Elections", "slug": "elections", "category_slug": "politics", "description": "الانتخابات والعمليات الديمقراطية", "description_en": "Elections and democratic processes", "is_active": True},
                {"name": "المعاهدات والاتفاقيات", "name_en": "Treaties and Agreements", "slug": "treaties-agreements", "category_slug": "politics", "description": "المعاهدات والاتفاقيات الدولية", "description_en": "International treaties and agreements", "is_active": True},
                {"name": "الميزانية والمالية العامة", "name_en": "Budget and Public Finance", "slug": "budget-public-finance", "category_slug": "economy", "description": "الميزانية العامة والسياسات المالية", "description_en": "Public budget and fiscal policies", "is_active": True},
                {"name": "البنوك والمصارف", "name_en": "Banks and Financial Institutions", "slug": "banks-financial", "category_slug": "economy", "description": "القطاع المصرفي والمؤسسات المالية", "description_en": "Banking sector and financial institutions", "is_active": True},
                {"name": "الاستثمار", "name_en": "Investment", "slug": "investment", "category_slug": "economy", "description": "الاستثمارات والمشاريع الاقتصادية", "description_en": "Investments and economic projects", "is_active": True},
                {"name": "التضخم والأسعار", "name_en": "Inflation and Prices", "slug": "inflation-prices", "category_slug": "economy", "description": "معدلات التضخم وأسعار السلع", "description_en": "Inflation rates and commodity prices", "is_active": True},
                {"name": "التجارة الخارجية", "name_en": "Foreign Trade", "slug": "foreign-trade", "category_slug": "economy", "description": "الصادرات والواردات", "description_en": "Exports and imports", "is_active": True},
                {"name": "الرعاية الصحية", "name_en": "Healthcare", "slug": "healthcare", "category_slug": "health", "description": "خدمات الرعاية الصحية", "description_en": "Healthcare services", "is_active": True},
                {"name": "الأدوية واللقاحات", "name_en": "Medicines and Vaccines", "slug": "medicines-vaccines", "category_slug": "health", "description": "الأدوية واللقاحات والعلاجات", "description_en": "Medicines, vaccines and treatments", "is_active": True},
                {"name": "الصحة العامة", "name_en": "Public Health", "slug": "public-health", "category_slug": "health", "description": "السياسات الصحية العامة", "description_en": "Public health policies", "is_active": True},
                {"name": "المستشفيات والمراكز الصحية", "name_en": "Hospitals and Health Centers", "slug": "hospitals-health-centers", "category_slug": "health", "description": "المستشفيات والمنشآت الصحية", "description_en": "Hospitals and health facilities", "is_active": True},
                {"name": "التأمين الصحي", "name_en": "Health Insurance", "slug": "health-insurance", "category_slug": "health", "description": "أنظمة التأمين الصحي", "description_en": "Health insurance systems", "is_active": True},
                {"name": "التعليم الأساسي", "name_en": "Basic Education", "slug": "basic-education", "category_slug": "education", "description": "التعليم الابتدائي والإعدادي", "description_en": "Primary and preparatory education", "is_active": True},
                {"name": "التعليم الثانوي", "name_en": "Secondary Education", "slug": "secondary-education", "category_slug": "education", "description": "التعليم الثانوي والمهني", "description_en": "Secondary and vocational education", "is_active": True},
                {"name": "التعليم العالي", "name_en": "Higher Education", "slug": "higher-education", "category_slug": "education", "description": "الجامعات والمعاهد العليا", "description_en": "Universities and higher institutes", "is_active": True},
                {"name": "البحث العلمي", "name_en": "Scientific Research", "slug": "scientific-research", "category_slug": "education", "description": "البحث العلمي والتطوير", "description_en": "Scientific research and development", "is_active": True},
                {"name": "المناهج الدراسية", "name_en": "Curricula", "slug": "curricula", "category_slug": "education", "description": "المناهج والبرامج التعليمية", "description_en": "Educational curricula and programs", "is_active": True},
                {"name": "تقنية المعلومات", "name_en": "Information Technology", "slug": "information-technology", "category_slug": "technology", "description": "تقنية المعلومات والبرمجيات", "description_en": "Information technology and software", "is_active": True},
                {"name": "الأمن السيبراني", "name_en": "Cybersecurity", "slug": "cybersecurity", "category_slug": "technology", "description": "أمن المعلومات والحماية الرقمية", "description_en": "Information security and digital protection", "is_active": True},
                {"name": "الذكاء الاصطناعي", "name_en": "Artificial Intelligence", "slug": "artificial-intelligence", "category_slug": "technology", "description": "تقنيات الذكاء الاصطناعي", "description_en": "Artificial intelligence technologies", "is_active": True},
                {"name": "التحول الرقمي", "name_en": "Digital Transformation", "slug": "digital-transformation", "category_slug": "technology", "description": "مشاريع التحول الرقمي", "description_en": "Digital transformation projects", "is_active": True},
                {"name": "الابتكار التقني", "name_en": "Tech Innovation", "slug": "tech-innovation", "category_slug": "technology", "description": "الابتكارات والتقنيات الجديدة", "description_en": "New innovations and technologies", "is_active": True},
                {"name": "كرة القدم", "name_en": "Football", "slug": "football", "category_slug": "sports", "description": "أخبار وقرارات كرة القدم", "description_en": "Football news and decisions", "is_active": True},
                {"name": "الألعاب الأولمبية", "name_en": "Olympic Games", "slug": "olympic-games", "category_slug": "sports", "description": "الألعاب الأولمبية والبطولات", "description_en": "Olympic games and championships", "is_active": True},
                {"name": "الرياضة المحلية", "name_en": "Local Sports", "slug": "local-sports", "category_slug": "sports", "description": "الأنشطة الرياضية المحلية", "description_en": "Local sports activities", "is_active": True},
                {"name": "المنشآت الرياضية", "name_en": "Sports Facilities", "slug": "sports-facilities", "category_slug": "sports", "description": "الملاعب والمراكز الرياضية", "description_en": "Stadiums and sports centers", "is_active": True},
                {"name": "الاتحادات الرياضية", "name_en": "Sports Federations", "slug": "sports-federations", "category_slug": "sports", "description": "الاتحادات والمنظمات الرياضية", "description_en": "Sports federations and organizations", "is_active": True},
                {"name": "الفنون والآداب", "name_en": "Arts and Literature", "slug": "arts-literature", "category_slug": "culture", "description": "الفنون والأعمال الأدبية", "description_en": "Arts and literary works", "is_active": True},
                {"name": "التراث الثقافي", "name_en": "Cultural Heritage", "slug": "cultural-heritage", "category_slug": "culture", "description": "التراث والآثار الثقافية", "description_en": "Cultural heritage and artifacts", "is_active": True},
                {"name": "المهرجانات والفعاليات", "name_en": "Festivals and Events", "slug": "festivals-events", "category_slug": "culture", "description": "المهرجانات والفعاليات الثقافية", "description_en": "Cultural festivals and events", "is_active": True},
                {"name": "المتاحف والمعارض", "name_en": "Museums and Exhibitions", "slug": "museums-exhibitions", "category_slug": "culture", "description": "المتاحف والمعارض الفنية", "description_en": "Museums and art exhibitions", "is_active": True},
                {"name": "الإنتاج الثقافي", "name_en": "Cultural Production", "slug": "cultural-production", "category_slug": "culture", "description": "الإنتاج السينمائي والمسرحي", "description_en": "Film and theater production", "is_active": True},
                {"name": "السياحة الداخلية", "name_en": "Domestic Tourism", "slug": "domestic-tourism", "category_slug": "tourism", "description": "السياحة المحلية والداخلية", "description_en": "Local and domestic tourism", "is_active": True},
                {"name": "السياحة الخارجية", "name_en": "International Tourism", "slug": "international-tourism", "category_slug": "tourism", "description": "السياحة الدولية والوافدة", "description_en": "International and inbound tourism", "is_active": True},
                {"name": "المواقع السياحية", "name_en": "Tourist Sites", "slug": "tourist-sites", "category_slug": "tourism", "description": "المعالم والمواقع السياحية", "description_en": "Tourist landmarks and sites", "is_active": True},
                {"name": "الخدمات السياحية", "name_en": "Tourism Services", "slug": "tourism-services", "category_slug": "tourism", "description": "الفنادق والخدمات السياحية", "description_en": "Hotels and tourism services", "is_active": True},
                {"name": "التسويق السياحي", "name_en": "Tourism Marketing", "slug": "tourism-marketing", "category_slug": "tourism", "description": "الترويج والتسويق السياحي", "description_en": "Tourism promotion and marketing", "is_active": True},
                {"name": "حماية البيئة", "name_en": "Environmental Protection", "slug": "environmental-protection", "category_slug": "environment", "description": "حماية البيئة والموارد الطبيعية", "description_en": "Environmental and natural resource protection", "is_active": True},
                {"name": "التغير المناخي", "name_en": "Climate Change", "slug": "climate-change", "category_slug": "environment", "description": "قضايا التغير المناخي", "description_en": "Climate change issues", "is_active": True},
                {"name": "إدارة النفايات", "name_en": "Waste Management", "slug": "waste-management", "category_slug": "environment", "description": "إدارة النفايات والتدوير", "description_en": "Waste management and recycling", "is_active": True},
                {"name": "المحميات الطبيعية", "name_en": "Nature Reserves", "slug": "nature-reserves", "category_slug": "environment", "description": "المحميات والمناطق المحمية", "description_en": "Reserves and protected areas", "is_active": True},
                {"name": "التنمية المستدامة", "name_en": "Sustainable Development", "slug": "sustainable-development", "category_slug": "environment", "description": "مشاريع التنمية المستدامة", "description_en": "Sustainable development projects", "is_active": True},
                {"name": "النقل البري", "name_en": "Land Transportation", "slug": "land-transportation", "category_slug": "transportation", "description": "الطرق والنقل البري", "description_en": "Roads and land transportation", "is_active": True},
                {"name": "النقل الجوي", "name_en": "Air Transportation", "slug": "air-transportation", "category_slug": "transportation", "description": "المطارات والنقل الجوي", "description_en": "Airports and air transportation", "is_active": True},
                {"name": "النقل البحري", "name_en": "Maritime Transportation", "slug": "maritime-transportation", "category_slug": "transportation", "description": "الموانئ والنقل البحري", "description_en": "Ports and maritime transportation", "is_active": True},
                {"name": "السكك الحديدية", "name_en": "Railways", "slug": "railways", "category_slug": "transportation", "description": "القطارات والسكك الحديدية", "description_en": "Trains and railways", "is_active": True},
                {"name": "النقل العام", "name_en": "Public Transportation", "slug": "public-transportation", "category_slug": "transportation", "description": "وسائل النقل العام", "description_en": "Public transportation means", "is_active": True},
                {"name": "الكهرباء", "name_en": "Electricity", "slug": "electricity", "category_slug": "energy", "description": "توليد وتوزيع الكهرباء", "description_en": "Electricity generation and distribution", "is_active": True},
                {"name": "النفط والغاز", "name_en": "Oil and Gas", "slug": "oil-gas", "category_slug": "energy", "description": "قطاع النفط والغاز", "description_en": "Oil and gas sector", "is_active": True},
                {"name": "الطاقة المتجددة", "name_en": "Renewable Energy", "slug": "renewable-energy", "category_slug": "energy", "description": "مصادر الطاقة المتجددة", "description_en": "Renewable energy sources", "is_active": True},
                {"name": "كفاءة الطاقة", "name_en": "Energy Efficiency", "slug": "energy-efficiency", "category_slug": "energy", "description": "ترشيد استهلاك الطاقة", "description_en": "Energy consumption rationalization", "is_active": True},
                {"name": "البنية التحتية للطاقة", "name_en": "Energy Infrastructure", "slug": "energy-infrastructure", "category_slug": "energy", "description": "شبكات ومحطات الطاقة", "description_en": "Energy networks and stations", "is_active": True},
                {"name": "الإنتاج الزراعي", "name_en": "Agricultural Production", "slug": "agricultural-production", "category_slug": "agriculture", "description": "الإنتاج الزراعي والمحاصيل", "description_en": "Agricultural production and crops", "is_active": True},
                {"name": "الثروة الحيوانية", "name_en": "Livestock", "slug": "livestock", "category_slug": "agriculture", "description": "تربية المواشي والدواجن", "description_en": "Livestock and poultry farming", "is_active": True},
                {"name": "الري والمياه", "name_en": "Irrigation and Water", "slug": "irrigation-water", "category_slug": "agriculture", "description": "أنظمة الري والموارد المائية", "description_en": "Irrigation systems and water resources", "is_active": True},
                {"name": "الأمن الغذائي", "name_en": "Food Security", "slug": "food-security", "category_slug": "agriculture", "description": "الأمن الغذائي والاكتفاء الذاتي", "description_en": "Food security and self-sufficiency", "is_active": True},
                {"name": "التقنيات الزراعية", "name_en": "Agricultural Technologies", "slug": "agricultural-technologies", "category_slug": "agriculture", "description": "التقنيات الحديثة في الزراعة", "description_en": "Modern agricultural technologies", "is_active": True},
                {"name": "المحاكم والقضاء", "name_en": "Courts and Judiciary", "slug": "courts-judiciary", "category_slug": "justice", "description": "النظام القضائي والمحاكم", "description_en": "Judicial system and courts", "is_active": True},
                {"name": "التشريعات والقوانين", "name_en": "Legislation and Laws", "slug": "legislation-laws", "category_slug": "justice", "description": "القوانين والتشريعات الجديدة", "description_en": "New laws and legislation", "is_active": True},
                {"name": "حقوق الإنسان", "name_en": "Human Rights", "slug": "human-rights", "category_slug": "justice", "description": "قضايا حقوق الإنسان", "description_en": "Human rights issues", "is_active": True},
                {"name": "الإصلاح القضائي", "name_en": "Judicial Reform", "slug": "judicial-reform", "category_slug": "justice", "description": "إصلاح النظام القضائي", "description_en": "Judicial system reform", "is_active": True},
                {"name": "العدالة الاجتماعية", "name_en": "Social Justice", "slug": "social-justice", "category_slug": "justice", "description": "قضايا العدالة الاجتماعية", "description_en": "Social justice issues", "is_active": True},
                {"name": "الأمن الداخلي", "name_en": "Internal Security", "slug": "internal-security", "category_slug": "security", "description": "الأمن الداخلي وحفظ النظام", "description_en": "Internal security and order maintenance", "is_active": True},
                {"name": "الدفاع الوطني", "name_en": "National Defense", "slug": "national-defense", "category_slug": "security", "description": "الدفاع والقوات المسلحة", "description_en": "Defense and armed forces", "is_active": True},
                {"name": "مكافحة الإرهاب", "name_en": "Counter-terrorism", "slug": "counter-terrorism", "category_slug": "security", "description": "جهود مكافحة الإرهاب", "description_en": "Counter-terrorism efforts", "is_active": True},
                {"name": "الأمن الحدودي", "name_en": "Border Security", "slug": "border-security", "category_slug": "security", "description": "أمن الحدود والمعابر", "description_en": "Border and crossing security", "is_active": True},
                {"name": "الحماية المدنية", "name_en": "Civil Protection", "slug": "civil-protection", "category_slug": "security", "description": "الدفاع المدني والطوارئ", "description_en": "Civil defense and emergencies", "is_active": True},
                {"name": "الإسكان الاجتماعي", "name_en": "Social Housing", "slug": "social-housing", "category_slug": "housing", "description": "مشاريع الإسكان الاجتماعي", "description_en": "Social housing projects", "is_active": True},
                {"name": "التطوير العقاري", "name_en": "Real Estate Development", "slug": "real-estate-development", "category_slug": "housing", "description": "مشاريع التطوير العقاري", "description_en": "Real estate development projects", "is_active": True},
                {"name": "التخطيط العمراني", "name_en": "Urban Planning", "slug": "urban-planning", "category_slug": "housing", "description": "التخطيط المدني والعمراني", "description_en": "Civil and urban planning", "is_active": True},
                {"name": "البناء والتشييد", "name_en": "Construction", "slug": "construction", "category_slug": "housing", "description": "قطاع البناء والتشييد", "description_en": "Construction sector", "is_active": True},
                {"name": "الخدمات العقارية", "name_en": "Real Estate Services", "slug": "real-estate-services", "category_slug": "housing", "description": "الخدمات والتسجيل العقاري", "description_en": "Real estate services and registration", "is_active": True}
            ]
        }
        
        # Create categories
        category_map = {}  # Map slug to category object for subcategory creation
        categories_created = 0
        categories_updated = 0
        
        for cat_data in category_data["categories"]:
            try:
                category = Category.objects.get(slug=cat_data["slug"])
                # Update existing category
                category.name = cat_data["name_en"]  # English name in 'name' field
                category.name_ar = cat_data["name"]  # Arabic name in 'name_ar' field
                category.description = cat_data.get("description_en", "")
                category.description_ar = cat_data.get("description", "")
                category.icon = cat_data.get("icon", "default")
                category.is_active = cat_data.get("is_active", True)
                category.save()
                created = False
            except Category.DoesNotExist:
                # Create new category
                category = Category.objects.create(
                    slug=cat_data["slug"],
                    name=cat_data["name_en"],  # English name in 'name' field
                    name_ar=cat_data["name"],  # Arabic name in 'name_ar' field
                    description=cat_data.get("description_en", ""),
                    description_ar=cat_data.get("description", ""),
                    icon=cat_data.get("icon", "default"),
                    is_active=cat_data.get("is_active", True)
                )
                created = True
            category_map[cat_data["slug"]] = category
            if created:
                categories_created += 1
            else:
                categories_updated += 1
        
        self.stdout.write(f"  Created {categories_created} categories, updated {categories_updated} categories")
        
        # Create subcategories
        subcategories_created = 0
        subcategories_updated = 0
        
        for subcat_data in category_data["subcategories"]:
            category = category_map.get(subcat_data["category_slug"])
            if not category:
                self.stdout.write(self.style.WARNING(f"    Warning: Category slug {subcat_data['category_slug']} not found for subcategory {subcat_data['name']}"))
                continue
            
            try:
                subcategory = SubCategory.objects.get(slug=subcat_data["slug"], category=category)
                # Update existing subcategory
                subcategory.name = subcat_data["name_en"]  # English name in 'name' field
                subcategory.name_ar = subcat_data["name"]  # Arabic name in 'name_ar' field
                subcategory.description = subcat_data.get("description_en", "")
                subcategory.description_ar = subcat_data.get("description", "")
                subcategory.is_active = subcat_data.get("is_active", True)
                subcategory.save()
                created = False
            except SubCategory.DoesNotExist:
                # Create new subcategory
                subcategory = SubCategory.objects.create(
                    slug=subcat_data["slug"],
                    category=category,
                    name=subcat_data["name_en"],  # English name in 'name' field
                    name_ar=subcat_data["name"],  # Arabic name in 'name_ar' field
                    description=subcat_data.get("description_en", ""),
                    description_ar=subcat_data.get("description", ""),
                    is_active=subcat_data.get("is_active", True)
                )
                created = True
            if created:
                subcategories_created += 1
            else:
                subcategories_updated += 1
        
        self.stdout.write(f"  Created {subcategories_created} subcategories, updated {subcategories_updated} subcategories")
        self.stdout.write(self.style.SUCCESS("Category data seeded successfully!"))
    
    @transaction.atomic
    def seed_producers(self):
        """Seed producer data (organizations, subsidiaries, departments)"""
        self.stdout.write(self.style.NOTICE('Seeding producer data...'))
        
        # Get geographic references
        country = Country.objects.get(code="SYR")
        states = {state.name: state for state in State.objects.filter(country=country)}
        cities = {}
        for city in City.objects.filter(state__country=country):
            if city.state.name not in cities:
                cities[city.state.name] = {}
            cities[city.state.name][city.name] = city
        
        # Producer data
        producer_data = {
            "organizations": [
                {
                    "name": "Ministry of Education",
                    "name_ar": "وزارة التربية",
                    "code": "MOE",
                    "description": "Responsible for education policy, curriculum development, and educational institutions management across Syria",
                    "description_ar": "مسؤولة عن السياسة التعليمية وتطوير المناهج وإدارة المؤسسات التعليمية في سوريا",
                    "website": "http://moed.gov.sy",
                    "email": "info@moed.gov.sy",
                    "phone": "+963-11-2139000",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Health",
                    "name_ar": "وزارة الصحة",
                    "code": "MOH",
                    "description": "Oversees healthcare system, medical services, and public health policies in Syria",
                    "description_ar": "تشرف على النظام الصحي والخدمات الطبية وسياسات الصحة العامة في سوريا",
                    "website": "http://moh.gov.sy",
                    "email": "info@moh.gov.sy",
                    "phone": "+963-11-3336000",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Interior",
                    "name_ar": "وزارة الداخلية",
                    "code": "MOI",
                    "description": "Responsible for internal security, civil affairs, and administrative services",
                    "description_ar": "مسؤولة عن الأمن الداخلي والشؤون المدنية والخدمات الإدارية",
                    "website": "http://moi.gov.sy",
                    "email": "info@moi.gov.sy",
                    "phone": "+963-11-2226000",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Defense",
                    "name_ar": "وزارة الدفاع",
                    "code": "MOD",
                    "description": "Responsible for national defense and military affairs",
                    "description_ar": "مسؤولة عن الدفاع الوطني والشؤون العسكرية",
                    "website": "http://mod.gov.sy",
                    "email": "info@mod.gov.sy",
                    "phone": "+963-11-6666000",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Foreign Affairs",
                    "name_ar": "وزارة الخارجية",
                    "code": "MOFA",
                    "description": "Handles diplomatic relations and foreign policy matters",
                    "description_ar": "تتعامل مع العلاقات الدبلوماسية وشؤون السياسة الخارجية",
                    "website": "http://mofa.gov.sy",
                    "email": "info@mofa.gov.sy",
                    "phone": "+963-11-3318000",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Finance",
                    "name_ar": "وزارة المالية",
                    "code": "MOF",
                    "description": "Manages government finances, taxation, and economic policies",
                    "description_ar": "تدير المالية الحكومية والضرائب والسياسات الاقتصادية",
                    "website": "http://mof.gov.sy",
                    "email": "info@mof.gov.sy",
                    "phone": "+963-11-2218000",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Justice",
                    "name_ar": "وزارة العدل",
                    "code": "MOJ",
                    "description": "Oversees judicial system and legal affairs",
                    "description_ar": "تشرف على النظام القضائي والشؤون القانونية",
                    "website": "http://moj.gov.sy",
                    "email": "info@moj.gov.sy",
                    "phone": "+963-11-2226500",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Agriculture",
                    "name_ar": "وزارة الزراعة",
                    "code": "MOA",
                    "description": "Responsible for agricultural development and rural affairs",
                    "description_ar": "مسؤولة عن التنمية الزراعية والشؤون الريفية",
                    "website": "http://moa.gov.sy",
                    "email": "info@moa.gov.sy",
                    "phone": "+963-11-5419000",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Industry",
                    "name_ar": "وزارة الصناعة",
                    "code": "MOIN",
                    "description": "Promotes industrial development and manufacturing",
                    "description_ar": "تعزز التنمية الصناعية والتصنيع",
                    "website": "http://moi.gov.sy",
                    "email": "info@moin.gov.sy",
                    "phone": "+963-11-5433000",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Oil and Mineral Resources",
                    "name_ar": "وزارة النفط والثروة المعدنية",
                    "code": "MOMR",
                    "description": "Manages oil, gas and mineral resources",
                    "description_ar": "تدير موارد النفط والغاز والثروة المعدنية",
                    "website": "http://momr.gov.sy",
                    "email": "info@momr.gov.sy",
                    "phone": "+963-11-6648000",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Transport",
                    "name_ar": "وزارة النقل",
                    "code": "MOT",
                    "description": "Oversees transportation infrastructure and services",
                    "description_ar": "تشرف على البنية التحتية للنقل والخدمات",
                    "website": "http://mot.gov.sy",
                    "email": "info@mot.gov.sy",
                    "phone": "+963-11-2223000",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Communications and Technology",
                    "name_ar": "وزارة الاتصالات والتقانة",
                    "code": "MOCT",
                    "description": "Manages telecommunications and information technology",
                    "description_ar": "تدير الاتصالات وتكنولوجيا المعلومات",
                    "website": "http://moct.gov.sy",
                    "email": "info@moct.gov.sy",
                    "phone": "+963-11-3737000",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Information",
                    "name_ar": "وزارة الإعلام",
                    "code": "MOINF",
                    "description": "Oversees media and information dissemination",
                    "description_ar": "تشرف على وسائل الإعلام ونشر المعلومات",
                    "website": "http://moi.gov.sy",
                    "email": "info@moinf.gov.sy",
                    "phone": "+963-11-3332000",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Culture",
                    "name_ar": "وزارة الثقافة",
                    "code": "MOC",
                    "description": "Promotes cultural heritage and artistic activities",
                    "description_ar": "تعزز التراث الثقافي والأنشطة الفنية",
                    "website": "http://moc.gov.sy",
                    "email": "info@moc.gov.sy",
                    "phone": "+963-11-2223500",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Tourism",
                    "name_ar": "وزارة السياحة",
                    "code": "MOTO",
                    "description": "Develops tourism industry and promotes Syrian heritage",
                    "description_ar": "تطور صناعة السياحة وتروج للتراث السوري",
                    "website": "http://moto.gov.sy",
                    "email": "info@moto.gov.sy",
                    "phone": "+963-11-2224500",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Social Affairs and Labor",
                    "name_ar": "وزارة الشؤون الاجتماعية والعمل",
                    "code": "MOSAL",
                    "description": "Handles social welfare and labor affairs",
                    "description_ar": "تتعامل مع الرفاه الاجتماعي وشؤون العمل",
                    "website": "http://mosal.gov.sy",
                    "email": "info@mosal.gov.sy",
                    "phone": "+963-11-2447000",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Higher Education",
                    "name_ar": "وزارة التعليم العالي",
                    "code": "MOHE",
                    "description": "Oversees universities and higher education institutions",
                    "description_ar": "تشرف على الجامعات ومؤسسات التعليم العالي",
                    "website": "http://mohe.gov.sy",
                    "email": "info@mohe.gov.sy",
                    "phone": "+963-11-2133000",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Awqaf (Religious Endowments)",
                    "name_ar": "وزارة الأوقاف",
                    "code": "MOAW",
                    "description": "Manages religious endowments and Islamic affairs",
                    "description_ar": "تدير الأوقاف الدينية والشؤون الإسلامية",
                    "website": "http://awqaf.gov.sy",
                    "email": "info@awqaf.gov.sy",
                    "phone": "+963-11-5412000",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Water Resources",
                    "name_ar": "وزارة الموارد المائية",
                    "code": "MOWR",
                    "description": "Manages water resources and irrigation systems",
                    "description_ar": "تدير الموارد المائية وأنظمة الري",
                    "website": "http://mowr.gov.sy",
                    "email": "info@mowr.gov.sy",
                    "phone": "+963-11-4433000",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                },
                {
                    "name": "Ministry of Housing and Construction",
                    "name_ar": "وزارة الإسكان والتعمير",
                    "code": "MOHC",
                    "description": "Oversees housing development and construction projects",
                    "description_ar": "تشرف على تطوير الإسكان ومشاريع البناء",
                    "website": "http://mohc.gov.sy",
                    "email": "info@mohc.gov.sy",
                    "phone": "+963-11-6662000",
                    "country": "Syria",
                    "state": "دمشق",
                    "city": "دمشق",
                    "is_active": True,
                    "is_verified": True
                }
            ],
            "subsidiaries": []  # Will be added next
        }
        
        # Create or update organizations
        organization_map = {}  # Map code to organization object for subsidiary creation
        organizations_created = 0
        organizations_updated = 0
        
        for org_data in producer_data["organizations"]:
            # Get geographic references
            state = states.get(org_data["state"])
            city = None
            if state and org_data["state"] in cities:
                city = cities[org_data["state"]].get(org_data["city"])
            
            try:
                organization = Organization.objects.get(code=org_data["code"])
                # Update existing organization
                organization.name = org_data["name_ar"]  # Arabic name in 'name' field
                organization.name_ar = org_data["name_ar"]
                organization.description = org_data.get("description", "")
                organization.description_ar = org_data.get("description_ar", "")
                organization.website = org_data.get("website", "")
                organization.email = org_data.get("email", "")
                organization.phone = org_data.get("phone", "")
                organization.country = country
                organization.state = state
                organization.city = city
                organization.is_active = org_data.get("is_active", True)
                organization.is_verified = org_data.get("is_verified", False)
                organization.save()
                created = False
            except Organization.DoesNotExist:
                # Create new organization
                organization = Organization.objects.create(
                    code=org_data["code"],
                    name=org_data["name_ar"],  # Arabic name in 'name' field
                    name_ar=org_data["name_ar"],
                    description=org_data.get("description", ""),
                    description_ar=org_data.get("description_ar", ""),
                    website=org_data.get("website", ""),
                    email=org_data.get("email", ""),
                    phone=org_data.get("phone", ""),
                    country=country,
                    state=state,
                    city=city,
                    is_active=org_data.get("is_active", True),
                    is_verified=org_data.get("is_verified", False)
                )
                created = True
            
            organization_map[org_data["code"]] = organization
            if created:
                organizations_created += 1
            else:
                organizations_updated += 1
        
        self.stdout.write(f"  Created {organizations_created} organizations, updated {organizations_updated} organizations")
        
        # Now add subsidiaries data
        subsidiaries_data = [
            {
                "name": "Damascus Education Directorate",
                "name_ar": "مديرية تربية دمشق",
                "code": "MOE_DAM",
                "parent_organization_code": "MOE",
                "description": "Regional education administration for Damascus governorate",
                "description_ar": "الإدارة التعليمية الإقليمية لمحافظة دمشق",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "Aleppo Education Directorate",
                "name_ar": "مديرية تربية حلب",
                "code": "MOE_ALP",
                "parent_organization_code": "MOE",
                "description": "Regional education administration for Aleppo governorate",
                "description_ar": "الإدارة التعليمية الإقليمية لمحافظة حلب",
                "country": "Syria",
                "state": "حلب",
                "city": "حلب",
                "is_active": True
            },
            {
                "name": "Higher Education Planning Commission",
                "name_ar": "هيئة التخطيط والتطوير للتعليم العالي",
                "code": "MOE_HEC",
                "parent_organization_code": "MOE",
                "description": "Strategic planning for higher education development",
                "description_ar": "التخطيط الاستراتيجي لتطوير التعليم العالي",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "Damascus University Hospital",
                "name_ar": "مشفى جامعة دمشق",
                "code": "MOH_DUH",
                "parent_organization_code": "MOH",
                "description": "Major teaching hospital and medical center",
                "description_ar": "مشفى تعليمي ومركز طبي رئيسي",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "National Center for Disease Control",
                "name_ar": "المركز الوطني لمكافحة الأمراض",
                "code": "MOH_NCDC",
                "parent_organization_code": "MOH",
                "description": "Epidemiological surveillance and disease prevention",
                "description_ar": "المراقبة الوبائية ومنع الأمراض",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "Public Health Institute",
                "name_ar": "معهد الصحة العامة",
                "code": "MOH_PHI",
                "parent_organization_code": "MOH",
                "description": "Public health research and training center",
                "description_ar": "مركز بحوث وتدريب الصحة العامة",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "General Security Directorate",
                "name_ar": "مديرية الأمن العام",
                "code": "MOI_GSD",
                "parent_organization_code": "MOI",
                "description": "General security and internal affairs",
                "description_ar": "الأمن العام والشؤون الداخلية",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "Civil Affairs Directorate",
                "name_ar": "مديرية الأحوال المدنية",
                "code": "MOI_CAD",
                "parent_organization_code": "MOI",
                "description": "Civil registration and identification services",
                "description_ar": "خدمات التسجيل المدني والهوية",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "Immigration and Passports Directorate",
                "name_ar": "مديرية الهجرة والجوازات",
                "code": "MOI_IPD",
                "parent_organization_code": "MOI",
                "description": "Immigration services and passport issuance",
                "description_ar": "خدمات الهجرة وإصدار الجوازات",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "Syrian Arab Army",
                "name_ar": "الجيش العربي السوري",
                "code": "MOD_SAA",
                "parent_organization_code": "MOD",
                "description": "Main military force of Syria",
                "description_ar": "القوة العسكرية الرئيسية في سوريا",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "Syrian Air Force",
                "name_ar": "القوات الجوية السورية",
                "code": "MOD_SAF",
                "parent_organization_code": "MOD",
                "description": "Air force branch of Syrian military",
                "description_ar": "فرع القوات الجوية في الجيش السوري",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "Tax Administration",
                "name_ar": "إدارة الضرائب",
                "code": "MOF_TAX",
                "parent_organization_code": "MOF",
                "description": "Tax collection and administration",
                "description_ar": "جمع الضرائب والإدارة الضريبية",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "Customs Directorate",
                "name_ar": "مديرية الجمارك",
                "code": "MOF_CUS",
                "parent_organization_code": "MOF",
                "description": "Customs control and trade regulation",
                "description_ar": "مراقبة الجمارك وتنظيم التجارة",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "Damascus Courts Complex",
                "name_ar": "مجمع محاكم دمشق",
                "code": "MOJ_DCC",
                "parent_organization_code": "MOJ",
                "description": "Main judicial complex in Damascus",
                "description_ar": "المجمع القضائي الرئيسي في دمشق",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "General Authority for Agriculture Development",
                "name_ar": "الهيئة العامة للتنمية الزراعية",
                "code": "MOA_GAAD",
                "parent_organization_code": "MOA",
                "description": "Agricultural development and extension services",
                "description_ar": "التنمية الزراعية وخدمات الإرشاد",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "Syrian Petroleum Company",
                "name_ar": "الشركة السورية للبترول",
                "code": "MOMR_SPC",
                "parent_organization_code": "MOMR",
                "description": "National oil and gas company",
                "description_ar": "الشركة الوطنية للنفط والغاز",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "Syrian Railways",
                "name_ar": "السكك الحديدية السورية",
                "code": "MOT_SR",
                "parent_organization_code": "MOT",
                "description": "National railway transportation system",
                "description_ar": "نظام النقل بالسكك الحديدية الوطني",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "Syrian Telecom",
                "name_ar": "المؤسسة العامة للاتصالات",
                "code": "MOCT_ST",
                "parent_organization_code": "MOCT",
                "description": "National telecommunications provider",
                "description_ar": "مزود الاتصالات الوطني",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "Syrian Arab News Agency (SANA)",
                "name_ar": "وكالة الأنباء العربية السورية (سانا)",
                "code": "MOINF_SANA",
                "parent_organization_code": "MOINF",
                "description": "Official news agency of Syria",
                "description_ar": "وكالة الأنباء الرسمية لسوريا",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            },
            {
                "name": "Syrian TV and Radio",
                "name_ar": "التلفزيون والإذاعة السورية",
                "code": "MOINF_STR",
                "parent_organization_code": "MOINF",
                "description": "National broadcasting corporation",
                "description_ar": "مؤسسة الإذاعة والتلفزيون الوطنية",
                "country": "Syria",
                "state": "Damascus",
                "city": "Damascus",
                "is_active": True
            }
        ]
        
        # Create or update subsidiaries
        subsidiary_map = {}  # Map code to subsidiary object for department creation
        subsidiaries_created = 0
        subsidiaries_updated = 0
        
        for sub_data in subsidiaries_data:
            # Get parent organization
            parent_org = organization_map.get(sub_data["parent_organization_code"])
            if not parent_org:
                self.stdout.write(self.style.WARNING(f"    Warning: Parent organization {sub_data['parent_organization_code']} not found for subsidiary {sub_data['name']}"))
                continue
            
            # Get geographic references
            state = states.get(sub_data["state"])
            city = None
            if state and sub_data["state"] in cities:
                city = cities[sub_data["state"]].get(sub_data["city"])
            
            try:
                subsidiary = Subsidiary.objects.get(code=sub_data["code"])
                # Update existing subsidiary
                subsidiary.name = sub_data["name_ar"]  # Arabic name in 'name' field
                subsidiary.name_ar = sub_data["name_ar"]
                subsidiary.parent_organization = parent_org
                subsidiary.description = sub_data.get("description", "")
                subsidiary.description_ar = sub_data.get("description_ar", "")
                subsidiary.country = country
                subsidiary.state = state
                subsidiary.city = city
                subsidiary.is_active = sub_data.get("is_active", True)
                subsidiary.save()
                created = False
            except Subsidiary.DoesNotExist:
                # Create new subsidiary
                subsidiary = Subsidiary.objects.create(
                    code=sub_data["code"],
                    name=sub_data["name_ar"],  # Arabic name in 'name' field
                    name_ar=sub_data["name_ar"],
                    parent_organization=parent_org,
                    description=sub_data.get("description", ""),
                    description_ar=sub_data.get("description_ar", ""),
                    country=country,
                    state=state,
                    city=city,
                    is_active=sub_data.get("is_active", True)
                )
                created = True
            
            subsidiary_map[sub_data["code"]] = subsidiary
            if created:
                subsidiaries_created += 1
            else:
                subsidiaries_updated += 1
        
        self.stdout.write(f"  Created {subsidiaries_created} subsidiaries, updated {subsidiaries_updated} subsidiaries")
        
        # Now add departments data
        departments_data = [
            {
                "name": "Primary Education Department",
                "name_ar": "قسم التعليم الأساسي",
                "code": "MOE_DAM_PED",
                "subsidiary_code": "MOE_DAM",
                "description": "Manages primary education in Damascus",
                "description_ar": "يدير التعليم الأساسي في دمشق",
                "head_name": "Ahmad Al-Khatib",
                "head_email": "a.khatib@moed.gov.sy",
                "head_phone": "+963-11-2139001",
                "employee_count": 45,
                "department_type": "admin",
                "is_active": True
            },
            {
                "name": "Secondary Education Department",
                "name_ar": "قسم التعليم الثانوي",
                "code": "MOE_DAM_SED",
                "subsidiary_code": "MOE_DAM",
                "description": "Manages secondary education in Damascus",
                "description_ar": "يدير التعليم الثانوي في دمشق",
                "head_name": "Fatima Al-Zahra",
                "head_email": "f.zahra@moed.gov.sy",
                "head_phone": "+963-11-2139002",
                "employee_count": 38,
                "department_type": "admin",
                "is_active": True
            },
            {
                "name": "Curriculum Development Department",
                "name_ar": "قسم تطوير المناهج",
                "code": "MOE_DAM_CDD",
                "subsidiary_code": "MOE_DAM",
                "description": "Develops and updates educational curricula",
                "description_ar": "يطور ويحدث المناهج التعليمية",
                "head_name": "Omar Mansour",
                "head_email": "o.mansour@moed.gov.sy",
                "head_phone": "+963-11-2139003",
                "employee_count": 22,
                "department_type": "technical",
                "is_active": True
            },
            {
                "name": "Emergency Medicine Department",
                "name_ar": "قسم طب الطوارئ",
                "code": "MOH_DUH_EMD",
                "subsidiary_code": "MOH_DUH",
                "description": "Emergency medical services and trauma care",
                "description_ar": "خدمات الطب الطارئ ورعاية الصدمات",
                "head_name": "Dr. Layla Kassem",
                "head_email": "l.kassem@duh.gov.sy",
                "head_phone": "+963-11-3336001",
                "employee_count": 85,
                "department_type": "technical",
                "is_active": True
            },
            {
                "name": "Internal Medicine Department",
                "name_ar": "قسم الطب الباطني",
                "code": "MOH_DUH_IMD",
                "subsidiary_code": "MOH_DUH",
                "description": "Internal medicine and general healthcare",
                "description_ar": "الطب الباطني والرعاية الصحية العامة",
                "head_name": "Dr. Mahmoud Habib",
                "head_email": "m.habib@duh.gov.sy",
                "head_phone": "+963-11-3336002",
                "employee_count": 120,
                "department_type": "technical",
                "is_active": True
            },
            {
                "name": "Nursing Department",
                "name_ar": "قسم التمريض",
                "code": "MOH_DUH_ND",
                "subsidiary_code": "MOH_DUH",
                "description": "Nursing services and patient care",
                "description_ar": "خدمات التمريض ورعاية المرضى",
                "head_name": "Nour Al-Din",
                "head_email": "n.aldin@duh.gov.sy",
                "head_phone": "+963-11-3336003",
                "employee_count": 200,
                "department_type": "technical",
                "is_active": True
            },
            {
                "name": "Epidemiology Department",
                "name_ar": "قسم الوبائيات",
                "code": "MOH_NCDC_EPD",
                "subsidiary_code": "MOH_NCDC",
                "description": "Disease surveillance and outbreak investigation",
                "description_ar": "مراقبة الأمراض والتحقيق في الفاشيات",
                "head_name": "Dr. Rami Yousef",
                "head_email": "r.yousef@ncdc.gov.sy",
                "head_phone": "+963-11-3336100",
                "employee_count": 35,
                "department_type": "technical",
                "is_active": True
            },
            {
                "name": "Laboratory Services Department",
                "name_ar": "قسم الخدمات المخبرية",
                "code": "MOH_NCDC_LSD",
                "subsidiary_code": "MOH_NCDC",
                "description": "Diagnostic laboratory services",
                "description_ar": "خدمات المختبرات التشخيصية",
                "head_name": "Dr. Salma Khoury",
                "head_email": "s.khoury@ncdc.gov.sy",
                "head_phone": "+963-11-3336101",
                "employee_count": 42,
                "department_type": "technical",
                "is_active": True
            },
            {
                "name": "Criminal Investigation Department",
                "name_ar": "قسم المباحث الجنائية",
                "code": "MOI_GSD_CID",
                "subsidiary_code": "MOI_GSD",
                "description": "Criminal investigation and law enforcement",
                "description_ar": "التحقيق الجنائي وإنفاذ القانون",
                "head_name": "Colonel Khaled Sweiss",
                "head_email": "k.sweiss@gsd.gov.sy",
                "head_phone": "+963-11-2226001",
                "employee_count": 150,
                "department_type": "admin",
                "is_active": True
            },
            {
                "name": "Traffic Police Department",
                "name_ar": "قسم شرطة المرور",
                "code": "MOI_GSD_TPD",
                "subsidiary_code": "MOI_GSD",
                "description": "Traffic control and road safety",
                "description_ar": "مراقبة المرور والسلامة على الطرق",
                "head_name": "Major Yussef Nader",
                "head_email": "y.nader@gsd.gov.sy",
                "head_phone": "+963-11-2226002",
                "employee_count": 95,
                "department_type": "admin",
                "is_active": True
            },
            {
                "name": "Birth Registration Department",
                "name_ar": "قسم تسجيل المواليد",
                "code": "MOI_CAD_BRD",
                "subsidiary_code": "MOI_CAD",
                "description": "Birth certificate issuance and registration",
                "description_ar": "إصدار شهادات الولادة والتسجيل",
                "head_name": "Mariam Othman",
                "head_email": "m.othman@cad.gov.sy",
                "head_phone": "+963-11-2226050",
                "employee_count": 30,
                "department_type": "admin",
                "is_active": True
            },
            {
                "name": "ID Card Services Department",
                "name_ar": "قسم خدمات الهوية",
                "code": "MOI_CAD_ISD",
                "subsidiary_code": "MOI_CAD",
                "description": "National ID card issuance and renewal",
                "description_ar": "إصدار وتجديد بطاقات الهوية الوطنية",
                "head_name": "Bashar Qaddour",
                "head_email": "b.qaddour@cad.gov.sy",
                "head_phone": "+963-11-2226051",
                "employee_count": 55,
                "department_type": "admin",
                "is_active": True
            },
            {
                "name": "Passport Issuance Department",
                "name_ar": "قسم إصدار الجوازات",
                "code": "MOI_IPD_PID",
                "subsidiary_code": "MOI_IPD",
                "description": "Passport application processing and issuance",
                "description_ar": "معالجة طلبات الجوازات وإصدارها",
                "head_name": "Lina Hakim",
                "head_email": "l.hakim@ipd.gov.sy",
                "head_phone": "+963-11-2226060",
                "employee_count": 40,
                "department_type": "admin",
                "is_active": True
            },
            {
                "name": "Visa Services Department",
                "name_ar": "قسم خدمات الفيزا",
                "code": "MOI_IPD_VSD",
                "subsidiary_code": "MOI_IPD",
                "description": "Visa processing and immigration services",
                "description_ar": "معالجة الفيزا وخدمات الهجرة",
                "head_name": "Nabil Kurdi",
                "head_email": "n.kurdi@ipd.gov.sy",
                "head_phone": "+963-11-2226061",
                "employee_count": 25,
                "department_type": "admin",
                "is_active": True
            },
            {
                "name": "Land Forces Command",
                "name_ar": "قيادة القوات البرية",
                "code": "MOD_SAA_LFC",
                "subsidiary_code": "MOD_SAA",
                "description": "Command and control of land forces",
                "description_ar": "قيادة والسيطرة على القوات البرية",
                "head_name": "General Ali Hassan",
                "head_email": "a.hassan@saa.gov.sy",
                "head_phone": "+963-11-6666001",
                "employee_count": 500,
                "department_type": "admin",
                "is_active": True
            },
            {
                "name": "Military Intelligence Department",
                "name_ar": "قسم المخابرات العسكرية",
                "code": "MOD_SAA_MID",
                "subsidiary_code": "MOD_SAA",
                "description": "Military intelligence operations",
                "description_ar": "عمليات المخابرات العسكرية",
                "head_name": "Colonel Fadi Antoun",
                "head_email": "f.antoun@saa.gov.sy",
                "head_phone": "+963-11-6666002",
                "employee_count": 200,
                "department_type": "admin",
                "is_active": True
            },
            {
                "name": "Income Tax Department",
                "name_ar": "قسم ضريبة الدخل",
                "code": "MOF_TAX_ITD",
                "subsidiary_code": "MOF_TAX",
                "description": "Individual and corporate income tax collection",
                "description_ar": "جمع ضريبة الدخل للأفراد والشركات",
                "head_name": "Sami Khalil",
                "head_email": "s.khalil@tax.gov.sy",
                "head_phone": "+963-11-2218001",
                "employee_count": 75,
                "department_type": "financial",
                "is_active": True
            },
            {
                "name": "VAT Department",
                "name_ar": "قسم ضريبة القيمة المضافة",
                "code": "MOF_TAX_VAT",
                "subsidiary_code": "MOF_TAX",
                "description": "Value Added Tax administration",
                "description_ar": "إدارة ضريبة القيمة المضافة",
                "head_name": "Rana Mustafa",
                "head_email": "r.mustafa@tax.gov.sy",
                "head_phone": "+963-11-2218002",
                "employee_count": 60,
                "department_type": "financial",
                "is_active": True
            },
            {
                "name": "Import/Export Control Department",
                "name_ar": "قسم مراقبة الاستيراد والتصدير",
                "code": "MOF_CUS_IED",
                "subsidiary_code": "MOF_CUS",
                "description": "Import and export customs procedures",
                "description_ar": "إجراءات الجمارك للاستيراد والتصدير",
                "head_name": "Tareq Farouk",
                "head_email": "t.farouk@customs.gov.sy",
                "head_phone": "+963-11-2218100",
                "employee_count": 85,
                "department_type": "admin",
                "is_active": True
            },
            {
                "name": "Criminal Court Department",
                "name_ar": "قسم المحكمة الجنائية",
                "code": "MOJ_DCC_CCD",
                "subsidiary_code": "MOJ_DCC",
                "description": "Criminal justice proceedings",
                "description_ar": "إجراءات العدالة الجنائية",
                "head_name": "Judge Amina Sabbagh",
                "head_email": "a.sabbagh@courts.gov.sy",
                "head_phone": "+963-11-2226500",
                "employee_count": 45,
                "department_type": "legal",
                "is_active": True
            },
            {
                "name": "Civil Court Department",
                "name_ar": "قسم المحكمة المدنية",
                "code": "MOJ_DCC_CIVD",
                "subsidiary_code": "MOJ_DCC",
                "description": "Civil litigation and legal disputes",
                "description_ar": "التقاضي المدني والنزاعات القانونية",
                "head_name": "Judge Hassan Nakhleh",
                "head_email": "h.nakhleh@courts.gov.sy",
                "head_phone": "+963-11-2226501",
                "employee_count": 40,
                "department_type": "legal",
                "is_active": True
            },
            {
                "name": "Crop Production Department",
                "name_ar": "قسم الإنتاج النباتي",
                "code": "MOA_GAAD_CPD",
                "subsidiary_code": "MOA_GAAD",
                "description": "Crop cultivation and agricultural extension",
                "description_ar": "زراعة المحاصيل والإرشاد الزراعي",
                "head_name": "Eng. Walid Shahin",
                "head_email": "w.shahin@gaad.gov.sy",
                "head_phone": "+963-11-5419001",
                "employee_count": 65,
                "department_type": "technical",
                "is_active": True
            },
            {
                "name": "Livestock Department",
                "name_ar": "قسم الثروة الحيوانية",
                "code": "MOA_GAAD_LD",
                "subsidiary_code": "MOA_GAAD",
                "description": "Animal husbandry and veterinary services",
                "description_ar": "تربية الماشية والخدمات البيطرية",
                "head_name": "Dr. Samar Jundi",
                "head_email": "s.jundi@gaad.gov.sy",
                "head_phone": "+963-11-5419002",
                "employee_count": 50,
                "department_type": "technical",
                "is_active": True
            },
            {
                "name": "Exploration Department",
                "name_ar": "قسم الاستكشاف",
                "code": "MOMR_SPC_ED",
                "subsidiary_code": "MOMR_SPC",
                "description": "Oil and gas exploration activities",
                "description_ar": "أنشطة استكشاف النفط والغاز",
                "head_name": "Eng. Munir Tlass",
                "head_email": "m.tlass@spc.gov.sy",
                "head_phone": "+963-11-6648001",
                "employee_count": 120,
                "department_type": "technical",
                "is_active": True
            },
            {
                "name": "Production Department",
                "name_ar": "قسم الإنتاج",
                "code": "MOMR_SPC_PD",
                "subsidiary_code": "MOMR_SPC",
                "description": "Oil and gas production operations",
                "description_ar": "عمليات إنتاج النفط والغاز",
                "head_name": "Eng. Diana Malouf",
                "head_email": "d.malouf@spc.gov.sy",
                "head_phone": "+963-11-6648002",
                "employee_count": 180,
                "department_type": "technical",
                "is_active": True
            },
            {
                "name": "Railway Operations Department",
                "name_ar": "قسم عمليات السكك الحديدية",
                "code": "MOT_SR_ROD",
                "subsidiary_code": "MOT_SR",
                "description": "Train operations and scheduling",
                "description_ar": "عمليات القطارات والجدولة",
                "head_name": "Eng. Fouad Salloum",
                "head_email": "f.salloum@railways.gov.sy",
                "head_phone": "+963-11-2223001",
                "employee_count": 95,
                "department_type": "technical",
                "is_active": True
            },
            {
                "name": "Infrastructure Maintenance Department",
                "name_ar": "قسم صيانة البنية التحتية",
                "code": "MOT_SR_IMD",
                "subsidiary_code": "MOT_SR",
                "description": "Railway infrastructure maintenance",
                "description_ar": "صيانة البنية التحتية للسكك الحديدية",
                "head_name": "Eng. Mazen Qasemi",
                "head_email": "m.qasemi@railways.gov.sy",
                "head_phone": "+963-11-2223002",
                "employee_count": 150,
                "department_type": "technical",
                "is_active": True
            },
            {
                "name": "Network Operations Department",
                "name_ar": "قسم عمليات الشبكة",
                "code": "MOCT_ST_NOD",
                "subsidiary_code": "MOCT_ST",
                "description": "Telecommunications network management",
                "description_ar": "إدارة شبكة الاتصالات",
                "head_name": "Eng. Riad Sabbagha",
                "head_email": "r.sabbagha@syriatel.gov.sy",
                "head_phone": "+963-11-3737001",
                "employee_count": 200,
                "department_type": "technical",
                "is_active": True
            },
            {
                "name": "Customer Services Department",
                "name_ar": "قسم خدمات العملاء",
                "code": "MOCT_ST_CSD",
                "subsidiary_code": "MOCT_ST",
                "description": "Customer support and services",
                "description_ar": "دعم العملاء والخدمات",
                "head_name": "Nadia Hojeily",
                "head_email": "n.hojeily@syriatel.gov.sy",
                "head_phone": "+963-11-3737002",
                "employee_count": 120,
                "department_type": "admin",
                "is_active": True
            },
            {
                "name": "News Editorial Department",
                "name_ar": "قسم تحرير الأخبار",
                "code": "MOINF_SANA_NED",
                "subsidiary_code": "MOINF_SANA",
                "description": "News writing and editorial services",
                "description_ar": "كتابة الأخبار والخدمات التحريرية",
                "head_name": "Journalist Laila Hamdan",
                "head_email": "l.hamdan@sana.sy",
                "head_phone": "+963-11-3332001",
                "employee_count": 80,
                "department_type": "media",
                "is_active": True
            },
            {
                "name": "Broadcasting Department",
                "name_ar": "قسم البث",
                "code": "MOINF_SANA_BD",
                "subsidiary_code": "MOINF_SANA",
                "description": "News broadcasting and distribution",
                "description_ar": "بث الأخبار والتوزيع",
                "head_name": "Adel Rifai",
                "head_email": "a.rifai@sana.sy",
                "head_phone": "+963-11-3332002",
                "employee_count": 45,
                "department_type": "technical",
                "is_active": True
            },
            {
                "name": "TV Production Department",
                "name_ar": "قسم إنتاج التلفزيون",
                "code": "MOINF_STR_TVD",
                "subsidiary_code": "MOINF_STR",
                "description": "Television program production",
                "description_ar": "إنتاج البرامج التلفزيونية",
                "head_name": "Director Rima Khoury",
                "head_email": "r.khoury@syriatv.gov.sy",
                "head_phone": "+963-11-3332100",
                "employee_count": 150,
                "department_type": "media",
                "is_active": True
            },
            {
                "name": "Radio Programming Department",
                "name_ar": "قسم برامج الإذاعة",
                "code": "MOINF_STR_RPD",
                "subsidiary_code": "MOINF_STR",
                "description": "Radio program development and broadcasting",
                "description_ar": "تطوير وبث البرامج الإذاعية",
                "head_name": "Presenter Ghassan Matar",
                "head_email": "g.matar@syriaradio.gov.sy",
                "head_phone": "+963-11-3332101",
                "employee_count": 75,
                "department_type": "media",
                "is_active": True
            }
        ]
        
        # Create or update departments
        departments_created = 0
        departments_updated = 0
        
        for dept_data in departments_data:
            # Get parent subsidiary
            parent_sub = subsidiary_map.get(dept_data["subsidiary_code"])
            if not parent_sub:
                self.stdout.write(self.style.WARNING(f"    Warning: Parent subsidiary {dept_data['subsidiary_code']} not found for department {dept_data['name']}"))
                continue
            
            try:
                department = Department.objects.get(code=dept_data["code"])
                # Update existing department
                department.name = dept_data["name_ar"]  # Arabic name in 'name' field
                department.name_ar = dept_data["name_ar"]
                department.subsidiary = parent_sub
                department.description = dept_data.get("description", "")
                department.description_ar = dept_data.get("description_ar", "")
                department.head_name = dept_data.get("head_name", "")
                department.head_email = dept_data.get("head_email", "")
                department.head_phone = dept_data.get("head_phone", "")
                department.employee_count = dept_data.get("employee_count", 0)
                department.department_type = dept_data.get("department_type", "other")
                department.is_active = dept_data.get("is_active", True)
                department.save()
                created = False
            except Department.DoesNotExist:
                # Create new department
                department = Department.objects.create(
                    code=dept_data["code"],
                    name=dept_data["name_ar"],  # Arabic name in 'name' field
                    name_ar=dept_data["name_ar"],
                    subsidiary=parent_sub,
                    description=dept_data.get("description", ""),
                    description_ar=dept_data.get("description_ar", ""),
                    head_name=dept_data.get("head_name", ""),
                    head_email=dept_data.get("head_email", ""),
                    head_phone=dept_data.get("head_phone", ""),
                    employee_count=dept_data.get("employee_count", 0),
                    department_type=dept_data.get("department_type", "other"),
                    is_active=dept_data.get("is_active", True)
                )
                created = True
            
            if created:
                departments_created += 1
            else:
                departments_updated += 1
        
        self.stdout.write(f"  Created {departments_created} departments, updated {departments_updated} departments")
        self.stdout.write(self.style.SUCCESS("Producer data seeded successfully!"))
    
    @transaction.atomic
    def seed_post_types(self):
        """Seed post type data"""
        self.stdout.write(self.style.NOTICE('Seeding post type data...'))
        
        # Post type data
        post_types_data = [
            {
                "name": "Statement",
                "name_ar": "بيان",
                "description": "Official government statements and public announcements regarding policies, events, or positions",
                "description_ar": "البيانات الحكومية الرسمية والإعلانات العامة المتعلقة بالسياسات أو الأحداث أو المواقف",
                "is_active": True
            },
            {
                "name": "Announcement",
                "name_ar": "إعلان",
                "description": "Public announcements for services, opportunities, or important information for citizens",
                "description_ar": "الإعلانات العامة للخدمات أو الفرص أو المعلومات المهمة للمواطنين",
                "is_active": True
            },
            {
                "name": "Circular",
                "name_ar": "تعميم",
                "description": "Internal circulars and directives distributed within government departments and agencies",
                "description_ar": "التعاميم والتوجيهات الداخلية الموزعة داخل الإدارات والوكالات الحكومية",
                "is_active": True
            },
            {
                "name": "Decision",
                "name_ar": "قرار",
                "description": "Official government decisions, resolutions, and administrative orders with legal binding",
                "description_ar": "القرارات الحكومية الرسمية والأوامر الإدارية ذات الطابع الإلزامي قانونياً",
                "is_active": True
            },
            {
                "name": "Recommendation",
                "name_ar": "توصية",
                "description": "Professional recommendations and advisory guidelines for policy implementation",
                "description_ar": "التوصيات المهنية والإرشادات الاستشارية لتنفيذ السياسات",
                "is_active": True
            },
            {
                "name": "Agreement",
                "name_ar": "اتفاقية",
                "description": "Formal agreements, treaties, contracts, and bilateral or multilateral arrangements",
                "description_ar": "الاتفاقيات والمعاهدات والعقود والترتيبات الثنائية أو متعددة الأطراف",
                "is_active": True
            },
            {
                "name": "Memorandum",
                "name_ar": "مذكرة",
                "description": "Official memorandums, notes, and internal communications between government entities",
                "description_ar": "المذكرات الرسمية والملاحظات والاتصالات الداخلية بين الجهات الحكومية",
                "is_active": True
            },
            {
                "name": "Document",
                "name_ar": "وثيقة",
                "description": "Official documents, reports, studies, and formal papers of governmental importance",
                "description_ar": "الوثائق الرسمية والتقارير والدراسات والأوراق الرسمية ذات الأهمية الحكومية",
                "is_active": True
            },
            {
                "name": "General",
                "name_ar": "عام",
                "description": "General governmental content that doesn't fit into specific categories, including news, updates, and miscellaneous information",
                "description_ar": "المحتوى الحكومي العام الذي لا يندرج ضمن فئات محددة، بما في ذلك الأخبار والتحديثات والمعلومات المتنوعة",
                "is_active": True
            }
        ]
        
        # Create or update post types
        post_types_created = 0
        post_types_updated = 0
        
        for pt_data in post_types_data:
            # Create a unique identifier based on Arabic name since PostType doesn't have a code field
            try:
                post_type = PostType.objects.get(name_ar=pt_data["name_ar"])
                # Update existing post type
                post_type.name = pt_data["name_ar"]  # Arabic name in 'name' field
                post_type.name_ar = pt_data["name_ar"]
                post_type.description = pt_data.get("description", "")
                post_type.description_ar = pt_data.get("description_ar", "")
                post_type.is_active = pt_data.get("is_active", True)
                post_type.save()
                created = False
            except PostType.DoesNotExist:
                # Create new post type
                post_type = PostType.objects.create(
                    name=pt_data["name_ar"],  # Arabic name in 'name' field
                    name_ar=pt_data["name_ar"],
                    description=pt_data.get("description", ""),
                    description_ar=pt_data.get("description_ar", ""),
                    is_active=pt_data.get("is_active", True)
                )
                created = True
            
            if created:
                post_types_created += 1
            else:
                post_types_updated += 1
        
        self.stdout.write(f"  Created {post_types_created} post types, updated {post_types_updated} post types")
        self.stdout.write(self.style.SUCCESS("Post type data seeded successfully!"))
    
    @transaction.atomic
    def clean_all_data(self):
        """Clean all seeded data in reverse order of dependencies"""
        self.stdout.write(self.style.WARNING('Cleaning all seeded data...'))
        
        # Clean in reverse order of dependencies
        
        # 1. Clean Departments first (depends on Subsidiaries)
        dept_count = Department.objects.all().delete()[0]
        self.stdout.write(f"  Deleted {dept_count} departments")
        
        # 2. Clean Subsidiaries (depends on Organizations)
        sub_count = Subsidiary.objects.all().delete()[0]
        self.stdout.write(f"  Deleted {sub_count} subsidiaries")
        
        # 3. Clean Organizations
        org_count = Organization.objects.all().delete()[0]
        self.stdout.write(f"  Deleted {org_count} organizations")
        
        # 4. Clean SubCategories (depends on Categories)
        subcat_count = SubCategory.objects.all().delete()[0]
        self.stdout.write(f"  Deleted {subcat_count} subcategories")
        
        # 5. Clean Categories
        cat_count = Category.objects.all().delete()[0]
        self.stdout.write(f"  Deleted {cat_count} categories")
        
        # 6. Clean Post Types
        pt_count = PostType.objects.all().delete()[0]
        self.stdout.write(f"  Deleted {pt_count} post types")
        
        # 7. Clean Cities (depends on States)
        city_count = City.objects.all().delete()[0]
        self.stdout.write(f"  Deleted {city_count} cities")
        
        # 8. Clean States (depends on Countries)
        state_count = State.objects.all().delete()[0]
        self.stdout.write(f"  Deleted {state_count} states")
        
        # 9. Clean Countries
        country_count = Country.objects.all().delete()[0]
        self.stdout.write(f"  Deleted {country_count} countries")
        
        self.stdout.write(self.style.SUCCESS("All seeded data has been cleaned successfully!"))