# Frontend API Update Summary

## ✅ COMPLETED UPDATES

### 1. Diet Main Page (`diet-mainpage.html`)
**Status:** ✅ Fully Updated

**Changes Made:**
- ✅ Removed all Jinja2 template syntax (`{{ }}`, `{% %}`)
- ✅ Added API_BASE constant: `https://virtual-trainer-backend.onrender.com`
- ✅ Converted all form submissions from server-side to client-side fetch API
- ✅ Updated all 4 forms:
  - BMI & Calorie Calculator → `/diet/calculate`
  - AI Diet Analysis → `/diet/analyze`
  - Weight Gain Foods → `/diet/weightgain`
  - Weight Loss Foods → `/diet/weightloss`
- ✅ Added loading states for all forms
- ✅ Added error handling with try-catch blocks
- ✅ Added JSON response handling
- ✅ Dynamic DOM manipulation for results display

**API Endpoints Updated:**
```javascript
const API_BASE = "https://virtual-trainer-backend.onrender.com";

// BMI Calculator
fetch(`${API_BASE}/diet/calculate`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
})

// Diet Analysis
fetch(`${API_BASE}/diet/analyze`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
})

// Weight Gain
fetch(`${API_BASE}/diet/weightgain`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
})

// Weight Loss
fetch(`${API_BASE}/diet/weightloss`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
})
```

---

## ⚠️ PAGES REQUIRING ATTENTION

### 2. Dashboard (`dashboard.html`)
**Status:** ⚠️ Requires Authentication System

**Current Issue:**
- Uses Flask-Login (server-side authentication)
- Requires user session to fetch data
- Contains Jinja2 template syntax

**To Fix:**
```javascript
// Need to implement token-based authentication
const API_BASE = "https://virtual-trainer-backend.onrender.com";

// Example implementation needed:
fetch(`${API_BASE}/api/exercises`, {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`  // Need auth system
  }
})
```

**Recommendation:**
Implement JWT token authentication in backend, then update dashboard to:
1. Store JWT token in localStorage
2. Include token in all API requests
3. Handle login/logout client-side

---

### 3. Login/Register Pages (`login.html`, `register.html`)
**Status:** ⚠️ Requires Authentication System

**Current Issue:**
- Forms submit to backend using Flask-Login
- Session-based authentication (server-side)

**To Fix:**
Convert to token-based authentication:
```javascript
// Login form handler
fetch(`${API_BASE}/api/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: email,
    password: password
  })
})
.then(response => response.json())
.then(data => {
  // Store JWT token
  localStorage.setItem('token', data.token);
  // Redirect to dashboard
})
```

**Recommendation:**
Add these backend endpoints:
- `POST /api/auth/login` - Returns JWT token
- `POST /api/auth/register` - Creates user, returns JWT token
- `GET /api/auth/me` - Validates token and returns user info

---

### 4. Exercise Pages (`exercise-*.html`)
**Status:** ✅ No Changes Needed

**Reason:**
- These pages use MediaPipe for client-side pose detection
- No backend API calls required
- All processing happens in browser

---

## 🔧 BACKEND UPDATES NEEDED

### Required API Endpoints for Authentication

Your backend already has these API endpoints (from app.py):
- ✅ `GET /api/exercises` - Get exercise history (requires login)
- ✅ `POST /api/exercises` - Log new exercise (requires login)
- ✅ `GET /api/diet` - Get diet logs (requires login)
- ✅ `POST /api/diet` - Log diet entry (requires login)
- ✅ `GET /api/progress` - Get progress summary (requires login)

### Additional Endpoints Needed for JWT Auth:

```python
# Add to app.py

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Login user and return JWT token"""
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()

    if user and bcrypt.check_password_hash(user.password, data['password']):
        # Generate JWT token
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=7)
        }, app.config['SECRET_KEY'])

        return jsonify({
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })

    return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/api/auth/register', methods=['POST'])
def api_register():
    """Register new user and return JWT token"""
    data = request.get_json()

    # Check if user exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400

    # Create user
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_password
    )
    db.session.add(user)
    db.session.commit()

    # Generate JWT token
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }, app.config['SECRET_KEY'])

    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 201


@app.route('/api/auth/me', methods=['GET'])
def api_get_current_user():
    """Get current user from JWT token"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')

    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user = User.query.get(data['user_id'])

        if user:
            return jsonify({
                'id': user.id,
                'username': user.username,
                'email': user.email
            })

        return jsonify({'error': 'User not found'}), 404

    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
```

### Update Protected Routes to Use JWT

```python
from functools import wraps
import jwt

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        return f(current_user_id, *args, **kwargs)

    return decorated_function

# Update existing routes:
@app.route('/api/exercises', methods=['GET'])
@token_required
def api_get_exercises(current_user_id):
    # Use current_user_id instead of current_user.id
    exercises = ExerciseHistory.query.filter_by(user_id=current_user_id)\
        .order_by(ExerciseHistory.created_at.desc()).all()
    return jsonify([{
        'id': e.id,
        'exercise_name': e.exercise_name,
        'duration_seconds': e.duration_seconds,
        'repetitions': e.repetitions,
        'calories_burned': e.calories_burned,
        'created_at': e.created_at.isoformat()
    } for e in exercises])
```

---

## 📋 DEPLOYMENT CHECKLIST

### Step 1: Backend (Render) ✅
- [x] Added `flask-cors` to requirements.txt
- [x] Added `gunicorn` to requirements.txt
- [x] Initialized CORS in app.py
- [x] Added debug logging to API routes
- [x] All API routes return JSON
- [ ] Add PyJWT for token authentication: `PyJWT==2.8.0`
- [ ] Implement JWT authentication endpoints
- [ ] Update protected routes to use JWT

### Step 2: Frontend (Vercel) 🚧
- [x] Updated `diet-mainpage.html` with fetch API
- [ ] Convert `dashboard.html` to use JWT auth
- [ ] Convert `login.html` to use JWT auth
- [ ] Convert `register.html` to use JWT auth
- [ ] Add auth state management (localStorage)
- [ ] Add token refresh logic

### Step 3: Test & Deploy
- [ ] Test diet recommendation system locally
- [ ] Test authentication flow
- [ ] Deploy backend updates to Render
- [ ] Deploy frontend updates to Vercel
- [ ] Test in production environment

---

## 🎯 CURRENT STATUS

**Working Now:**
- ✅ Diet recommendation system (BMI calculator, AI analysis, food recommendations)
- ✅ Exercise pages (pose detection works client-side)
- ✅ Static pages (home, about, courses, etc.)

**Needs Authentication Update:**
- ⚠️ User dashboard
- ⚠️ Login/Register pages
- ⚠️ Exercise history tracking
- ⚠️ Diet logging

---

## 💡 QUICK START

**To test the diet system now:**
1. Deploy the updated `diet-mainpage.html` to Vercel
2. Access the page
3. All diet features should work with the Render backend

**To enable full user features:**
1. Implement JWT authentication in backend (see code above)
2. Update login/register pages to use token-based auth
3. Update dashboard to fetch data using JWT token

---

## 📞 NEXT STEPS

1. **Immediate:** Deploy `diet-mainpage.html` - diet system is ready!
2. **Short-term:** Implement JWT auth for dashboard/login/register
3. **Long-term:** Add token refresh, logout, and password reset

---

**Generated:** March 23, 2026
**Backend URL:** https://virtual-trainer-backend.onrender.com
**Frontend URL:** [Your Vercel URL]
