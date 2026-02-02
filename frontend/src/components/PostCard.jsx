import { useState } from 'react';
import { postsAPI } from '../api';
import CommentList from './CommentList';

function PostCard({ post, expanded, refreshFeed }) {
  const [isLiked, setIsLiked] = useState(post.user_has_liked || false);
  const [likeCount, setLikeCount] = useState(post.like_count);
  const [showComments, setShowComments] = useState(expanded);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleLike = async (e) => {
    e.stopPropagation();
    try {
      const response = await postsAPI.like(post.id);
      setIsLiked(response.data.liked);
      setLikeCount(response.data.like_count);
    } catch (error) {
      console.error('Error liking post:', error);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 hover:shadow-md transition-shadow">
      {/* Post Header */}
      <div className="flex items-center space-x-3 mb-3">
        <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">
          {post.author?.username?.charAt(0).toUpperCase() || 'U'}
        </div>
        <div>
          <h3 className="font-semibold text-gray-800">
            {post.author?.username || 'Unknown User'}
          </h3>
          <p className="text-sm text-gray-500">
            {formatDate(post.created_at)}
          </p>
        </div>
      </div>

      {/* Post Content */}
      <p className="text-gray-700 mb-4 whitespace-pre-wrap">
        {post.content}
      </p>

      {/* Post Actions */}
      <div className="flex items-center space-x-4 pt-3 border-t border-gray-100">
        <button
          onClick={handleLike}
          className={`flex items-center space-x-2 ${
            isLiked ? 'text-red-500' : 'text-gray-500 hover:text-red-500'
          }`}
        >
          <svg
            className="w-5 h-5"
            fill={isLiked ? 'currentColor' : 'none'}
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
            />
          </svg>
          <span>{likeCount}</span>
        </button>

        <button
          onClick={() => setShowComments(!showComments)}
          className={`flex items-center space-x-2 ${
            showComments ? 'text-blue-500' : 'text-gray-500 hover:text-blue-500'
          }`}
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          <span>{post.comment_count || 0}</span>
        </button>
      </div>

      {/* Comments Section */}
      {showComments && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <CommentList
            post={post}
            comments={post.comments || []}
            refreshFeed={refreshFeed}
          />
        </div>
      )}
    </div>
  );
}

export default PostCard;
