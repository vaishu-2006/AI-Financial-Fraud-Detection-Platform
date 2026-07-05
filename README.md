# AI Financial Fraud Detection & Risk Intelligence Platform

A production-grade fraud detection system featuring real-time ML scoring, explainable AI (SHAP), and comprehensive risk analytics.

## Features

- **Real-time Fraud Scoring**: Sub-100ms transaction risk assessment with Safe/Suspicious/Fraudulent labels
- **Explainable AI**: SHAP value explanations for every prediction with waterfall/force plot visualizations
- **ML Model Training**: Multiple algorithms (XGBoost, LightGBM, Random Forest, Neural Network) with automatic comparison
- **Anomaly Detection**: Isolation Forest, LOF, and Autoencoder for novel fraud patterns
- **Modern Dashboard**: React + TypeScript with Recharts visualizations
- **Role-Based Access Control**: Analyst, Manager, and Admin roles with JWT authentication
- **Production Ready**: Docker containerization, CI/CD pipeline, and cloud deployment

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                        │
│   React + TypeScript Frontend (Tailwind, Shadcn UI, Framer Motion, Recharts)│
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY (FastAPI)                              │
│   JWT Auth + RBAC + Rate Limiting + Input Validation                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
  ┌──────────────────────┐ ┌──────────────────┐ ┌──────────────────────┐
  │ Transaction Service  │ │   ML Service     │ │  Alert Service       │
  └──────────────────────┘ └──────────────────┘ └──────────────────────┘
                    │                 │                 │
                    └─────────────────┼─────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│   PostgreSQL (Supabase)    │    Redis Cache    │    Model Storage           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Tailwind CSS, Shadcn UI |
| Charts | Recharts |
| Animations | Framer Motion |
| Backend | FastAPI (Python 3.11+) |
| Database | PostgreSQL (Supabase) |
| Cache | Redis |
| ML | XGBoost, LightGBM, scikit-learn, SHAP |
| Container | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Deployment | Vercel (frontend), Render (backend) |

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Supabase account (free tier works)

### 1. Clone and Setup

```bash
git clone https://github.com/your-repo/fraud-detection-platform.git
cd fraud-detection-platform

# Copy environment variables
cp .env.example .env
```

### 2. Configure Environment Variables

Create a `.env` file with your Supabase credentials:

```env
# Supabase (from your Supabase project settings)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_DB_URL=your-database-url

# JWT Secret
JWT_SECRET_KEY=your-secure-secret-key

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### 3. Run Database Migrations

The database schema is automatically applied via Supabase migrations. Tables created:
- `users` - User profiles with roles
- `transactions` - Transaction records
- `fraud_labels` - Ground truth labels
- `models` - ML model registry
- `alerts` - Fraud alerts
- `audit_logs` - Audit trail

### 4. Start Development Environment

```bash
# Start all services
docker-compose up -d

# Or run separately:

# Backend
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000

# Frontend
npm install
npm run dev
```

Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user profile

### Transactions
- `GET /api/v1/transactions` - List transactions (paginated, filtered)
- `POST /api/v1/transactions` - Create transaction
- `POST /api/v1/transactions/upload` - Bulk upload CSV
- `GET /api/v1/transactions/{id}` - Get transaction details
- `PATCH /api/v1/transactions/{id}` - Update status

### Scoring
- `POST /api/v1/scoring/single` - Score single transaction
- `POST /api/v1/scoring/batch` - Batch scoring
- `GET /api/v1/scoring/explain/{id}` - Get SHAP explanation

### Models
- `GET /api/v1/models` - List trained models
- `GET /api/v1/models/active` - Get active model
- `POST /api/v1/models/train` - Start training job
- `POST /api/v1/models/{id}/deploy` - Deploy model

### Alerts
- `GET /api/v1/alerts` - List alerts
- `PATCH /api/v1/alerts/{id}` - Update alert status

### Reports
- `GET /api/v1/reports/dashboard` - Dashboard metrics
- `GET /api/v1/reports/risk-distribution` - Risk distribution
- `GET /api/v1/reports/timeseries` - Time series data

## ML Pipeline

### Feature Engineering

Automatic feature extraction includes:
- **Velocity Features**: Transaction count/amount in 1h, 6h, 24h, 168h windows
- **Customer Behavior**: Age, transaction patterns, amount percentiles
- **Time Features**: Hour of day, day of week, weekend/night flags
- **Location Features**: Country risk scores, device patterns
- **Cross Features**: Amount-time interactions, velocity combinations

### Model Training

```python
# Example training configuration
config = {
    "model_types": ["xgboost", "lightgbm"],
    "selection_metric": "f1_score",
    "train_test_split": 0.8,
    "time_based_split": True,
    "hyperparameter_tuning": True,
    "sampling_strategy": "smote",
    "random_seed": 42
}

# Start training via API
POST /api/v1/models/train
```

### Supported Algorithms

| Algorithm | Use Case | Pros |
|-----------|----------|------|
| XGBoost | General purpose | High accuracy, fast inference |
| LightGBM | Large datasets | Memory efficient, fast training |
| Random Forest | Baseline | Interpretable, robust |
| Logistic Regression | Interpretability | Simple, fast |

### Anomaly Detection

- **Isolation Forest**: Detect novel fraud patterns
- **Local Outlier Factor**: Density-based anomalies
- **Autoencoder**: Learn normal patterns, detect deviations

## SHAP Explainability

Every prediction includes SHAP values explaining:

```json
{
  "base_value": 0.35,
  "output_value": 0.72,
  "feature_contributions": [
    {"feature": "amount", "shap_value": 0.15, "explanation": "High amount increases risk"},
    {"feature": "is_night", "shap_value": 0.08, "explanation": "Night-time transaction"}
  ],
  "top_factors": [...]
}
```

Visualizations:
- Waterfall charts for single predictions
- Feature importance rankings
- Force plots for feature contributions

## Database Schema

### Entity Relationship Diagram

```
┌─────────────┐     ┌────────────────────┐     ┌─────────────┐
│   users     │────<│   transactions    │>────│   models    │
│─────────────│     │────────────────────│     │─────────────│
│ id          │     │ transaction_id     │     │ model_type  │
│ email       │     │ customer_id        │     │ metrics     │
│ role        │     │ merchant_id        │     │ is_active   │
│ created_at  │     │ amount             │     │ trained_at  │
└─────────────┘     │ risk_score         │     └─────────────┘
                    │ risk_label         │
                    └────────────────────┘
                           │
                    ┌──────┴──────┐
                    │ fraud_labels│
                    │─────────────│
                    │ is_fraud    │
                    │ source      │
                    └─────────────┘
```

## Deployment

### Vercel (Frontend)

1. Connect GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main

```bash
# Or use Vercel CLI
vercel --prod
```

### Render (Backend)

1. Create new Web Service on Render
2. Connect GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables

### Docker Deployment

```bash
# Build images
docker-compose build

# Push to registry
docker-compose push

# Deploy to your infrastructure
docker-compose -f docker-compose.prod.yml up -d
```

## Security

- **Authentication**: JWT tokens with refresh mechanism
- **Password Storage**: bcrypt hashing
- **Input Validation**: Pydantic models for all inputs
- **SQL Injection**: Parameterized queries via Supabase client
- **XSS Prevention**: React's built-in escaping
- **CSRF Protection**: SameSite cookies
- **Rate Limiting**: SlowAPI middleware
- **HTTPS**: Enforced in production
- **Secrets Management**: Environment variables, never in code

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=api --cov=ml

# Frontend tests
npm test
npm run typecheck
npm run lint
```

## Project Structure

```
.
├── app/                      # Next.js app router
│   ├── dashboard/           # Dashboard page
│   ├── transactions/        # Transaction management
│   ├── scoring/             # Real-time scoring
│   ├── models/              # Model management
│   └── alerts/              # Alert center
├── components/
│   ├── ui/                  # Shadcn UI components
│   ├── dashboard/           # Dashboard components
│   ├── layout/              # Layout components
│   └── scoring/             # Scoring components
├── lib/
│   ├── types.ts             # TypeScript interfaces
│   ├── api.ts               # API client
│   └── utils.ts             # Utilities
├── backend/
│   ├── api/
│   │   ├── routes/          # API route handlers
│   │   ├── middleware/      # Auth, rate limiting
│   │   └── main.py          # FastAPI app
│   ├── ml/
│   │   ├── feature_engineering/
│   │   ├── training/
│   │   ├── inference/
│   │   └── explainability/
│   └── requirements.txt
├── data/                    # Data and model storage
├── docs/                    # Documentation
├── docker-compose.yml
├── Dockerfile.frontend
└── .github/workflows/       # CI/CD
```

## License

MIT License - See LICENSE file for details.

## Acknowledgments

- [SHAP](https://github.com/slundberg/shap) for model explainability
- [XGBoost](https://github.com/dmlc/xgboost) and [LightGBM](https://github.com/microsoft/LightGBM)
- [Supabase](https://supabase.com) for backend infrastructure
- [Shadcn UI](https://ui.shadcn.com) for beautiful components
