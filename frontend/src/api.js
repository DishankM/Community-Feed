import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Posts API
export const postsAPI = {
  list: () => api.get('/posts/'),
  retrieve: (id) => api.get(`/posts/${id}/`),
  create: (data) => api.post('/posts/', data),
  like: (id) => api.post(`/posts/${id}/like/`),
};

// Comments API
export const commentsAPI = {
  create: (data) => api.post('/comments/', data),
  like: (id) => api.post(`/comments/${id}/like/`),
};

// Leaderboard API
export const leaderboardAPI = {
  get: () => api.get('/leaderboard/'),
};

// Users API
export const usersAPI = {
  list: () => api.get('/users/'),
};

export default api;
