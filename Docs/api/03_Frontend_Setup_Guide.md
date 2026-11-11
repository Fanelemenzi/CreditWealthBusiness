# Frontend Configuration Guide - ECHS API Connection

## 🎯 Where to Set the Backend URL

### For React Applications

#### 1. Create `.env` file in your frontend project root

```
my-frontend-project/
├── public/
├── src/
├── .env                 ← Create this file
├── .env.example         ← Template (optional)
├── package.json
└── README.md
```

#### 2. Add backend URL to `.env`

**For Vite (React + Vite):**
```env
# .env file
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
```

**For Create React App:**
```env
# .env file
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_API_TIMEOUT=30000
```

**Important:** 
- Vite env vars must start with `VITE_`; CRA vars must start with `REACT_APP_`
- Don't commit `.env` to git (add it to `.gitignore`)
- Create `.env.example` for team reference

#### 3. Create `.env.example` (for team reference)

**Vite:**
```env
# .env.example
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
```

**Create React App:**
```env
# .env.example
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_API_TIMEOUT=30000
```

---

### For Vue.js Applications

```env
# .env
VUE_APP_API_BASE_URL=http://localhost:8000
VUE_APP_API_TIMEOUT=30000
```

---

### For Next.js Applications

```env
# .env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_TIMEOUT=30000
```

---

## 📁 Recommended Project Structure

```
frontend-project/
├── src/
│   ├── api/
│   │   ├── client.js          ← Axios instance with config
│   │   ├── auth.js            ← Authentication API calls
│   │   ├── assessment.js      ← Assessment API calls
│   │   └── score.js           ← Score API calls
│   ├── config/
│   │   └── api.config.js      ← API configuration constants
│   ├── utils/
│   │   └── errorHandler.js    ← Error handling utilities
│   ├── components/
│   ├── pages/
│   └── App.js
├── .env                        ← Environment variables (gitignored)
├── .env.example                ← Template for team
└── package.json
```

---

## 🔧 Step-by-Step Setup

### Step 1: Create API Configuration File

**Create `src/config/api.config.js`:**

```javascript
// src/config/api.config.js

// Read from environment variables
// Vite uses import.meta.env.VITE_*; CRA uses process.env.REACT_APP_*
const BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) ||
  process.env?.REACT_APP_API_BASE_URL ||
  'http://localhost:8000';

export const API_CONFIG = {
  baseURL: BASE_URL,
  timeout: 30000,
  withCredentials: true, // Enable cookies for CORS
};

// API endpoints — all correct paths as of backend v1.0
export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    SIGNUP:        '/api/auth/signup/',
    SIGNIN:        '/api/auth/signin/',
    LOGOUT:        '/api/auth/auth-logout/',
    REFRESH:       '/api/auth/token/refresh/',
    VERIFY_PHONE:  '/api/auth/verify-phone/',
  },
  
  // Assessment Sessions
  ASSESSMENT: {
    CREATE:        '/api/assessment-sessions/',
    ACTIVE:        '/api/assessment-sessions/active-session/',
    DETAIL:        (id) => `/api/assessment-sessions/${id}/`,
    SAVE_ANSWER:   (id) => `/api/assessment-sessions/${id}/save_answer/`,
    SAVE_MULTIPLE: (id) => `/api/assessment-sessions/${id}/save_multiple_answers/`,
    ADVANCE:       (id) => `/api/assessment-sessions/${id}/advance_question/`,
    GO_BACK:       (id) => `/api/assessment-sessions/${id}/go_back_question/`,
    MARK_SECTION:  (id) => `/api/assessment-sessions/${id}/mark_section_completed/`,
    SUBMIT:        (id) => `/api/assessment-sessions/${id}/mark_completed/`,
  },
  
  // Score Calculation
  SCORE: {
    CALCULATE: '/api/assessments/calculate-score/',
    LATEST:    '/api/assessments/latest-score/',
  },
  
  // Validation
  VALIDATION: {
    FIELD:  '/api/assessments/validate-field/',
    BATCH:  '/api/assessments/batch-validate/',
    SCHEMA: '/api/assessments/field-schema/',
  },
  
  // Landing Page
  LANDING: {
    CONFIG: '/api/landing/config/',
  },
};

export default API_CONFIG;
```

---

### Step 2: Create Axios Client

**Create `src/api/client.js`:**

```javascript
// src/api/client.js
import axios from 'axios';
import API_CONFIG from '../config/api.config';

// Create axios instance with base configuration
const apiClient = axios.create({
  baseURL: API_CONFIG.baseURL,
  timeout: API_CONFIG.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: API_CONFIG.withCredentials,
});

// Request interceptor - Add JWT token to requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and we haven't retried yet, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        // Request new access token
        const response = await axios.post(
          `${API_CONFIG.baseURL}/api/auth/token/refresh/`,
          { refresh: refreshToken }
        );

        const { access } = response.data;
        
        // Store new token
        localStorage.setItem('access_token', access);

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return apiClient(originalRequest);
        
      } catch (refreshError) {
        // Refresh failed - logout user
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Redirect to login
        window.location.href = '/login';
        
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
```

---

### Step 3: Create API Service Files

**Create `src/api/auth.js`:**

```javascript
// src/api/auth.js
import apiClient from './client';
import { API_ENDPOINTS } from '../config/api.config';

export const authAPI = {
  // Sign up new user
  signup: async (userData) => {
    const response = await apiClient.post(API_ENDPOINTS.AUTH.SIGNUP, userData);
    
    // Store tokens returned at the top level
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    
    return response.data;
  },

  // Sign in existing user
  signin: async (credentials) => {
    const response = await apiClient.post(API_ENDPOINTS.AUTH.SIGNIN, credentials);
    
    // Store tokens returned at the top level
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    
    return response.data;
  },

  // Logout user
  logout: async () => {
    try {
      await apiClient.post(API_ENDPOINTS.AUTH.LOGOUT);
    } finally {
      // Always clear tokens
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  },

  // Check if user is authenticated
  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  },
};
```

**Create `src/api/assessment.js`:**

```javascript
// src/api/assessment.js
import apiClient from './client';
import { API_ENDPOINTS } from '../config/api.config';

export const assessmentAPI = {
  // Get or create active session
  getActiveSession: async () => {
    const response = await apiClient.get(API_ENDPOINTS.ASSESSMENT.ACTIVE);
    return response.data;
  },

  // Create new session
  createSession: async (sessionData) => {
    const response = await apiClient.post(API_ENDPOINTS.ASSESSMENT.CREATE, sessionData);
    return response.data;
  },

  // Get session by ID
  getSession: async (sessionId) => {
    const response = await apiClient.get(API_ENDPOINTS.ASSESSMENT.DETAIL(sessionId));
    return response.data;
  },

  // Save single answer
  saveAnswer: async (sessionId, questionId, value) => {
    const response = await apiClient.post(
      API_ENDPOINTS.ASSESSMENT.SAVE_ANSWER(sessionId),
      {
        question_id: questionId,
        answer_value: value,
      }
    );
    return response.data;
  },

  // Save multiple answers
  saveMultipleAnswers: async (sessionId, answers) => {
    const response = await apiClient.post(
      API_ENDPOINTS.ASSESSMENT.SAVE_MULTIPLE(sessionId),
      { answers }
    );
    return response.data;
  },

  // Advance to next question
  advanceQuestion: async (sessionId) => {
    const response = await apiClient.post(API_ENDPOINTS.ASSESSMENT.ADVANCE(sessionId));
    return response.data;
  },

  // Go back to previous question
  goBackQuestion: async (sessionId) => {
    const response = await apiClient.post(API_ENDPOINTS.ASSESSMENT.GO_BACK(sessionId));
    return response.data;
  },

  // Mark section as completed
  markSectionCompleted: async (sessionId, sectionName) => {
    const response = await apiClient.post(
      API_ENDPOINTS.ASSESSMENT.MARK_SECTION(sessionId),
      { section_name: sectionName }
    );
    return response.data;
  },

  // Submit assessment for scoring
  submitAssessment: async (sessionId) => {
    const response = await apiClient.post(API_ENDPOINTS.ASSESSMENT.SUBMIT(sessionId));
    return response.data;
  },
};
```

**Create `src/api/score.js`:**

```javascript
// src/api/score.js
import apiClient from './client';
import { API_ENDPOINTS } from '../config/api.config';

export const scoreAPI = {
  // Calculate user's score
  calculateScore: async (forceRecalculate = false) => {
    const response = await apiClient.post(API_ENDPOINTS.SCORE.CALCULATE, {
      force_recalculate: forceRecalculate,
    });
    return response.data;
  },

  // Get latest score
  getLatestScore: async () => {
    const response = await apiClient.get(API_ENDPOINTS.SCORE.LATEST);
    return response.data;
  },
};
```

---

### Step 4: Create Error Handler

**Create `src/utils/errorHandler.js`:**

```javascript
// src/utils/errorHandler.js

export function handleApiError(error) {
  // Network error (no response from server)
  if (!error.response) {
    if (error.request) {
      return {
        message: 'Network error. Please check your internet connection.',
        code: 'NETWORK_ERROR',
      };
    }
    return {
      message: error.message || 'An unexpected error occurred',
      code: 'UNKNOWN_ERROR',
    };
  }

  // Server responded with error
  const { status, data } = error.response;

  switch (status) {
    case 400:
      return {
        message: data.message || 'Invalid request. Please check your input.',
        code: 'BAD_REQUEST',
        details: data.details,
      };

    case 401:
      return {
        message: 'Your session has expired. Please login again.',
        code: 'UNAUTHORIZED',
      };

    case 403:
      return {
        message: 'You do not have permission to perform this action.',
        code: 'FORBIDDEN',
      };

    case 404:
      return {
        message: 'Resource not found.',
        code: 'NOT_FOUND',
      };

    case 429:
      return {
        message: 'Too many requests. Please slow down and try again.',
        code: 'RATE_LIMITED',
      };

    case 500:
    case 502:
    case 503:
      return {
        message: 'Server error. Please try again later.',
        code: 'SERVER_ERROR',
      };

    default:
      return {
        message: data.message || 'An error occurred. Please try again.',
        code: 'UNKNOWN_ERROR',
      };
  }
}

// Usage in components:
// try {
//   await someAPICall();
// } catch (error) {
//   const errorInfo = handleApiError(error);
//   console.error(errorInfo.message);
// }
```

---

### Step 5: Usage in React Components

**Example: Login Component**

```javascript
// src/pages/Login.jsx
import React, { useState } from 'react';
import { authAPI } from '../api/auth';
import { handleApiError } from '../utils/errorHandler';

function Login() {
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authAPI.signin({
        phone_number: phone,
        password: password,
      });

      // Redirect to assessment
      window.location.href = '/assessment';
      
    } catch (err) {
      const errorInfo = handleApiError(err);
      setError(errorInfo.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <h1>Login</h1>
      
      {error && <div className="error">{error}</div>}
      
      <input
        type="tel"
        placeholder="Phone Number"
        value={phone}
        onChange={(e) => setPhone(e.target.value)}
        required
      />
      
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}

export default Login;
```

**Example: Assessment Component**

```javascript
// src/pages/Assessment.jsx
import React, { useState, useEffect } from 'react';
import { assessmentAPI } from '../api/assessment';
import { scoreAPI } from '../api/score';
import { handleApiError } from '../utils/errorHandler';

function Assessment() {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadSession();
  }, []);

  const loadSession = async () => {
    try {
      const sessionData = await assessmentAPI.getActiveSession();
      setSession(sessionData.session_data);
    } catch (err) {
      const errorInfo = handleApiError(err);
      setError(errorInfo.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = async (questionId, value) => {
    try {
      const updated = await assessmentAPI.saveAnswer(session.id, questionId, value);
      setSession(updated);
    } catch (err) {
      const errorInfo = handleApiError(err);
      setError(errorInfo.message);
    }
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      
      // Submit assessment
      await assessmentAPI.submitAssessment(session.id);
      
      // Calculate score
      const scoreData = await scoreAPI.calculateScore();
      
      // Navigate to results
      window.location.href = `/score/${scoreData.score.score_id}`;
      
    } catch (err) {
      const errorInfo = handleApiError(err);
      setError(errorInfo.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>Assessment</h1>
      <p>Progress: {session.completion_percentage}%</p>
      
      {/* Your form fields here */}
      
      <button onClick={handleSubmit}>Submit Assessment</button>
    </div>
  );
}

export default Assessment;
```

---

## 🔄 Environment-Specific Configuration

### Development (Vite)
```env
VITE_API_BASE_URL=http://localhost:8000
```

### Development (Create React App)
```env
REACT_APP_API_BASE_URL=http://localhost:8000
```

### Staging
```env
VITE_API_BASE_URL=https://staging-api.yourdomain.com
```

### Production
```env
VITE_API_BASE_URL=https://api.yourdomain.com
```

### Vite Proxy Alternative (no CORS needed in dev)

Add this to `vite.config.js` to proxy all `/api` calls to Django — no `CORS_ALLOWED_ORIGINS` config needed:

```javascript
// vite.config.js
export default {
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
};
```

---

## ✅ Checklist

- [ ] Create `.env` file in project root
- [ ] Add `REACT_APP_API_BASE_URL=http://localhost:8000`
- [ ] Add `.env` to `.gitignore`
- [ ] Create `.env.example` for team
- [ ] Create `src/config/api.config.js`
- [ ] Create `src/api/client.js` with axios
- [ ] Create API service files (auth, assessment, score)
- [ ] Create error handler utility
- [ ] Test connection with simple API call
- [ ] Verify token storage and refresh works

---

## 🧪 Test Your Connection

**Create a test file to verify connection:**

```javascript
// src/api/test.js
import apiClient from './client';

export async function testConnection() {
  try {
    const response = await apiClient.get('/health/');
    console.log('✅ Backend connection successful:', response.data);
    return true;
  } catch (error) {
    console.error('❌ Backend connection failed:', error.message);
    return false;
  }
}

// Run in your App.js or component:
// import { testConnection } from './api/test';
// testConnection();
```

---

## 🚀 You're Ready!

Now you can start building your frontend with full access to all backend features:

- ✅ User authentication
- ✅ Assessment sessions
- ✅ Score calculation
- ✅ Real-time validation
- ✅ Progress tracking

**Next steps:**
1. Start the backend: `.venv\Scripts\python.exe manage.py runserver`
2. Start your frontend: `npm run dev` (Vite) or `npm start` (CRA)
3. Browse the live API docs: `http://localhost:8000/api/docs/`
