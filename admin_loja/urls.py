from django.urls import path
from . import views

app_name = 'admin_loja'

urlpatterns = [
    # Temporário - será implementado na segunda fase
    path('', views.DashboardView.as_view(), name='dashboard'),
]
