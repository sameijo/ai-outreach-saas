# 🚀 AI Outreach — Email Lead Generation SaaS

AI-powered cold email outreach platform. Find leads, personalize with AI, send bulk campaigns, track everything.

## ⚡ Quick Start (2 minutes)

```bash
cd ai-outreach-saas/backend

# Install dependencies
pip install -r requirements.txt

# Start server (uses SQLite — no database setup needed)
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open **http://localhost:8000/docs** for full API documentation.

## 🐳 Docker Start (Production)

```bash
cd ai-outreach-saas
cp .env.example .env   # Edit with your API keys
docker compose up -d
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📦 What's Built

### Module A — Lead Discovery
- **Apollo.io** integration — search by niche/industry/title
- **Hunter.io** integration — domain search + email finder
- **CSV upload** — import your existing leads
- **Email verification** — DNS MX check, disposable detection, Hunter deep verify

### Module B — AI Personalization
- **OpenAI GPT-4o-mini** generates unique intro per lead
- Scrapes company website for context
- 3 tones: Professional, Casual, Persuasive
- Example: *"Hi John, I noticed Acme Corp's recent Series B — congrats on the fintech growth!"*

### Module C — Email Sending Engine
- **5 providers**: SendGrid, Amazon SES, Mailgun, Resend, Custom SMTP
- **Campaign management**: subject lines, HTML body, follow-up sequences
- **Rate limiting**: emails per hour/day, send windows
- **Tracking**: open pixel, click redirect, reply detection, bounce handling
- **Unsubscribe**: CAN-SPAM/GDPR compliant auto-injected links

### Module D — Dashboard & Analytics
- Overview stats: leads, sent, open/click/reply rates
- Activity chart: daily performance over time
- Campaign table: status and metrics
- CSV export

---

## 🔑 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Login, get JWT |
| GET | `/api/v1/auth/me` | Current user |
| POST | `/api/v1/leads/search` | Search leads (Apollo/Hunter) |
| POST | `/api/v1/leads/upload-csv` | Upload CSV |
| POST | `/api/v1/leads/enrich` | AI personalize intros |
| POST | `/api/v1/leads/verify` | Verify emails |
| GET | `/api/v1/leads/lists` | List all lead lists |
| GET | `/api/v1/leads/lists/:id` | List detail with leads |
| POST | `/api/v1/campaigns` | Create campaign |
| POST | `/api/v1/campaigns/:id/start` | Start sending |
| POST | `/api/v1/campaigns/:id/pause` | Pause |
| GET | `/api/v1/campaigns/:id/stats` | Campaign stats |
| GET | `/api/v1/campaigns/:id/events` | Email events |
| POST | `/api/v1/campaigns/smtp-configs` | Add email provider |
| GET | `/api/v1/dashboard/overview` | Dashboard stats |
| GET | `/api/v1/dashboard/activity` | Activity chart data |
| GET | `/api/v1/track/open/:id` | Open tracking pixel |
| GET | `/api/v1/track/unsubscribe/:id` | Unsubscribe |

---

## 🧪 Test the API

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test1234!","full_name":"Test User"}'

# Use the token from register response
TOKEN="your-token-here"

# Upload leads
curl -X POST http://localhost:8000/api/v1/leads/upload-csv?list_name=MyLeads \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@your-leads.csv"

# Create campaign
curl -X POST http://localhost:8000/api/v1/campaigns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q1 Outreach",
    "lead_list_id": 1,
    "subject": "Hi {{first_name}}",
    "body_html": "<p>Hi {{first_name}}, {{ai_intro}}</p>",
    "personalize_with_ai": true,
    "ai_tone": "professional"
  }'

# Start campaign
curl -X POST http://localhost:8000/api/v1/campaigns/1/start \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📁 CSV Format

```csv
email,first_name,last_name,job_title,company,website,linkedin
alice@acme.com,Alice,Smith,CEO,Acme Corp,https://acme.com,linkedin.com/in/alice
bob@tech.io,Bob,Jones,CTO,Tech Inc,https://tech.io,linkedin.com/in/bob
```

Required: `email` column. All others optional (become template variables).

---

## ⚙️ Configuration

### Required API Keys (at least one per category)

| Category | Service | Env Variable |
|----------|---------|-------------|
| Lead Search | Apollo.io | `APOLLO_API_KEY` |
| Lead Search | Hunter.io | `HUNTER_API_KEY` |
| Email Send | SendGrid | `SENDGRID_API_KEY` |
| Email Send | Amazon SES | `AWS_SES_ACCESS_KEY` + `AWS_SES_SECRET_KEY` |
| Email Send | Mailgun | `MAILGUN_API_KEY` + `MAILGUN_DOMAIN` |
| Email Send | Resend | `RESEND_API_KEY` |
| AI | OpenAI | `OPENAI_API_KEY` |

### Template Variables

Use in subject lines and body:
- `{{first_name}}` `{{last_name}}` `{{full_name}}`
- `{{email}}` `{{company}}` `{{job_title}}`
- `{{industry}}` `{{website}}`
- `{{ai_intro}}` — AI-generated personalized opening

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python FastAPI |
| Database | PostgreSQL (prod) / SQLite (dev) |
| Queue | Redis + Celery (optional) |
| Frontend | Next.js + Tailwind CSS + Recharts |
| AI | OpenAI GPT-4o-mini |
| Auth | JWT (access + refresh tokens) |

---

## 📂 Project Structure

```
ai-outreach-saas/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI entry
│   │   ├── core/                ← Config, DB, Auth
│   │   ├── models/              ← SQLAlchemy models
│   │   ├── schemas/             ← Pydantic schemas
│   │   ├── api/v1/endpoints/    ← All API routes
│   │   ├── services/            ← Business logic
│   │   └── tasks/               ← Background workers
│   └── requirements.txt
├── frontend/
│   └── src/app/                 ← Next.js pages
└── docs/README.md
```

---

## 💰 Cost Estimate

| Item | Cost |
|------|------|
| Server (VPS) | $20/mo |
| Apollo.io | $49/mo (250 leads) |
| SendGrid | Free (100/day) → $20/mo |
| OpenAI | ~$0.01/lead personalization |
| **Total MVP** | **~$70-90/mo** |

Per-email cost: **~$0.003** (including AI personalization)
