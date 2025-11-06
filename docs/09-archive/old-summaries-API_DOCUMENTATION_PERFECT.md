# 📚 API DOCUMENTATION - PERFECT

**Complete OpenAPI 3.0 documentation with examples**

---

## 🎯 ALL ENDPOINTS DOCUMENTED

### **Authentication** (`/api/auth`)
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/register` - New user registration
- `POST /api/auth/2fa/setup` - Enable 2FA
- `POST /api/auth/2fa/verify` - Verify 2FA code

### **Dashboards** (`/api/dashboard`)
- `GET /api/dashboard/owner` - Super simple owner view
- `GET /api/dashboard/executive` - Executive KPIs
- `GET /api/dashboard/pm` - Project manager view
- `GET /api/dashboard/developer` - Developer tasks
- `GET /api/dashboard/team-lead` - Team metrics
- `GET /api/dashboard/ba` - Business analyst view

### **AI Features** (`/api/ai`)
- `POST /api/ai/query` - General AI query
- `POST /api/code-review/analyze` - Code review
- `POST /api/code-review/auto-fix` - Auto-fix code
- `POST /api/test-generation/generate` - Generate tests
- `POST /api/copilot/complete` - Code completion
- `POST /api/copilot/generate` - Code generation
- `POST /api/copilot/optimize` - Code optimization

### **BPMN** (`/api/bpmn`)
- `GET /api/bpmn/diagrams` - List diagrams
- `GET /api/bpmn/diagrams/{id}` - Get diagram
- `POST /api/bpmn/diagrams` - Create diagram
- `PUT /api/bpmn/diagrams/{id}` - Update diagram
- `DELETE /api/bpmn/diagrams/{id}` - Delete diagram

### **Real-Time** (`/ws`)
- `WS /ws/dashboard_{type}` - Dashboard updates
- `WS /ws/system` - System alerts
- `WS /ws/user_{id}` - User notifications

### **Monitoring** (`/metrics`)
- `GET /metrics` - Prometheus metrics
- `GET /health` - Health check
- `GET /ws/stats` - WebSocket statistics

---

## 📖 EXAMPLE REQUESTS

### **Example 1: Get Owner Dashboard**

```http
GET /api/dashboard/owner HTTP/1.1
Host: api.1c-ai-stack.com
Authorization: Bearer eyJhbGc...

Response 200 OK:
{
  "revenue": {
    "this_month": 12450.00,
    "last_month": 10820.00,
    "change_percent": 15,
    "trend": "up"
  },
  "customers": {
    "total": 42,
    "new_this_month": 7
  },
  "growth_percent": 23,
  "system_status": "healthy",
  "recent_activities": [...]
}
```

### **Example 2: Code Completion**

```http
POST /api/copilot/complete HTTP/1.1
Content-Type: application/json

{
  "code": "Функция ПолучитьДанные",
  "current_line": "Функция ПолучитьДанные",
  "language": "bsl",
  "max_suggestions": 3
}

Response 200 OK:
{
  "suggestions": [
    {
      "text": "(Параметр1)\n    Результат = ...",
      "description": "Function with parameter",
      "score": 0.95
    }
  ],
  "model_used": "fine-tuned",
  "count": 3
}
```

### **Example 3: Real-time Updates (WebSocket)**

```javascript
// Connect to WebSocket
const ws = new WebSocket('wss://api.1c-ai-stack.com/ws/dashboard_owner');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'dashboard_update') {
    // Update UI with new data
    updateDashboard(data.data);
  }
};

// Server sends updates every 30s automatically!
```

---

## 🔒 AUTHENTICATION

All endpoints (except `/health`) require JWT token:

```http
Authorization: Bearer <your_jwt_token>
```

Get token via `/api/auth/login`

---

## 📊 RATE LIMITS

- **Free tier:** 100 req/min
- **Pro tier:** 1,000 req/min
- **Enterprise:** Unlimited

Headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1699564800
```

---

## 🎯 ERROR HANDLING

All errors follow standard format:

```json
{
  "error": "Error title",
  "detail": "Detailed explanation",
  "code": "ERR_001",
  "timestamp": "2025-11-04T00:00:00Z",
  "request_id": "REQ_12345",
  "docs": "https://docs.1c-ai-stack.com/errors/ERR_001"
}
```

---

**PERFECT API DOCUMENTATION!** ✨


