from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import IntegrityError, transaction
from django.db.models import Count, Q, F, Subquery, OuterRef, IntegerField
from django.utils import timezone
from datetime import timedelta
from .models import User, Post, Comment, PostLike, CommentLike
from .serializers import (
    PostSerializer,
    PostDetailSerializer,
    PostCreateSerializer,
    CommentCreateSerializer,
    CommentSerializer,
    LikeToggleSerializer,
    LeaderboardSerializer,
    UserSerializer,
)


class PostViewSet(viewsets.ModelViewSet):
    """ViewSet for Post CRUD operations."""
    queryset = Post.objects.all()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return PostDetailSerializer
        elif self.action == 'create':
            return PostCreateSerializer
        return PostSerializer
    
    def perform_create(self, serializer):
        """
        Create a new post with the current user as author.
        For demo purposes, creates a default user if none exists.
        """
        user = self.request.user
        # For demo: create default user if not authenticated
        if not user or not user.is_authenticated:
            user, _ = User.objects.get_or_create(
                username='demo_user',
                defaults={'password': 'demo123'}
            )
        serializer.save(author=user)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """
        Toggle like on a post.
        
        Handles concurrency by catching IntegrityError and returning
        appropriate response (idempotent operation).
        """
        post = self.get_object()
        user = request.user
        
        # For demo purposes, create a default user if not authenticated
        if not user or not user.is_authenticated:
            user, _ = User.objects.get_or_create(
                username='demo_user',
                defaults={'password': 'demo123'}
            )
        
        # Check if user already liked this post
        existing_like = PostLike.objects.filter(user=user, post=post).first()
        
        if existing_like:
            # Unlike: remove the like
            existing_like.delete()
            liked = False
            karma_change = -5  # Remove karma
        else:
            # Like: try to create the like
            try:
                with transaction.atomic():
                    # Select for update prevents race conditions
                    # But unique_together constraint is the primary safeguard
                    PostLike.objects.create(user=user, post=post)
                liked = True
                karma_change = 5  # Add karma
            except IntegrityError:
                # Race condition: another request created the like first
                # Treat as successful (idempotent)
                liked = True
                karma_change = 5
        
        # Get updated like count
        like_count = PostLike.objects.filter(post=post).count()
        
        response_data = {
            'liked': liked,
            'like_count': like_count,
            'karma_earned': karma_change if liked else karma_change
        }
        
        return Response(response_data)


class CommentViewSet(viewsets.ModelViewSet):
    """ViewSet for Comment CRUD operations."""
    queryset = Comment.objects.all()
    
    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'create':
            return CommentCreateSerializer
        return CommentSerializer
    
    def perform_create(self, serializer):
        """
        Create a new comment with the current user as author.
        For demo purposes, creates a default user if none exists.
        """
        user = self.request.user
        # For demo: create default user if not authenticated
        if not user or not user.is_authenticated:
            user, _ = User.objects.get_or_create(
                username='demo_user',
                defaults={'password': 'demo123'}
            )
        serializer.save(author=user)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """
        Toggle like on a comment.
        
        Handles concurrency by catching IntegrityError and returning
        appropriate response (idempotent operation).
        """
        comment = self.get_object()
        user = request.user
        
        # For demo purposes, create a default user if not authenticated
        if not user or not user.is_authenticated:
            user, _ = User.objects.get_or_create(
                username='demo_user',
                defaults={'password': 'demo123'}
            )
        
        # Check if user already liked this comment
        existing_like = CommentLike.objects.filter(user=user, comment=comment).first()
        
        if existing_like:
            # Unlike: remove the like
            existing_like.delete()
            liked = False
            karma_change = -1  # Remove karma
        else:
            # Like: try to create the like
            try:
                with transaction.atomic():
                    CommentLike.objects.create(user=user, comment=comment)
                liked = True
                karma_change = 1  # Add karma
            except IntegrityError:
                # Race condition: another request created the like first
                liked = True
                karma_change = 1
        
        # Get updated like count
        like_count = CommentLike.objects.filter(comment=comment).count()
        
        response_data = {
            'liked': liked,
            'like_count': like_count,
            'karma_earned': karma_change if liked else karma_change
        }
        
        return Response(response_data)


class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for the leaderboard endpoint.
    
    Calculates karma dynamically from activity in the last 24 hours.
    Does not use a stored "Daily Karma" field.
    """
    serializer_class = LeaderboardSerializer
    
    def list(self, request, *args, **kwargs):
        """
        Get top 5 users by karma earned in the last 24 hours.
        
        Karma Calculation:
        - 1 Like on a Post = 5 Karma
        - 1 Like on a Comment = 1 Karma
        
        Time Window: Last 24 hours from current time.
        """
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
        
        # Get top 5 users with their total karma
        top_users = User.objects.annotate(
            post_karma=Subquery(
                post_karma_subquery,
                output_field=IntegerField()
            ),
            comment_karma=Subquery(
                comment_karma_subquery,
                output_field=IntegerField()
            )
        ).annotate(
            karma=(
                (F('post_karma') if F('post_karma') is not None else 0) +
                (F('comment_karma') if F('comment_karma') is not None else 0)
            )
        ).filter(karma__gt=0).order_by('-karma')[:5]
        
        # Build response
        leaderboard_data = {
            'users': [
                {'id': user.id, 'username': user.username, 'karma': user.karma}
                for user in top_users
            ],
            'last_updated': timezone.now()
        }
        
        serializer = LeaderboardSerializer(leaderboard_data)
        return Response(serializer.data)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for User read operations (for testing)."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
