# 🔐 Authentication System - Complete Implementation Guide

## ✅ What Was Implemented

### 1. **Backend User Model** 
📁 `backend/app/models/user.py`

```python
# Fields:
- id: Integer (primary key)
- name: String
- email: String (unique, indexed)
- hashed_password: String
- is_active: Boolean (default: True)
- created_at: DateTime (auto-timestamp)
```

### 2. **Authentication Utilities**
📁 `backend/app/core/auth.py`

**Functions:**
- `hash_password(password)` → Bcrypt hashing
- `verify_password(plain, hashed)` → Password verification
- `create_access_token(data)` → JWT token (24-hour expiry)
- `verify_access_token(token)` → Token validation
- `get_token_from_header(request)` → Extract Bearer token

### 3. **Backend Authentication Endpoints**
📁 `backend/app/api/routes.py`

**New Endpoints:**
- `POST /register` - Create user account
  - Input: `{name, email, password}`
  - Output: `{access_token, token_type, user_name, user_id}`
  - Errors: 400 (email exists), 503 (DB error)

- `POST /login` - Login user
  - Input: `{email, password}`
  - Output: `{access_token, token_type, user_name, user_id}`
  - Errors: 401 (invalid credentials), 503 (DB error)

**Protected Endpoints:**
- `POST /chat` - Now requires `Authorization: Bearer {token}` header
  - Returns: 401 if token missing/invalid/expired
  - Returns: 401 if user not found or inactive

**Unchanged Endpoints:**
- `GET /health` - Still public
- `POST /subscribe` - Still public (no auth required)
- `DELETE /unsubscribe` - Still public
- `POST /trigger-digest` - Still public
- `GET /daily-digest` - Still public

### 4. **Frontend - Complete Rewrite**
📁 `frontend/app.py`

**Architecture:**
- Session state management (token, user_name, is_logged_in, user_id)
- Helper function: `make_api_request()` with error handling
- Helper function: `logout()` to clear session
- Dynamic sidebar based on auth state
- 5-page application

**Pages:**

#### Page 1: Landing (Public)
- Hero section with feature descriptions
- AI news preview (fetches /daily-digest)
- Subscribe form (email → /subscribe)
- CTA buttons to Login/Register

#### Page 2: Login/Register (Public)
- Tab interface: Login | Register
- Login form → POST /login → save token + redirect
- Register form → POST /register → save token + redirect
- Email format validation
- Password confirmation check (min 8 chars)

#### Page 3: Dashboard (Protected)
- Welcome message with user name
- 3 quick action cards:
  - Chat: Start asking questions
  - Digest: View all content
  - System: Check health status
- Tech stack info

#### Page 4: Chat (Protected)
- Question input field
- Filter dropdown: All / Research / News
- POST /chat with Bearer token
- Display: Answer + Sources + Metadata
- Error handling for auth failures

#### Page 5: Full Digest (Protected)
- Vector store metrics (chunks, collection, storage)
- Trigger digest pipeline button
- Content categories overview
- Refresh button
- Error handling for access denied

**Sidebar:**
- Authenticated: Dashboard | Digest | Chat + Logout button
- Public: Landing | Login/Register
- Shows logged-in user name for authenticated users

### 5. **Dependencies Added**
📁 `requirements.txt`

```
python-jose[cryptography]==3.3.0    # JWT token management
passlib[bcrypt]==1.7.4               # Password hashing
```

## 🚀 How to Test

### 1. **Install Dependencies**
```bash
cd /workspaces/ai_explore
pip install -r requirements.txt
```

### 2. **Configure Environment** (if needed)
```bash
# Make sure SECRET_KEY is set in .env
# Default: "CHANGE_ME" (from config.py)
# For production: Use a strong random key
export SECRET_KEY="your-secret-key-here"
```

### 3. **Start Backend**
```bash
cd /workspaces/ai_explore
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. **Start Frontend** (in new terminal)
```bash
cd /workspaces/ai_explore
streamlit run frontend/app.py
```

### 5. **Test Flow**

#### Register New User
1. Navigate to frontend (http://localhost:8501)
2. Click "Login / Register" in sidebar
3. Go to "Register" tab
4. Fill form: Name, Email, Password
5. Click "Create Account"
6. ✅ Should redirect to Dashboard
7. ✅ Token saved in session state

#### Login Existing User
1. Click "Logout" button
2. Navigate back to "Login / Register"
3. Go to "Login" tab
4. Fill form: Email, Password
5. Click "Login"
6. ✅ Should redirect to Dashboard
7. ✅ Token saved in session state

#### Protected Chat Endpoint
1. While logged in, navigate to "Chat"
2. Ask a question: "What is AI?"
3. ✅ Should send POST /chat with Bearer token header
4. ✅ Should display answer + sources
5. Logout, try to chat again
6. ✅ Should show "You need to be logged in" warning

#### Public Subscribe
1. Go to "Landing" page (logout if needed)
2. Enter email in subscribe form
3. Click "Subscribe"
4. ✅ Should see success message (email doesn't need to be registered user)

## 🔐 Security Features

### Password Security
- ✅ Bcrypt hashing via passlib
- ✅ Password never stored in plain text
- ✅ Password verification in constant time

### Token Security
- ✅ JWT tokens with HS256 algorithm
- ✅ 24-hour expiration
- ✅ Token signed with SECRET_KEY
- ✅ User ID encoded in token ("sub" claim)
- ✅ Expiration claim ("exp") in token

### Endpoint Protection
- ✅ /chat requires Bearer token
- ✅ Invalid/missing token returns 401
- ✅ Expired token returns 401
- ✅ Inactive user returns 401

### Session Management
- ✅ Token stored in st.session_state
- ✅ User info (name, ID) in session
- ✅ Login state tracked separately
- ✅ Logout clears all session data

## ⚠️ Important Notes

### TOKEN HANDLING
- Tokens are stored in Streamlit session state (browser session)
- Tokens expire after 24 hours
- After expiry, user needs to login again
- No automatic refresh token mechanism (can add later)

### AUTHORIZATION HEADER
Frontend sends:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Backend extracts token:
```python
auth_header = request.headers.get("Authorization")
token = auth_header[7:]  # Remove "Bearer " prefix
```

### ERROR SCENARIOS

| Scenario | Status | Message |
|----------|--------|---------|
| Missing token | 401 | "Missing or invalid Authorization header" |
| Invalid token | 401 | "Invalid or expired token" |
| Expired token | 401 | "Invalid or expired token" |
| User not found | 401 | "User not found or inactive" |
| Wrong password | 401 | "Invalid email or password" |
| Email exists | 400 | "Email already registered" |
| DB error | 503 | "Database unavailable. Error: ..." |

## 🔄 API Response Examples

### POST /register (Success)
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_name": "John Doe",
  "user_id": 1
}
```

### POST /login (Success)
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_name": "Jane Smith",
  "user_id": 2
}
```

### POST /chat (Protected - Success)
```json
{
  "answer": "AI stands for Artificial Intelligence...",
  "sources": [...],
  "chunks_found": 5,
  "model": "Groq LLaMA"
}
```

### POST /chat (Auth Failure)
```json
{
  "detail": "Invalid or expired token"
}
```

## 📋 Frontend Session State

```python
st.session_state = {
    "is_logged_in": True/False,
    "token": "eyJhbGc...",
    "user_name": "John Doe",
    "user_id": 1
}
```

## 🧪 Testing Curl Commands

### Register
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepass123"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepass123"
  }'
```

### Protected Chat
```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is AI?",
    "doc_type": null,
    "n_results": 5
  }'
```

## 🐛 Troubleshooting

### "Cannot connect to backend"
- Check FastAPI is running on port 8000
- Check API_BASE environment variable

### "Invalid or expired token"
- Token may have expired (24-hour limit)
- Login again to get new token
- Check system clock is correct

### "Email already registered"
- Try login instead of register
- Use different email for new account

### "Database unavailable"
- Start PostgreSQL service
- Check DATABASE_URL in environment
- Ensure Docker services running

### "Missing or invalid Authorization header"
- Ensure token is in session state
- Try logout and login again
- Check Bearer prefix in header

## 📚 File References

- Backend User Model: `backend/app/models/user.py`
- Auth Utilities: `backend/app/core/auth.py`
- API Routes: `backend/app/api/routes.py`
- Frontend: `frontend/app.py`
- Config: `backend/app/core/config.py`
- Database: `backend/app/core/database.py`
- Requirements: `requirements.txt`

## 🎯 What's Still Working

✅ All existing functionality intact:
- /health endpoint
- /subscribe endpoint (no auth)
- /unsubscribe endpoint (no auth)
- /trigger-digest endpoint (no auth)
- /daily-digest endpoint (no auth)
- Email sending
- Celery tasks
- RAG pipeline
- Vector store

✅ New functionality:
- User registration
- User login
- JWT token management
- Protected routes
- Session state management
- Beautiful auth UI
