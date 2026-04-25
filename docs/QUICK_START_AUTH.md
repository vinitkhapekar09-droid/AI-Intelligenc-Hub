# 🚀 Quick Start - Authentication System

## Files Created/Modified

### ✨ New Files Created
- `backend/app/models/user.py` - User SQLAlchemy ORM model
- `backend/app/core/auth.py` - Authentication utilities
- `AUTH_SYSTEM_GUIDE.md` - Complete documentation

### 🔧 Modified Files
- `backend/app/api/routes.py` - Added /register, /login, protected /chat
- `backend/app/main.py` - Added User and Subscriber model imports
- `frontend/app.py` - Complete rewrite with 5-page authenticated app
- `requirements.txt` - Added python-jose and passlib

## ⚡ Quick Commands

### Start Backend
```bash
cd /workspaces/ai_explore
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend
```bash
cd /workspaces/ai_explore
streamlit run frontend/app.py
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## 📝 Test Script (curl)

### 1. Register User
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "testpass123"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"
```

### 2. Chat with Token
```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is AI?",
    "doc_type": null,
    "n_results": 5
  }'
```

### 3. Try Without Token (Should Fail)
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is AI?", "doc_type": null, "n_results": 5}'
```

## 🔐 Key Features

✅ **JWT Tokens** - 24-hour expiry, HS256 algorithm
✅ **Bcrypt Hashing** - Passwords never stored in plain text
✅ **Protected Routes** - /chat requires valid JWT token
✅ **Session Management** - Token stored in st.session_state
✅ **Public Pages** - Landing, Login/Register open to all
✅ **Protected Pages** - Dashboard, Chat, Digest for authenticated users only
✅ **Clean UI** - Streamlit forms, tabs, columns for layouts
✅ **Error Handling** - User-friendly error messages
✅ **Logout Function** - Clears all session data

## 🎯 Frontend Pages

| Page | Auth? | Features |
|------|-------|----------|
| Landing | ❌ | Hero, news preview, subscribe |
| Login/Register | ❌ | Tabs, form validation, auto-redirect |
| Dashboard | ✅ | Welcome, quick links, health check |
| Chat | ✅ | Question input, filter, answer+sources |
| Full Digest | ✅ | Stats, trigger pipeline, content overview |

## 📊 Database Tables

### users table
```
id (PK)  | name | email (unique) | hashed_password | is_active | created_at
---------|------|----------------|-----------------|-----------|------------------
1        | John | john@ex.com    | $2b$12$...     | true      | 2026-04-21 ...
```

### subscribers table (unchanged)
```
id (PK) | email (unique) | is_active | subscribed_at
--------|----------------|-----------|------------------
1       | sub@ex.com     | true      | 2026-04-21 ...
```

## 🔗 API Endpoints

### Public Endpoints (No Auth)
- `GET /health` - Health check
- `POST /subscribe` - Subscribe to digest
- `DELETE /unsubscribe` - Unsubscribe
- `POST /trigger-digest` - Trigger pipeline
- `GET /daily-digest` - Get stats

### Auth Endpoints
- `POST /register` - Register new user
- `POST /login` - Login user

### Protected Endpoints (Require JWT)
- `POST /chat` - Ask question (requires Authorization header)

## 🛡️ Request Format

### With Authentication
```
POST /chat HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "question": "What is AI?",
  "doc_type": null,
  "n_results": 5
}
```

### Without Authentication (Will Fail)
```
POST /chat HTTP/1.1
Content-Type: application/json

{
  "question": "What is AI?"
}
```

## 🧪 Environment Variables

```bash
# Backend
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
API_BASE=http://localhost:8000

# Frontend
API_BASE=http://localhost:8000
```

## 📱 Frontend Session State

```python
# After successful login/register:
st.session_state = {
    "is_logged_in": True,
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user_name": "John Doe",
    "user_id": 1
}

# After logout:
st.session_state = {
    "is_logged_in": False,
    "token": None,
    "user_name": None,
    "user_id": None
}
```

## ⚠️ Common Issues

| Issue | Solution |
|-------|----------|
| Token expired | Login again to get new token |
| 401 Unauthorized | Check Bearer token format |
| Email already exists | Use different email or login |
| Cannot connect to backend | Ensure FastAPI running on 8000 |
| Database unavailable | Start PostgreSQL service |

## 📚 Documentation

See `AUTH_SYSTEM_GUIDE.md` for:
- Complete implementation details
- Security features explained
- Testing procedures
- Troubleshooting guide
- API response examples
- Curl command examples

## ✨ Next Steps (Optional)

1. Add password reset functionality
2. Implement token refresh endpoint
3. Add user profile page
4. Add email verification
5. Add rate limiting for auth endpoints
6. Add 2FA (two-factor authentication)
7. Add social login (Google, GitHub)
8. Add role-based access control (RBAC)

---

🎉 **Implementation complete! All files are syntactically correct and ready to run.**
