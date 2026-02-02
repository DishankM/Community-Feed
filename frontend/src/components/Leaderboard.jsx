import { useEffect } from 'react';
import { leaderboardAPI } from '../api';

function Leaderboard({ leaderboard, onRefresh }) {
  useEffect(() => {
    // Refresh leaderboard every 30 seconds
    const interval = setInterval(() => {
      onRefresh();
    }, 30000);

    return () => clearInterval(interval);
  }, [onRefresh]);

  const getRankIcon = (index) => {
    switch (index) {
      case 0:
        return (
          <span className="text-yellow-500">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          </span>
        );
      case 1:
        return (
          <span className="text-gray-400">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          </span>
        );
      case 2:
        return (
          <span className="text-amber-600">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
          </span>
        );
      default:
        return <span className="text-gray-400 font-medium">{index + 1}</span>;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 sticky top-24">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-800">Top Contributors</h2>
        <span className="text-xs text-gray-500">24h</span>
      </div>

      <div className="space-y-3">
        {leaderboard.users && leaderboard.users.length > 0 ? (
          leaderboard.users.map((user, index) => (
            <div
              key={user.id}
              className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex-shrink-0">{getRankIcon(index)}</div>
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white text-sm font-bold">
                {user.username.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-800 truncate">
                  {user.username}
                </p>
                <p className="text-xs text-gray-500">
                  {user.karma} Karma points
                </p>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-blue-500">
                  {user.karma}
                </span>
              </div>
            </div>
          ))
        ) : (
          <p className="text-center text-gray-500 text-sm py-4">
            No activity in the last 24 hours
          </p>
        )}
      </div>

      <div className="mt-4 pt-3 border-t border-gray-100">
        <p className="text-xs text-gray-400 text-center">
          Points: Post like = 5, Comment like = 1
        </p>
      </div>
    </div>
  );
}

export default Leaderboard;
