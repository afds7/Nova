from django.contrib import admin
from django.urls import path, include
from assessments.auth_views import RegisterView, EmailLoginView
from assessments.dashboard_views import DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/assessments/', include('assessments.urls')),
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'),
    # Endpoints de autenticação chamados pelo NextAuth
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/login/', EmailLoginView.as_view(), name='auth_login'),
]
