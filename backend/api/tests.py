"""
Tests for the Community Feed API.

These tests verify the core functionality including:
- Post creation and retrieval
- Threaded comments (nested structure)
- Like functionality with concurrency handling
- Leaderboard calculation with 24-hour window

Run with: python manage.py test
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.db import IntegrityError
from rest_framework.test import APITestCase
from rest_framework import status

from api.models import User, Post, Comment, PostLike, CommentLike
from api.views import LeaderboardViewSet


class UserModelTest(TestCase):
    """Test User model creation."""
    
    def test_create_user(self):
        """Test basic user creation."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)


class PostModelTest(TestCase):
    """Test Post model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='poster',
            password='pass123'
        )
    
    def test_create_post(self):
        """Test post creation."""
        post = Post.objects.create(
            author=self.user,
            content='Test post content'
        )
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.content, 'Test post content')
        self.assertIsNotNone(post.created_at)
    
    def test_post_str(self):
        """Test post string representation."""
        post = Post.objects.create(
            author=self.user,
            content='A' * 100  # Long content
        )
        self.assertIn('Test post content', str(post))  # Truncated to 50 chars


class CommentModelTest(TestCase):
    """Test Comment model with threading."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='commenter',
            password='pass123'
        )
        self.post = Post.objects.create(
            author=self.user,
            content='Test post'
        )
    
    def test_create_root_comment(self):
        """Test creating a root comment (no parent)."""
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Root comment'
        )
        self.assertIsNone(comment.parent)
        self.assertEqual(comment.content, 'Root comment')
    
    def test_create_nested_comment(self):
        """Test creating a nested comment (reply)."""
        parent = Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Parent comment'
        )
        child = Comment.objects.create(
            post=self.post,
            parent=parent,
            author=self.user,
            content='Child comment'
        )
        self.assertEqual(child.parent, parent)
        self.assertIn(child, parent.replies.all())
    
    def test_deeply_nested_comments(self):
        """Test creating deeply nested comment thread."""
        comments = []
        for i in range(5):
            parent = comments[-1] if comments else None
            comment = Comment.objects.create(
                post=self.post,
                parent=parent,
                author=self.user,
                content=f'Level {i} comment'
            )
            comments.append(comment)
        
        # Verify the chain
        for i in range(1, len(comments)):
            self.assertEqual(comments[i].parent, comments[i - 1])


class LikeModelTest(TestCase):
    """Test Like models with concurrency control."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='liker',
            password='pass123'
        )
        self.post_author = User.objects.create_user(
            username='postauthor',
            password='pass123'
        )
        self.post = Post.objects.create(
            author=self.post_author,
            content='Test post to like'
        )
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.post_author,
            content='Test comment'
        )
    
    def test_create_post_like(self):
        """Test creating a post like."""
        like = PostLike.objects.create(user=self.user, post=self.post)
        self.assertEqual(like.user, self.user)
        self.assertEqual(like.post, self.post)
    
    def test_post_like_uniqueness(self):
        """Test that same user cannot like same post twice."""
        PostLike.objects.create(user=self.user, post=self.post)
        
        with self.assertRaises(IntegrityError):
            PostLike.objects.create(user=self.user, post=self.post)
    
    def test_create_comment_like(self):
        """Test creating a comment like."""
        like = CommentLike.objects.create(user=self.user, comment=self.comment)
        self.assertEqual(like.user, self.user)
        self.assertEqual(like.comment, self.comment)
    
    def test_comment_like_uniqueness(self):
        """Test that same user cannot like same comment twice."""
        CommentLike.objects.create(user=self.user, comment=self.comment)
        
        with self.assertRaises(IntegrityError):
            CommentLike.objects.create(user=self.user, comment=self.comment)


class LeaderboardCalculationTest(TestCase):
    """
    Test leaderboard karma calculation.
    
    This is the most critical test as it verifies the 24-hour
    time window constraint for the leaderboard.
    """
    
    def setUp(self):
        """Set up test data with users who have varying karma."""
        self.now = timezone.now()
        self.cutoff = self.now - timedelta(hours=24)
        self.just_before_cutoff = self.cutoff - timedelta(seconds=1)
        
        # Create users
        self.user1 = User.objects.create(username='user1')
        self.user2 = User.objects.create(username='user2')
        self.user3 = User.objects.create(username='user3')
        
        # Create posts
        self.post1 = Post.objects.create(
            author=self.user1,
            content='Post by user1'
        )
        self.post2 = Post.objects.create(
            author=self.user2,
            content='Post by user2'
        )
        
        # Create comments
        self.comment1 = Comment.objects.create(
            post=self.post1,
            author=self.user2,
            content='Comment by user2 on user1 post'
        )
        
    def test_leaderboard_calculates_karma_correctly(self):
        """
        Test that karma is calculated correctly for likes.
        
        - 1 Post Like = 5 Karma
        - 1 Comment Like = 1 Karma
        """
        # User1 gets 5 karma (1 post like)
        PostLike.objects.create(
            user=self.user2,  # Likers
            post=self.post1,
            created_at=self.now
        )
        
        # User2 gets 1 karma (1 comment like)
        CommentLike.objects.create(
            user=self.user3,
            comment=self.comment1,
            created_at=self.now
        )
        
        # User2 also gets 5 karma (their post was liked)
        PostLike.objects.create(
            user=self.user3,
            post=self.post2,
            created_at=self.now
        )
        
        # Manually calculate expected karma
        expected_user1_karma = 5  # From post1 being liked
        expected_user2_karma = 6  # 5 from post2 + 1 from comment1
        
        # Verify through the API
        from api.serializers import LeaderboardSerializer
        
        view = LeaderboardViewSet()
        view.request = type('Request', (), {'user': self.user1})()
        
        # The view's list method should return correct order
        response = view.list(request=type('Request', (), {'user': self.user1})())
        
        # Check that user2 has more karma than user1
        data = response.data['users']
        user1_karma = next((u['karma'] for u in data if u['id'] == self.user1.id), 0)
        user2_karma = next((u['karma'] for u in data if u['id'] == self.user2.id), 0)
        
        self.assertEqual(user1_karma, expected_user1_karma)
        self.assertEqual(user2_karma, expected_user2_karma)
    
    def test_leaderboard_respects_24h_window(self):
        """Test that likes older than 24 hours are NOT counted."""
        # Create a like in the past (should NOT count)
        PostLike.objects.create(
            user=self.user1,
            post=self.post2,
            created_at=self.just_before_cutoff  # Before 24h window
        )
        
        # Create a like in the window (should count)
        PostLike.objects.create(
            user=self.user2,
            post=self.post1,
            created_at=self.now  # Within 24h window
        )
        
        # Fetch leaderboard
        view = LeaderboardViewSet()
        response = view.list(request=type('Request', (), {'user': self.user1})())
        
        data = response.data['users']
        
        # Only user2 should have karma
        user1_karma = next((u['karma'] for u in data if u['id'] == self.user1.id), 0)
        user2_karma = next((u['karma'] for u in data if u['id'] == self.user2.id), 0)
        
        self.assertEqual(user1_karma, 0)
        self.assertEqual(user2_karma, 5)
    
    def test_leaderboard_returns_top_5(self):
        """Test that leaderboard returns at most 5 users."""
        # Create 7 users with varying karma
        users = []
        for i in range(7):
            user = User.objects.create(username=f'testuser{i}')
            users.append(user)
            PostLike.objects.create(
                user=user,
                post=self.post1,
                created_at=self.now
            )
        
        response = self.client.get('/api/leaderboard/')
        data = response.data['users']
        
        # Should only return top 5
        self.assertLessEqual(len(data), 5)
        
        # Users should be ordered by karma descending
        karmas = [u['karma'] for u in data]
        self.assertEqual(karmas, sorted(karmas, reverse=True))
    
    def test_leaderboard_excludes_zero_karma_users(self):
        """Test that users with 0 karma are not in leaderboard."""
        # Create users with no likes
        User.objects.create(username='inactive_user')
        
        response = self.client.get('/api/leaderboard/')
        data = response.data['users']
        
        # Only active users should be in results
        for entry in data:
            self.assertGreater(entry['karma'], 0)


class APIEndpointsTest(APITestCase):
    """Test API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.post = Post.objects.create(
            author=self.user,
            content='Test post content'
        )
    
    def test_list_posts(self):
        """Test GET /api/posts/."""
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_post(self):
        """Test POST /api/posts/."""
        self.client.force_authenticate(user=self.user)
        data = {'content': 'New post content'}
        response = self.client.post('/api/posts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)
    
    def test_retrieve_post_with_comments(self):
        """Test GET /api/posts/{id}/ includes comments."""
        # Create a comment
        Comment.objects.create(
            post=self.post,
            author=self.user,
            content='Test comment'
        )
        
        response = self.client.get(f'/api/posts/{self.post.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('comments', response.data)
        self.assertEqual(len(response.data['comments']), 1)
    
    def test_like_post(self):
        """Test POST /api/posts/{id}/like/."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/posts/{self.post.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('liked', response.data)
        self.assertIn('like_count', response.data)
    
    def test_like_toggle(self):
        """Test that liking twice toggles off."""
        self.client.force_authenticate(user=self.user)
        
        # First like
        response1 = self.client.post(f'/api/posts/{self.post.id}/like/')
        self.assertTrue(response1.data['liked'])
        self.assertEqual(response1.data['like_count'], 1)
        
        # Unlike
        response2 = self.client.post(f'/api/posts/{self.post.id}/like/')
        self.assertFalse(response2.data['liked'])
        self.assertEqual(response2.data['like_count'], 0)
    
    def test_leaderboard_endpoint(self):
        """Test GET /api/leaderboard/."""
        response = self.client.get('/api/leaderboard/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('users', response.data)
        self.assertIn('last_updated', response.data)


class N1QueryTest(TestCase):
    """
    Test that comment retrieval does not cause N+1 queries.
    
    This test verifies the optimized comment loading strategy.
    """
    
    def setUp(self):
        """Set up test data with many comments."""
        self.user = User.objects.create_user(
            username='commenter',
            password='pass123'
        )
        self.post = Post.objects.create(
            author=self.user,
            content='Test post'
        )
        
        # Create 20 comments in a nested structure
        parent = None
        for i in range(20):
            comment = Comment.objects.create(
                post=self.post,
                parent=parent,
                author=self.user,
                content=f'Comment {i}'
            )
            parent = comment  # Next comment is a reply to this one
    
    def test_comment_query_count(self):
        """
        Verify that loading a post with comments uses constant queries.
        
        This test checks that our optimized serialization strategy
        (fetch all + build tree in memory) is being used.
        """
        from django.db import connection
        
        # Clear query log
        connection.queries_log.clear()
        
        # Fetch the post with comments
        response = self.client.get(f'/api/posts/{self.post.id}/')
        
        # Count queries
        query_count = len(connection.queries)
        
        # Should be very few queries (2-3 max), not O(N) where N = number of comments
        # The 20 nested comments should not cause 20+ queries
        self.assertLess(query_count, 10, 
            f"Expected < 10 queries for 20 comments, got {query_count}. "
            "N+1 query problem detected!"
        )
        
        # Verify all comments are returned
        comments = response.data['comments']
        self.assertEqual(len(comments), 1)  # 1 root comment with 19 children
        
        # Verify nesting depth
        def count_depth(comment):
            if not comment.get('replies'):
                return 1
            return 1 + max(count_depth(r) for r in comment['replies'])
        
        depth = count_depth(comments[0])
        self.assertEqual(depth, 20)  # Should have 20 levels of nesting
