# Producers App API Documentation

This app provides endpoints for managing organizations, subsidiaries, and departments.

## Endpoints

### Organizations

- **List Organizations**: `GET /api/v1/producers/organizations/`
  - Returns list of active organizations with subsidiary and department counts
  - Supports filtering by country, state, city, and verification status
  - Supports search by name, code, and description

- **Organization Detail**: `GET /api/v1/producers/organizations/{code}/`
  - Returns full organization details with nested subsidiaries and departments
  - Includes post count across the entire organization hierarchy

- **Organization Posts**: `GET /api/v1/producers/organizations/{code}/posts/`
  - Returns all posts from the organization, its subsidiaries, and departments
  - Supports pagination

- **Organization Subsidiaries**: `GET /api/v1/producers/organizations/{code}/subsidiaries/`
  - Returns list of subsidiaries for the organization

- **Organization Departments**: `GET /api/v1/producers/organizations/{code}/departments/`
  - Returns all departments under the organization

### Subsidiaries

- **List Subsidiaries**: `GET /api/v1/producers/subsidiaries/`
  - Returns list of active subsidiaries
  - Supports filtering by organization, country, state, city
  - Supports search by name, code, and description

- **Subsidiary Detail**: `GET /api/v1/producers/subsidiaries/{code}/`
  - Returns subsidiary details with parent organization info

- **Subsidiary Departments**: `GET /api/v1/producers/subsidiaries/{code}/departments/`
  - Returns departments under the subsidiary

- **Subsidiary Posts**: `GET /api/v1/producers/subsidiaries/{code}/posts/`
  - Returns posts from the subsidiary and its departments

### Departments

- **List Departments**: `GET /api/v1/producers/departments/`
  - Returns list of active departments
  - Supports filtering by subsidiary, organization, department type, and employee count
  - Supports search by name, code, description, and head name

- **Department Detail**: `GET /api/v1/producers/departments/{code}/`
  - Returns department details with subsidiary and organization info

- **Department Posts**: `GET /api/v1/producers/departments/{code}/posts/`
  - Returns posts from the department

## Post Filtering

Posts can now be filtered by organization hierarchy:

- `?organization={id}` - Filter by organization ID
- `?organization_code={code}` - Filter by organization code
- `?subsidiary={id}` - Filter by subsidiary ID
- `?subsidiary_code={code}` - Filter by subsidiary code
- `?department={id}` - Filter by department ID
- `?department_code={code}` - Filter by department code

## Response Examples

### Organization List Response
```json
{
  "count": 1,
  "results": [{
    "id": "123",
    "name": "Ministry of Information",
    "name_ar": "وزارة الإعلام",
    "code": "MOI",
    "subsidiary_count": 5,
    "department_count": 15,
    "active_subsidiary_count": 5,
    "active_department_count": 15,
    "is_verified": true
  }]
}
```

### Organization Detail Response
```json
{
  "id": "123",
  "name": "Ministry of Information",
  "name_ar": "وزارة الإعلام",
  "code": "MOI",
  "subsidiary_count": 2,
  "department_count": 5,
  "post_count": 150,
  "subsidiaries": [{
    "id": "456",
    "name": "News Agency",
    "name_ar": "وكالة الأنباء",
    "code": "NEWS",
    "department_count": 3,
    "departments": [{
      "id": "789",
      "name": "Editorial Department",
      "name_ar": "قسم التحرير",
      "code": "EDIT",
      "department_type": "media",
      "employee_count": 25
    }]
  }]
}
```