# Setup Guide - Dynamic Formula Benchmark System

מדריך התקנה מפורט למערכת השוואת שיטות חישוב דינמיות.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start with Docker](#quick-start-with-docker)
- [Manual Setup](#manual-setup)
  - [Database Setup](#database-setup)
  - [.NET Engine Setup](#net-engine-setup)
  - [Python Engine Setup](#python-engine-setup)
  - [API Setup](#api-setup)
  - [Frontend Setup](#frontend-setup)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have the following installed:

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Docker** | 20.10+ | Container runtime for database |
| **Docker Compose** | 2.0+ | Multi-container orchestration |
| **.NET SDK** | 7.0+ | Running the .NET calculation engine |
| **Python** | 3.10+ | Running the Python engine and API |
| **Node.js** | 18.0+ | Running the React frontend |
| **npm** or **pnpm** | Latest | JavaScript package management |

### Verify Installation

```bash
# Check Docker
docker --version
docker compose version

# Check .NET
dotnet --version

# Check Python
python --version
pip --version

# Check Node.js
node --version
npm --version
```

---

## Quick Start with Docker

The fastest way to get started is using Docker Compose, which sets up PostgreSQL automatically.

### Step 1: Start the Database

```bash
# From the project root directory
docker compose up -d postgres
```

This will:
- Pull the PostgreSQL 15 Alpine image
- Create a database named `formula_benchmark`
- Create a user `benchmark_user` with password `benchmark_pass`
- Initialize the database schema automatically
- Populate the database with 1 million test records
- Create all stored procedures

### Step 2: Wait for Database Initialization

The database initialization (especially populating 1 million records) takes a few minutes. Monitor progress with:

```bash
# Watch container logs
docker compose logs -f postgres
```

Wait until you see:
```
database system is ready to accept connections
```

### Step 3: (Optional) Access pgAdmin

A web-based database management tool is included:

```bash
docker compose up -d pgadmin
```

Access at: http://localhost:5050
- Email: `admin@benchmark.local`
- Password: `admin`

To connect to PostgreSQL from pgAdmin:
- Host: `postgres`
- Port: `5432`
- Database: `formula_benchmark`
- Username: `benchmark_user`
- Password: `benchmark_pass`

### Step 4: Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (deletes all data)
docker compose down -v
```

---

## Manual Setup

If you prefer manual setup or need to customize the installation.

### Database Setup

#### Option A: Using Docker (Recommended)

```bash
docker compose up -d postgres
```

#### Option B: Manual PostgreSQL Installation

1. **Install PostgreSQL 15+** on your system

2. **Create the database and user:**

```sql
-- Connect as superuser (postgres)
CREATE DATABASE formula_benchmark;
CREATE USER benchmark_user WITH PASSWORD 'benchmark_pass';
GRANT ALL PRIVILEGES ON DATABASE formula_benchmark TO benchmark_user;
```

3. **Run initialization scripts:**

```bash
# Connect to the database
psql -U benchmark_user -d formula_benchmark

# Run schema creation
\i database/init.sql

# Run data population (takes several minutes)
\i database/populate_data.sql

# Run stored procedures
\i database/stored_procedures.sql
```

### .NET Engine Setup

The .NET engine uses DataTable.Compute for formula calculation.

1. **Navigate to the .NET engine directory:**

```bash
cd dotnet-engine/FormulaEngine
```

2. **Restore NuGet packages:**

```bash
dotnet restore
```

3. **Configure database connection:**

Edit `appsettings.json`:

```json
{
  "ConnectionStrings": {
    "PostgreSQL": "Host=localhost;Port=5432;Database=formula_benchmark;Username=benchmark_user;Password=benchmark_pass"
  }
}
```

4. **Build the project:**

```bash
dotnet build
```

5. **Run the engine:**

```bash
dotnet run
```

### Python Engine Setup

The Python engine uses eval() with AST safety checks.

1. **Navigate to the Python engine directory:**

```bash
cd python-engine
```

2. **Create a virtual environment (recommended):**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**

Create a `.env` file in the `python-engine/` directory:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=formula_benchmark
DB_USER=benchmark_user
DB_PASSWORD=benchmark_pass
ENGINE_NAME=Python_Eval
BATCH_SIZE=10000
ENABLE_LOGGING=true
```

5. **Run the engine:**

```bash
python main.py
```

### API Setup

The FastAPI backend provides REST endpoints for the dashboard.

1. **Navigate to the API directory:**

```bash
cd api
```

2. **Create a virtual environment:**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**

Create a `.env` file in the `api/` directory:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=formula_benchmark
DB_USER=benchmark_user
DB_PASSWORD=benchmark_pass
DEBUG=false
```

5. **Run the API server:**

```bash
# Development mode
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at: http://localhost:8000

API documentation (Swagger UI): http://localhost:8000/docs

### Frontend Setup

The React dashboard displays benchmark results.

1. **Navigate to the frontend directory:**

```bash
cd frontend
```

2. **Install dependencies:**

```bash
npm install
```

3. **Configure API endpoint:**

The frontend expects the API at `http://localhost:8000`. To change this, update `src/services/api.ts`.

4. **Run in development mode:**

```bash
npm run dev
```

The dashboard will be available at: http://localhost:5173

5. **Build for production:**

```bash
npm run build
```

The built files will be in the `dist/` directory.

---

## Environment Variables

### Database Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `localhost` | PostgreSQL server hostname |
| `DB_PORT` | `5432` | PostgreSQL server port |
| `DB_NAME` | `formula_benchmark` | Database name |
| `DB_USER` | `benchmark_user` | Database username |
| `DB_PASSWORD` | `benchmark_pass` | Database password |

### Python Engine Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ENGINE_NAME` | `Python_Eval` | Name used in results logging |
| `BATCH_SIZE` | `10000` | Records processed per batch |
| `ENABLE_LOGGING` | `true` | Enable verbose logging |
| `FLOAT_TOLERANCE` | `1e-9` | Tolerance for floating-point comparisons |

### API Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `DB_MIN_POOL_SIZE` | `5` | Minimum database connections |
| `DB_MAX_POOL_SIZE` | `20` | Maximum database connections |

---

## Troubleshooting

### Database Connection Issues

**Problem:** Cannot connect to PostgreSQL

**Solutions:**
1. Verify Docker container is running:
   ```bash
   docker ps
   ```
2. Check container logs for errors:
   ```bash
   docker compose logs postgres
   ```
3. Ensure the correct port is exposed:
   ```bash
   docker port formula_benchmark_db
   ```

### .NET Build Errors

**Problem:** NuGet package restore fails

**Solutions:**
1. Clear NuGet cache:
   ```bash
   dotnet nuget locals all --clear
   ```
2. Restore packages explicitly:
   ```bash
   dotnet restore --force
   ```

### Python Import Errors

**Problem:** Module not found errors

**Solutions:**
1. Ensure virtual environment is activated
2. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

### Frontend Build Errors

**Problem:** npm install fails

**Solutions:**
1. Delete `node_modules` and lock file:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```
2. Check Node.js version (requires 18+)

### Data Population Taking Too Long

**Problem:** Database initialization is slow

**Solutions:**
1. The initial population of 1 million records takes 5-10 minutes
2. Monitor progress with:
   ```bash
   docker compose logs -f postgres
   ```
3. Verify data was populated:
   ```sql
   SELECT COUNT(*) FROM t_data;
   -- Should return 1,000,000
   ```

### API CORS Errors

**Problem:** Frontend cannot connect to API

**Solutions:**
1. Ensure API is running on port 8000
2. Check CORS configuration in `api/config.py`
3. Verify frontend API URL in `frontend/src/services/api.ts`

---

## Next Steps

Once setup is complete, see [usage.md](usage.md) for:
- Running benchmarks
- Understanding the formulas
- Using the API
- Using the dashboard
- Verifying results
