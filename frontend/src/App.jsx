import { useState, useEffect } from 'react';
import { postsAPI, leaderboardAPI } from './api';
import Navbar from './components/Navbar';
import Feed from './components/Feed';
import Leaderboard from './components/Leaderboard';

function App() {
  const [posts, setPosts] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [postsRes, leaderboardRes] = await Promise.all([
        postsAPI.list(),
        leaderboardAPI.get(),
      ]);
      setPosts(postsRes.data);
      setLeaderboard(leaderboardRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handlePostCreated = () => {
    fetchData();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <Navbar />
      <main className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Feed */}
          <div className="lg:col-span-2">
            <Feed
              posts={posts}
              onPostCreated={handlePostCreated}
              refreshFeed={fetchData}
            />
          </div>
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <Leaderboard leaderboard={leaderboard} onRefresh={fetchData} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
