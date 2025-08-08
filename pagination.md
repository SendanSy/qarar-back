# API Pagination Guide

The Qarar platform API uses consistent pagination across all list endpoints to handle large datasets efficiently.

## Pagination Structure

All paginated responses follow this standard format:

```json
{
  "count": 150,
  "next": "http://api.example.com/endpoint/?page=2",
  "previous": null,
  "results": [
    // Array of items
  ]
}
```

## Pagination Parameters

### Page Number
Use the `page` parameter to navigate through pages:
```bash
GET /api/v1/content/hashtags/?page=2
GET /api/v1/producers/organizations/?page=3
```

### Page Size
Control the number of items per page using `page_size`:
```bash
# Get 5 items per page
GET /api/v1/content/hashtags/?page_size=5

# Get 50 items per page (max: 100)
GET /api/v1/content/posts/?page_size=50
```

- Default page size: 20 items
- Maximum page size: 100 items

## Paginated Endpoints

The following endpoints support pagination:

### Content Endpoints
- `/api/v1/content/posts/` - Posts
- `/api/v1/content/hashtags/` - Hashtags
- `/api/v1/content/categories/` - Categories
- `/api/v1/content/post-types/` - Post Types
- `/api/v1/content/bookmarks/` - Bookmarks (authenticated)

### Producer Endpoints
- `/api/v1/producers/organizations/` - Organizations
- `/api/v1/producers/subsidiaries/` - Subsidiaries
- `/api/v1/producers/departments/` - Departments

## Combining Pagination with Filters

Pagination works seamlessly with filters and search:

```bash
# Search with pagination
GET /api/v1/content/hashtags/?search=سوريا&page=2

# Filter with custom page size
GET /api/v1/content/posts/?status=published&page_size=10

# Order and paginate
GET /api/v1/producers/organizations/?ordering=name&page=1
```

## Examples

### Get First Page of Hashtags
```bash
GET /api/v1/content/hashtags/
```

Response:
```json
{
  "count": 607,
  "next": "http://api.example.com/api/v1/content/hashtags/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "name": "سوريا",
      "slug": "سوريا",
      "post_count": 4230
    }
    // ... 19 more items
  ]
}
```

### Get Organizations with Custom Page Size
```bash
GET /api/v1/producers/organizations/?page_size=5
```

Response:
```json
{
  "count": 20,
  "next": "http://api.example.com/api/v1/producers/organizations/?page=2&page_size=5",
  "previous": null,
  "results": [
    // 5 organizations
  ]
}
```

### Navigate to Specific Page
```bash
GET /api/v1/content/posts/?page=5&page_size=30
```

Response:
```json
{
  "count": 500,
  "next": "http://api.example.com/api/v1/content/posts/?page=6&page_size=30",
  "previous": "http://api.example.com/api/v1/content/posts/?page=4&page_size=30",
  "results": [
    // 30 posts
  ]
}
```

## Best Practices

1. **Use Appropriate Page Sizes**: Choose page sizes based on your use case:
   - Mobile apps: 10-20 items
   - Web interfaces: 20-50 items
   - Data exports: 50-100 items

2. **Handle Pagination in Your App**: Always check for `next` and `previous` URLs to enable navigation

3. **Cache Pages**: Consider caching frequently accessed pages to improve performance

4. **Use Filters**: Combine pagination with filters to reduce the total number of pages

## Error Handling

When requesting a page that doesn't exist:
```bash
GET /api/v1/content/hashtags/?page=999
```

Response:
```json
{
  "detail": "Invalid page."
}
```

## Performance Notes

- Pagination is optimized with database-level LIMIT and OFFSET
- Related data is efficiently loaded using select_related and prefetch_related
- Results are ordered consistently to ensure reliable pagination
- Some endpoints cache results for improved performance