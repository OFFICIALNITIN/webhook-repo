# GitHub Webhook Receiver - Flask Backend

A production-ready Flask backend application for receiving GitHub webhook events (Push, Pull Request, Merge) and storing them in MongoDB.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [MongoDB Schema](#mongodb-schema)
- [GitHub Webhook Setup](#github-webhook-setup)
- [Deployment](#deployment)

---

## ✨ Features

- **Webhook Receiver**: Handles GitHub `push`, `pull_request`, and `merge` events
- **Event Storage**: Stores events in MongoDB with a defined schema
- **REST API**: Exposes events for frontend consumption
- **Production Ready**: Includes logging, error handling, retry logic, and CORS support
- **MongoDB Atlas Support**: SSL/TLS certificate handling with certifi

---

## 🛠 Tech Stack

| Technology | Purpose |
|------------|---------|
| Flask | Web framework |
| PyMongo | MongoDB driver |
| Flask-CORS | Cross-origin resource sharing |
| Gunicorn | Production WSGI server |
| MongoDB Atlas | Cloud database |

---

## 📁 Project Structure

```
webhook/
├── app/
│   ├── __init__.py      # Flask app factory
│   ├── extensions.py    # MongoDB connection
│   ├── routes.py        # API endpoints
│   └── utils.py         # Helper functions
├── logs/                # Application logs
├── .env                 # Environment variables (not in git)
├── .env.example         # Environment template
├── .gitignore           # Git ignore rules
├── config.py            # Configuration classes
├── requirements.txt     # Python dependencies
├── run.py               # Application entry point
└── README.md            # Documentation
```

---

## 🚀 Installation

### Prerequisites

- Python 3.8+
- MongoDB (local or Atlas)
- Git

### Steps

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/webhook.git
cd webhook

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Unix/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your MongoDB URI
# Run the application
python run.py
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `FLASK_ENV` | Environment mode | `development` |
| `SECRET_KEY` | Flask secret key | `dev-secret-key...` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `5000` |

### Example `.env` file

```env
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/webhook_db
FLASK_ENV=production
SECRET_KEY=your-super-secret-key
HOST=0.0.0.0
PORT=5000
```

---

## 📡 API Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

### Webhook Receiver

```http
POST /webhook/receiver
```

**Headers:**
| Header | Value |
|--------|-------|
| `Content-Type` | `application/json` |
| `X-GitHub-Event` | `push` / `pull_request` |

**Supported Events:**

| GitHub Event | Action Stored |
|--------------|---------------|
| `push` | `PUSH` |
| `pull_request` (opened/edited/reopened) | `PULL_REQUEST` |
| `pull_request` (closed + merged=true) | `MERGE` |

**Response (Success):**
```json
{
  "status": "success",
  "message": "Event processed and stored",
  "event": {
    "request_id": "abc123...",
    "author": "username",
    "action": "PUSH",
    "from_branch": "main",
    "to_branch": "main",
    "timestamp": "29 January 2026 - 10:30 PM UTC"
  }
}
```

---

### Get Events

```http
GET /api/events
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 10 | Number of events (max: 100) |

**Response:**
```json
[
  {
    "request_id": "abc123...",
    "author": "username",
    "action": "PUSH",
    "from_branch": "feature-branch",
    "to_branch": "main",
    "timestamp": "29 January 2026 - 10:30 PM UTC"
  }
]
```

---

## 📊 MongoDB Schema

**Database:** `webhook_db`  
**Collection:** `events`

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | String | Commit SHA (push) or PR number |
| `author` | String | GitHub username |
| `action` | String | `PUSH`, `PULL_REQUEST`, or `MERGE` |
| `from_branch` | String | Source branch |
| `to_branch` | String | Target branch |
| `timestamp` | String | Formatted as `DD Month YYYY - HH:MM AM/PM UTC` |

---

## 🔗 GitHub Webhook Setup

1. Go to your GitHub repository
2. Navigate to **Settings** → **Webhooks** → **Add webhook**
3. Configure:
   - **Payload URL:** `https://your-deployed-url.com/webhook/receiver`
   - **Content type:** `application/json`
   - **Secret:** (optional)
   - **Events:** Select "Let me select individual events"
     - ✅ Pushes
     - ✅ Pull requests

4. Click **Add webhook**

---

## 🌐 Deployment

### Deploy to Render

1. Push your code to GitHub
2. Create a new **Web Service** on [Render](https://render.com)
3. Connect your GitHub repository
4. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn "app:create_app()" --bind 0.0.0.0:$PORT`
5. Add environment variables in Render dashboard
6. Deploy!

### Production Command

```bash
gunicorn "app:create_app()" --bind 0.0.0.0:5000 --workers 4
```

---

## 📝 Testing with cURL

### Test Push Event

```bash
curl -X POST http://localhost:5000/webhook/receiver \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -d '{
    "ref": "refs/heads/main",
    "head_commit": {
      "id": "abc123def456",
      "timestamp": "2026-01-29T16:30:00Z"
    },
    "pusher": {"name": "testuser"}
  }'
```

### Test Pull Request Event

```bash
curl -X POST http://localhost:5000/webhook/receiver \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -d '{
    "action": "opened",
    "number": 42,
    "pull_request": {
      "merged": false,
      "head": {"ref": "feature"},
      "base": {"ref": "main"},
      "user": {"login": "testuser"},
      "updated_at": "2026-01-29T16:30:00Z"
    }
  }'
```

### Get Events

```bash
curl http://localhost:5000/api/events
```

---

## 📄 License

MIT License

---

## 👤 Author

**NITIN**

- GitHub: [@NitinJangid7](https://github.com/NitinJangid7)
