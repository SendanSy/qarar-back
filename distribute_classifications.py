from apps.content.models import Post
import random

# Get all posts
posts = list(Post.objects.all())
print(f"Found {len(posts)} posts to update with classifications")

# Available classifications
classifications = [
    ('decision', 'قرار'),
    ('circular', 'تعميم'),
    ('announcement', 'اعلان'),
    ('statement', 'بيان')
]

# Distribute the classifications evenly
for i, post in enumerate(posts):
    # Select classification in a rotating manner (i % 4)
    classification_code, classification_name = classifications[i % 4]
    
    # Update the post
    post.classification = classification_code
    post.save()
    
    print(f"Updated post #{post.id} by {post.author.username}: classification set to '{classification_name}' ({classification_code})")

print("\nFinished distributing classifications to all posts!") 