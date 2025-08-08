# Hashtag Filtering Guide

This guide explains how to filter posts by hashtags in the Qarar platform API.

## Filter Posts by Hashtag

### Basic Hashtag Filtering

**Endpoint:** `GET /api/v1/content/posts/?hashtag={hashtag_name}`

Filter posts containing a specific hashtag (case-insensitive partial match):

```bash
# Filter posts with hashtag containing "التعليم"
GET /api/v1/content/posts/?hashtag=التعليم

# Filter posts with hashtag containing "سوريا"
GET /api/v1/content/posts/?hashtag=سوريا

# Filter posts with hashtag containing "قرار"
GET /api/v1/content/posts/?hashtag=قرار
```

### Get Posts for Specific Hashtag

**Endpoint:** `GET /api/v1/content/hashtags/{hashtag-slug}/posts/`

Get all posts associated with a specific hashtag using its slug:

```bash
# Get posts for hashtag with slug "education"
GET /api/v1/content/hashtags/education/posts/

# Get posts for hashtag with slug "syria"
GET /api/v1/content/hashtags/syria/posts/
```

### Combined Filters

Combine hashtag filtering with other parameters:

```bash
# Published posts with specific hashtag
GET /api/v1/content/posts/?hashtag=التعليم&status=published

# Posts with hashtag from specific organization
GET /api/v1/content/posts/?hashtag=إعلان&organization_code=MOE

# Posts with hashtag created after specific date
GET /api/v1/content/posts/?hashtag=قرار&created_after=2025-06-01

# Posts with hashtag and minimum views
GET /api/v1/content/posts/?hashtag=تعميم&min_views=1000
```

## Hashtag Management Endpoints

### List All Hashtags
```bash
GET /api/v1/content/hashtags/
```

### Get Trending Hashtags
```bash
GET /api/v1/content/hashtags/trending/
# Returns top 20 trending hashtags (cached for 15 minutes)
```

### Get Popular Hashtags
```bash
GET /api/v1/content/hashtags/popular/
# Returns top 30 popular hashtags by post count (cached for 30 minutes)
```

### Search Hashtags
```bash
GET /api/v1/content/hashtags/?search=تعليم
# Search hashtags by name
```

### Get Hashtag Details
```bash
GET /api/v1/content/hashtags/{slug}/
# Example: GET /api/v1/content/hashtags/التعليم/
```

## Ordering Results

Order filtered posts by different criteria:

```bash
# By newest first
GET /api/v1/content/posts/?hashtag=سوريا&ordering=-created_at

# By most viewed
GET /api/v1/content/posts/?hashtag=قرار&ordering=-view_count

# By publication date
GET /api/v1/content/posts/?hashtag=تعميم&ordering=-published_at
```

## Response Format

Posts endpoint returns paginated results with hashtag details:

```json
{
  "count": 150,
  "next": "http://api.example.com/api/v1/content/posts/?hashtag=تعليم&page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "title": "عنوان المنشور",
      "title_ar": "عنوان المنشور",
      "hashtags": [
        {
          "id": "uuid",
          "name": "التعليم",
          "slug": "التعليم",
          "post_count": 45
        },
        {
          "id": "uuid",
          "name": "وزارة_التربية",
          "slug": "وزارة-التربية",
          "post_count": 120
        }
      ]
    }
  ]
}
```

## Important Notes

- **No Authentication Required**: Hashtag endpoints are publicly accessible
- **Case-Insensitive**: Hashtag searches ignore case differences
- **Partial Matching**: The `hashtag` parameter matches partial names (e.g., "تعليم" matches "التعليم", "التعليم_العالي")
- **Arabic/English Support**: Full support for both Arabic and English hashtags
- **Performance**: Results are cached and optimized for fast retrieval