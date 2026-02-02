# Technical Explainer - Playto Engineering Challenge

This document explains the key technical decisions and solutions implemented in the Community Feed prototype.

## 1. The Tree: Nested Comment Modeling and Serialization

### Database Schema: Adjacency List Pattern

Comments are stored using the **Adjacency List** pattern, which is the simplest and most flexible approach for tree structures in relational databases:

```python
class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
    author = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
```

**Why Adjacency List?**
- **Simplicity**: Each comment has a single `parent_id` reference
- **Flexibility**: Unlimited nesting depth without schema changes
- **Query Flexibility**: Easy to find direct children of any node
- **Database Indexing**: `parent` and `post` fields are indexed for fast lookups

**Alternatives Considered:**
- **Nested Sets**: Faster reads but complex writes and maintenance
- **Closure Table**: Good read performance, but more complex implementation
- **Materialized Path**: Storing full path strings, but more storage overhead

### Serialization Strategy: Fetch All, Build in Memory

The critical challenge is efficiently loading a post with 50+ nested comments without triggering N+1 queries.

**The Problem with Default DRF Serialization:**
If we naively use nested serializers, DRF would:
1. Fetch the post (1 query)
2. For each comment, fetch its author (50 queries)
3. For each comment, fetch its likes (50 queries)
4. For each comment, fetch its children, and repeat...

Total: **O(N)** queries where N is the number of comments.

**The Solution: Single Query + In-Memory Tree Building**

```python
def get_comments(self, obj):
    """Efficiently serialize the comment tree."""
    # Step 1: Fetch ALL comments for this post in ONE query
    all_comments = list(
        obj.comments.select_related('author')
        .prefetch_related('likes')
        .order_by('created_at')
    )
    
    if not all_comments:
        return []
    
    # Step 2: Build lookup dictionary in memory
    comment_dict = {}
    root_comments = []
    
    for comment in all_comments:
        # Add computed like_count to avoid separate queries
        comment.like_count = comment.likes.count()
        comment_dict[comment.id] = comment
        comment.replies_list = []  # Initialize replies container
    
    # Step 3: Build tree by linking children to parents
    for comment in all_comments:
        if comment.parent:
            if comment.parent.id in comment_dict:
                comment_dict[comment.parent.id].replies_list.append(comment)
        else:
            root_comments.append(comment)
    
    # Step 4: Recursively serialize
    def serialize_comment(comment):
        return {
            'id': comment.id,
            'author': UserSerializer(comment.author).data,
            'content': comment.content,
            'like_count': comment.like_count,
            'replies': [serialize_comment(reply) for reply in comment.replies_list]
        }
    
    return [serialize_comment(comment) for comment in root_comments]
```

**Query Count Analysis:**
- Fetch post: 1 query
- Fetch all comments + authors + likes: 1 query (with `select_related` and `prefetch_related`)
- **Total: 2-3 queries maximum**, regardless of comment count

This approach scales from 10 to 10,000 comments without any code changes or performance degradation.

### Frontend: Recursive Component Rendering

The React frontend uses a recursive `CommentNode` component to render the tree:

```jsx
const CommentNode = ({ comment }) => {
  return (
    <div className="pl-4 border-l-2 border-gray-200">
      <CommentBody data={comment} />
      {comment.replies && comment.replies.map(reply => (
        <CommentNode key={reply.id} comment={reply} />
      ))}
    </div>
  );
};
```

## 2. The Math: 24-Hour Leaderboard Calculation

### Constraint
Calculate karma **dynamically from activity history**—no stored "Daily Karma" field.

### The QuerySet

```python
from django.db.models import Count, Q, F, Subquery, IntegerField
from django.utils import timezone
from datetime import timedelta

def get_leaderboard():
    cutoff = timezone.now() - timedelta(hours=24)
    
    # Calculate post likes karma (5 points each)
    post_karma_subquery = PostLike.objects.filter(
        created_at__gte=cutoff,
        post__author=OuterRef('pk')
    ).values('post__author').annotate(
        total=Count('id') * 5
    ).values('total')[:1]
    
    # Calculate comment likes karma (1 point each)
    comment_karma_subquery = CommentLike.objects.filter(
        created_at__gte=cutoff,
        comment__author=OuterRef('pk')
    ).values('comment__author').annotate(
        total=Count('id') * 1
    ).values('total')[:1]
    
    # Get top 5 users with total karma
    top_users = User.objects.annotate(
        post_karma=Subquery(post_karma_subquery, output_field=IntegerField()),
        comment_karma=Subquery(comment_karma_subquery, output_field=IntegerField())
    ).annotate(
        karma=(
            Coalesce(F('post_karma'), 0) + 
            Coalesce(F('comment_karma'), 0)
        )
    ).filter(karma__gt=0).order_by('-karma')[:5]
    
    return top_users
```

### SQL Equivalent

For PostgreSQL, the generated SQL would look like:

```sql
SELECT 
    u.id,
    u.username,
    (
        COALESCE(
            (SELECT COUNT(pl.id) * 5
             FROM api_postlike pl
             WHERE pl.created_at >= NOW() - INTERVAL '24 hours'
             AND pl.post_id IN (SELECT p.id FROM api_post p WHERE p.author_id = u.id)
            ), 0
        ) + COALESCE(
            (SELECT COUNT(cl.id) * 1
             FROM api_commentlike cl
             WHERE cl.created_at >= NOW() - INTERVAL '24 hours'
             AND cl.comment_id IN (SELECT c.id FROM api_comment c WHERE c.author_id = u.id)
            ), 0
        )
    ) AS karma
FROM api_user u
WHERE (
    COALESCE(
        (SELECT COUNT(pl.id) * 5 FROM api_postlike pl 
         WHERE pl.created_at >= NOW() - INTERVAL '24 hours' 
         AND pl.post_id IN (SELECT p.id FROM api_post p WHERE p.author_id = u.id)), 0
    ) + COALESCE(
        (SELECT COUNT(cl.id) * 1 FROM api_commentlike cl 
         WHERE cl.created_at >= NOW() - INTERVAL '24 hours' 
         AND cl.comment_id IN (SELECT c.id FROM api_comment c WHERE c.author_id = u.id)), 0
    )
) > 0
ORDER BY karma DESC
LIMIT 5;
```

### Key Design Decisions

1. **Time Window**: Uses `timezone.now() - timedelta(hours=24)` for a rolling 24-hour window
2. **Separate Subqueries**: Post likes and comment likes calculated separately for clarity
3. **Multiplication in Query**: `Count('id') * 5` done at database level for efficiency
4. **Filter Before Order**: `filter(karma__gt=0)` ensures only active users appear
5. **Limit 5**: Database-level limit prevents transferring unnecessary data

### Performance Characteristics

- **Single Database Round Trip**: Both subqueries run in one query via annotations
- **Indexed Fields**: `created_at`, `post__author`, `comment__author` all indexed
- **No Application-Level Filtering**: All filtering happens in the database
- **Scalable**: Adding users doesn't increase query complexity

## 3. The AI Audit: Real Bugs Caught and Fixed

### Example 1: Incorrect Leaderboard Calculation (Major Bug)

**AI-Generated Code:**
```python
def get_leaderboard(self, request):
    cutoff = timezone.now() - timedelta(hours=24)
    
    # AI suggested this approach - BUGGY!
    top_users = User.objects.annotate(
        karma=Count('posts__likes', filter=Q(posts__likes__created_at__gte=cutoff)) * 5 +
              Count('comments__likes', filter=Q(comments__likes__created_at__gte=cutoff)) * 1
    ).order_by('-karma')[:5]
    
    return Response([{
        'id': user.id,
        'username': user.username,
        'karma': user.karma
    } for user in top_users])
```

**The Problem:**
Django's `annotate()` with multiple `Count()` calls on reverse relations causes **double-counting** and incorrect aggregation. When you count `posts__likes` and `comments__likes` in the same annotate call, Django can produce cartesian products that inflate the counts.

**How I Fixed It:**
Used separate `Subquery()` calls to ensure each aggregation is calculated independently before being combined:

```python
# Correct approach: separate subqueries
post_karma_subquery = PostLike.objects.filter(
    created_at__gte=cutoff,
    post__author=OuterRef('pk')
).values('post__author').annotate(
    total=Count('id') * 5
).values('total')[:1]

comment_karma_subquery = CommentLike.objects.filter(
    created_at__gte=cutoff,
    comment__author=OuterRef('pk')
).values('comment__author').annotate(
    total=Count('id') * 1
).values('total')[:1]

top_users = User.objects.annotate(
    post_karma=Subquery(post_karma_subquery, output_field=IntegerField()),
    comment_karma=Subquery(comment_karma_subquery, output_field=IntegerField())
).annotate(
    karma=Coalesce(F('post_karma'), 0) + Coalesce(F('comment_karma'), 0)
).filter(karma__gt=0).order_by('-karma')[:5]
```

### Example 2: N+1 Query in Comment Serialization

**AI-Generated Code (Initial):**
```python
class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    def get_replies(self, obj):
        # AI suggested this - Triggers N+1 queries!
        return CommentSerializer(obj.replies.all(), many=True).data
```

**The Problem:**
When `obj.replies.all()` is called for each comment in a nested serializer, Django fires a separate query for each comment's replies. With 50 comments, this means 50+ database queries.

**How I Fixed It:**
Modified the parent serializer to:
1. Fetch ALL comments in a single query upfront
2. Build the tree structure in Python memory
3. Serialize the pre-built tree

```python
def get_comments(self, obj):
    # Single query for ALL comments
    all_comments = list(
        obj.comments.select_related('author')
        .prefetch_related('likes')
        .order_by('created_at')
    )
    
    # Build tree in memory (O(N) operation)
    comment_dict = {c.id: c for c in all_comments}
    for comment in all_comments:
        comment.replies_list = []
    for comment in all_comments:
        if comment.parent_id:
            comment_dict[comment.parent_id].replies_list.append(comment)
    
    # Recursive serialization
    def serialize(c):
        return {
            'id': c.id,
            'replies': [serialize(r) for r in c.replies_list]
        }
    
    return [serialize(c) for c in all_comments if not c.parent_id]
```

### Example 3: Race Condition in Like Toggle

**AI-Generated Code (Naive):**
```python
@action(detail=True, methods=['post'])
def like(self, request, pk=None):
    post = self.get_object()
    user = request.user
    
    # BUG: Check-then-act pattern causes race conditions
    if PostLike.objects.filter(user=user, post=post).exists():
        PostLike.objects.filter(user=user, post=post).delete()
        return Response({'liked': False})
    else:
        PostLike.objects.create(user=user, post=post)
        return Response({'liked': True}
```

**The Problem:**
Between the check and the action, another request could create the like, resulting in:
- Two likes created (double karma)
- Or trying to delete a non-existent like

**How I Fixed It:**
1. Used `unique_together` constraint at database level
2. Added `try/except IntegrityError` handling
3. Made the operation idempotent

```python
@action(detail=True, methods=['post'])
def like(self, request, pk=None):
    post = self.get_object()
    user = request.user
    
    existing_like = PostLike.objects.filter(user=user, post=post).first()
    
    if existing_like:
        existing_like.delete()
        liked = False
    else:
        try:
            PostLike.objects.create(user=user, post=post)
            liked = True
        except IntegrityError:
            # Race condition: like was created by another request
            # Treat as success (idempotent operation)
            liked = True
    
    return Response({
        'liked': liked,
        'like_count': post.likes.count()
    })
```

The `unique_together = ('user', 'post')` in the model Meta class ensures that even if two requests pass the check simultaneously, only one can insert. The second insert will raise `IntegrityError`, which we catch and handle gracefully.

## Summary

| Challenge | Solution | Query Count |
|-----------|----------|-------------|
| Nested Comments | Fetch all + in-memory tree build | O(1) |
| Leaderboard | Dynamic calculation with Subqueries | O(1) |
| Double-Likes | Database constraints + IntegrityError handling | N/A |

All three technical constraints were met without compromising on code clarity or maintainability.
