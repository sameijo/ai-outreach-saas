#!/bin/bash
# Production deployment script
set -e

echo "🚀 AI Outreach — Production Deployment"
echo "======================================="

# Check .env
if [ ! -f .env ]; then
    echo "❌ .env not found. Copy .env.example and fill in your values."
    exit 1
fi

# Source .env for validation
source .env 2>/dev/null || true

# Validate required vars
MISSING=()
[ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "change-me" ] && MISSING+=("SECRET_KEY")
[ -z "$JWT_SECRET_KEY" ] || [ "$JWT_SECRET_KEY" = "change-me-jwt-secret" ] && MISSING+=("JWT_SECRET_KEY")

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "⚠️  Missing or default values: ${MISSING[*]}"
    echo "   Edit .env before deploying to production!"
    exit 1
fi

echo "✅ .env validated"

# Build and deploy
echo ""
echo "📦 Building Docker images..."
docker compose build --no-cache

echo ""
echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health check
echo ""
echo "🏥 Health check..."
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker compose logs backend
    exit 1
fi

if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "⚠️  Frontend may still be starting..."
fi

echo ""
echo "======================================="
echo "✅ Deployment complete!"
echo ""
echo "   Frontend:  http://localhost:3000"
echo "   Backend:   http://localhost:8000"
echo "   API Docs:  http://localhost:8000/docs"
echo ""
echo "📋 Useful commands:"
echo "   docker compose logs -f          # View all logs"
echo "   docker compose logs -f backend  # Backend logs only"
echo "   docker compose ps               # Service status"
echo "   docker compose down             # Stop all"
echo "======================================="
