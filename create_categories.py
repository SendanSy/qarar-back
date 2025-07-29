from apps.content.models import Category
from django.utils.text import slugify

categories = [
    {
        'name': 'التنمية الاقتصادية',
        'description': 'مواضيع تتعلق بالنمو الاقتصادي والاستثمار والتجارة والتنمية الصناعية وتطوير القطاعات الاقتصادية المختلفة',
        'slug': 'economic-development'
    },
    {
        'name': 'البنية التحتية',
        'description': 'مشاريع ومبادرات تطوير البنية التحتية مثل الطرق والجسور والمطارات والموانئ وشبكات المياه والكهرباء',
        'slug': 'infrastructure'
    },
    {
        'name': 'التعليم والبحث العلمي',
        'description': 'تطوير المنظومة التعليمية والبحث العلمي وتحسين جودة التعليم وتطوير المناهج والمؤسسات التعليمية',
        'slug': 'education-research'
    },
    {
        'name': 'الصحة العامة',
        'description': 'تطوير النظام الصحي والخدمات الطبية والوقاية من الأمراض وتحسين الرعاية الصحية للمواطنين',
        'slug': 'public-health'
    },
    {
        'name': 'التكنولوجيا والابتكار',
        'description': 'التحول الرقمي وتطوير التكنولوجيا والابتكارات التقنية ودعم ريادة الأعمال في مجال التكنولوجيا',
        'slug': 'technology-innovation'
    },
    {
        'name': 'التنمية الاجتماعية',
        'description': 'برامج الرعاية الاجتماعية وتطوير المجتمع ومكافحة الفقر وتمكين الفئات المحرومة وتحقيق العدالة الاجتماعية',
        'slug': 'social-development'
    },
    {
        'name': 'البيئة والاستدامة',
        'description': 'حماية البيئة والموارد الطبيعية والتنمية المستدامة ومكافحة التلوث والتغير المناخي',
        'slug': 'environment-sustainability'
    },
    {
        'name': 'الحوكمة والإصلاح الإداري',
        'description': 'تطوير النظم الإدارية والحكومية ومكافحة الفساد وتعزيز الشفافية والمساءلة في المؤسسات العامة',
        'slug': 'governance-reform'
    },
    {
        'name': 'الثقافة والفنون',
        'description': 'تطوير المشهد الثقافي والفني والحفاظ على التراث الثقافي وتشجيع الإبداع والفنون المختلفة',
        'slug': 'culture-arts'
    },
    {
        'name': 'الشباب والرياضة',
        'description': 'تنمية مهارات الشباب وتمكينهم وتطوير المنشآت الرياضية ودعم الأنشطة الشبابية والرياضية',
        'slug': 'youth-sports'
    },
    {
        'name': 'القانون والتشريع',
        'description': 'التطورات التشريعية والقانونية وسيادة القانون وتعزيز العدالة وإصلاح النظام القضائي',
        'slug': 'law-legislation'
    }
]

for category_data in categories:
    Category.objects.create(
        name=category_data['name'],
        description=category_data['description'],
        slug=category_data['slug']
    )
    print(f'تم إنشاء تصنيف: {category_data["name"]}')

print('تم إنشاء جميع التصنيفات بنجاح!') 