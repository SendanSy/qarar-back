"""
Management command to seed posts from CSV data
"""
import pandas as pd
import os
import mimetypes
import json
import re
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from apps.content.models.post import Post, PostType, PostAttachment
from apps.content.models.classification import Category, SubCategory, HashTag
from apps.producers.models import Organization, Subsidiary, Department

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds posts from CSV data file'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            default='apps/core/management/commands/posts_data.csv',
            help='Path to CSV file containing post data'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean all seeded posts before seeding new ones'
        )
        parser.add_argument(
            '--clean-posts',
            action='store_true',
            help='Force delete ALL posts and hashtags in the database'
        )
        parser.add_argument(
            '--clean-orphaned-hashtags',
            action='store_true',
            help='Delete only orphaned hashtags (hashtags with no posts)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually creating posts (for testing)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of posts to create in each batch'
        )

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        # Handle cleanup options
        if options.get('clean_posts'):
            self.force_clean_all_posts()
            return
        
        if options.get('clean_orphaned_hashtags'):
            self.clean_orphaned_hashtags()
            return
        
        if options.get('clean'):
            self.clean_posts()
            if not dry_run:
                return
        
        self.stdout.write(self.style.NOTICE(f'Starting post seeding from {csv_path}...'))
        
        try:
            # Read CSV file
            df = self.read_csv_data(csv_path)
            if df.empty:
                self.stdout.write(self.style.WARNING('CSV file is empty or not found'))
                return
            
            # Cache related objects
            self.stdout.write(self.style.NOTICE('Caching related objects...'))
            related_objects = self.cache_related_objects()
            
            # Get or create author user
            author = self.get_author_user()
            if not author:
                self.stdout.write(self.style.ERROR('Could not find or create author user'))
                return
            
            # Process posts in batches
            total_posts = len(df)
            created_posts = 0
            failed_posts = []
            
            for batch_start in range(0, total_posts, batch_size):
                batch_end = min(batch_start + batch_size, total_posts)
                batch_df = df.iloc[batch_start:batch_end]
                
                if dry_run:
                    self.stdout.write(f'[DRY RUN] Would process posts {batch_start+1} to {batch_end}')
                    continue
                
                try:
                    with transaction.atomic():
                        posts_created, attachments_created, errors = self.process_batch(
                            batch_df, 
                            related_objects, 
                            author,
                            batch_start
                        )
                        created_posts += posts_created
                        
                        if errors:
                            failed_posts.extend(errors)
                        
                        self.stdout.write(
                            f'Batch {batch_start//batch_size + 1}: '
                            f'Created {posts_created} posts with {attachments_created} attachments'
                        )
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to process batch {batch_start//batch_size + 1}: {str(e)}')
                    )
                    failed_posts.append(f'Batch {batch_start}-{batch_end}: {str(e)}')
            
            # Report results
            self.stdout.write(self.style.SUCCESS(f'\nSeeding completed!'))
            self.stdout.write(f'Total posts created: {created_posts}/{total_posts}')
            
            if failed_posts:
                self.stdout.write(self.style.WARNING(f'\nFailed entries ({len(failed_posts)}):'))
                for error in failed_posts[:10]:  # Show first 10 errors
                    self.stdout.write(f'  - {error}')
                if len(failed_posts) > 10:
                    self.stdout.write(f'  ... and {len(failed_posts) - 10} more')
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Fatal error: {str(e)}'))
            raise

    def clean_posts(self):
        """Remove all posts created by Qarar Platform user and clean orphaned hashtags"""
        try:
            author = User.objects.filter(username='qarar').first()
            if author:
                count = Post.objects.filter(author=author).count()
                if count > 0:
                    # Get hashtags used by these posts before deletion
                    hashtags_to_check = set()
                    for post in Post.objects.filter(author=author):
                        hashtags_to_check.update(post.hashtags.all())
                    
                    # Delete the posts
                    Post.objects.filter(author=author).delete()
                    self.stdout.write(self.style.SUCCESS(f'Deleted {count} existing posts'))
                    
                    # Clean up orphaned hashtags (hashtags with no posts)
                    orphaned_count = 0
                    for hashtag in hashtags_to_check:
                        if hashtag.posts.count() == 0:
                            hashtag.delete()
                            orphaned_count += 1
                    
                    if orphaned_count > 0:
                        self.stdout.write(self.style.SUCCESS(f'Deleted {orphaned_count} orphaned hashtags'))
                else:
                    self.stdout.write('No posts to clean')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error cleaning posts: {str(e)}'))
    
    def force_clean_all_posts(self):
        """Force delete ALL posts and hashtags from the database"""
        try:
            post_count = Post.objects.all().count()
            hashtag_count = HashTag.objects.all().count()
            
            if post_count > 0 or hashtag_count > 0:
                self.stdout.write(self.style.WARNING('\n' + '='*60))
                self.stdout.write(self.style.WARNING('WARNING: This will delete:'))
                self.stdout.write(self.style.WARNING(f'  - ALL {post_count} posts'))
                self.stdout.write(self.style.WARNING(f'  - ALL {hashtag_count} hashtags'))
                self.stdout.write(self.style.WARNING('='*60))
                
                confirm = input('\nType "yes" to confirm: ')
                if confirm.lower() == 'yes':
                    # Delete all posts first (this will clear M2M relationships)
                    if post_count > 0:
                        Post.objects.all().delete()
                        self.stdout.write(self.style.SUCCESS(f'✓ Deleted ALL {post_count} posts'))
                    
                    # Then delete all hashtags
                    if hashtag_count > 0:
                        HashTag.objects.all().delete()
                        self.stdout.write(self.style.SUCCESS(f'✓ Deleted ALL {hashtag_count} hashtags'))
                    
                    self.stdout.write(self.style.SUCCESS('\nDatabase cleaned successfully!'))
                else:
                    self.stdout.write(self.style.WARNING('Operation cancelled'))
            else:
                self.stdout.write('No posts or hashtags to delete')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error cleaning database: {str(e)}'))
    
    def get_or_create_hashtags(self, hashtag_names):
        """Get or create hashtag objects from a list of names"""
        hashtags = []
        
        for tag_name in hashtag_names:
            if not tag_name:
                continue
                
            try:
                # Clean the name - NO # sign should be in the name
                tag_name = tag_name.strip()
                if tag_name.startswith('#'):
                    tag_name = tag_name[1:]
                
                # Skip if invalid length
                if len(tag_name) < 2 or len(tag_name) > 100:
                    continue
                
                # For slug, use the name itself for Arabic, slugify for English
                # This ensures Arabic hashtags keep their Arabic slug
                if any('\u0600' <= c <= '\u06FF' for c in tag_name):
                    # Arabic hashtag - use name as slug
                    tag_slug = tag_name
                else:
                    # English hashtag - slugify it
                    tag_slug = slugify(tag_name) or tag_name
                
                # First try to get by name (exact match)
                hashtag = HashTag.objects.filter(name=tag_name).first()
                
                if not hashtag:
                    # If not found by name, check if slug already exists
                    # This handles cases where different names might generate the same slug
                    existing_by_slug = HashTag.objects.filter(slug=tag_slug).first()
                    
                    if existing_by_slug:
                        # Slug conflict - use the existing hashtag
                        hashtag = existing_by_slug
                        self.stdout.write(self.style.WARNING(
                            f"  Slug conflict for '{tag_name}' - using existing hashtag '{existing_by_slug.name}'"
                        ))
                    else:
                        # Create new hashtag
                        hashtag = HashTag.objects.create(
                            name=tag_name,  # Store WITHOUT # sign
                            slug=tag_slug,
                            description=f'Hashtag for {tag_name}',
                            is_active=True,
                            order=0
                        )
                        self.stdout.write(self.style.SUCCESS(f"✓ Created new hashtag: {tag_name}"))
                else:
                    self.stdout.write(f"  Using existing hashtag: {tag_name}")
                
                hashtags.append(hashtag)
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error with hashtag '{tag_name}': {str(e)}"))
        
        return hashtags
    
    def clean_orphaned_hashtags(self):
        """Delete only orphaned hashtags (hashtags with no posts)"""
        try:
            # Find all hashtags with no posts
            orphaned_hashtags = HashTag.objects.filter(posts__isnull=True)
            orphaned_count = orphaned_hashtags.count()
            
            if orphaned_count > 0:
                self.stdout.write(self.style.WARNING(f'\nFound {orphaned_count} orphaned hashtag(s)'))
                
                # Show some examples
                examples = orphaned_hashtags[:10]
                for hashtag in examples:
                    self.stdout.write(f'  - #{hashtag.name}')
                if orphaned_count > 10:
                    self.stdout.write(f'  ... and {orphaned_count - 10} more')
                
                confirm = input('\nDelete all orphaned hashtags? Type "yes" to confirm: ')
                if confirm.lower() == 'yes':
                    orphaned_hashtags.delete()
                    self.stdout.write(self.style.SUCCESS(f'✓ Deleted {orphaned_count} orphaned hashtag(s)'))
                else:
                    self.stdout.write(self.style.WARNING('Operation cancelled'))
            else:
                self.stdout.write(self.style.SUCCESS('No orphaned hashtags found'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error cleaning orphaned hashtags: {str(e)}'))

    def read_csv_data(self, csv_path):
        """Read and validate CSV data"""
        try:
            # Read CSV with proper encoding for Arabic text
            df = pd.read_csv(csv_path, encoding='utf-8')
            
            # Clean column names (remove spaces, lowercase)
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            self.stdout.write(f'Loaded {len(df)} rows from CSV')
            self.stdout.write(f'Columns found: {", ".join(df.columns.tolist())}')
            
            return df
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'CSV file not found: {csv_path}'))
            return pd.DataFrame()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading CSV: {str(e)}'))
            return pd.DataFrame()

    def cache_related_objects(self):
        """Cache all related objects for efficient lookup"""
        cache = {
            'post_types': {},
            'categories': {},
            'subcategories': {},
            'organizations': {},
            'subsidiaries': {},
            'departments': {}
        }
        
        # Cache PostTypes by name and name_ar
        for pt in PostType.objects.all():
            cache['post_types'][pt.name.lower()] = pt
            cache['post_types'][pt.name_ar] = pt
            
        # Cache Categories by name and name_ar
        for cat in Category.objects.all():
            cache['categories'][cat.name.lower()] = cat
            if hasattr(cat, 'name_ar') and cat.name_ar:
                cache['categories'][cat.name_ar] = cat
                
        # Cache SubCategories by name
        for subcat in SubCategory.objects.all():
            cache['subcategories'][subcat.name.lower()] = subcat
            if hasattr(subcat, 'name_ar') and subcat.name_ar:
                cache['subcategories'][subcat.name_ar] = subcat
                
        # Cache Organizations by name and code
        for org in Organization.objects.all():
            cache['organizations'][org.name.lower()] = org
            if hasattr(org, 'name_ar') and org.name_ar:
                cache['organizations'][org.name_ar] = org
            if hasattr(org, 'code') and org.code:
                cache['organizations'][org.code.lower()] = org
                
        # Cache Subsidiaries
        for sub in Subsidiary.objects.all():
            cache['subsidiaries'][sub.name.lower()] = sub
            if hasattr(sub, 'name_ar') and sub.name_ar:
                cache['subsidiaries'][sub.name_ar] = sub
                
        # Cache Departments
        for dept in Department.objects.all():
            cache['departments'][dept.name.lower()] = dept
            if hasattr(dept, 'name_ar') and dept.name_ar:
                cache['departments'][dept.name_ar] = dept
        
        self.stdout.write(f'Cached: {len(cache["post_types"])} post types, '
                         f'{len(cache["categories"])} categories, '
                         f'{len(cache["subcategories"])} subcategories, '
                         f'{len(cache["organizations"])} organizations')
        
        return cache

    def get_author_user(self):
        """Get or create the Qarar Platform user"""
        try:
            user, created = User.objects.get_or_create(
                username='qarar',
                defaults={
                    'email': 'platform@qarar.sy',
                    'first_name': 'Qarar',
                    'last_name': 'Platform',
                    'is_active': True,
                    'is_staff': False
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS('Created Qarar Platform user'))
            else:
                self.stdout.write('Using existing Qarar Platform user')
            return user
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting author user: {str(e)}'))
            return None

    def process_batch(self, batch_df, related_objects, author, start_index):
        """Process a batch of posts"""
        posts_to_create = []
        posts_data = []  # Store additional data for M2M relations and attachments
        errors = []
        
        # First, collect all unique hashtag names from this batch
        all_hashtag_names = set()
        
        for idx, row in batch_df.iterrows():
            try:
                # Prepare post data
                post_data = self.prepare_post_data(row, related_objects, author, start_index + idx)
                if post_data:
                    # Collect hashtag names
                    hashtag_names = post_data.get('hashtag_names', [])
                    all_hashtag_names.update(hashtag_names)
                    
                    # Separate core fields from M2M and attachment data
                    core_fields = {k: v for k, v in post_data.items() 
                                 if k not in ['categories', 'subcategories', 'hashtag_names', 'attachments_data']}
                    
                    post = Post(**core_fields)
                    posts_to_create.append(post)
                    
                    # Store M2M and attachment data for later
                    attachment_urls = post_data.get('attachments_data', [])
                    posts_data.append({
                        'categories': post_data.get('categories', []),
                        'subcategories': post_data.get('subcategories', []),
                        'hashtag_names': hashtag_names,  # Store names, not objects yet
                        'attachments_data': attachment_urls
                    })
                    
                    # Debug log for attachments
                    if attachment_urls:
                        self.stdout.write(f"Row {start_index + idx}: Prepared {len(attachment_urls)} attachment URL(s) for later processing")
                else:
                    errors.append(f'Row {start_index + idx}: Could not prepare post data')
                    
            except Exception as e:
                errors.append(f'Row {start_index + idx}: {str(e)}')
        
        # Pre-create all hashtags outside the transaction
        hashtag_cache = {}
        if all_hashtag_names:
            unique_names = list(all_hashtag_names)
            self.stdout.write(f"\nPre-creating/fetching {len(unique_names)} unique hashtag(s) for this batch...")
            hashtag_objects = self.get_or_create_hashtags(unique_names)
            
            # Create a mapping from name to object
            # Important: hashtag names are stored WITHOUT # sign
            for hashtag in hashtag_objects:
                # Store with the clean name (no # sign)
                clean_name = hashtag.name
                hashtag_cache[clean_name] = hashtag
                # Also store with # for matching if needed
                hashtag_cache[f"#{clean_name}"] = hashtag
            
            self.stdout.write(f"Successfully cached {len(hashtag_cache)} hashtag mappings")
        
        # Bulk create posts
        created_posts = []
        if posts_to_create:
            created_posts = Post.objects.bulk_create(posts_to_create, batch_size=100)
            
            # Process M2M relations and attachments for created posts
            attachments_count = 0
            for post, data in zip(created_posts, posts_data):
                try:
                    # Add categories
                    if data['categories']:
                        post.categories.set(data['categories'])
                        self.stdout.write(f"Set {len(data['categories'])} categories for post {post.id}")
                    
                    # Add subcategories
                    if data['subcategories']:
                        post.subcategories.set(data['subcategories'])
                        self.stdout.write(f"Set {len(data['subcategories'])} subcategories for post {post.id}")
                    
                    # Add hashtags using the pre-created objects
                    hashtag_names = data.get('hashtag_names', [])
                    if hashtag_names:
                        hashtags_to_link = []
                        for name in hashtag_names:
                            # Clean the name (remove # if present)
                            clean_name = name.strip()
                            if clean_name.startswith('#'):
                                clean_name = clean_name[1:]
                            
                            # Find in cache
                            if clean_name in hashtag_cache:
                                hashtags_to_link.append(hashtag_cache[clean_name])
                            else:
                                self.stdout.write(self.style.WARNING(f"Hashtag '{clean_name}' not found in cache"))
                        
                        if hashtags_to_link:
                            post.hashtags.add(*hashtags_to_link)
                            self.stdout.write(self.style.SUCCESS(f"✓ Linked {len(hashtags_to_link)} hashtag(s) to post {post.id}"))
                            
                            # Update hashtag post counts
                            for hashtag in hashtags_to_link:
                                try:
                                    hashtag.update_post_count()
                                except:
                                    pass  # Continue if update fails
                    
                    # Create attachments
                    if data.get('attachments_data'):
                        self.stdout.write(f"Processing attachments for post {post.id}: {data['attachments_data']}")
                        attachments = self.create_attachments(post, data['attachments_data'])
                        attachments_count += len(attachments)
                    else:
                        self.stdout.write(f"No attachments found for post {post.id}")
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing post {post.id} relations: {str(e)}"))
                    # Continue with next post instead of failing the whole batch
        
        return len(created_posts), attachments_count, errors

    def prepare_post_data(self, row, related_objects, author, index):
        """Prepare post data from CSV row"""
        try:
            # Get category for title generation
            category_name = self.safe_get(row, ['category', 'categories'])
            category = None
            if category_name:
                category_key = str(category_name).strip().lower()
                category = related_objects['categories'].get(category_key)
            
            # Generate titles
            category_display = category.name if category else 'General'
            category_display_ar = category.name_ar if category and hasattr(category, 'name_ar') else 'عام'
            
            title = f"Post - {category_display} - #Syria"
            title_ar = f"منشور - {category_display_ar} - #سوريا"
            
            # Generate unique slug
            slug_base = slugify(title)
            slug = f"{slug_base}-{index + 1}"
            
            # Get post type
            post_type_name = self.safe_get(row, ['type', 'post_type'])
            post_type = None
            if post_type_name:
                type_key = str(post_type_name).strip().lower()
                post_type = related_objects['post_types'].get(type_key)
            
            if not post_type:
                # Default to first available post type
                post_type = PostType.objects.first()
            
            # Get organization
            org_name = self.safe_get(row, ['organization', 'org'])
            organization = None
            if org_name:
                org_key = str(org_name).strip().lower()
                organization = related_objects['organizations'].get(org_key)
            
            if not organization:
                # Default to first available organization
                organization = Organization.objects.first()
            
            # Get subsidiary (optional)
            sub_name = self.safe_get(row, ['subsidiary', 'sub'])
            subsidiary = None
            if sub_name and pd.notna(sub_name):
                sub_key = str(sub_name).strip().lower()
                subsidiary = related_objects['subsidiaries'].get(sub_key)
            
            # Get department (optional)
            dept_name = self.safe_get(row, ['department', 'dept'])
            department = None
            if dept_name and pd.notna(dept_name):
                dept_key = str(dept_name).strip().lower()
                department = related_objects['departments'].get(dept_key)
            
            # Get content fields - PRESERVE FORMATTING
            content = self.safe_get(row, ['content', 'description'], '')
            content_ar = self.safe_get(row, ['content_ar', 'arabic_content'], '')
            summary = self.safe_get(row, ['summary'], '')
            summary_ar = self.safe_get(row, ['summary_ar', 'arabic_summary'], '')
            
            # Process content fields to handle newlines properly
            # Rule: 2+ spaces = newline, 1 space = normal space
            def process_content_newlines(text):
                if not text or pd.isna(text):
                    return ''
                
                text = str(text)
                
                # Replace 2 or more consecutive spaces with a newline
                import re
                # Match 2 or more spaces
                text = re.sub(r'  +', '\n', text)
                
                # Also preserve any existing newlines from CSV
                # CSV might have \n encoded as literal string
                text = text.replace('\\n', '\n')
                
                # Add double newline before hashtags at the end
                # Find hashtags at the end of content (after the last non-hashtag text)
                # Pattern: Find where hashtags start (consecutive hashtags with spaces between them at the end)
                hashtag_pattern = r'(\s*#[a-zA-Z0-9_\u0600-\u06FF]+(?:\s+#[a-zA-Z0-9_\u0600-\u06FF]+)*\s*)$'
                match = re.search(hashtag_pattern, text)
                if match:
                    # Get the position where hashtags start
                    hashtag_start = match.start()
                    if hashtag_start > 0:
                        # Get the text before hashtags and the hashtags
                        text_before = text[:hashtag_start].rstrip()
                        hashtags_part = match.group(1).strip()
                        
                        # Combine with double newline separator
                        text = text_before + '\n\n' + hashtags_part
                
                return text
            
            content = process_content_newlines(content)
            content_ar = process_content_newlines(content_ar)
            summary = process_content_newlines(summary)
            summary_ar = process_content_newlines(summary_ar)
            
            # Get status
            status = self.safe_get(row, ['status'], 'published')
            if status not in ['draft', 'pending', 'published', 'archived', 'rejected']:
                status = 'published'
            
            # Get published date
            published_at = None
            pub_date = self.safe_get(row, ['published_at', 'publish_date', 'date'])
            if pub_date and pd.notna(pub_date):
                try:
                    published_at = pd.to_datetime(pub_date)
                    if pd.isna(published_at):
                        published_at = None
                except:
                    published_at = None
            
            if status == 'published' and not published_at:
                published_at = timezone.now()
            
            # Prepare post data
            post_data = {
                'title': title,
                'title_ar': title_ar,
                'content': content if pd.notna(content) else '',
                'content_ar': content_ar if pd.notna(content_ar) else '',
                'summary': summary if pd.notna(summary) else '',
                'summary_ar': summary_ar if pd.notna(summary_ar) else '',
                'author': author,
                'type': post_type,
                'organization': organization,
                'subsidiary': subsidiary,
                'department': department,
                'status': status,
                'published_at': published_at,
                'slug': slug,
                'view_count': 0
            }
            
            # Get categories (M2M)
            categories = []
            cat_names = self.safe_get(row, ['category', 'categories'])
            if cat_names and pd.notna(cat_names):
                for cat_name in str(cat_names).split(','):
                    cat_key = cat_name.strip().lower()
                    if cat_key in related_objects['categories']:
                        categories.append(related_objects['categories'][cat_key])
            
            post_data['categories'] = categories
            
            # Get subcategories (M2M)
            subcategories = []
            subcat_names = self.safe_get(row, ['subcategory', 'subcategories'])
            if subcat_names and pd.notna(subcat_names):
                for subcat_name in str(subcat_names).split(','):
                    subcat_key = subcat_name.strip().lower()
                    if subcat_key in related_objects['subcategories']:
                        subcategories.append(related_objects['subcategories'][subcat_key])
            
            post_data['subcategories'] = subcategories
            
            # Parse hashtags from CSV column ONLY
            hashtag_names = []
            hashtags_csv = self.safe_get(row, ['hashtags', 'hashtag', 'tags'])
            
            if hashtags_csv and pd.notna(hashtags_csv):
                try:
                    hashtag_list = []
                    
                    # Check if it's a JSON array
                    if isinstance(hashtags_csv, str):
                        hashtags_csv = hashtags_csv.strip()
                        
                        if hashtags_csv.startswith('[') and hashtags_csv.endswith(']'):
                            # It's a JSON array - parse it
                            # CSV escapes quotes by doubling them, pandas already handles this
                            hashtag_list = json.loads(hashtags_csv)
                        else:
                            # Not JSON, try comma-separated
                            hashtag_list = [h.strip() for h in hashtags_csv.split(',') if h.strip()]
                    
                    # Clean each hashtag
                    for tag in hashtag_list:
                        if tag:
                            tag = str(tag).strip()
                            # Remove # sign if present
                            if tag.startswith('#'):
                                tag = tag[1:]
                            
                            # Remove any remaining quotes
                            tag = tag.strip('"\'')
                            
                            # Only add if valid
                            if tag and 2 <= len(tag) <= 100:
                                hashtag_names.append(tag)
                                
                except (json.JSONDecodeError, ValueError) as e:
                    self.stdout.write(self.style.ERROR(f"Error parsing hashtags at row {index}: {str(e)}"))
                    self.stdout.write(f"  Raw value: {repr(hashtags_csv)}")  # Use repr to see escape characters
            
            # Store hashtag names for later processing
            post_data['hashtag_names'] = hashtag_names
            
            if hashtag_names:
                self.stdout.write(self.style.SUCCESS(f"Row {index}: Found {len(hashtag_names)} hashtag(s):"))
                for ht in hashtag_names:
                    self.stdout.write(f"  - {ht}")
            
            # Get attachments data from media_url column
            attachments_data = []
            attachment_urls = self.safe_get(row, ['media_url', 'attachment', 'files'])
            if attachment_urls and pd.notna(attachment_urls):
                # Convert to string and clean
                url_text = str(attachment_urls).strip()
                
                # The media_url could be a single URL or multiple URLs
                # Handle both newline-separated and space-separated URLs
                if url_text:
                    # Split by newlines first, then by spaces
                    potential_urls = []
                    for line in url_text.split('\n'):
                        line = line.strip()
                        if line:
                            # Check if it's multiple space-separated URLs
                            parts = line.split()
                            for part in parts:
                                part = part.strip()
                                # Accept any URL that looks valid
                                if part and (
                                    part.startswith(('http://', 'https://')) or 
                                    part.startswith('s3://') or
                                    part.startswith('/') or
                                    '.amazonaws.com' in part or
                                    '.s3.' in part
                                ):
                                    potential_urls.append(part)
                    
                    # If no URLs found by splitting, treat the whole thing as one URL
                    if not potential_urls and url_text and (
                        'http' in url_text or 
                        's3://' in url_text or 
                        '.amazonaws.com' in url_text
                    ):
                        potential_urls = [url_text]
                    
                    # Process each URL
                    for url in potential_urls:
                        url = url.strip()
                        if url and url not in attachments_data:  # Avoid duplicates
                            attachments_data.append(url)
                            self.stdout.write(f"Found attachment URL: {url[:80]}...")  # Show first 80 chars
            
            if attachments_data:
                self.stdout.write(self.style.SUCCESS(f"Row {index}: Found {len(attachments_data)} attachment URL(s)"))
            
            post_data['attachments_data'] = attachments_data
            
            return post_data
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error preparing post data: {str(e)}'))
            return None

    def safe_get(self, row, columns, default=None):
        """Safely get value from row by trying multiple column names"""
        if isinstance(columns, str):
            columns = [columns]
        
        for col in columns:
            if col in row and pd.notna(row[col]):
                return row[col]
        
        return default

    def extract_s3_key_from_url(self, url):
        """
        Extract S3 key/path from various S3 URL formats
        
        Handles:
        - https://bucket.s3.region.amazonaws.com/path/to/file.jpg
        - https://bucket.s3.amazonaws.com/path/to/file.jpg
        - https://s3.region.amazonaws.com/bucket/path/to/file.jpg
        - s3://bucket/path/to/file.jpg
        - /path/to/file.jpg (already a path)
        
        Returns the S3 key (path without bucket/domain)
        IMPORTANT: Removes 'media/' prefix to avoid duplication
        """
        import re
        from urllib.parse import urlparse
        
        if not url:
            return None
        
        # If it's already just a path, clean it
        if not url.startswith(('http://', 'https://', 's3://')):
            path = url.lstrip('/')
        else:
            # Parse the URL
            parsed = urlparse(url)
            
            # Handle s3:// URLs
            if parsed.scheme == 's3':
                # s3://bucket/path/to/file.jpg -> path/to/file.jpg
                path = parsed.path.lstrip('/')
            
            # Handle https:// URLs
            elif parsed.scheme in ('http', 'https'):
                # Extract path from different S3 URL patterns
                
                # Pattern 1: https://bucket.s3.region.amazonaws.com/path/to/file
                # Pattern 2: https://bucket.s3.amazonaws.com/path/to/file
                if '.s3.' in parsed.netloc and '.amazonaws.com' in parsed.netloc:
                    # Path is everything after the domain
                    path = parsed.path.lstrip('/')
                
                # Pattern 3: https://s3.region.amazonaws.com/bucket/path/to/file
                elif parsed.netloc.startswith('s3.') and '.amazonaws.com' in parsed.netloc:
                    # Remove bucket name from path
                    path_parts = parsed.path.lstrip('/').split('/', 1)
                    if len(path_parts) > 1:
                        path = path_parts[1]
                    else:
                        path = path_parts[0] if path_parts else ''
                
                # For other URLs, just return the path
                else:
                    path = parsed.path.lstrip('/')
            else:
                # Default: return path part
                path = parsed.path.lstrip('/') if hasattr(parsed, 'path') else url
        
        # CRITICAL: Remove 'media/' prefix if present to avoid duplication
        # Django will add 'media/' automatically when serving the file
        if path.startswith('media/'):
            path = path[6:]  # Remove 'media/' (6 characters)
            self.stdout.write(f"  Removed 'media/' prefix from path: {path}")
        
        return path

    def create_attachments(self, post, attachment_urls):
        """
        Create PostAttachment objects for existing S3 files
        IMPORTANT: Does not upload files - references existing S3 files
        """
        attachments = []
        
        self.stdout.write(f"Creating {len(attachment_urls)} attachment(s) for post {post.id}")
        
        for idx, url in enumerate(attachment_urls):
            try:
                # Extract S3 key from URL
                s3_key = self.extract_s3_key_from_url(url)
                
                if not s3_key:
                    self.stdout.write(
                        self.style.WARNING(f"✗ Could not extract S3 key from URL: {url}")
                    )
                    continue
                
                # Extract file name from S3 key
                file_name = s3_key.split('/')[-1].split('?')[0]  # Remove query params if any
                
                # Determine file type from file name
                file_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
                
                # Generate a title from file name
                title_base = file_name.rsplit('.', 1)[0]  # Remove extension
                title = title_base.replace('_', ' ').replace('-', ' ')
                
                # Truncate title to 200 characters (model field limit)
                if len(title) > 200:
                    title = title[:197] + '...'  # 197 chars + '...' = 200
                
                # IMPORTANT: We need to create the attachment carefully to avoid file system access
                # First, create the object with all fields EXCEPT the file
                attachment = PostAttachment.objects.create(
                    post=post,
                    title=title if title else f"Attachment {idx+1}",
                    file_type=file_type,
                    order=idx,
                    is_public=True,
                    size=0,  # Set to 0 since we can't get S3 file size without downloading
                    file=''  # Create with empty file first
                )
                
                # Now update ONLY the file field with the S3 key
                # This bypasses the save() method that tries to access file.size
                PostAttachment.objects.filter(id=attachment.id).update(file=s3_key)
                
                attachments.append(attachment)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Created attachment #{idx+1}: {file_name}")
                )
                self.stdout.write(f"  S3 Key: {s3_key}")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Failed to create attachment #{idx+1} for post {post.id}")
                )
                self.stdout.write(f"  Error: {str(e)}")
                self.stdout.write(f"  URL: {url}")
                import traceback
                self.stdout.write(f"  Traceback: {traceback.format_exc()}")
        
        if attachments:
            self.stdout.write(
                self.style.SUCCESS(f"Successfully created {len(attachments)} attachment(s) for post {post.id}")
            )
        
        return attachments