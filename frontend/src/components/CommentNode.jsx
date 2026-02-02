import { commentsAPI } from '../api';

function CommentNode({
  comment,
  postId,
  replyingTo,
  setReplyingTo,
  replyContent,
  setReplyContent,
  handleReply,
  loading,
  refreshFeed,
  formatDate,
}) {
  const [isLiked, setIsLiked] = useState(comment.user_has_liked || false);
  const [likeCount, setLikeCount] = useState(comment.like_count || 0);
  const [showReplies, setShowReplies] = useState(true);

  const handleLike = async (e) => {
    e.stopPropagation();
    try {
      const response = await commentsAPI.like(comment.id);
      setIsLiked(response.data.liked);
      setLikeCount(response.data.like_count);
    } catch (error) {
      console.error('Error liking comment:', error);
    }
  };

  return (
    <div className="space-y-2">
      {/* Comment Content */}
      <div className="flex space-x-3">
        {/* Thread Line */}
        <div className="flex flex-col items-center">
          <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-gray-600 text-sm font-bold flex-shrink-0">
            {comment.author?.username?.charAt(0).toUpperCase() || 'U'}
          </div>
          <button
            onClick={() => setShowReplies(!showReplies)}
            className="w-0.5 flex-1 bg-gray-200 hover:bg-gray-300 transition-colors"
          />
        </div>

        {/* Comment Body */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            <span className="font-medium text-gray-800 text-sm">
              {comment.author?.username || 'Unknown User'}
            </span>
            <span className="text-xs text-gray-500">
              {formatDate(comment.created_at)}
            </span>
          </div>
          <p className="text-gray-700 text-sm mb-2">{comment.content}</p>

          {/* Comment Actions */}
          <div className="flex items-center space-x-4">
            <button
              onClick={handleLike}
              className={`flex items-center space-x-1 text-xs ${
                isLiked ? 'text-red-500' : 'text-gray-500 hover:text-red-500'
              }`}
            >
              <svg
                className="w-4 h-4"
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
              onClick={() =>
                setReplyingTo(replyingTo === comment.id ? null : comment.id)
              }
              className="text-xs text-gray-500 hover:text-blue-500"
            >
              Reply
            </button>
          </div>

          {/* Reply Form */}
          {replyingTo === comment.id && (
            <form
              onSubmit={(e) => handleReply(e, comment.id)}
              className="mt-3 mb-3"
            >
              <div className="flex space-x-2">
                <textarea
                  value={replyContent}
                  onChange={(e) => setReplyContent(e.target.value)}
                  placeholder={`Replying to ${comment.author?.username}...`}
                  className="flex-1 p-2 border border-gray-200 rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  rows={2}
                  autoFocus
                />
              </div>
              <div className="flex justify-end space-x-2 mt-2">
                <button
                  type="button"
                  onClick={() => {
                    setReplyingTo(null);
                    setReplyContent('');
                  }}
                  className="px-3 py-1 text-sm text-gray-500 hover:text-gray-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || !replyContent.trim()}
                  className={`px-3 py-1 text-sm rounded font-medium transition-colors ${
                    loading || !replyContent.trim()
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-500 text-white hover:bg-blue-600'
                  }`}
                >
                  Reply
                </button>
              </div>
            </form>
          )}

          {/* Nested Replies */}
          {showReplies && comment.replies && comment.replies.length > 0 && (
            <div className="mt-3 space-y-3 pl-4 border-l-2 border-gray-100">
              {comment.replies.map((reply) => (
                <CommentNode
                  key={reply.id}
                  comment={reply}
                  postId={postId}
                  replyingTo={replyingTo}
                  setReplyingTo={setReplyingTo}
                  replyContent={replyContent}
                  setReplyContent={setReplyContent}
                  handleReply={handleReply}
                  loading={loading}
                  refreshFeed={refreshFeed}
                  formatDate={formatDate}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

import { useState } from 'react';

export default CommentNode;
