# Dynamic Formula Benchmark System

A comprehensive benchmarking system that compares dynamic formula calculation methods across three different technologies: **.NET (C#)**, **Python**, and **SQL**. The system processes 1 million data records, calculates complex formulas, measures performance, and displays results in an interactive dashboard.

## 🌐 Live Demo

**Dashboard**: [Add Vercel URL after deployment]

> To deploy the dashboard to Vercel, see [Frontend Deployment](#frontend-deployment-vercel) or refer to [frontend/DEPLOYMENT.md](frontend/DEPLOYMENT.md) for detailed instructions.

## 🎯 Project Overview

This project addresses the challenge of calculating dynamic payment formulas that change frequently based on payment types, dates, agreements, and regulations. Instead of hardcoding each formula and making frequent manual updates, the system learns new formulas at runtime directly from database tables.

**Goal**: Compare different approaches for dynamic formula calculation to determine the fastest and most efficient solution.

## ✨ Features

- **Multi-Engine Comparison**: Compare .NET DataTable.Compute, Python eval(), and SQL Dynamic procedures
- **Large-Scale Testing**: Process 1 million records per benchmark run
- **Formula Types**: Support for simple, complex, and conditional formulas
- **Mathematical Operations**: Addition, subtraction, multiplication, division, power, sqrt, log, abs
- **Conditional Logic**: if(condition, true_value, false_value) syntax support
- **Interactive Dashboard**: React-based visualization with charts and comparison tables
- **Result Verification**: Cross-method validation ensures all engines produce identical results
- **Performance Logging**: Detailed timing logs for each formula and method

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Frontend (React)                                │
│                    Dashboard with Charts & Reports                          │
│                         Deployed on Vercel                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            API Layer (FastAPI)                              │
│                    REST API for data access                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Calculation Engines                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  .NET Engine    │  │  Python Engine  │  │   SQL Engine    │             │
│  │ DataTable.      │  │ eval() + ast    │  │ Dynamic SQL     │             │
│  │ Compute         │  │                 │  │ Stored Proc     │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PostgreSQL Database                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │ t_data   │  │ t_targil │  │ t_results│  │  t_log   │                    │
│  │ 1M rows  │  │ Formulas │  │ Results  │  │ Timings  │                    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- **Docker** and **Docker Compose** (for database setup)
- **.NET SDK 7.0+** (for .NET engine)
- **Python 3.11+** (for Python engine and API)
- **Node.js 18+** and **npm** (for frontend)
- **PostgreSQL client** (psql) - optional, for direct database access

## 🚀 Quick Start with Docker Compose

### 1. Clone the Repository

```bash
git clone <repository-url>
cd dynamic-formula-benchmark
```

### 2. Start the Database

```bash
# Start PostgreSQL and pgAdmin
docker-compose up -d

# Wait for initialization (populates 1M records - may take a few minutes)
docker-compose logs -f postgres
```

The database will automatically:
- Create all required tables (t_data, t_targil, t_results, t_log)
- Populate t_data with 1,000,000 random records
- Load all test formulas into t_targil
- Create stored procedures for SQL benchmarking

### 3. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| PostgreSQL | `localhost:5432` | `benchmark_user` / `benchmark_pass` |
| pgAdmin | `http://localhost:5050` | `admin@benchmark.local` / `admin` |

### 4. Start the API Server

```bash
cd api
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API available at: `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 5. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard available at: `http://localhost:5173`

## 🔧 Manual Setup Guide

### Database Setup (without Docker)

1. Install PostgreSQL 15+
2. Create database and user:

```sql
CREATE DATABASE formula_benchmark;
CREATE USER benchmark_user WITH PASSWORD 'benchmark_pass';
GRANT ALL PRIVILEGES ON DATABASE formula_benchmark TO benchmark_user;
```

3. Run initialization scripts:

```bash
psql -U benchmark_user -d formula_benchmark -f database/init.sql
psql -U benchmark_user -d formula_benchmark -f database/populate_data.sql
psql -U benchmark_user -d formula_benchmark -f database/stored_procedures.sql
```

### Python Engine Setup

```bash
cd python-engine
pip install -r requirements.txt

# Configure environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=formula_benchmark
export DB_USER=benchmark_user
export DB_PASSWORD=benchmark_pass
```

### .NET Engine Setup

```bash
cd dotnet-engine/FormulaEngine
dotnet restore
dotnet build

# Configuration is in appsettings.json
```

## ⚡ Running Benchmarks

### Run All Benchmarks (Recommended)

**Windows (PowerShell):**
```powershell
.\scripts\run_all_benchmarks.ps1
```

**Linux/Mac (Bash):**
```bash
./scripts/run_all_benchmarks.sh
```

This script will:
1. Check prerequisites
2. Run Python benchmark
3. Run .NET benchmark
4. Run SQL benchmark
5. Display summary results

### Run Individual Engines

**Python Engine:**
```bash
cd python-engine
python main.py
```

**. NET Engine:**
```bash
cd dotnet-engine/FormulaEngine
dotnet run
```

**SQL Engine (via psql):**
```bash
psql -U benchmark_user -d formula_benchmark -c "CALL run_sql_benchmark();"
```

### Verify Results Consistency

```bash
python scripts/compare_results.py
```

This verifies all three methods produce identical results within floating-point tolerance.

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/benchmark/results` | GET | Get benchmark results for all formulas |
| `/api/benchmark/comparison` | GET | Get overall comparison between methods |
| `/api/benchmark/run/{method}` | POST | Trigger benchmark for specific method |
| `/api/formulas` | GET | Get all formula definitions |
| `/api/results/verify` | GET | Verify result consistency across methods |
| `/health` | GET | API health check |

## 📁 Project Structure

```
dynamic-formula-benchmark/
├── README.md                    # This file
├── docker-compose.yml           # Docker Compose configuration
├── .gitignore                   # Git ignore rules
│
├── database/                    # Database scripts
│   ├── init.sql                 # Schema creation
│   ├── populate_data.sql        # Data generation (1M records)
│   ├── stored_procedures.sql    # SQL calculation procedures
│   └── verify_results.sql       # Result verification queries
│
├── dotnet-engine/               # .NET calculation engine
│   ├── FormulaEngine.sln
│   └── FormulaEngine/
│       ├── Engines/             # DataTable.Compute implementation
│       ├── Models/              # Data models
│       ├── Repositories/        # Database access
│       └── Services/            # Benchmark orchestration
│
├── python-engine/               # Python calculation engine
│   ├── engines/                 # eval() + ast implementation
│   ├── models/                  # Data classes
│   ├── repositories/            # Database access
│   └── services/                # Benchmark orchestration
│
├── api/                         # FastAPI backend
│   ├── routers/                 # API endpoints
│   ├── schemas/                 # Pydantic models
│   └── services/                # Database service
│
├── frontend/                    # React dashboard
│   ├── src/
│   │   ├── components/          # UI components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── services/            # API client
│   │   └── types/               # TypeScript types
│   └── vercel.json              # Vercel deployment config
│
├── scripts/                     # Automation scripts
│   ├── run_all_benchmarks.sh    # Linux/Mac benchmark runner
│   ├── run_all_benchmarks.ps1   # Windows benchmark runner
│   └── compare_results.py       # Result verification
│
└── docs/                        # Documentation
    ├── setup.md                 # Detailed setup guide
    ├── usage.md                 # Usage instructions
    └── report.md                # Benchmark report
```

## 🧮 Supported Formula Types

### Simple Formulas
- `a + b` - Addition
- `c * 2` - Multiplication
- `b - a` - Subtraction
- `d / 4` - Division

### Complex Formulas
- `(a + b) * 8` - Compound expressions
- `sqrt(c * c + d * d)` - Pythagorean calculation
- `log(b) + c` - Logarithmic functions
- `abs(d - b)` - Absolute value

### Conditional Formulas
- `if(a > 5, b * 2, b / 2)` - Conditional multiplication/division
- `if(b < 10, a + 1, d - 1)` - Conditional addition/subtraction
- `if(a == c, 1, 0)` - Equality check

## 🌐 Frontend Deployment (Vercel)

The React dashboard can be deployed to Vercel for public access.

### Prerequisites

- A [Vercel account](https://vercel.com) (free tier available)
- [Vercel CLI](https://vercel.com/docs/cli) installed (optional, for CLI deployment)

### Option 1: Deploy via Vercel Dashboard (Recommended)

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New" → "Project"
3. Import your Git repository
4. Configure the project:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Add environment variables (if needed):
   - `VITE_API_BASE_URL`: Your API URL (or leave empty for static demo)
6. Click "Deploy"

### Option 2: Deploy via Vercel CLI

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to frontend directory
cd frontend

# Deploy to Vercel (follow prompts for authentication)
vercel

# For production deployment
vercel --prod
```

### After Deployment

1. Copy your deployed URL from Vercel
2. Update the [Live Demo](#-live-demo) section in this README
3. (Optional) Update `vercel.json` API rewrites if you have a backend deployed

For detailed deployment instructions, see [frontend/DEPLOYMENT.md](frontend/DEPLOYMENT.md).

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| Database | PostgreSQL 15 |
| .NET Engine | .NET 7 / C# |
| Python Engine | Python 3.11 |
| API | FastAPI |
| Frontend | React 18 + TypeScript |
| Charts | Recharts |
| Styling | Tailwind CSS |
| Build Tool | Vite |
| Containerization | Docker Compose |
| Cloud Hosting | Vercel |

## 📝 License

This project is created for benchmarking and educational purposes.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For questions or issues, please open a GitHub issue.
