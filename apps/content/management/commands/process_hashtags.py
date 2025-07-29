"""
Management command to process hashtags for existing posts.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.content.models.post import Post
from apps.content.models.classification import HashTag


class Command(BaseCommand):
    help = 'Process and extract hashtags for existing posts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--post-id',
            type=str,
            help='Process hashtags for a specific post ID',
        )
        parser.add_argument(
            '--status',
            type=str,
            default='published',
            help='Process posts with specific status (default: published)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reprocessing even if hashtags already exist',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes',
        )

    def handle(self, *args, **options):
        """Process hashtags for posts."""
        
        # Get posts to process
        if options['post_id']:
            posts = Post.objects.filter(id=options['post_id'])
            if not posts.exists():
                self.stdout.write(
                    self.style.ERROR(f'Post with ID {options["post_id"]} not found')
                )
                return
        else:
            posts = Post.objects.filter(status=options['status'])
            
        if not options['force']:
            # Only process posts that don't have hashtags yet
            posts = posts.filter(hashtags__isnull=True).distinct()
        
        total_posts = posts.count()
        self.stdout.write(f'Found {total_posts} posts to process')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            
            for post in posts[:10]:  # Show first 10 for preview
                content = f"{post.content} {post.content_ar} {post.summary} {post.summary_ar}"
                hashtags = HashTag.extract_from_content(content)
                self.stdout.write(f'Post "{post.title[:50]}..." would get hashtags: {hashtags}')
            
            if total_posts > 10:
                self.stdout.write(f'... and {total_posts - 10} more posts')
            return

        # Process posts
        processed_count = 0
        hashtag_count = 0
        
        with transaction.atomic():
            for post in posts:
                try:
                    # Get old hashtag count
                    old_hashtags = set(post.hashtags.values_list('name', flat=True))
                    
                    # Process hashtags
                    post._process_hashtags()
                    
                    # Get new hashtag count
                    new_hashtags = set(post.hashtags.values_list('name', flat=True))
                    
                    hashtags_added = new_hashtags - old_hashtags
                    hashtags_removed = old_hashtags - new_hashtags
                    
                    if hashtags_added or hashtags_removed:
                        self.stdout.write(
                            f'Post "{post.title[:50]}...": '
                            f'+{len(hashtags_added)} -{len(hashtags_removed)} hashtags'
                        )
                        if hashtags_added:
                            self.stdout.write(f'  Added: {list(hashtags_added)}')
                        if hashtags_removed:
                            self.stdout.write(f'  Removed: {list(hashtags_removed)}')
                    
                    processed_count += 1
                    hashtag_count += len(new_hashtags)
                    
                    if processed_count % 100 == 0:
                        self.stdout.write(f'Processed {processed_count}/{total_posts} posts...')
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error processing post {post.id}: {str(e)}')
                    )
                    continue

        # Update hashtag post counts
        self.stdout.write('Updating hashtag post counts...')
        for hashtag in HashTag.objects.all():
            hashtag.update_post_count()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {processed_count} posts with {hashtag_count} total hashtags'
            )
        )