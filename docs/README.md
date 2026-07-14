# AI Outreach — Email Lead Generation Platform

A comprehensive, AI-powered SaaS platform for cold email outreach and lead generation.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                    │
│  Dashboard │ Leads │ Campaigns │ Settings │ Auth         │
└────────────────────────┬────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────┐
│                 Backend (FastAPI)                         │
│  /api/v1/auth  │ /leads │ /campaigns │ /track │ /dashboard│
├─────────────────────────────────────────────────────────┤
│  Services                                               │
│  LeadService │ AIService │ EmailService │ CampaignService │
├──────────┬──────────┬──────────┬────────────────────────┤
│ Apollo.io│ Hunter.io│ OpenAI   │ SendGrid/SES/Mailgun   │
└──────────┴──────────┴──────────┴────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    PostgreSQL        Redis          Celery Worker
   (data store)    (queue/cache)   (background tasks)
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- API keys for at least one:
  - **Lead data**: Apollo.io or Hunter.io
  - **Email sending**: SendGrid, Amazon SES, Mailgun, or Resend
  - **AI**: OpenAI (optional, for personalization)

### 1. Clone & Configure

```bash
cd ai-outreach-saas
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required
SECRET_KEY=your-random-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here

# Database (Docker default works out of the box)
DATABASE_URL=postgresql+asyncpg://outreach:outreach_secret@postgres:5432/outreach_db

# At least one lead API
APOLLO_API_KEY=your-apollo-key

# At least one email provider
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.your-key-here

# AI (optional but recommended)
OPENAI_API_KEY=sk-your-key-here
```

### 2. Launch with Docker

```bash
docker compose up -d
```

This starts:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Celery Worker**: background task processing
- **Celery Beat**: scheduled task execution

### 3. Create Your Account

1. Open http://localhost:3000
2. Click "Sign up" → register with email/password
3. You're in! 100 free credits to start.

---

## 📦 Modules

### Module A: Lead Discovery

**Search for leads** by niche/industry:
- Type a query like "SaaS Founders in London" or "Marketing Directors in Tech"
- Choose provider: Apollo.io or Hunter.io
- Results auto-populate with: Name, Title, Company, Email, LinkedIn, Phone

**Upload CSV** with your existing leads:
- Required column: `email`
- Optional: `first_name`, `last_name`, `job_title`, `company`, `website`, `linkedin`

**Email Verification**:
- DNS MX record check
- Disposable email detection
- Hunter.io deep verification (if configured)

### Module B: AI Personalization

**Enrich leads with AI**:
- Click "✨ AI Enrich" on any lead list
- AI scrapes company website for context
- Generates personalized opening lines per lead
- Choose tone: Professional, Casual, or Persuasive

**Example output**:
```
Instead of: "Hi John,"
Generates:  "Hi John, I noticed Acme Corp's recent Series B — 
             congrats on the growth in the fintech space!"
```

### Module C: Email Campaigns

**Create campaigns** with:
- Subject lines with variables: `{{first_name}}`, `{{company}}`, `{{ai_intro}}`
- HTML email body with full formatting
- Follow-up sequences (drip campaigns)
- Rate limiting (emails per hour/day)
- Send window (e.g., 9 AM - 5 PM in recipient's timezone)

**Sending engine supports**:
- SendGrid API
- Amazon SES
- Mailgun
- Resend
- Custom SMTP

**Tracking**:
- Open tracking (pixel)
- Click tracking (link redirect)
- Reply detection (webhook)
- Bounce handling
- Unsubscribe management (CAN-SPAM/GDPR compliant)

### Module D: Dashboard & Analytics

- **Overview**: Total leads, emails sent, open/click/reply rates
- **Activity chart**: Daily email performance over time
- **Engagement breakdown**: Visual pie chart
- **Campaign table**: Status and metrics for all campaigns
- **Export**: Download leads as CSV

---

## 🔧 API Reference

Once running, visit **http://localhost:8000/docs** for full Swagger documentation.

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Get JWT tokens |
| POST | `/api/v1/leads/search` | Search leads via API |
| POST | `/api/v1/leads/upload-csv` | Upload CSV leads |
| POST | `/api/v1/leads/enrich` | AI enrich leads |
| POST | `/api/v1/leads/verify` | Verify emails |
| GET | `/api/v1/leads/lists` | List lead lists |
| POST | `/api/v1/campaigns` | Create campaign |
| POST | `/api/v1/campaigns/{id}/start` | Start campaign |
| GET | `/api/v1/campaigns/{id}/stats` | Campaign stats |
| GET | `/api/v1/dashboard/overview` | Dashboard stats |
| GET | `/api/v1/track/open/{id}` | Open tracking pixel |
| GET | `/api/v1/track/unsubscribe/{id}` | Unsubscribe handler |

---

## 🌐 Production Deployment

### Option 1: Docker Compose (VPS/EC2)

```bash
# On your server
git clone <repo>
cd ai-outreach-saas
cp .env.example .env
# Edit .env with production values

# Build and start
docker compose -f docker-compose.yml up -d --build

# Check logs
docker compose logs -f backend
```

### Option 2: AWS (ECS + RDS + ElastiCache)

1. **Database**: Create RDS PostgreSQL instance
2. **Cache**: Create ElastiCache Redis cluster
3. **Backend**: Deploy to ECS Fargate
4. **Frontend**: Deploy to Vercel or CloudFront + S3
5. **Worker**: Separate ECS service for Celery

### Option 3: Vercel + Railway

1. **Frontend**: Deploy to Vercel (`cd frontend && vercel`)
2. **Backend**: Deploy to Railway (connect GitHub repo)
3. **Database**: Railway PostgreSQL addon
4. **Redis**: Railway Redis addon

### Environment Variables for Production

```env
# Security
DEBUG=false
SECRET_KEY=<random-64-char-string>
JWT_SECRET_KEY=<random-64-char-string>
ALLOWED_ORIGINS=https://yourdomain.com

# Database (use connection pooling)
DATABASE_URL=postgresql+asyncpg://user:pass@rds-host:5432/outreach_db

# Redis
REDIS_URL=redis://elasticache-host:6379/0
CELERY_BROKER_URL=redis://elasticache-host:6379/1

# Tracking
TRACKING_DOMAIN=https://api.yourdomain.com
```

### DNS Setup for Deliverability

**Critical for cold email** — configure these DNS records:

```
# SPF (TXT record)
v=spf1 include:sendgrid.net ~all

# DKIM (CNAME records from your email provider)
s1._domainkey.yourdomain.com → s1.domainkey.uXXX.wl.sendgrid.net
s2._domainkey.yourdomain.com → s2.domainkey.uXXX.wl.sendgrid.net

# DMARC (TXT record)
_dmarc.yourdomain.com → v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com
```

---

## 📊 Cost Breakdown

### Infrastructure (Monthly)

| Service | Small (< 1K emails/day) | Medium (< 10K/day) |
|---------|------------------------|---------------------|
| VPS/Server | $20 (Hetzner/DigitalOcean) | $80 (AWS ECS) |
| PostgreSQL | Included | $15 (RDS) |
| Redis | Included | $10 (ElastiCache) |
| **Total** | **~$20/mo** | **~$105/mo** |

### API Costs (Per 1,000 operations)

| Service | Cost |
|---------|------|
| Apollo.io | $49/mo (250 credits) — $0.20/lead |
| Hunter.io | $49/mo (500 searches) — $0.10/lead |
| OpenAI (gpt-4o-mini) | ~$0.01 per personalized intro |
| SendGrid | Free (100/day) → $19.95/mo (50K/mo) |
| Amazon SES | $0.10 per 1,000 emails |
| Resend | Free (3K/mo) → $20/mo (50K) |

### Estimated MVP Cost

- **Development**: 2-3 weeks full-time
- **Monthly operating**: $20-100 depending on volume
- **Per email cost**: ~$0.001-0.005 (including AI personalization)

---

## 🔒 Security & Compliance

- **JWT authentication** with access + refresh tokens
- **bcrypt password hashing**
- **API key encryption** at rest
- **CORS** configured for frontend origin only
- **Rate limiting** on all endpoints
- **CAN-SPAM compliant**: automatic unsubscribe links
- **GDPR compliant**: data export, deletion, consent tracking

---

## 🛠️ Development

### Local Development (without Docker)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Celery Worker
cd backend
celery -A app.tasks.worker worker -l info

# Celery Beat
celery -A app.tasks.worker beat -l info
```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

---

## 📁 Project Structure

```
ai-outreach-saas/
├── docker-compose.yml          # Full stack orchestration
├── .env.example                # Environment template
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # FastAPI entry point
│       ├── core/
│       │   ├── config.py       # Settings from env
│       │   ├── database.py     # Async SQLAlchemy
│       │   └── security.py     # JWT + password hashing
│       ├── models/
│       │   ├── user.py         # User model
│       │   ├── lead.py         # Lead + LeadList models
│       │   └── campaign.py     # Campaign + EmailEvent + SMTPConfig
│       ├── schemas/
│       │   ├── user.py         # Pydantic request/response
│       │   ├── lead.py
│       │   └── campaign.py
│       ├── api/v1/endpoints/
│       │   ├── auth.py         # Register, login, refresh
│       │   ├── leads.py        # Search, upload, enrich, verify
│       │   ├── campaigns.py    # CRUD, start/pause, SMTP configs
│       │   ├── tracking.py     # Open pixel, click, unsubscribe, webhooks
│       │   └── dashboard.py    # Analytics + export
│       ├── services/
│       │   ├── lead_service.py # Apollo, Hunter, email verification
│       │   ├── ai_service.py   # OpenAI personalization
│       │   ├── email_service.py # SendGrid, SES, Mailgun, Resend, SMTP
│       │   └── campaign_service.py # Campaign orchestration
│       └── tasks/
│           ├── worker.py       # Celery configuration
│           └── campaign_tasks.py # Background tasks
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── lib/api.ts          # API client
│       └── app/
│           ├── layout.tsx      # Root layout
│           ├── globals.css     # Tailwind styles
│           ├── auth/
│           │   ├── login/page.tsx
│           │   └── register/page.tsx
│           └── dashboard/
│               ├── layout.tsx  # Sidebar navigation
│               ├── page.tsx    # Analytics dashboard
│               ├── leads/page.tsx
│               ├── campaigns/page.tsx
│               └── settings/page.tsx
│
└── docs/
    └── README.md               # This file
```

---

## 📝 License

MIT
