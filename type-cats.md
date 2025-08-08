# PostTypes & Organizations API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
- Most endpoints are **public** (no authentication required)
- Post creation/update requires JWT token in header: `Authorization: Bearer {token}`

---

## 📝 PostTypes API

### List All Post Types
```http
GET /content/post-types/
```

**Response Example:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Decision",
    "name_ar": "قرار",
    "description": "Official decisions",
    "description_ar": "القرارات الرسمية",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Circular",
    "name_ar": "تعميم",
    "description": "Official circulars",
    "description_ar": "التعاميم الرسمية",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

### Get Single Post Type
```http
GET /content/post-types/{id}/
```

### Search Post Types
```http
GET /content/post-types/?search=قرار
GET /content/post-types/?search=decision
```

---

## 🏢 Organizations API

### List All Organizations
```http
GET /producers/organizations/
```

**Response Example:**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/v1/producers/organizations/?page=2",
  "previous": null,
  "results": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "name": "Ministry of Interior",
      "name_ar": "وزارة الداخلية",
      "code": "MOI",
      "description": "Ministry of Interior Affairs",
      "description_ar": "وزارة الشؤون الداخلية",
      "website": "https://moi.gov.sy",
      "email": "info@moi.gov.sy",
      "phone": "+963-11-2345678",
      "country": {
        "id": 1,
        "name": "Syria",
        "code": "SYR"
      },
      "state": {
        "id": 1,
        "name": "Damascus",
        "code": "DAM"
      },
      "city": {
        "id": 1,
        "name": "Damascus",
        "code": "DAM"
      },
      "is_active": true,
      "is_verified": true,
      "active_subsidiary_count": 5,
      "active_department_count": 23,
      "created_at": "2024-01-10T09:00:00Z"
    }
  ]
}
```

### Get Single Organization
```http
GET /producers/organizations/{code}/
```
**Note:** Uses `code` field (e.g., "MOI") not ID

### Get Organization's Posts
```http
GET /producers/organizations/{code}/posts/
```

### Get Organization's Subsidiaries
```http
GET /producers/organizations/{code}/subsidiaries/
```

### Get Organization's Departments
```http
GET /producers/organizations/{code}/departments/
```

### Search Organizations
```http
GET /producers/organizations/?search=ministry
GET /producers/organizations/?search=وزارة
```

### Filter Organizations
```http
GET /producers/organizations/?country=1
GET /producers/organizations/?state=1
GET /producers/organizations/?city=1
GET /producers/organizations/?is_verified=true
```

---

## 📰 Filtering Posts

### Filter by Post Type

#### By Type ID (UUID)
```http
GET /content/posts/?type_id=550e8400-e29b-41d4-a716-446655440000
```

#### By Type Name (English)
```http
GET /content/posts/?type_name=decision
```

#### By Type Name (Arabic)
```http
GET /content/posts/?type_name_ar=قرار
```

#### By Type (exact match - backwards compatibility)
```http
GET /content/posts/?type=550e8400-e29b-41d4-a716-446655440000
```

### Filter by Organization

#### By Organization ID (UUID)
```http
GET /content/posts/?organization_id=770e8400-e29b-41d4-a716-446655440002
```

#### By Organization Code
```http
GET /content/posts/?organization_code=MOI
```

#### By Organization (exact match - backwards compatibility)
```http
GET /content/posts/?organization=770e8400-e29b-41d4-a716-446655440002
```

### Filter by Subsidiary

#### By Subsidiary ID (UUID)
```http
GET /content/posts/?subsidiary_id=880e8400-e29b-41d4-a716-446655440003
```

#### By Subsidiary Code
```http
GET /content/posts/?subsidiary_code=MOI-DAM
```

### Filter by Department

#### By Department ID (UUID)
```http
GET /content/posts/?department_id=990e8400-e29b-41d4-a716-446655440004
```

#### By Department Code
```http
GET /content/posts/?department_code=MOI-DAM-HR
```

---

## 🔄 Combining Filters

You can combine multiple filters in a single request:

### Example 1: Posts of type "قرار" from Ministry of Interior
```http
GET /content/posts/?type_name_ar=قرار&organization_code=MOI
```

### Example 2: Published posts from a specific department
```http
GET /content/posts/?status=published&department_code=MOI-DAM-HR
```

### Example 3: Search with filters
```http
GET /content/posts/?search=visa&type_name=circular&organization_code=MOI
```

### Example 4: Posts with multiple filters
```http
GET /content/posts/?type_id=550e8400-e29b-41d4-a716-446655440000&organization_id=770e8400-e29b-41d4-a716-446655440002&status=published&ordering=-created_at
```

---

## 📊 Pagination

All list endpoints support pagination:

```http
GET /content/posts/?page=2&page_size=20
```

Default page size: 20 items

---

## 🔍 Search

Most endpoints support search via the `search` parameter:

```http
GET /content/posts/?search=تأشيرة
GET /producers/organizations/?search=ministry
GET /content/post-types/?search=قرار
```

---

## 📝 Ordering

Posts can be ordered by various fields:

```http
GET /content/posts/?ordering=-created_at  # Newest first
GET /content/posts/?ordering=created_at   # Oldest first
GET /content/posts/?ordering=-view_count  # Most viewed
GET /content/posts/?ordering=-published_at # Recently published
```

---

## 💡 Frontend Implementation Tips

### 1. Dropdown Filters
```javascript
// Fetch post types for dropdown
const postTypes = await fetch('/api/v1/content/post-types/');

// Fetch organizations for dropdown
const organizations = await fetch('/api/v1/producers/organizations/');
```

### 2. Filter Posts by Selection
```javascript
// When user selects a post type
const filteredPosts = await fetch(`/api/v1/content/posts/?type_id=${selectedTypeId}`);

// When user selects an organization
const filteredPosts = await fetch(`/api/v1/content/posts/?organization_id=${selectedOrgId}`);
```

### 3. Multi-Filter Component
```javascript
const filters = {
  type_id: selectedType,
  organization_id: selectedOrg,
  status: 'published',
  ordering: '-created_at'
};

const queryString = new URLSearchParams(filters).toString();
const posts = await fetch(`/api/v1/content/posts/?${queryString}`);
```

### 4. Bilingual Support
```javascript
// Detect user language preference
const lang = getUserLanguage(); // 'en' or 'ar'

// Use appropriate fields
const displayName = lang === 'ar' ? postType.name_ar : postType.name;
const displayDescription = lang === 'ar' ? org.description_ar : org.description;
```

### 5. Error Handling
```javascript
try {
  const response = await fetch('/api/v1/content/posts/?type_id=invalid-uuid');
  if (!response.ok) {
    // Handle error - invalid UUID format will return 400
    console.error('Invalid filter parameters');
  }
} catch (error) {
  console.error('Network error:', error);
}
```

---

## 🎯 Common Use Cases

### Show Government Decisions
```http
GET /content/posts/?type_name_ar=قرار&status=published&ordering=-published_at
```

### Show Ministry Announcements
```http
GET /content/posts/?type_name_ar=اعلان&organization_code=MOI&status=published
```

### Department-Specific Circulars
```http
GET /content/posts/?type_name_ar=تعميم&department_code=MOI-DAM-HR&status=published
```

### Recent Posts from All Organizations
```http
GET /content/posts/?status=published&ordering=-created_at&page_size=10
```

---

## 📌 Important Notes

1. **UUIDs**: Most IDs are UUIDs (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)
2. **Codes**: Organizations, subsidiaries, and departments use unique `code` fields for lookups
3. **Status**: Only `published` posts are visible to non-authenticated users
4. **Pagination**: Large result sets are automatically paginated
5. **Caching**: Some endpoints have caching (5-30 minutes) for performance
6. **Bilingual**: All content supports Arabic (`_ar` suffix) and English fields

---

## 🚀 Quick Start Example

```javascript
// Frontend filter component example
async function loadFilters() {
  // Load post types
  const typesResponse = await fetch('http://localhost:8000/api/v1/content/post-types/');
  const postTypes = await typesResponse.json();
  
  // Load organizations
  const orgsResponse = await fetch('http://localhost:8000/api/v1/producers/organizations/');
  const orgsData = await orgsResponse.json();
  const organizations = orgsData.results;
  
  // Populate dropdowns
  populateDropdown('postTypeSelect', postTypes, 'name_ar', 'id');
  populateDropdown('organizationSelect', organizations, 'name_ar', 'id');
}

async function filterPosts() {
  const selectedType = document.getElementById('postTypeSelect').value;
  const selectedOrg = document.getElementById('organizationSelect').value;
  
  let url = 'http://localhost:8000/api/v1/content/posts/?status=published';
  
  if (selectedType) url += `&type_id=${selectedType}`;
  if (selectedOrg) url += `&organization_id=${selectedOrg}`;
  
  const response = await fetch(url);
  const data = await response.json();
  displayPosts(data.results);
}
```

---

## 📞 Support

For additional filtering options and advanced queries, refer to the main API documentation at `/swagger/` when the server is running.