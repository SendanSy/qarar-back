# Qarar News Platform - Backend

This is the backend API for the Qarar News Platform, built with Django and Django REST Framework.

## Features

- User management with JWT authentication
- Content management with different content types (articles, images, videos, etc.)
- Personalized feed algorithm
- Engagement features (comments, reactions, etc.)
- Real-time notifications
- Analytics tracking

## Getting Started

### Prerequisites

- Python 3.10+
- pip
- virtualenv (recommended)

### Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/qarar.git
cd qarar/backend
```

2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install required packages:

```bash
pip install -r requirements.txt
```

4. Apply migrations:

```bash
python manage.py migrate
```

5. Create a superuser:

```bash
python manage.py createsuperuser
```

6. Run the development server:

```bash
python manage.py runserver
```

The API will be available at http://127.0.0.1:8000/

## API Documentation

Once the server is running, you can access the API documentation at:

- Swagger UI: http://127.0.0.1:8000/swagger/
- ReDoc: http://127.0.0.1:8000/redoc/

## Running Tests

To run the test suite:

```bash
pytest
```

For test coverage report:

```bash
coverage run -m pytest
coverage report
coverage html  # For detailed HTML report
```

## Architecture

The project follows a Domain-Driven Design approach with the following main components:

1. **User Management**

   - Authentication and authorization
   - User profiles and preferences
   - User following system

2. **Content Management**

   - Polymorphic content model (articles, images, videos, etc.)
   - Categories and tagging
   - Content lifecycle management

3. **Feed & Discovery**

   - Personalized feed algorithm
   - Content discovery
   - Search functionality

4. **Engagement**

   - Comments with threading
   - Reactions system
   - Content saving/bookmarking
   - Content reporting

5. **Notifications**

   - Real-time notification system
   - Notification preferences
   - Push notification device management

6. **Analytics**
   - User activity tracking
   - Content performance metrics
   - Search analytics
   - Aggregated metrics

## Project Structure

```
backend/
├── apps/                  # Application modules
│   ├── users/             # User management
│   ├── content/           # Content management
│   ├── feed/              # Feed and discovery
│   ├── engagement/        # User engagement
│   ├── notifications/     # Notification system
│   └── analytics/         # Analytics and tracking
├── core/                  # Core project settings
├── templates/             # Django templates
├── manage.py              # Django management script
├── requirements.txt       # Project dependencies
└── pytest.ini             # Pytest configuration
```

## License

This project is licensed under the [MIT License](LICENSE).

#filters:

# categories

# text

# decision numbers and dates and types

# the one who signed the decision/post

# the name of the party who issued the decision / the sub party too

# make tables for those too

# to whom the decision is targeted to

# the status of the decision ( active/ terminated/ suspended/ pending)

# location: area, city, county

# dates: miladi and hijri

# CLASSIFICATION_CHOICES = (

        ('decision', _('قرار')),
        ('circular', _('تعميم')),
        ('announcement', _('اعلان')),
        ('statement', _('بيان')),
        ('command', _('امر اداري')),
        ('command', _('امر مهمة')),
        ('command', _('امر قضائي')),
        ('command', _('حكم قضائي')),
        ('request', _('طلب')),
        ('', _('مرسوم')),
        ('', _('بلاغ')),
        ('', _('كتاب')),
        ('', _('إحالة')),
        ('', _('اشارة')),
        ('', _('توصية')),
        ('', _('محضر')),
        ('', _('اذن')),
        ('', _('انذار')),
        ('', _('اتفاقية')),
        ('', _('تقرير')),
        ('', _('مذكرة')),
        ('', _('تكليف')),
        ('', _('اخرى')),
        ('', _('وثيقة عقارية')),
        ('', _('وثيقة ادارية')),
    )

# do support for whatsapp notifications

# think of doing a mobile app

# do some sort of priv policy where some users can see certain posts while others cant

# this depends on how the organizations would define those policies and apply the needed restrictions

# add more child to the organizations tree

# figure out the type of stamps you would need to have, coming from the government mainly and maybe other options

# add a stamp for speech based posts to make things more interesting for the users

# add impressions and analytics that can help in displaying the satisfaction of the people to those who are in charge

# figure out the logo and visual identity

# fix the dates and unhide the tags posts.. get ready for production lad

# make the admin panel arabic, and make sure objects names in admin appear in arabic when arabic is selected
