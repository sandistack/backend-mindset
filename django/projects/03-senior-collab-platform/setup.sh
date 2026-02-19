#!/bin/bash

# Senior Collaboration Platform Setup Script

echo "🚀 Setting up Senior Collaboration Platform..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create logs directory
mkdir -p logs

# Start Docker services
echo "📦 Starting Docker services..."
docker-compose up -d db redis elasticsearch

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run migrations
echo "🔄 Running database migrations..."
docker-compose run --rm api python manage.py makemigrations
docker-compose run --rm api python manage.py migrate

# Create superuser (optional - commented out for automation)
# echo "👤 Creating superuser..."
# docker-compose run --rm api python manage.py createsuperuser

# Start all services
echo "🎉 Starting all services..."
docker-compose up -d

# Show service status
echo ""
echo "✅ Setup complete! Services status:"
docker-compose ps

echo ""
echo "📍 Access points:"
echo "   - API: http://localhost:8000"
echo "   - WebSocket: ws://localhost:8001"
echo "   - Admin: http://localhost:8000/admin"
echo "   - API Docs: http://localhost:8000/swagger/"
echo ""
echo "📝 Logs:"
echo "   docker-compose logs -f api"
echo "   docker-compose logs -f websocket"
echo "   docker-compose logs -f celery"
echo ""
echo "🛠️  Create superuser:"
echo "   docker-compose exec api python manage.py createsuperuser"
