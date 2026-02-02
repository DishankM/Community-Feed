# Community Feed - Playto Engineering Challenge

A full-stack Community Feed prototype featuring threaded discussions and a dynamic 24-hour leaderboard.

## Features

- **Feed System**: Display text posts with author info and like counts
- **Threaded Comments**: Nested comment system (Reddit-style, unlimited depth)
- **Gamification**: 
  - 1 Like on Post = 5 Karma
  - 1 Like on Comment = 1 Karma
- **Dynamic Leaderboard**: Top 5 users by Karma in the last 24 hours
- **Concurrency Control**: Database-level prevention of double-likes
- **Optimized Queries**: Efficient N+1-free comment tree loading

## Tech Stack

- **Backend**: Django 5.0 + Django REST Framework 3.14
- **Frontend**: React 18 + Tailwind CSS 3.4
- **Database**: SQLite (development) / PostgreSQL (production)
- **Build Tool**: Vite 5.0

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- npm or yarn

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (creates SQLite database)
python manage.py migrate

# Create a test superuser
python manage.py createsuperuser --username=admin --email=admin@example.com

# Start development server
python manage.py runserver
```

The backend API will be available at `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory (in a new terminal)
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Project Structure

```
community-feed/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── community_project/     # Django project configuration
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── api/                    # Main API application
│       ├── __init__.py
│       ├── models.py           # User, Post, Comment, PostLike, CommentLike
│       ├── serializers.py      # Efficient nested comment serialization
│       ├── views.py            # ViewSets with concurrency handling
│       └── urls.py             # API routing
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx            # React entry point
│       ├── index.css           # Tailwind imports
│       ├── api.js              # Axios API client
│       ├── App.jsx             # Main app component
│       └── components/
│           ├── Navbar.jsx
│           ├── Feed.jsx
│           ├── PostCard.jsx
│           ├── CreatePost.jsx
│           ├── CommentList.jsx
│           ├── CommentNode.jsx  # Recursive comment rendering
│           └── Leaderboard.jsx
├── README.md
└── EXPLAINER.md                # Technical documentation
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/` | List all users (for testing) |
| GET/POST | `/api/posts/` | List/Create posts |
| GET | `/api/posts/{id}/` | Get post with full nested comment tree |
| POST | `/api/posts/{id}/like/` | Toggle like on a post |
| POST | `/api/posts/{id}/comments/` | Create a comment on a post |
| GET | `/api/comments/` | List all comments |
| POST | `/api/comments/{id}/like/` | Toggle like on a comment |
| GET | `/api/leaderboard/` | Get top 5 users by 24h Karma |

## Testing the Application

1. Start both backend and frontend servers
2. Open `http://localhost:5173` in your browser
3. Create posts using the text area at the top
4. Click on posts to view details and add comments
5. Reply to comments to create nested threads
6. Like posts and comments to earn Karma
7. Check the leaderboard for top contributors

## Database Schema

### User Model
- Extends Django's `AbstractUser`
- No additional fields needed (karma calculated dynamically)

### Post Model
- `author`: ForeignKey to User
- `content`: TextField
- `created_at`: DateTimeField (auto_now_add)
- `updated_at`: DateTimeField (auto_now)

### Comment Model
- `post`: ForeignKey to Post (with database index)
- `parent`: ForeignKey to self, nullable (adjacency list pattern)
- `author`: ForeignKey to User
- `content`: TextField
- `created_at`: DateTimeField (auto_now_add)

### PostLike Model
- `user`: ForeignKey to User
- `post`: ForeignKey to Post
- `created_at`: DateTimeField (auto_now_add)
- `unique_together = ('user', 'post')` - Prevents double-likes

### CommentLike Model
- `user`: ForeignKey to User
- `comment`: ForeignKey to Comment
- `created_at`: DateTimeField (auto_now_add)
- `unique_together = ('user', 'comment')` - Prevents double-likes

## License

MIT
