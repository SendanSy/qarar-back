"""
Management command to check hashtag database state and clean duplicates
"""
from django.core.management.base import BaseCommand
from django.db import connection
from apps.content.models.classification import HashTag


class Command(BaseCommand):
    help = 'Check hashtag database state and identify issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix issues found'
        )
        parser.add_argument(
            '--check-slug',
            type=str,
            help='Check specific slug for conflicts'
        )

    def handle(self, *args, **options):
        check_slug = options.get('check_slug')
        fix = options.get('fix')
        
        if check_slug:
            self.check_specific_slug(check_slug)
            return
        
        self.stdout.write(self.style.NOTICE('Checking hashtag database state...\n'))
        
        # 0. Show basic counts
        self.show_counts()
        
        # 1. Check for duplicate slugs (shouldn't exist due to unique constraint)
        self.check_duplicate_slugs()
        
        # 2. Check for orphaned index entries
        self.check_index_state()
        
        # 3. Check for case sensitivity issues
        self.check_case_issues()
        
        # 4. Check for invisible characters
        self.check_invisible_chars()
        
        # 5. Show sample hashtags
        self.show_sample_hashtags()
        
        if fix:
            self.stdout.write(self.style.WARNING('\nAttempting to fix issues...'))
            self.fix_issues()
    
    def show_counts(self):
        """Show basic hashtag counts"""
        from django.db import connection
        
        # ORM count
        orm_count = HashTag.objects.all().count()
        orphaned_count = HashTag.objects.filter(posts__isnull=True).count()
        
        # SQL count
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM content_hashtag")
            sql_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(DISTINCT h.id) 
                FROM content_hashtag h
                LEFT JOIN content_posthashtag ph ON h.id = ph.hashtag_id
                WHERE ph.id IS NULL
            """)
            sql_orphaned = cursor.fetchone()[0]
        
        self.stdout.write(f"Hashtag counts:")
        self.stdout.write(f"  Total (ORM): {orm_count}")
        self.stdout.write(f"  Total (SQL): {sql_count}")
        self.stdout.write(f"  Orphaned (ORM): {orphaned_count}")
        self.stdout.write(f"  Orphaned (SQL): {sql_orphaned}")
        self.stdout.write("")
    
    def show_sample_hashtags(self):
        """Show sample hashtags to understand what's in the database"""
        self.stdout.write("\nSample hashtags in database:")
        
        # Get first 10 hashtags
        hashtags = HashTag.objects.all()[:10]
        if hashtags:
            for h in hashtags:
                post_count = h.posts.count()
                self.stdout.write(f"  - ID: {h.id}, Name: '{h.name}', Slug: '{h.slug}', Posts: {post_count}")
        else:
            self.stdout.write("  No hashtags found via ORM")
        
        # Also check via SQL
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT h.id, h.name, h.slug, COUNT(ph.id) as post_count
                FROM content_hashtag h
                LEFT JOIN content_posthashtag ph ON h.id = ph.hashtag_id
                GROUP BY h.id, h.name, h.slug
                LIMIT 10
            """)
            sql_hashtags = cursor.fetchall()
            
            if sql_hashtags:
                self.stdout.write("\nVia SQL:")
                for row in sql_hashtags:
                    self.stdout.write(f"  - ID: {row[0]}, Name: '{row[1]}', Slug: '{row[2]}', Posts: {row[3]}")
    
    def check_specific_slug(self, slug):
        """Check a specific slug for conflicts"""
        self.stdout.write(f"\nChecking slug: '{slug}'")
        
        # Direct database query
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, name, slug, created_at FROM content_hashtag WHERE slug = %s OR slug LIKE %s",
                [slug, f"{slug}%"]
            )
            results = cursor.fetchall()
            
            if results:
                self.stdout.write(self.style.WARNING(f"Found {len(results)} matching records:"))
                for row in results:
                    self.stdout.write(f"  ID: {row[0]}, Name: '{row[1]}', Slug: '{row[2]}', Created: {row[3]}")
            else:
                self.stdout.write(self.style.SUCCESS(f"No records found with slug '{slug}'"))
        
        # Check via ORM
        orm_results = HashTag.objects.filter(slug=slug)
        self.stdout.write(f"\nORM query found {orm_results.count()} results")
        
        # Check for similar slugs
        similar = HashTag.objects.filter(slug__icontains=slug[:10])
        if similar.exists():
            self.stdout.write(f"\nSimilar slugs (containing '{slug[:10]}'):")
            for h in similar[:10]:
                self.stdout.write(f"  - '{h.slug}' (name: '{h.name}')")
    
    def check_duplicate_slugs(self):
        """Check for duplicate slugs using raw SQL"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT slug, COUNT(*) as count, array_agg(id) as ids, array_agg(name) as names
                FROM content_hashtag
                GROUP BY slug
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            
            if duplicates:
                self.stdout.write(self.style.ERROR(f'Found {len(duplicates)} duplicate slugs:'))
                for slug, count, ids, names in duplicates:
                    self.stdout.write(f"  Slug: '{slug}' appears {count} times")
                    self.stdout.write(f"    IDs: {ids}")
                    self.stdout.write(f"    Names: {names}")
            else:
                self.stdout.write(self.style.SUCCESS('No duplicate slugs found'))
    
    def check_index_state(self):
        """Check PostgreSQL index state"""
        with connection.cursor() as cursor:
            # Check index validity
            cursor.execute("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'content_hashtag' 
                AND indexname LIKE '%slug%'
            """)
            indexes = cursor.fetchall()
            
            self.stdout.write(f"\nSlug-related indexes:")
            for name, definition in indexes:
                self.stdout.write(f"  {name}: {definition[:100]}...")
            
            # Check for bloat
            cursor.execute("""
                SELECT 
                    pg_size_pretty(pg_relation_size('content_hashtag')) as table_size,
                    pg_size_pretty(pg_total_relation_size('content_hashtag')) as total_size,
                    pg_stat_get_live_tuples('content_hashtag'::regclass) as live_tuples,
                    pg_stat_get_dead_tuples('content_hashtag'::regclass) as dead_tuples
            """)
            stats = cursor.fetchone()
            
            self.stdout.write(f"\nTable statistics:")
            self.stdout.write(f"  Table size: {stats[0]}")
            self.stdout.write(f"  Total size: {stats[1]}")
            self.stdout.write(f"  Live tuples: {stats[2]}")
            self.stdout.write(f"  Dead tuples: {stats[3]}")
            
            if stats[3] > stats[2] * 0.1:  # More than 10% dead tuples
                self.stdout.write(self.style.WARNING("  Warning: High number of dead tuples. Consider VACUUM ANALYZE."))
    
    def check_case_issues(self):
        """Check for case sensitivity issues"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT h1.id, h1.slug, h1.name, h2.id, h2.slug, h2.name
                FROM content_hashtag h1
                JOIN content_hashtag h2 ON LOWER(h1.slug) = LOWER(h2.slug)
                WHERE h1.id < h2.id
            """)
            case_conflicts = cursor.fetchall()
            
            if case_conflicts:
                self.stdout.write(self.style.WARNING(f'\nFound {len(case_conflicts)} case-sensitive conflicts:'))
                for row in case_conflicts:
                    self.stdout.write(f"  '{row[1]}' (id:{row[0]}) vs '{row[4]}' (id:{row[3]})")
            else:
                self.stdout.write(self.style.SUCCESS('\nNo case-sensitivity conflicts found'))
    
    def check_invisible_chars(self):
        """Check for invisible characters in slugs"""
        hashtags = HashTag.objects.all()
        issues = []
        
        for h in hashtags:
            # Check for zero-width characters, RTL/LTR marks, etc.
            if any(ord(c) in [0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0xFEFF] for c in h.slug):
                issues.append(h)
            # Check for leading/trailing whitespace
            if h.slug != h.slug.strip():
                issues.append(h)
        
        if issues:
            self.stdout.write(self.style.WARNING(f'\nFound {len(issues)} hashtags with invisible characters:'))
            for h in issues[:10]:
                self.stdout.write(f"  ID: {h.id}, Slug: '{h.slug}', Slug bytes: {h.slug.encode('utf-8')}")
        else:
            self.stdout.write(self.style.SUCCESS('\nNo invisible character issues found'))
    
    def fix_issues(self):
        """Attempt to fix common issues"""
        # 1. VACUUM ANALYZE the table
        with connection.cursor() as cursor:
            self.stdout.write("\nRunning VACUUM ANALYZE on content_hashtag...")
            cursor.execute("VACUUM ANALYZE content_hashtag")
            
            # 2. REINDEX the unique constraint
            self.stdout.write("Reindexing slug unique constraint...")
            try:
                cursor.execute("REINDEX INDEX content_hashtag_slug_key")
                self.stdout.write(self.style.SUCCESS("Index reindexed successfully"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Could not reindex: {e}"))
        
        self.stdout.write(self.style.SUCCESS("\nFix attempts completed"))