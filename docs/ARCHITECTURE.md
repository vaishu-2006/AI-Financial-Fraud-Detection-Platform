# AI Financial Fraud Detection & Risk Intelligence Platform

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  React + TypeScript Frontend (Tailwind CSS, Shadcn UI, Framer Motion) │  │
│  │  - Dashboard with Risk Metrics                                        │  │
│  │  - Transaction Management (Search, Filter, Pagination)               │  │
│  │  - Real-time Scoring Interface                                        │  │
│  │  - SHAP Explainability Visualizations (Recharts)                     │  │
│  │  - Model Management Console                                            │  │
│  │  - Alert Center & Reports                                              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY LAYER                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Backend (Python 3.11+)                                       │  │
│  │  - JWT Authentication + RBAC (Analyst, Manager, Admin)                │  │
│  │  - Rate Limiting (Redis-backed)                                        │  │
│  │  - Input Validation (Pydantic)                                         │  │
│  │  - CORS, Security Headers                                              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
┌──────────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│  TRANSACTION SERVICE │  │  ML SERVICE      │  │  ALERT SERVICE       │
│  - CRUD Operations   │  │  - Scoring API   │  │  - Alert Generation  │
│  - CSV Ingestion     │  │  - Model Training│  │  - Notification      │
│  - Search & Filter   │  │  - SHAP Values   │  │  - Report Generation │
│  - Export            │  │  - Model Registry│  │                      │
└──────────────────────┘  └──────────────────┘  └──────────────────────┘
                    │                 │                 │
                    └─────────────────┼─────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                         │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │  PostgreSQL         │  │  Redis Cache        │  │  Model Storage      │  │
│  │  (Supabase)         │  │  - Session Cache    │  │  - Serialized ML    │  │
│  │  - Users            │  │  - Feature Cache    │  │    Models (.pkl)    │  │
│  │  - Transactions     │  │  - Rate Limits      │  │  - SHAP Explainers  │  │
│  │  - Fraud Labels     │  │  - Scoring Results  │  │  - Feature Configs  │  │
│  │  - Model Registry   │  │                     │  │                     │  │
│  │  - Alerts           │  │                     │  │                     │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Frontend (React + TypeScript)
- **Dashboard**: Real-time fraud metrics, risk score distribution, transaction volume trends
- **Transaction Management**: Upload CSV, view/search/filter transactions, manual review
- **Scoring Interface**: Single transaction scoring with real-time results
- **Explainability**: SHAP waterfall charts, force plots, feature importance rankings
- **Model Management**: Train models, compare performance, select active model
- **Alerts**: View fraud alerts, mark as reviewed, generate reports

### Backend API (FastAPI)
- **Auth Service**: JWT token generation, role-based access control
- **Transaction Service**: CRUD, bulk import, search/filter, export
- **ML Service**: Real-time scoring, model training pipeline, SHAP computation
- **Alert Service**: Rule-based alerts, notifications, report generation

### ML Pipeline
- **Feature Engineering**: Velocity features, distance calculations, merchant/device scoring
- **Training Pipeline**: Cross-validation, hyperparameter tuning, model comparison
- **Inference Engine**: Low-latency scoring (<100ms), batch scoring support
- **Explainability**: SHAP value computation, feature contribution analysis
- **Anomaly Detection**: Isolation Forest, LOF, Autoencoder for novel patterns

### Data Layer
- **PostgreSQL**: Persistent storage for transactions, users, models, alerts
- **Redis**: Caching for feature lookups, scoring results, rate limiting
- **Model Storage**: Serialized models with versioning and metadata

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React 18, TypeScript, Tailwind CSS, Shadcn UI | Modern responsive UI |
| Animations | Framer Motion | Smooth transitions and interactions |
| Charts | Recharts | Data visualization, SHAP plots |
| Backend | FastAPI (Python 3.11+) | REST API with async support |
| Auth | JWT, bcrypt | Secure authentication |
| Database | PostgreSQL (Supabase) | Relational data storage |
| Cache | Redis | Session, feature cache, rate limiting |
| ML | scikit-learn, XGBoost, LightGBM | Model training and inference |
| Explainability | SHAP | Feature contribution analysis |
| Anomaly | Isolation Forest, LOF, Autoencoder | Novel fraud detection |
| Container | Docker, Docker Compose | Development and deployment |
| CI/CD | GitHub Actions | Automated testing and deployment |
| Hosting | Vercel (frontend), Render (backend) | Production deployment |
