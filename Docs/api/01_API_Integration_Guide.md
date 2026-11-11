# ECHS Backend API Integration Guide

## Table of Contents
1. [Configuration](#configuration)
2. [Authentication APIs](#authentication-apis)
3. [Assessment Session APIs](#assessment-session-apis)
4. [Score Calculation APIs](#score-calculation-apis)
5. [Validation APIs](#validation-apis)
6. [Landing Page APIs](#landing-page-apis)
7. [Error Handling](#error-handling)
8. [Example Usage](#example-usage)

---

## Configuration

### Backend URL Setup

**Development Environment (.env file):**
```env
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_API_TIMEOUT=30000
```

**Production Environment:**
```env
REACT_APP_API_BASE_URL=https://api.yourdomain.com
REACT_APP_API_TIMEOUT=30000
```

### Axios Configuration (Recommended)

Create an API client file (e.g., `src/services/api.js`):

```javascript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for cookies/sessions
});

// Request interceptor - add JWT token to headers
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retried, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(
          `${API_BASE_URL}/api/auth/token/refresh/`,
          { refresh: refreshToken }
        );

        const { access } = response.data;
        localStorage.setItem('access_token', access);

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
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

## Authentication APIs

### 1. User Signup

**Endpoint:** `POST /api/auth/signup/`

**Request Body:**
```json
{
  "phone_number": "+26878123456",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!",
  "email": "john@example.com",
  "full_name": "John Doe",
  "registration_channel": "web",
  "preferred_language": "en"
}
```

**Response (Success - 201):**
```json
{
  "message": "User registered successfully.",
  "user_id": "uuid-here",
  "phone_number": "+26878123456",
  "access_token": "jwt-access-token",
  "refresh_token": "jwt-refresh-token",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Rate Limit:** 5 requests per hour per IP

**Example:**
```javascript
import apiClient from './api';

async function signup(userData) {
  try {
    const response = await apiClient.post('/api/auth/signup/', userData);
    
    // Store tokens
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    
    return response.data;
  } catch (error) {
    console.error('Signup error:', error.response?.data);
    throw error;
  }
}
```

---

### 2. User Signin

**Endpoint:** `POST /api/auth/signin/`

**Request Body:**
```json
{
  "phone_number": "+26878123456",
  "password": "SecurePass123!"
}
```

**Response (Success - 200):**
```json
{
  "message": "Authentication successful.",
  "user_id": "uuid-here",
  "phone_number": "+26878123456",
  "access_token": "jwt-access-token",
  "refresh_token": "jwt-refresh-token",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Rate Limit:** 10 requests per hour per IP

---

### 3. Token Refresh

**Endpoint:** `POST /api/auth/token/refresh/`

**Request Body:**
```json
{
  "refresh": "jwt-refresh-token"
}
```

**Response (Success - 200):**
```json
{
  "access": "new-jwt-access-token"
}
```

---

### 4. Logout

**Endpoint:** `POST /api/auth/auth-logout/`

**Headers Required:** `Authorization: Bearer {access_token}`

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**Example:**
```javascript
async function logout() {
  try {
    await apiClient.post('/api/auth/auth-logout/');
    
    // Clear local storage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    window.location.href = '/login';
  } catch (error) {
    console.error('Logout error:', error);
  }
}
```

---

## Assessment Session APIs

### 1. Create New Assessment Session

**Endpoint:** `POST /api/assessment-sessions/`

**Headers Required:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "session_name": "My Assessment",
  "device_type": "desktop",
  "user_agent": "Mozilla/5.0..."
}
```

**Response (Success - 201):**
```json
{
  "id": "session-uuid",
  "user": "user-uuid",
  "session_name": "My Assessment",
  "current_question": 1,
  "current_section": "financial_obligations",
  "form_answers": {},
  "completed_sections": [],
  "skipped_questions": [],
  "status": "in_progress",
  "start_time": "2024-01-15T10:00:00Z",
  "expires_at": "2024-02-14T10:00:00Z",
  "completion_percentage": 0,
  "is_expired": false,
  "is_active": true,
  "time_remaining_days": 30,
  "answered_question_count": 0
}
```

---

### 2. Get Active Session

**Endpoint:** `GET /api/assessment-sessions/active-session/`

**Headers Required:** `Authorization: Bearer {access_token}`

**Response (Success - 200):**
```json
{
  "session_id": "session-uuid",
  "current_question": 5,
  "current_section": "income_employment",
  "completion_percentage": 15,
  "last_saved_at": "2024-01-15T10:30:00Z",
  "time_remaining_days": 28,
  "session_data": {
    "id": "session-uuid",
    "form_answers": {},
    "completed_sections": ["financial_obligations"],
    "status": "in_progress"
  }
}
```

**Note:** If no active session exists, a new one will be created automatically.

---

### 3. Save Single Answer

**Endpoint:** `POST /api/assessment-sessions/{session_id}/save_answer/`

**Headers Required:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "question_id": "income_employment_monthly_income",
  "answer_value": 15000
}
```

**Response (Success - 200):**
```json
{
  "id": "session-uuid",
  "form_answers": {
    "income_employment_monthly_income": 15000
  },
  "completion_percentage": 2,
  "current_question": 5
}
```

**Example:**
```javascript
async function saveAnswer(sessionId, questionId, value) {
  try {
    const response = await apiClient.post(
      `/api/assessment-sessions/${sessionId}/save_answer/`,
      {
        question_id: questionId,
        answer_value: value
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error saving answer:', error);
    throw error;
  }
}
```

---

### 4. Save Multiple Answers (Bulk Save)

**Endpoint:** `POST /api/assessment-sessions/{session_id}/save_multiple_answers/`

**Headers Required:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "answers": {
    "income_employment_monthly_income": 15000,
    "income_employment_employment_status": "employed",
    "income_employment_employer_name": "ABC Company"
  }
}
```

**Response (Success - 200):**
```json
{
  "id": "session-uuid",
  "form_answers": {},
  "completion_percentage": 8,
  "answered_question_count": 3
}
```

---

### 5. Navigate Questions

**Advance to Next Question:**
```
POST /api/assessment-sessions/{session_id}/advance_question/
```

**Go Back to Previous Question:**
```
POST /api/assessment-sessions/{session_id}/go_back_question/
```

**Response (Success - 200):**
```json
{
  "id": "session-uuid",
  "current_question": 6,
  "current_section": "income_employment"
}
```

---

### 6. Mark Section Completed

**Endpoint:** `POST /api/assessment-sessions/{session_id}/mark_section_completed/`

**Headers Required:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "section_name": "income_employment"
}
```

**Response (Success - 200):**
```json
{
  "id": "session-uuid",
  "completed_sections": ["financial_obligations", "income_employment"],
  "completion_percentage": 22
}
```

---

### 7. Submit Assessment for Scoring

**Endpoint:** `POST /api/assessment-sessions/{session_id}/mark_completed/`

**Headers Required:** `Authorization: Bearer {access_token}`

**Response (Success - 200):**
```json
{
  "id": "session-uuid",
  "status": "submitted",
  "completed_at": "2024-01-15T12:00:00Z",
  "completion_percentage": 100
}
```

**Example Flow:**
```javascript
async function submitAssessment(sessionId) {
  try {
    // 1. Mark assessment as completed
    const session = await apiClient.post(
      `/api/assessment-sessions/${sessionId}/mark_completed/`
    );
    
    // 2. Trigger score calculation
    const scoreResponse = await apiClient.post(
      '/api/score-calculation/calculate/'
    );
    
    return scoreResponse.data;
  } catch (error) {
    console.error('Error submitting assessment:', error);
    throw error;
  }
}
```

---

## Score Calculation APIs

### 1. Calculate Score

**Endpoint:** `POST /api/score-calculation/calculate/`

**Headers Required:** `Authorization: Bearer {access_token}`

**Request Body (Optional):**
```json
{
  "force_recalculate": false
}
```

**Response (Success - 200):**
```json
{
  "success": true,
  "score": {
    "composite_score": 720,
    "score_band": "good",
    "score_band_display": "Good (650-749)",
    "calculated_at": "2024-01-15T14:30:00Z",
    "pillar_scores": {
      "financial_obligations": 75,
      "income_employment": 82,
      "mobile_money": 68,
      "assets": 71,
      "savings_banking": 79,
      "expense_management": 73,
      "household_profile": 65,
      "financial_literacy": 77,
      "business_profile": 70
    },
    "pillar_breakdown": {
      "financial_obligations": {
        "score": 75,
        "weight": 15.0,
        "contribution": 11.25,
        "status": "complete"
      },
      "income_employment": {
        "score": 82,
        "weight": 15.0,
        "contribution": 12.3,
        "status": "complete"
      }
    },
    "validation_flags": [
      {
        "flag_type": "outlier_income",
        "severity": "warning",
        "message": "Income appears unusually high for reported employment",
        "impact": -5
      }
    ],
    "honesty_bonus": 3,
    "validation_adjustment": -2,
    "is_sufficient_data": true,
    "missing_sections": [],
    "score_id": "score-uuid"
  }
}
```

**Error Response (Insufficient Data - 400):**
```json
{
  "success": false,
  "error": "insufficient_data",
  "message": "Not enough data to calculate score",
  "missing_sections": ["financial_obligations", "assets"],
  "completed_sections": 3,
  "required_sections": 5
}
```

**Score Bands:**
- **Poor:** 300-449 (red)
- **Weak:** 450-549 (orange)
- **Fair:** 550-649 (yellow)
- **Good:** 650-749 (light green)
- **Excellent:** 750-850 (dark green)

---

### 2. Get Latest Score

**Endpoint:** `GET /api/score-calculation/latest/`

**Headers Required:** `Authorization: Bearer {access_token}`

**Response (Success - 200):** Same structure as Calculate Score

**Response (No Score - 404):**
```json
{
  "success": false,
  "error": "no_score",
  "message": "No score calculation found. Please complete your assessment first."
}
```

**Example:**
```javascript
async function getLatestScore() {
  try {
    const response = await apiClient.get('/api/score-calculation/latest/');
    return response.data.score;
  } catch (error) {
    if (error.response?.status === 404) {
      console.log('No score found. User needs to complete assessment.');
    }
    throw error;
  }
}
```

---

## Validation APIs

### 1. Validate Single Field

**Endpoint:** `POST /api/assessments/validate-field/`

**Headers Required:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "question_id": "income_employment_monthly_income",
  "field_value": 15000,
  "context": {
    "expense_management_monthly_expenses": 8000
  }
}
```

**Response (Success - 200):**
```json
{
  "question_id": "income_employment_monthly_income",
  "is_valid": true,
  "status": "valid",
  "error_message": "",
  "warning_message": "",
  "suggestions": [],
  "field_metadata": {
    "numeric_value": 15000,
    "validation_time_ms": 45
  }
}
```

**Response (Invalid):**
```json
{
  "question_id": "income_employment_monthly_income",
  "is_valid": false,
  "status": "invalid",
  "error_message": "Monthly income must be between 100 and 500,000",
  "warning_message": "",
  "suggestions": ["Please enter a value between 100 and 500,000"],
  "field_metadata": {
    "validation_time_ms": 32
  }
}
```

**Rate Limit:** 30 requests per minute per user

**Example:**
```javascript
async function validateField(questionId, value, context = {}) {
  try {
    const response = await apiClient.post('/api/assessments/validate-field/', {
      question_id: questionId,
      field_value: value,
      context: context
    });
    return response.data;
  } catch (error) {
    if (error.response?.status === 429) {
      console.error('Rate limit exceeded. Please slow down.');
    }
    throw error;
  }
}

// Usage in React component
const handleInputChange = async (questionId, value) => {
  const validation = await validateField(questionId, value);
  
  if (!validation.is_valid) {
    setError(validation.error_message);
  } else {
    setError('');
  }
};
```

---

### 2. Batch Validate Multiple Fields

**Endpoint:** `POST /api/assessments/batch-validate/`

**Headers Required:** `Authorization: Bearer {access_token}`

**Request Body:**
```json
{
  "fields": {
    "income_employment_monthly_income": 15000,
    "expense_management_monthly_expenses": 8000,
    "savings_banking_monthly_savings": 2000
  }
}
```

**Response (Success - 200):**
```json
{
  "results": {
    "income_employment_monthly_income": {
      "is_valid": true,
      "status": "valid",
      "error_message": "",
      "warning_message": "",
      "suggestions": []
    },
    "expense_management_monthly_expenses": {
      "is_valid": true,
      "status": "valid",
      "error_message": "",
      "warning_message": "Expenses seem high relative to income",
      "suggestions": []
    }
  },
  "overall_valid": true,
  "total_fields": 3,
  "valid_fields": 3,
  "invalid_fields": 0
}
```

**Rate Limit:** 10 requests per minute per user

---

### 3. Get Field Validation Schema

**Endpoint:** `GET /api/assessments/field-schema/`

**Query Parameters:**
- `question_id` (optional): Get schema for specific field

**Example:**
```
GET /api/assessments/field-schema/?question_id=income_employment_monthly_income
```

**Response (Success - 200):**
```json
{
  "income_employment_monthly_income": {
    "type": "number",
    "required": true,
    "min_value": 100,
    "max_value": 500000,
    "label": "Monthly Income",
    "help_text": "Enter your total monthly income in SZL"
  }
}
```

---

## Landing Page APIs

### Get Landing Page Configuration

**Endpoint:** `GET /api/landing/config/`

**Headers Required:** None (public endpoint)

**Response (Success - 200):**
```json
{
  "cta_text": "Take Credit Score",
  "cta_subtitle": "Assess your financial health today",
  "testimonials": [
    {
      "name": "Thandi M.",
      "improvement": 140,
      "quote": "ECHS helped me improve from 580 to 720 in 6 months",
      "year": 2024
    }
  ],
  "metrics": {
    "users_assessed": 15000,
    "average_score_improvement": 82,
    "users_improved": 12500,
    "satisfaction_rate": 0.94
  },
  "score_range_info": {
    "min_score": 300,
    "max_score": 850,
    "bands": [
      {"name": "Poor", "min": 300, "max": 449, "color": "red"},
      {"name": "Weak", "min": 450, "max": 549, "color": "orange"},
      {"name": "Fair", "min": 550, "max": 649, "color": "yellow"},
      {"name": "Good", "min": 650, "max": 749, "color": "lightgreen"},
      {"name": "Excellent", "min": 750, "max": 850, "color": "darkgreen"}
    ]
  },
  "features": [
    {
      "title": "2-Minute Assessment",
      "description": "Complete your financial health assessment quickly",
      "icon": "clock"
    }
  ]
}
```

---

## Error Handling

### Common Error Codes

| Status Code | Meaning | Action |
|------------|---------|--------|
| 400 | Bad Request | Check request body format |
| 401 | Unauthorized | Token expired, refresh or login |
| 403 | Forbidden | User doesn't have permission |
| 404 | Not Found | Resource doesn't exist |
| 429 | Rate Limit | Too many requests, slow down |
| 500 | Server Error | Backend issue, try again later |

### Error Response Format

```json
{
  "success": false,
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {}
}
```

### Global Error Handler

```javascript
// src/utils/errorHandler.js
export function handleApiError(error) {
  if (error.response) {
    // Server responded with error
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        return data.message || 'Invalid request';
      case 401:
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        return 'Session expired. Please login again.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return 'Resource not found.';
      case 429:
        return 'Too many requests. Please slow down.';
      case 500:
        return 'Server error. Please try again later.';
      default:
        return data.message || 'An error occurred';
    }
  } else if (error.request) {
    // Request made but no response
    return 'Network error. Please check your connection.';
  } else {
    // Error setting up request
    return error.message || 'An unexpected error occurred';
  }
}
```

---

## Example Usage

### Complete Assessment Flow

```javascript
// src/services/assessmentService.js
import apiClient from './api';
import { handleApiError } from '../utils/errorHandler';

class AssessmentService {
  // Start or resume assessment
  async getActiveSession() {
    try {
      const response = await apiClient.get('/api/assessment-sessions/active-session/');
      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  }

  // Save answer with validation
  async saveAnswer(sessionId, questionId, value) {
    try {
      // Validate first
      const validation = await apiClient.post('/api/assessments/validate-field/', {
        question_id: questionId,
        field_value: value
      });

      if (!validation.data.is_valid) {
        throw new Error(validation.data.error_message);
      }

      // Save if valid
      const response = await apiClient.post(
        `/api/assessment-sessions/${sessionId}/save_answer/`,
        {
          question_id: questionId,
          answer_value: value
        }
      );

      return response.data;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  }

  // Complete assessment and get score
  async submitAndCalculateScore(sessionId) {
    try {
      // Mark as completed
      await apiClient.post(`/api/assessment-sessions/${sessionId}/mark_completed/`);

      // Calculate score
      const scoreResponse = await apiClient.post('/api/score-calculation/calculate/');

      if (!scoreResponse.data.success) {
        throw new Error(scoreResponse.data.message);
      }

      return scoreResponse.data.score;
    } catch (error) {
      throw new Error(handleApiError(error));
    }
  }
}

export default new AssessmentService();
```

### React Component Example

```jsx
// src/components/AssessmentForm.jsx
import React, { useState, useEffect } from 'react';
import AssessmentService from '../services/assessmentService';

function AssessmentForm() {
  const [session, setSession] = useState(null);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadSession();
  }, []);

  async function loadSession() {
    try {
      const sessionData = await AssessmentService.getActiveSession();
      setSession(sessionData.session_data);
      setAnswers(sessionData.session_data.form_answers);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAnswerChange(questionId, value) {
    try {
      const updated = await AssessmentService.saveAnswer(
        session.id,
        questionId,
        value
      );
      setSession(updated);
      setAnswers(updated.form_answers);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSubmit() {
    try {
      setLoading(true);
      const score = await AssessmentService.submitAndCalculateScore(session.id);
      
      // Navigate to score page
      window.location.href = `/score/${score.score_id}`;
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>Assessment Progress: {session.completion_percentage}%</h1>
      {/* Render form fields */}
      <button onClick={handleSubmit}>Submit Assessment</button>
    </div>
  );
}

export default AssessmentForm;
```

---

## CORS Configuration

The backend is configured to accept requests from:
- `http://localhost:5173` (Vite default ✅)
- `http://127.0.0.1:5173`
- `http://localhost:3000` (Create React App default)
- `http://127.0.0.1:3000`
- `http://localhost:8080`

**To add more origins**, update `CORS_ALLOWED_ORIGINS` in the backend `.env` file:

```env
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,https://yourfrontend.com
```

---

## Security Best Practices

1. **Always use HTTPS in production**
2. **Store JWT tokens in localStorage** (handled in examples)
3. **Include Authorization header** for authenticated requests
4. **Handle token refresh** automatically (see axios interceptor)
5. **Validate user input** before sending to API
6. **Handle rate limits** gracefully
7. **Never expose sensitive data** in logs or error messages

---

## Support and Documentation

- **API Base URL (Dev):** `http://localhost:8000`
- **Django Admin:** `http://localhost:8000/admin/`
- **Health Check:** `http://localhost:8000/health/`
- **Swagger UI (API Docs):** `http://localhost:8000/api/docs/`
- **ReDoc:** `http://localhost:8000/api/docs/redoc/`

For questions or issues, contact the backend team.
