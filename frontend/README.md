# 🌐 1C AI Stack - Frontend Portal

The modern web interface for the 1C AI Stack platform. Built with React, TypeScript, and Vite.

## 🛠️ Tech Stack

- **Framework:** React 18.2
- **Language:** TypeScript 5.3
- **Build Tool:** Vite 5.0
- **Styling:** TailwindCSS 3.3 + Radix UI
- **State Management:** Zustand + TanStack Query
- **Charts:** Recharts

## ✨ Key Features

### 1. 🎭 Scenario Hub (`/scenarios`)
Manage and execute automation scenarios.
- Visual scenario builder
- Real-time execution logs
- Success rate analytics

### 2. 📝 Technical Writer (`/technical-writer`)
Generate documentation from your 1C code.
- API Documentation generator
- Mermaid diagram preview
- Export to Markdown/PDF

### 3. 🛡️ Security Dashboard (`/security`)
Monitor the security posture of your 1C configuration.
- Vulnerability scan results
- Dependency audit
- Compliance reports

### 4. 📊 Analytics Dashboard (`/dashboard`)
Comprehensive view of your development process.
- CI/CD metrics
- Code quality trends
- Team velocity

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
# 1. Install dependencies
npm install

# 2. Start development server
npm run dev
```

The application will be available at `http://localhost:3000`.

### Configuration

Create a `.env` file in the root directory:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/api/v1/ws
```

## 🏗️ Project Structure

```
src/
├── components/     # Reusable UI components
├── features/       # Feature-based modules (dashboard, scenarios, etc.)
├── hooks/          # Custom React hooks
├── services/       # API clients
├── stores/         # Global state (Zustand)
└── types/          # TypeScript definitions
```
