# AWS Deployment Guide

## Environment Variables for Production

Add these to your `.env` file on the EC2 instance:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=your-domain.com,your-ec2-public-ip
SITE_URL=https://your-domain.com

# Database (RDS)
DB_HOST=your-rds-endpoint.region.rds.amazonaws.com
DB_PASSWORD=your-secure-password

# Redis (ElastiCache or EC2)
REDIS_URL=redis://your-redis-endpoint:6379/1

# AWS S3 Settings
USE_S3=True
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Optional: CloudFront CDN
AWS_S3_CUSTOM_DOMAIN=your-distribution.cloudfront.net

# SSL
SECURE_SSL_REDIRECT=True
```

## S3 Bucket Setup

1. Create an S3 bucket in AWS Console
2. Configure bucket policy for public static files:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::your-bucket-name/media/public/*"
        }
    ]
}
```

3. Configure CORS if needed:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": ["https://your-domain.com"],
        "ExposeHeaders": ["ETag"]
    }
]
```

## EC2 Deployment Steps

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Collect static files:**
```bash
python manage.py collectstatic --noinput
```

3. **Run migrations:**
```bash
python manage.py migrate
```

4. **Create superuser:**
```bash
python manage.py createsuperuser
```

5. **Run with Gunicorn:**
```bash
gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

## Storage Backends

The project now supports three storage backends:

- **MediaStorage**: Default for all media files (private)
- **PublicMediaStorage**: For publicly accessible files
- **PrivateMediaStorage**: For files requiring signed URLs

To use a specific backend in your models:

```python
from core.storage_backends import PublicMediaStorage

class MyModel(models.Model):
    public_file = models.FileField(storage=PublicMediaStorage())
```

## Performance Tips

1. Use CloudFront CDN for better global performance
2. Enable gzip compression in nginx
3. Set appropriate cache headers
4. Use Redis for caching
5. Configure database connection pooling

## Security Notes

- Always use HTTPS in production
- Keep AWS credentials secure (use IAM roles when possible)
- Regularly update dependencies
- Monitor AWS CloudTrail for S3 access
- Use VPC for RDS and ElastiCache