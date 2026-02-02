from rest_framework import serializers
from django.db.models import Count
from .models import User, Post, Comment, PostLike, CommentLike


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    class Meta:
        model = User
        fields = ['id', 'username']


class CommentSerializer(serializers.ModelSerializer):
    """Nested comment serializer with recursive replies."""
    author = UserSerializer(read_only=True)
    like_count = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'post', 'parent', 'author', 'content', 'created_at', 'like_count', 'replies']

    def get_like_count(self, obj):
        """Get like count for this comment."""
        return obj.likes.count()

    def get_replies(self, obj):
        """Recursively serialize replies - called only for root comments."""
        # Only serialize direct children, they will serialize their children
        replies = obj.replies.select_related('author').prefetch_related('likes')
        return CommentSerializer(replies, many=True, context=self.context).data


class PostSerializer(serializers.ModelSerializer):
    """Basic post serializer for list views."""
    author = UserSerializer(read_only=True)
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'author', 'content', 'created_at', 'like_count', 'comment_count']

    def get_like_count(self, obj):
        """Get like count for this post."""
        return obj.likes.count()

    def get_comment_count(self, obj):
        """Get total comment count for this post."""
        return obj.comments.count()


class PostDetailSerializer(serializers.ModelSerializer):
    """Detailed post serializer with full nested comment tree."""
    author = UserSerializer(read_only=True)
    like_count = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'author', 'content', 'created_at', 'like_count', 'comments', 'user_has_liked']

    def get_like_count(self, obj):
        """Get like count for this post."""
        return obj.likes.count()

    def get_comments(self, obj):
        """
        Efficiently serialize the comment tree.
        
        Strategy: Fetch ALL comments for the post in a single query,
        then build the tree structure in Python memory.
        This avoids the N+1 query problem.
        """
        # Get request from context for user authentication check
        request = self.context.get('request')
        user_id = request.user.id if request and request.user.is_authenticated else None
        
        # Step 1: Fetch all comments for this post with related data
        all_comments = list(
            obj.comments.select_related('author')
            .prefetch_related('likes')
            .order_by('created_at')
        )
        
        if not all_comments:
            return []
        
        # Step 2: Build lookup dictionary and tree structure in memory
        comment_dict = {}
        root_comments = []
        
        # Create a dictionary mapping comment ID to comment object
        for comment in all_comments:
            # Add like count to comment object for serialization
            comment.like_count = comment.likes.count()
            comment_dict[comment.id] = comment
            comment.replies_list = []  # Initialize replies list
        
        # Step 3: Build the tree by linking children to parents
        for comment in all_comments:
            if comment.parent:
                # This is a reply, add to parent's replies
                if comment.parent.id in comment_dict:
                    comment_dict[comment.parent.id].replies_list.append(comment)
            else:
                # This is a root comment
                root_comments.append(comment)
        
        # Step 4: Recursively serialize the tree
        def serialize_comment(comment):
            """Recursively serialize a comment and its replies."""
            # Serialize replies
            replies_data = []
            for reply in comment.replies_list:
                replies_data.append(serialize_comment(reply))
            
            # Build the serialized data
            return {
                'id': comment.id,
                'post': comment.post_id,
                'parent': comment.parent_id,
                'author': UserSerializer(comment.author).data,
                'content': comment.content,
                'created_at': comment.created_at.isoformat(),
                'like_count': comment.like_count,
                'replies': replies_data,
                'user_has_liked': user_id in [like.user_id for like in comment.likes.all()] if user_id else False
            }
        
        # Serialize all root comments
        return [serialize_comment(comment) for comment in root_comments]

    def get_user_has_liked(self, obj):
        """Check if the current user has liked this post."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class PostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new posts (excludes read-only fields)."""
    class Meta:
        model = Post
        fields = ['content']


class LikeToggleSerializer(serializers.Serializer):
    """Serializer for like toggle response."""
    liked = serializers.BooleanField()
    like_count = serializers.IntegerField()
    karma_earned = serializers.IntegerField()


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new comments."""
    class Meta:
        model = Comment
        fields = ['post', 'parent', 'content']


class LeaderboardEntrySerializer(serializers.Serializer):
    """Serializer for leaderboard entries."""
    id = serializers.IntegerField()
    username = serializers.CharField()
    karma = serializers.IntegerField()


class LeaderboardSerializer(serializers.Serializer):
    """Serializer for the leaderboard response."""
    users = LeaderboardEntrySerializer(many=True)
    last_updated = serializers.DateTimeField()
