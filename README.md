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

Setup
To run BotManager locally in your development environment, configure the following environment variables (names only):

APP_KEY

DB_CONNECTION / DATABASE_URL

FASTAPI_PORT

GOOGLE_CLIENT_ID

GOOGLE_CLIENT_SECRET

GOOGLE_REDIRECT_URI

GROQ_API_KEY

HUGGINGFACE_API_KEY

Pricing idea
Free and open for personal use / individual builders, with an optional tier for advanced cloud hosting and higher token capacities.
