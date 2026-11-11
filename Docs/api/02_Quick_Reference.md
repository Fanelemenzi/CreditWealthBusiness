# ECHS Backend API - Quick Reference

## 🔧 Configuration

### Set API Base URL in your frontend `.env` file:

**For Vite (React + Vite):**
```env
VITE_API_BASE_URL=http://localhost:8000
```

**For Create React App:**
```env
REACT_APP_API_BASE_URL=http://localhost:8000
```

### Import and use in your code:

**Vite:**
```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
```

**Create React App:**
```javascript
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
```

---

## 🔐 Authentication Endpoints

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/api/auth/signup/` | POST | Register new user | No |
| `/api/auth/signin/` | POST | Login user | No |
| `/api/auth/token/refresh/` | POST | Refresh JWT token | No |
| `/api/auth/verify-phone/` | POST | Verify phone via SMS code | No |
| `/api/auth/auth-logout/` | POST | Logout user | Yes |

### Token Storage:
```javascript
// After login/signup
localStorage.setItem('access_token', response.data.access_token);
localStorage.setItem('refresh_token', response.data.refresh_token);

// Add to requests
headers: { 'Authorization': `Bearer ${localStorage.getItem('access_token')}` }
```

---

## 📝 Assessment Session Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/assessment-sessions/` | POST | Create new session |
| `/api/assessment-sessions/active-session/` | GET | Get/create active session |
| `/api/assessment-sessions/{id}/` | GET | Get session details |
| `/api/assessment-sessions/{id}/save_answer/` | POST | Save single answer |
| `/api/assessment-sessions/{id}/save_multiple_answers/` | POST | Save multiple answers |
| `/api/assessment-sessions/{id}/advance_question/` | POST | Next question |
| `/api/assessment-sessions/{id}/go_back_question/` | POST | Previous question |
| `/api/assessment-sessions/{id}/mark_section_completed/` | POST | Complete section |
| `/api/assessment-sessions/{id}/mark_completed/` | POST | Submit for scoring |

### Key Request/Response Examples:

**Save Answer:**
```javascript
POST /api/assessment-sessions/{id}/save_answer/
Body: {
  "question_id": "income_employment_monthly_income",
  "answer_value": 15000
}
```

**Save Multiple:**
```javascript
POST /api/assessment-sessions/{id}/save_multiple_answers/
Body: {
  "answers": {
    "question_id_1": "value1",
    "question_id_2": "value2"
  }
}
```

---

## 📊 Score Calculation Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/score-calculation/calculate/` | POST | Calculate user's score |
| `/api/score-calculation/latest/` | GET | Get latest score |

### Score Response Structure:
```javascript
{
  "success": true,
  "score": {
    "composite_score": 720,           // 300-850 range
    "score_band": "good",              // poor/weak/fair/good/excellent
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
        "weight": 15.0,               // Percentage
        "contribution": 11.25,        // Actual contribution to final score
        "status": "complete"
      }
      // ... other pillars
    },
    "validation_flags": [
      {
        "flag_type": "outlier_income",
        "severity": "warning",
        "message": "Income appears unusually high",
        "impact": -5
      }
    ],
    "honesty_bonus": 3,
    "validation_adjustment": -2,
    "is_sufficient_data": true,
    "missing_sections": [],
    "score_id": "uuid"
  }
}
```

### Score Bands:
- **Poor**: 300-449 (🔴 red)
- **Weak**: 450-549 (🟠 orange)
- **Fair**: 550-649 (🟡 yellow)
- **Good**: 650-749 (🟢 light green)
- **Excellent**: 750-850 (🟢 dark green)

---

## ✅ Validation Endpoints

| Endpoint | Method | Purpose | Rate Limit |
|----------|--------|---------|-----------|
| `/api/assessments/validate-field/` | POST | Validate single field | 30/min |
| `/api/assessments/batch-validate/` | POST | Validate multiple fields | 10/min |
| `/api/assessments/field-schema/` | GET | Get field validation rules | None |

### Validation Request:
```javascript
POST /api/assessments/validate-field/
Body: {
  "question_id": "income_employment_monthly_income",
  "field_value": 15000,
  "context": {
    "expense_management_monthly_expenses": 8000
  }
}
```

### Validation Response:
```javascript
{
  "question_id": "income_employment_monthly_income",
  "is_valid": true,
  "status": "valid",            // valid/invalid/warning/error
  "error_message": "",
  "warning_message": "",
  "suggestions": [],
  "field_metadata": {
    "validation_time_ms": 45
  }
}
```

---

## 🏠 Landing Page Endpoints

| Endpoint | Method | Auth Required |
|----------|--------|---------------|
| `/api/landing/config/` | GET | No |

Returns testimonials, metrics, score ranges, and feature list.

---

## 🚨 Error Handling

### HTTP Status Codes:

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Process response |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Check request format |
| 401 | Unauthorized | Refresh token or redirect to login |
| 403 | Forbidden | User lacks permission |
| 404 | Not Found | Resource doesn't exist |
| 429 | Rate Limited | Slow down requests |
| 500 | Server Error | Retry or show error message |

### Standard Error Response:
```javascript
{
  "success": false,
  "error": "error_code",
  "message": "Human-readable message",
  "details": {}
}
```

---

## 📱 Complete User Flow

### 1. User Signs Up
```javascript
POST /api/auth/signup/
→ Store tokens in localStorage
```

### 2. User Takes Assessment
```javascript
// Get or create session
GET /api/assessment-sessions/active-session/

// Save answers as user fills form
POST /api/assessment-sessions/{id}/save_answer/
// or
POST /api/assessment-sessions/{id}/save_multiple_answers/

// Navigate questions
POST /api/assessment-sessions/{id}/advance_question/
POST /api/assessment-sessions/{id}/go_back_question/

// Mark sections complete
POST /api/assessment-sessions/{id}/mark_section_completed/
Body: { "section_name": "income_employment" }
```

### 3. User Completes Assessment
```javascript
// Submit for scoring
POST /api/assessment-sessions/{id}/mark_completed/

// Calculate score
POST /api/score-calculation/calculate/
→ Returns full score breakdown
```

### 4. User Views Score
```javascript
// Get latest score anytime
GET /api/score-calculation/latest/
→ Returns score with pillars and recommendations
```

---

## 🔑 Required Headers

### For Authenticated Requests:
```javascript
{
  'Content-Type': 'application/json',
  'Authorization': 'Bearer YOUR_ACCESS_TOKEN_HERE'
}
```

### With Axios:
```javascript
axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
```

---

## ⚡ Rate Limits

| Endpoint | Limit |
|----------|-------|
| Signup | 5 per hour per IP |
| Signin | 10 per hour per IP |
| Field Validation | 30 per minute per user |
| Batch Validation | 10 per minute per user |
| Phone Verification | 5 per 10 minutes per IP |

---

## 🎯 Key Features for Frontend

### Assessment Features:
✅ Session persistence (30-day expiration)  
✅ Auto-save functionality  
✅ Question navigation (forward/backward)  
✅ Section progress tracking  
✅ Real-time validation  
✅ Skip optional questions  
✅ Resume incomplete assessments  

### Score Features:
✅ 9 financial pillars  
✅ Weighted scoring (300-850 range)  
✅ Score bands (Poor to Excellent)  
✅ Pillar breakdown with contributions  
✅ Validation flags and warnings  
✅ Honesty bonus tracking  

### Security Features:
✅ JWT token authentication  
✅ Automatic token refresh  
✅ Rate limiting  
✅ CORS protection  
✅ Encrypted sensitive data  
✅ Session expiration  

---

## 📝 9 Assessment Sections

1. **Financial Obligations** (Weight: 15%)
2. **Income & Employment** (Weight: 15%)
3. **Mobile Money** (Weight: 12%)
4. **Assets** (Weight: 12%)
5. **Savings & Banking** (Weight: 12%)
6. **Expense Management** (Weight: 12%)
7. **Household Profile** (Weight: 8%)
8. **Financial Literacy** (Weight: 8%)
9. **Business Profile** (Weight: 6%)

---

## 💡 Pro Tips

1. **Always handle token refresh** - Use axios interceptors
2. **Validate before saving** - Use validation endpoint first
3. **Auto-save frequently** - Don't wait for user to click save
4. **Show progress** - Use `completion_percentage` field
5. **Handle rate limits** - Debounce validation requests
6. **Cache landing page data** - It rarely changes
7. **Show time remaining** - Use `time_remaining_days` field
8. **Display validation flags** - Show warnings from score response

---

## 🔗 Quick Links

- **Backend URL (Dev):** `http://localhost:8000`
- **Admin Panel:** `http://localhost:8000/admin/`
- **Health Check:** `http://localhost:8000/health/`
- **Swagger UI:** `http://localhost:8000/api/docs/`
- **ReDoc:** `http://localhost:8000/api/docs/redoc/`

---

## 📞 Need Help?

Check the full API Integration Guide for:
- Complete request/response examples
- Error handling patterns
- React component examples
- Security best practices
- Advanced features
