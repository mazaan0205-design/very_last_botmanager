Bot Manager
What it is
Bot Manager helps solo developers, creators, and power users build, manage, and deploy custom AI chatbots and dynamic MCP agents so they can automate everyday digital workflows without the complexity of manual infrastructure setup.

Who it's for
Individual creators, independent developers, and power users who want their own centralized hub for custom AI assistants and agentic workflows.

Platforms supported
Web Dashboard & Embeddable Widgets (Custom web interfaces)

Google Workspace / Gmail (Official Google Cloud OAuth integration)

Model Context Protocol (MCP) for connecting external local tools and APIs.

Features (working today)
Multi-tenant bot creation and management dashboard.

Secure Google OAuth authentication and Gmail API scope integration for automated email workflows.

Custom knowledge base integration powered by vector embeddings and document retrieval.

Modular AI agent execution using LangChain, Groq, and Hugging Face inference models.

Features (planned / not built yet)
Expanded MCP toolsets supporting third-party platforms like Slack, Jira, and GitHub.

Advanced analytics dashboard for tracking token usage and agent interactions.

Enterprise-grade cloud multi-tenant isolation and automated deployment configurations.

Tech stack
Language/framework: FastAPI (Python) and Laravel 12 (PHP / Blade templates)

Database: Supabase (PostgreSQL) and ChromaDB (Vector Store)

Hosting (current or planned): Local environment / Render (static site and backend deployments)

External APIs used (AI, messaging, etc.): ChatGroq API, Hugging Face Inference, Google OAuth & Gmail API

How it works
Sign Up & Connect: Log into your personal dashboard and securely link your Google Workspace via OAuth credentials.

Configure Your Bot: Set up your custom prompt parameters, attach knowledge base documents, and configure your active MCP agents.

Deploy & Automate: Embed your chatbot widget or run background agentic workflows to handle automated tasks seamlessly.

Current status
Working locally and successfully packaged into a fully functional multi-tenant application layout.

Setup (Windows, local - no Docker)
Prerequisites: Python 3.10+, PHP 8.2+ (with Composer), and the php executable on PATH.

One-time setup:

1. Backend (FastAPI) - creates backend\venv and installs dependencies:

   cd backend
   python -m venv venv
   .\venv\Scripts\pip install -r requirements.txt
   copy .env.example .env

   Open backend\.env and paste your free GROQ_API_KEY from https://console.groq.com
   (without it, bots reply with a generic fallback message instead of AI answers).

2. Frontend (Laravel) - installs PHP dependencies:

   cd frontend
   composer install
   php artisan key:generate

   frontend\.env already ships with the correct local ports:
     APP_URL=http://localhost:9999
     PYTHON_API_URL=http://127.0.0.1:8001

Start the app (one command, from the repo root):

   .\start.ps1

This opens two PowerShell windows:
   - Backend  : uvicorn main:app --reload --port 8001  -> http://127.0.0.1:8001 (API docs at /docs)
   - Frontend : php artisan serve --port=9999           -> http://localhost:9999

Sign in / register at http://localhost:9999, then create a bot and try it in "Test".

Manual start (alternative to start.ps1), using two terminals:

   Terminal 1 (backend):
     cd backend
     .\venv\Scripts\activate
     uvicorn main:app --reload --port 8001

   Terminal 2 (frontend):
     cd frontend
     php artisan serve --port=9999

Notes:
   - If you edit frontend\.env, run `php artisan config:clear` afterwards so the
     changes take effect.
   - Bots, chat sessions, and knowledge documents persist in backend\botmanager.db
     (SQLite) across restarts.
   - docker-compose.yml exists for container deployments; it maps Laravel on
     port 8000 there, which does not affect the local setup above.

Pricing idea
Free and open for personal use / individual builders, with an optional tier for advanced cloud hosting and higher token capacities.
