# AI-Powered Inventory Monitor

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Flask%203.x-green.svg)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/database-SQLite%20%2B%20SQLAlchemy-orange.svg)](https://www.sqlalchemy.org/)
[![AI Integration](https://img.shields.io/badge/AI-Microsoft%20Foundry-0078D4.svg)](https://ai.azure.com/)

An enterprise-grade, full-stack college project delivering real-time stock tracking, audit transaction logging, automated low-stock threshold detection, and native AI integration with **Microsoft Foundry (Azure AI Foundry / Studio)**.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Architecture & System Flow](#architecture--system-flow)
4. [Project Structure](#project-structure)
5. [Database Schema & Design](#database-schema--design)
6. [Inventory Calculation Logic](#inventory-calculation-logic)
7. [Microsoft Foundry Setup Guide](#microsoft-foundry-setup-guide)
8. [Installation & Setup (Windows PowerShell)](#installation--setup-windows-powershell)
9. [Running the Application](#running-the-application)
10. [Default Login Credentials](#default-login-credentials)
11. [REST API Documentation](#rest-api-documentation)
12. [Testing & Verification](#testing--verification)
13. [Security & Error Handling](#security--error-handling)
14. [Troubleshooting](#troubleshooting)

---

## Project Overview

The **AI-Powered Inventory Monitor** provides organizations with complete visibility into warehouse catalog levels, replenishment needs, and movement history. The system combines traditional deterministic database transactions with the reasoning power of Microsoft Foundry AI models to deliver:

- **Full Catalog Lifecycle:** Product CRUD, pricing, categorization, and supplier tracking.
- **Stock Movements & Auditability:** Strict stock-in, stock-out, and audit adjustment logging.
- **Automated Stock Health Detection:** Dynamic evaluation of `NORMAL`, `LOW_STOCK`, and `OUT_OF_STOCK` states.
- **Dedicated Microsoft Foundry AI Agent:** "Inventory Intelligence Assistant" with live access to SQLite context for predictive restock advice, risk mitigation, and natural language Q&A.
- **Executive Dashboard:** Live KPIs, Chart.js visualizations, and quick replenishment action modals.

---

## Technology Stack

- **Backend:** Python 3.14, Flask 3.x, Flask-SQLAlchemy 3.x, Flask-CORS, python-dotenv, Werkzeug
- **AI / LLM:** Microsoft Foundry (Azure AI Foundry / Studio) via `azure-ai-inference` SDK and OpenAI-compatible inference client
- **Database:** SQLite 3 with parameterized SQLAlchemy ORM models
- **Frontend:** HTML5, Jinja2 Templates, Vanilla JavaScript (Fetch API), Chart.js, Font Awesome 6
- **Styling:** Custom responsive dark enterprise theme (`#0b0f19`, `#1e293b`, `#38bdf8`)

---

## Architecture & System Flow

```
[ Browser / User Interface ]
       │  (Fetch API / HTML5 / Chart.js)
       ▼
[ Flask REST API Controllers (routes/) ]
       │
       ├──► [ SQLAlchemy ORM & SQLite (database/inventory.db) ]
       │         ▲
       │         │ (Live Inventory Context Extracted)
       ▼         │
[ InventoryService (services/inventory_service.py) ]
       │
       ▼
[ Microsoft Foundry Service (services/foundry_service.py) ]
       │  (Uses Official azure-ai-inference SDK / HTTPS REST)
       ▼
[ Microsoft Foundry / Azure AI Studio Model Deployment ]
       │  (gpt-4o, gpt-4o-mini, Phi-3.5, Mistral, Llama 3)
       ▼
[ Analyzed Recommendations & Insights Persisted to SQLite ]
```

> **Security Rule:** The Microsoft Foundry API key is strictly maintained on the backend inside environment variables (`.env`). Client-side JavaScript never accesses or exposes the API key.

---

## Project Structure

```
AI_Inventory_Monitor/
│
├── app.py                     # Flask application factory, Foundry startup check, blueprints
├── config.py                  # Environment config loader and absolute path resolution
├── requirements.txt           # Project dependencies
├── .env                       # Local environment variables (git-ignored)
├── .env.example               # Template environment configuration
├── .gitignore                 # Git ignore rules (DB, keys, caches)
├── README.md                  # Comprehensive project documentation
├── init_db.py                 # SQLite database schema initializer
├── seed_data.py               # Realistic dataset seeder (12 products, users, transactions)
│
├── database/
│   └── inventory.db           # SQLite database file
│
├── models/
│   ├── __init__.py            # SQLAlchemy db instance and model exports
│   ├── user.py                # User account model with Werkzeug password hashing
│   ├── product.py             # Product catalog model and dynamic stock status property
│   ├── inventory_transaction.py # Audit log model (STOCK_IN, STOCK_OUT, ADJUSTMENT)
│   └── ai_insight.py          # Microsoft Foundry generated insights & recommendations
│
├── routes/
│   ├── __init__.py            # Blueprint registry
│   ├── auth.py                # User login, registration, logout views and APIs
│   ├── products.py            # Product CRUD and search/filter APIs
│   ├── inventory.py           # Stock-in, stock-out, adjust, and alert APIs
│   ├── dashboard.py           # KPI metrics endpoint and dashboard view
│   └── ai.py                  # Microsoft Foundry AI chat, analyze, and recommendation routes
│
├── services/
│   ├── __init__.py            # Service layer exports
│   ├── inventory_service.py   # Business logic, threshold formulas, and AI context extractor
│   └── foundry_service.py     # Microsoft Foundry SDK client, adapters, and error isolation
│
├── templates/
│   ├── base.html              # Core layout with responsive sidebar and topbar
│   ├── login.html             # Secure login view with sample credential helpers
│   ├── register.html          # User registration view
│   ├── dashboard.html         # Executive KPI dashboard and Chart.js visuals
│   ├── products.html          # Product catalog table with filters and modals
│   ├── add_product.html       # Validated product creation form
│   ├── edit_product.html      # Product modification form
│   ├── inventory.html         # Warehouse management and quick transaction hub
│   ├── transactions.html      # Audit trail table with transaction badges
│   ├── alerts.html            # Out-of-stock and low-stock monitor
│   ├── ai_assistant.html      # Interactive chat UI with quick prompt chips
│   └── ai_insights.html       # Advisory intelligence center and diagnostic runs
│
├── static/
│   ├── css/
│   │   └── style.css          # Sleek enterprise dark theme
│   └── js/
│       ├── dashboard.js       # Live metrics polling and Chart.js renderer
│       └── ai_assistant.js    # Interactive chat controller and markdown parser
│
└── tests/
    └── test_api.py            # Automated test suite (health, auth, inventory, AI)
```

---

## Database Schema & Design

SQLite database tables with relationships and constraints:

### 1. `users` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key | Auto-incrementing identifier |
| `username` | String(80) | Unique, Not Null | Unique username |
| `email` | String(120) | Unique, Not Null | Unique user email |
| `password_hash` | String(256) | Not Null | Werkzeug scrypt hash |
| `role` | String(50) | Default: 'admin' | User role (admin, manager, staff) |
| `created_at` | DateTime | Default: UTC | Timestamp of account creation |

### 2. `products` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key | Auto-incrementing identifier |
| `product_name` | String(150) | Not Null | Commercial item name |
| `category` | String(100) | Not Null | Classification group |
| `description` | Text | Nullable | Detailed specifications / SKU |
| `price` | Float | Not Null, >= 0 | Unit retail price |
| `quantity` | Integer | Not Null, >= 0 | Current units physically in stock |
| `minimum_stock` | Integer | Not Null, >= 0 | Restock alert threshold |
| `supplier` | String(150) | Nullable | Primary vendor / distributor |
| `created_at` | DateTime | Default: UTC | Creation timestamp |
| `updated_at` | DateTime | Auto-update | Last modification timestamp |

### 3. `inventory_transactions` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key | Auto-incrementing transaction ID |
| `product_id` | Integer | Foreign Key (`products.id`, CASCADE) | Referenced product |
| `transaction_type` | String(20) | Not Null | `STOCK_IN`, `STOCK_OUT`, `ADJUSTMENT` |
| `quantity` | Integer | Not Null, > 0 | Units involved in the movement |
| `previous_quantity` | Integer | Not Null | Stock balance before transaction |
| `new_quantity` | Integer | Not Null, >= 0 | Stock balance after transaction |
| `remarks` | String(255) | Nullable | Audit memo / reference number |
| `created_at` | DateTime | Default: UTC | Movement timestamp |

### 4. `ai_insights` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key | Auto-incrementing insight ID |
| `product_id` | Integer | Foreign Key (`products.id`, SET NULL) | Optional target product |
| `insight_type` | String(50) | Not Null | `RESTOCK_RECOMMENDATION`, `RISK_ALERT`, etc. |
| `recommendation` | Text | Not Null | AI-generated reasoning and guidance |
| `priority` | String(20) | Default: 'MEDIUM' | `HIGH`, `MEDIUM`, `LOW` |
| `created_at` | DateTime | Default: UTC | Timestamp of insight generation |

---

## Inventory Calculation Logic

All stock calculations are centralized in `services/inventory_service.py`:

### Status Determination:
```python
if quantity == 0:
    status = "OUT_OF_STOCK"
elif quantity <= minimum_stock:
    status = "LOW_STOCK"
else:
    status = "NORMAL"
```

### Stock Movements:
- **Stock-In:** `new_quantity = old_quantity + quantity`
- **Stock-Out:** `new_quantity = old_quantity - quantity`
  - Validates: `quantity > 0`
  - Validates: `quantity <= old_quantity` (prevents overdraft)
  - Validates: `new_quantity >= 0` (no negative inventory)
- **Adjustment:** `diff = new_quantity - old_quantity`
  - Validates: `new_quantity >= 0`
  - Automatically records an `ADJUSTMENT` transaction for physical audits.

---

## Microsoft Foundry Setup Guide

Follow these steps to connect your deployed Microsoft Foundry model:

### Step 1: Create Microsoft Foundry Resource
1. Sign in to the [Azure AI Foundry Portal](https://ai.azure.com/) or Azure Portal.
2. Create an **Azure AI Foundry Project** (or Azure OpenAI Resource) in your preferred Azure region (e.g., East US 2, Sweden Central).

### Step 2: Deploy an AI Model
1. In the Foundry Project, navigate to **Deployments** &rarr; **Deploy Model**.
2. Select an inference model:
   - `gpt-4o` or `gpt-4o-mini`
   - `Phi-3.5-mini-instruct` or `Phi-4`
   - `Mistral-Large` or `Meta-Llama-3-70B-Instruct`
3. Note your **Deployment Name** (e.g., `gpt-4o` or `phi-35-mini`).

### Step 3: Obtain Endpoint & API Key
1. Go to the deployment's **Overview** or **Project Settings &rarr; Keys and Endpoints**.
2. Copy the **Target Endpoint** URL (e.g., `https://your-resource.services.ai.azure.com/models` or `https://your-resource.openai.azure.com/`).
3. Copy **Key 1** (API Key).

### Step 4: Configure Your `.env` File
Open `.env` in the project root and replace placeholders:

```env
FOUNDRY_ENDPOINT=https://your-resource-name.services.ai.azure.com/models
FOUNDRY_API_KEY=your_actual_foundry_api_key_here
FOUNDRY_DEPLOYMENT_NAME=gpt-4o
FOUNDRY_API_VERSION=2024-06-01
```

### Step 5: Start & Verify
1. Start Flask (`python app.py`).
2. When configured correctly, app logs report:
   ```
   [OK] Microsoft Foundry configured successfully (Deployment: gpt-4o)
   ```
3. Test health check:
   ```
   GET http://127.0.0.1:5000/api/health
   ```
4. Access the **AI Assistant** at `http://127.0.0.1:5000/ai-assistant` and ask questions.

> **Graceful Unconfigured Handling:** If Foundry credentials are not yet configured, the system logs a startup warning, all core inventory functions remain completely operational, and AI endpoints return a clear configuration error response without crashing.

---

## Installation & Setup (Windows PowerShell)

Open PowerShell in the project directory:

```powershell
# 1. Create a Python virtual environment (recommended)
python -m venv .venv

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Install required packages
pip install -r requirements.txt

# 4. Initialize SQLite tables
python init_db.py

# 5. Populate realistic seed catalog & transactions
python seed_data.py
```

---

## Running the Application

```powershell
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

---

## Default Login Credentials

Seeded into the database by `seed_data.py`:

| Role | Username | Password | Email |
|---|---|---|---|
| **Administrator** | `admin` | `admin123` | `admin@inventory.local` |
| **Inventory Manager** | `manager` | `manager123` | `manager@inventory.local` |

---

## REST API Documentation

### Authentication Endpoints
- `POST /api/auth/register` — Register a new user (`{ username, email, password, role }`)
- `POST /api/auth/login` — Sign in and start session (`{ username, password }`)
- `POST /api/auth/logout` — End current session

### Product Endpoints
- `GET /api/products` — Retrieve all products (query params: `?search=...`, `?category=...`, `?status=...`)
- `GET /api/products/<id>` — Retrieve single product details
- `POST /api/products` — Create new product with validation
- `PUT /api/products/<id>` — Update product attributes (logs audit on quantity shift)
- `DELETE /api/products/<id>` — Delete product (cascades transactions and insights)

### Inventory Movement Endpoints
- `GET /api/inventory` — Live inventory status with computed health states
- `POST /api/inventory/stock-in` — Add stock (`{ product_id, quantity, remarks }`)
- `POST /api/inventory/stock-out` — Dispatch stock (`{ product_id, quantity, remarks }`)
- `POST /api/inventory/adjust` — Manual audit reconciliation (`{ product_id, quantity, remarks }`)
- `GET /api/inventory/low-stock` — All items where `0 < quantity <= minimum_stock`
- `GET /api/inventory/out-of-stock` — All items where `quantity == 0`
- `GET /api/inventory/transactions` — Transaction history (query params: `?type=...`, `?limit=...`)

### Dashboard Endpoints
- `GET /api/dashboard` — Aggregated KPIs, valuation, category counts, and alert lists

### AI & Microsoft Foundry Endpoints
- `POST /api/ai/chat` — Interactive Q&A with live SQLite context (`{ message: "..." }`)
- `POST /api/ai/analyze` — Run comprehensive catalog health diagnostic & persist insights
- `POST /api/ai/recommend` — Generate prioritized restocking plan
- `GET /api/ai/inventory-summary` — Concise executive summary from AI
- `GET /api/ai/insights` — Stored recommendations from SQLite (`?priority=HIGH|MEDIUM|LOW`)

### System Health
- `GET /api/health` — Service status and Microsoft Foundry connection state

---

## Testing & Verification

Run the automated test suite covering all core requirements:

```powershell
python -m unittest tests/test_api.py
```

All 10 test cases verify:
- Health check reporting
- User registration and login validation
- Product CRUD operations and negative value rejection
- Stock-in quantity balance and transaction logging
- Stock-out balance, overdraft prevention, and low-stock transition
- Dynamic low-stock and out-of-stock queries
- Dashboard statistics calculations
- Stored AI insights retrieval
- Graceful Microsoft Foundry error handling

---

## Security & Error Handling

1. **Password Security:** Hashes stored using Werkzeug `scrypt` hashing with unique salts.
2. **SQL Injection Defense:** All queries parameterized via SQLAlchemy ORM.
3. **No Credential Leakage:** API keys are never exposed in JavaScript or template source.
4. **Input Constraints:** Non-negative prices, quantities, and thresholds strictly enforced.
5. **No Stock Overdrafts:** Dispatches exceeding warehouse stock are rejected with HTTP 400.
6. **Graceful AI Degradation:** If Microsoft Foundry is unreachable or unconfigured, the application logs technical diagnostics on the server and returns clean, human-readable error messages to the client without crashing.

---

## Troubleshooting

### 1. Windows Application Control / DLL Warning
If your Windows workstation has strict software restriction policies blocking compiled C extensions in user AppData, the application uses pure Python execution mode for SQLAlchemy.

### 2. Microsoft Foundry Connection Issues
- Verify that `FOUNDRY_ENDPOINT` does not have trailing slashes or malformed paths.
- Ensure the API key corresponds to the selected resource.
- Check that `FOUNDRY_DEPLOYMENT_NAME` exactly matches the model deployment name in your Azure Foundry project.
- Test `GET http://127.0.0.1:5000/api/health` to inspect the reported status.
