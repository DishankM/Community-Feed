from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model."""
    pass


class Post(models.Model):
    """Post model representing a text post in the feed."""
    author = models.ForeignKey(
        User,
        related_name='posts',
        on_delete=models.CASCADE
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.author.username}: {self.content[:50]}"


class Comment(models.Model):
    """Comment model with threading support (adjacency list pattern)."""
    post = models.ForeignKey(
        Post,
        related_name='comments',
        on_delete=models.CASCADE
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='replies',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        related_name='comments',
        on_delete=models.CASCADE
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['post']),
            models.Index(fields=['parent']),
        ]
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.id}"


class PostLike(models.Model):
    """Like model for posts with concurrency control."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    post = models.ForeignKey(
        Post,
        related_name='likes',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Database-level constraint prevents double-likes
        unique_together = ('user', 'post')
        indexes = [
            models.Index(fields=['post']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} liked Post {self.post.id}"


class CommentLike(models.Model):
    """Like model for comments with concurrency control."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    comment = models.ForeignKey(
        Comment,
        related_name='likes',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Database-level constraint prevents double-likes
        unique_together = ('user', 'comment')
        indexes = [
            models.Index(fields=['comment']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} liked Comment {self.comment.id}"
