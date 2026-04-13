# Text2Query

> Transform natural language into SQL — no SQL knowledge required.

Text2Query is a web service that converts plain-text prompts into SQL queries using LLM. Built with FastAPI, PostgreSQL, and SQLAlchemy async stack.

---

## Features

**SQL Generation**
- Describe what you want in plain language, get back a ready-to-use SQL query
- Supports PostgreSQL, MySQL, MariaDB and SQLite dialects
- Automatic detection of potentially dangerous queries (DROP, TRUNCATE, DELETE without WHERE, etc.) with a warning to the user

**Authentication**
- Secure registration and login
- JWT-based authentication via httpOnly cookies (not localStorage)
- RS256 asymmetric key signing

**Query History**
- Last 20 queries are saved per user
- Stored with prompt, generated SQL, dialect, danger flag and timestamp
- Accessible via API for frontend display

**External Database Connection**
- Connect your own PostgreSQL or MySQL database
- Provide connection credentials — SQL is generated and executed against your real data
- Credentials are never stored persistently

**Security**
- Auth middleware validates JWT on every protected route
- Request logging middleware: IP, method, path, status code, response time
- Custom exception hierarchy for clean error handling
- Rate-limit friendly architecture (Redis-ready)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.11 |
| Database | PostgreSQL + SQLAlchemy async |
| Auth | JWT (RS256), httpOnly cookies |
| LLM | Groq API (Llama 3.3 70B) |
| Logging | Loguru |
| Containerization | Docker (multi-stage build) |

---

## Project Structure

```
Text2Query/
├── backend/
│   ├── app/
│   │   ├── core/          # config, exceptions, dependencies
│   │   ├── db/            # engine, session, base model
│   │   ├── middleware/    # auth, logging
│   │   ├── models/        # SQLAlchemy models
│   │   ├── repositories/  # data access layer
│   │   ├── route/         # API routers
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # LLM service, DB connection service
│   └── run.py
├── frontend/
└── Dockerfile
```

---

## API Overview

| Method | Path | Description | Auth required |
|---|---|---|---|
| POST | `/auth/login` | Login, sets httpOnly cookie | No |
| POST | `/auth/signup` | Register, sets httpOnly cookie | No |
| POST | `/auth/logout` | Clears auth cookie | No |
| GET | `/auth/me` | Returns current user info | Yes |
| POST | `/sql/get_sql` | Generate SQL from prompt | Yes |
| GET | `/history/get_history` | Get user query history | Yes |
| POST | `/user_db/try_connect` | Test external DB connection | Yes |
| POST | `/user_db/execute_query` | Execute SQL on external DB | Yes |

---

## Roadmap

### In Progress
- [ ] Email verification on registration
- [ ] Password reset via email
- [ ] LLM request timeout handling
- [ ] Broader error handling coverage

### Planned

**Schema-aware SQL generation** — the most impactful upcoming feature.

Currently the LLM generates SQL without knowing the actual structure of the user's database. The planned approach:

1. On DB connection, read and cache the full schema (tables, columns, types, relationships)
2. When a user submits a prompt, use a lightweight LLM (e.g. Llama 3 8B) to identify which tables are relevant to the request
3. Pass only the relevant schema fragment + the original prompt to the main model
4. Return a query that references real table and column names from the user's database

This eliminates the need for the user to know their own schema and makes the generated SQL immediately executable.

**Redis integration** — session caching, rate limiting, connection credential TTL storage

**Monitoring** — Prometheus metrics per endpoint, Grafana dashboard

**Encrypted credential storage** — connection credentials encrypted at rest, decryption key on a separate service (GDPR-oriented architecture)

---

## Running Locally

```bash
# Clone the repo
git clone https://github.com/yourname/text2query.git

# Create .env in project root (see .env.example)
cp .env.example .env

# Run with Docker
docker build -t text2query .
docker run -p 8000:8000 --env-file .env text2query
```

> Requires PostgreSQL instance and Groq API key.

---

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL async connection string |
| `PRIVATE_KEY_B64` | Base64-encoded RS256 private key |
| `PUBLIC_KEY_B64` | Base64-encoded RS256 public key |
| `LLM_API_KEY` | Groq API key |
| `DEBUG` | Enable debug mode (default: false) |

---

## License

MIT