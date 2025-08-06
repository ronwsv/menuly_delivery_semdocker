from django.urls import path
from . import views

app_name = 'superadmin'

urlpatterns = [
    # Temporário - será implementado na terceira fase
    path('', views.DashboardView.as_view(), name='dashboard'),
]
