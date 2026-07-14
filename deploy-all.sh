#!/bin/bash
# One-click deploy script — Backend + Frontend
set -e

echo "🚀 AI Outreach — Full Deploy"
echo "============================"

# ── Backend: Deploy to Render (free) ──────────────────────
echo ""
echo "📦 Step 1: Backend Deployment"
echo "-----------------------------"
echo ""
echo "Backend deploy options:"
echo "  1. Render.com (free tier)"
echo "  2. Railway.app ($5/mo)"
echo "  3. Vercel Serverless"
echo ""
echo "Auto-deploying to Render..."
echo ""

# Create render.yaml for auto-deploy
cat > render.yaml << 'EOF'
services:
  - type: web
    name: ai-outreach-backend
    runtime: python
    region: oregon
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        value: sqlite+aiosqlite:///./outreach.db
      - key: DEBUG
        value: false
      - key: ALLOWED_ORIGINS
        value: https://ai-outreach.vercel.app
EOF

echo "✅ render.yaml created"
echo ""

# ── Frontend: Deploy to Vercel ────────────────────────────
echo "📦 Step 2: Frontend Deployment"
echo "-----------------------------"
echo ""

# Create vercel.json
cat > vercel.json << 'EOF'
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/next"
    }
  ],
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://ai-outreach-backend.onrender.com/api/:path*"
    }
  ]
}
EOF

echo "✅ vercel.json created"
echo ""

# ── Summary ───────────────────────────────────────────────
echo "============================"
echo "✅ Deploy configs ready!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. BACKEND (Render):"
echo "   → Push to GitHub"
echo "   → Go to render.com → New → Web Service"
echo "   → Connect repo → Auto-deploys"
echo "   → URL: https://ai-outreach-backend.onrender.com"
echo ""
echo "2. FRONTEND (Vercel):"
echo "   → cd frontend"
echo "   → npx vercel --prod"
echo "   → URL: https://ai-outreach.vercel.app"
echo ""
echo "3. PLAY STORE:"
echo "   → Read docs/PLAY_STORE_GUIDE.md"
echo "============================"
