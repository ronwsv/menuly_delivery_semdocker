#!/bin/bash

echo "🐳 Menuly Delivery - Docker Setup"
echo "================================="

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
until python manage.py dbshell --command="SELECT 1" 2>/dev/null; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "✅ Database is ready!"

# Run migrations
echo "🔧 Running migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "👤 Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@menuly.com', 'admin123')
    print('Superuser created successfully!')
else:
    print('Superuser already exists!')
EOF

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create test data
echo "🎯 Creating test data..."
python manage.py shell << EOF
try:
    from core.models import Plano
    if Plano.objects.count() == 0:
        exec(open('core/management/commands/criar_dados_teste.py').read())
        print('Test data created successfully!')
    else:
        print('Test data already exists!')
except Exception as e:
    print(f'Error creating test data: {e}')
EOF

echo "🚀 Docker setup completed!"
echo ""
echo "📋 Access Information:"
echo "  🌐 Application: http://localhost:8000"
echo "  👨‍💼 Admin Panel: http://localhost:8000/admin/"
echo "  🏪 Store Panel: http://localhost:8000/admin-loja/login/"
echo "  🏍️ Delivery Panel: http://localhost:8000/entregador/login/"
echo ""
echo "🔑 Default Credentials:"
echo "  Admin: admin / admin123"
echo "  Store: lojista_teste / senha123"
echo "  Delivery: entregador_teste / senha123"
echo ""