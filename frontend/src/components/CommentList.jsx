import { useState } from 'react';
import { commentsAPI, postsAPI } from '../api';
import CommentNode from './CommentNode';

function CommentList({ post, comments, refreshFeed }) {
  const [newComment, setNewComment] = useState('');
  const [replyingTo, setReplyingTo] = useState(null);
  const [replyContent, setReplyContent] = useState('');
  const [loading, setLoading] = useState(false);

  const handleCreateComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    setLoading(true);
    try {
      // Backend handles author assignment automatically
      await commentsAPI.create({
        post: post.id,
        parent: null,
        content: newComment.trim(),
      });
      setNewComment('');
      refreshFeed();
    } catch (error) {
      console.error('Error creating comment:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReply = async (e, parentId) => {
    e.preventDefault();
    if (!replyContent.trim()) return;

    setLoading(true);
    try {
      // Backend handles author assignment automatically
      await commentsAPI.create({
        post: post.id,
        parent: parentId,
        content: replyContent.trim(),
      });
      setReplyContent('');
      setReplyingTo(null);
      refreshFeed();
    } catch (error) {
      console.error('Error creating reply:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-4">
      {/* New Comment Form */}
      <form onSubmit={handleCreateComment} className="mb-4">
        <div className="flex space-x-3">
          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
            Y
          </div>
          <div className="flex-1">
            <textarea
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              placeholder="Write a comment..."
              className="w-full p-2 border border-gray-200 rounded resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              rows={2}
            />
            <div className="flex justify-end mt-2">
              <button
                type="submit"
                disabled={loading || !newComment.trim()}
                className={`px-3 py-1 text-sm rounded font-medium transition-colors ${
                  loading || !newComment.trim()
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-500 text-white hover:bg-blue-600'
                }`}
              >
                Comment
              </button>
            </div>
          </div>
        </div>
      </form>

      {/* Comment Tree */}
      <div className="space-y-3">
        {comments.map((comment) => (
          <CommentNode
            key={comment.id}
            comment={comment}
            postId={post.id}
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

      {comments.length === 0 && (
        <p className="text-center text-gray-500 text-sm py-4">
          No comments yet. Be the first to comment!
        </p>
      )}
    </div>
  );
}

export default CommentList;
