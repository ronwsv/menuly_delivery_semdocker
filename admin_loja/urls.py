from django.urls import path
from . import views

app_name = 'admin_loja'

urlpatterns = [
    path('login/', views.admin_loja_login, name='login'),
    path('dashboard/', views.admin_loja_dashboard, name='dashboard'),
    path('pedidos/', views.admin_loja_pedidos, name='pedidos'),
    path('pedidos/<uuid:pedido_id>/', views.admin_loja_cupom_pedido, name='cupom_pedido'),
    path('pedidos/<uuid:pedido_id>/avancar/', views.admin_loja_avancar_status_pedido, name='avancar_status_pedido'),
    path('', views.DashboardView.as_view(), name='dashboard-old'),
]
