import { useState } from 'react';
import { postsAPI } from '../api';
import PostCard from './PostCard';
import CreatePost from './CreatePost';

function Feed({ posts, onPostCreated, refreshFeed }) {
  const [selectedPost, setSelectedPost] = useState(null);
  const [selectedPostData, setSelectedPostData] = useState(null);
  const [loadingPost, setLoadingPost] = useState(false);

  const handlePostClick = async (post) => {
    setSelectedPost(post);
    setLoadingPost(true);
    try {
      const response = await postsAPI.retrieve(post.id);
      setSelectedPostData(response.data);
    } catch (error) {
      console.error('Error fetching post details:', error);
    } finally {
      setLoadingPost(false);
    }
  };

  const handleBack = () => {
    setSelectedPost(null);
    setSelectedPostData(null);
    refreshFeed();
  };

  if (selectedPost) {
    return (
      <div>
        <button
          onClick={handleBack}
          className="mb-4 text-blue-500 hover:text-blue-700 font-medium"
        >
          ← Back to Feed
        </button>
        {loadingPost ? (
          <div className="text-center py-10 text-gray-500">Loading post...</div>
        ) : selectedPostData ? (
          <PostCard
            post={selectedPostData}
            expanded={true}
            refreshFeed={() => {
              // Refresh the detailed post data
              handlePostClick(selectedPost);
            }}
          />
        ) : null}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <CreatePost onPostCreated={onPostCreated} />
      <div className="space-y-4">
        {posts.map((post) => (
          <div
            key={post.id}
            onClick={() => handlePostClick(post)}
            className="cursor-pointer"
          >
            <PostCard post={post} expanded={false} refreshFeed={refreshFeed} />
          </div>
        ))}
      </div>
      {posts.length === 0 && (
        <div className="text-center py-10 text-gray-500">
          No posts yet. Be the first to share something!
        </div>
      )}
    </div>
  );
}

export default Feed;
