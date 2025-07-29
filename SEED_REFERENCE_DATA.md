# Seed Reference Data

This document explains how to use the `seed_reference_data` management command to populate the database with reference data.

## What it seeds

The command seeds the following data:

1. **Categories and Subcategories** (11 main categories with 22 subcategories)
   - Law (Civil Law, Criminal Law)
   - Education (Primary Education, Higher Education)
   - Healthcare (Public Health, Private Healthcare)
   - Economy (Agriculture, Industry)
   - Infrastructure (Transportation, Utilities)
   - Culture (Arts, Heritage)
   - Security (National Defense, Internal Security)
   - Environment (Natural Resources, Conservation)
   - Social Services (Social Welfare, Housing)
   - Technology (Information Technology, Telecommunications)
   - Media (Traditional Media, Digital Media)

2. **Post Types** (25 types)
   - Decision (قرار)
   - Circular (تعميم)
   - Announcement (إعلان)
   - Statement (بيان)
   - Administrative Order (أمر إداري)
   - And 20 more types...

3. **Geographic Data**
   - Syria as a country
   - 14 Governorates (States)
   - 56 Cities (4 per governorate)

## Usage

### Basic seeding (preserves existing data)
```bash
python manage.py seed_reference_data
```

### Clear existing data and reseed
```bash
python manage.py seed_reference_data --clear
```

## Important Notes

- The command uses `update_or_create` to avoid duplicates when run multiple times
- Categories and subcategories are properly linked with foreign keys
- Geographic data follows the hierarchy: Country → State (Governorate) → City
- All seeded data is marked as `is_active=True`
- The command runs in a database transaction for data integrity

## Data Mapping

The script correctly maps:
- English names to the `name` field
- Arabic names to the `name_ar` field
- English descriptions to the `description` field
- Arabic descriptions to the `description_ar` field
- Geographic data uses `State` model for Governorates and `City` model for cities