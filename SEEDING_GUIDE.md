# Seeding Guide for Geographic and Producer Models

This guide provides detailed information about all fields for geographic and producer models to help with database seeding.

## Geographic Models

### 1. Country Model
**Table**: `geographics_country`

| Field | Type | Required | Unique | Description | Example |
|-------|------|----------|---------|-------------|---------|
| id | Integer (Auto) | Yes | Yes | Primary key (auto-generated) | 1 |
| name | CharField(100) | Yes | Yes | Country name | "Syria" |
| code | CharField(3) | Yes | Yes | ISO 3166-1 alpha-3 country code | "SYR" |
| is_active | Boolean | No | No | Active status (default: True) | true |
| created_at | DateTime | Auto | No | Auto-generated timestamp | "2025-01-29T10:00:00Z" |
| updated_at | DateTime | Auto | No | Auto-updated timestamp | "2025-01-29T10:00:00Z" |

**Constraints**:
- `name` must be unique across all countries
- `code` must be unique and should follow ISO 3166-1 alpha-3 standard (3 letters)

### 2. State Model
**Table**: `geographics_state`

| Field | Type | Required | Unique | Description | Example |
|-------|------|----------|---------|-------------|---------|
| id | Integer (Auto) | Yes | Yes | Primary key (auto-generated) | 1 |
| name | CharField(100) | Yes | No | State/Province name | "Damascus" |
| code | CharField(10) | Yes | No* | State code | "DAM" |
| country_id | ForeignKey | Yes | No | Reference to Country | 1 |
| is_active | Boolean | No | No | Active status (default: True) | true |
| created_at | DateTime | Auto | No | Auto-generated timestamp | "2025-01-29T10:00:00Z" |
| updated_at | DateTime | Auto | No | Auto-updated timestamp | "2025-01-29T10:00:00Z" |

**Constraints**:
- Unique together: (`country_id`, `code`) - code must be unique within a country
- `country_id` must reference an existing Country

### 3. City Model
**Table**: `geographics_city`

| Field | Type | Required | Unique | Description | Example |
|-------|------|----------|---------|-------------|---------|
| id | Integer (Auto) | Yes | Yes | Primary key (auto-generated) | 1 |
| name | CharField(100) | Yes | No | City name | "Damascus City" |
| code | CharField(10) | Yes | No* | City code | "DAM-CTY" |
| state_id | ForeignKey | Yes | No | Reference to State | 1 |
| is_active | Boolean | No | No | Active status (default: True) | true |
| created_at | DateTime | Auto | No | Auto-generated timestamp | "2025-01-29T10:00:00Z" |
| updated_at | DateTime | Auto | No | Auto-updated timestamp | "2025-01-29T10:00:00Z" |

**Constraints**:
- Unique together: (`state_id`, `code`) - code must be unique within a state
- `state_id` must reference an existing State

## Producer Models

### 1. Organization Model
**Table**: `producers_organization`

| Field | Type | Required | Unique | Description | Example |
|-------|------|----------|---------|-------------|---------|
| id | Integer (Auto) | Yes | Yes | Primary key (auto-generated) | 1 |
| name | CharField(255) | Yes | No | Organization name (English) | "Ministry of Information" |
| name_ar | CharField(255) | Yes | No | Organization name (Arabic) | "وزارة الإعلام" |
| code | CharField(50) | Yes | Yes | Organization code | "MOI" |
| description | TextField | No | No | Description (English) | "Government ministry..." |
| description_ar | TextField | No | No | Description (Arabic) | "الوزارة الحكومية..." |
| website | URLField | No | No | Website URL | "https://moi.gov.sy" |
| email | EmailField | No | No | Contact email | "info@moi.gov.sy" |
| phone | CharField(50) | No | No | Contact phone | "+963-11-1234567" |
| country_id | ForeignKey | No | No | Reference to Country (nullable) | 1 |
| state_id | ForeignKey | No | No | Reference to State (nullable) | 1 |
| city_id | ForeignKey | No | No | Reference to City (nullable) | 1 |
| is_active | Boolean | No | No | Active status (default: True) | true |
| is_verified | Boolean | No | No | Verification status (default: False) | true |
| created_at | DateTime | Auto | No | Auto-generated timestamp | "2025-01-29T10:00:00Z" |
| updated_at | DateTime | Auto | No | Auto-updated timestamp | "2025-01-29T10:00:00Z" |

**Constraints**:
- `code` must be unique across all organizations
- `email` must be valid email format if provided
- `website` must be valid URL format if provided

### 2. Subsidiary Model
**Table**: `producers_subsidiary`

| Field | Type | Required | Unique | Description | Example |
|-------|------|----------|---------|-------------|---------|
| id | Integer (Auto) | Yes | Yes | Primary key (auto-generated) | 1 |
| name | CharField(255) | Yes | No | Subsidiary name (English) | "Syrian News Agency" |
| name_ar | CharField(255) | Yes | No | Subsidiary name (Arabic) | "وكالة الأنباء السورية" |
| code | CharField(50) | Yes | Yes | Subsidiary code | "SANA" |
| parent_organization_id | ForeignKey | Yes | No | Reference to Organization | 1 |
| description | TextField | No | No | Description (English) | "National news agency..." |
| description_ar | TextField | No | No | Description (Arabic) | "وكالة الأنباء الوطنية..." |
| country_id | ForeignKey | No | No | Reference to Country (nullable) | 1 |
| state_id | ForeignKey | No | No | Reference to State (nullable) | 1 |
| city_id | ForeignKey | No | No | Reference to City (nullable) | 1 |
| is_active | Boolean | No | No | Active status (default: True) | true |
| created_at | DateTime | Auto | No | Auto-generated timestamp | "2025-01-29T10:00:00Z" |
| updated_at | DateTime | Auto | No | Auto-updated timestamp | "2025-01-29T10:00:00Z" |

**Constraints**:
- `code` must be unique across all subsidiaries
- `parent_organization_id` must reference an existing Organization

### 3. Department Model
**Table**: `producers_department`

| Field | Type | Required | Unique | Description | Example |
|-------|------|----------|---------|-------------|---------|
| id | Integer (Auto) | Yes | Yes | Primary key (auto-generated) | 1 |
| name | CharField(255) | Yes | No | Department name (English) | "Editorial Department" |
| name_ar | CharField(255) | Yes | No | Department name (Arabic) | "قسم التحرير" |
| code | CharField(50) | Yes | Yes | Department code | "SANA-EDIT" |
| subsidiary_id | ForeignKey | Yes | No | Reference to Subsidiary | 1 |
| description | TextField | No | No | Description (English) | "Handles news editing..." |
| description_ar | TextField | No | No | Description (Arabic) | "يتولى تحرير الأخبار..." |
| head_name | CharField(255) | No | No | Department head name | "John Doe" |
| head_email | EmailField | No | No | Department head email | "john@sana.sy" |
| head_phone | CharField(50) | No | No | Department head phone | "+963-11-1234568" |
| employee_count | PositiveInteger | No | No | Number of employees (default: 0) | 25 |
| department_type | CharField(50) | No | No | Type of department | "media" |
| is_active | Boolean | No | No | Active status (default: True) | true |
| created_at | DateTime | Auto | No | Auto-generated timestamp | "2025-01-29T10:00:00Z" |
| updated_at | DateTime | Auto | No | Auto-updated timestamp | "2025-01-29T10:00:00Z" |

**Constraints**:
- `code` must be unique across all departments
- `subsidiary_id` must reference an existing Subsidiary
- Unique together: (`subsidiary_id`, `code`) - code must be unique within a subsidiary
- `department_type` choices: 'admin', 'media', 'technical', 'financial', 'legal', 'hr', 'it', 'other'

## Seeding Order

To properly seed the database, follow this order:

1. **Countries** - No dependencies
2. **States** - Requires Countries
3. **Cities** - Requires States
4. **Organizations** - Optional references to Country/State/City
5. **Subsidiaries** - Requires Organizations, optional Country/State/City
6. **Departments** - Requires Subsidiaries

## Example Seeding Data

### Countries
```json
[
  {
    "name": "Syria",
    "code": "SYR",
    "is_active": true
  },
  {
    "name": "Lebanon",
    "code": "LBN",
    "is_active": true
  }
]
```

### States
```json
[
  {
    "name": "Damascus",
    "code": "DM",
    "country_id": 1,
    "is_active": true
  },
  {
    "name": "Aleppo",
    "code": "HL",
    "country_id": 1,
    "is_active": true
  }
]
```

### Cities
```json
[
  {
    "name": "Damascus City",
    "code": "DM-CTY",
    "state_id": 1,
    "is_active": true
  },
  {
    "name": "Jaramana",
    "code": "DM-JRM",
    "state_id": 1,
    "is_active": true
  }
]
```

### Organizations
```json
[
  {
    "name": "Ministry of Information",
    "name_ar": "وزارة الإعلام",
    "code": "MOI",
    "description": "Government ministry responsible for media and information",
    "description_ar": "الوزارة الحكومية المسؤولة عن الإعلام والمعلومات",
    "website": "https://moi.gov.sy",
    "email": "info@moi.gov.sy",
    "phone": "+963-11-1234567",
    "country_id": 1,
    "state_id": 1,
    "city_id": 1,
    "is_active": true,
    "is_verified": true
  }
]
```

### Subsidiaries
```json
[
  {
    "name": "Syrian News Agency",
    "name_ar": "وكالة الأنباء السورية",
    "code": "SANA",
    "parent_organization_id": 1,
    "description": "National news agency of Syria",
    "description_ar": "وكالة الأنباء الوطنية السورية",
    "country_id": 1,
    "state_id": 1,
    "city_id": 1,
    "is_active": true
  }
]
```

### Departments
```json
[
  {
    "name": "Editorial Department",
    "name_ar": "قسم التحرير",
    "code": "SANA-EDIT",
    "subsidiary_id": 1,
    "description": "Handles news editing and content creation",
    "description_ar": "يتولى تحرير الأخبار وإنشاء المحتوى",
    "head_name": "Ahmad Hassan",
    "head_email": "ahmad.hassan@sana.sy",
    "head_phone": "+963-11-1234568",
    "employee_count": 25,
    "department_type": "media",
    "is_active": true
  }
]
```

## Tips for Seeding

1. **Use realistic codes**: Follow standard conventions (ISO for countries, abbreviations for organizations)
2. **Bilingual data**: Always provide both English and Arabic names for organizations
3. **Hierarchical structure**: Ensure parent entities exist before creating children
4. **Validation**: Ensure emails and URLs are properly formatted
5. **Unique constraints**: Be careful with unique fields (codes) to avoid duplicates