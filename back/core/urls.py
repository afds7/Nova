from django.contrib import admin
from django.urls import path, include
from assessments.auth_views import RegisterView, EmailLoginView
from assessments.dashboard_views import DashboardView
from assessments.portfolio_views import (
    EvidenciaPortfolioDetailView,
    EvidenciaPortfolioListCreateView,
    PortfolioUploadStartView,
)
from assessments.mission_flow_views import EvidencePublishView, MissionCompleteView
from assessments.dashboard_views import MissionSuggestionsView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/assessments/', include('assessments.urls')),
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'),
    path('api/dashboard/resumo/', DashboardView.as_view(), name='dashboard-summary'),
    path('api/portfolio/upload/iniciar/', PortfolioUploadStartView.as_view(), name='portfolio-upload-start-public'),
    path('api/portfolio/evidencias/', EvidenciaPortfolioListCreateView.as_view(), name='portfolio-evidencias-public'),
    path('api/portfolio/evidencias/<uuid:evidence_id>/', EvidenciaPortfolioDetailView.as_view(), name='portfolio-evidence-detail-public'),
    path('api/missoes/<uuid:mission_id>/concluir/', MissionCompleteView.as_view(), name='mission-complete-public'),
    path('api/missoes/sugeridas/', MissionSuggestionsView.as_view(), name='mission-suggestions-public'),
    path('api/portfolio/evidencias/<uuid:evidence_id>/publicar/', EvidencePublishView.as_view(), name='portfolio-evidence-publish-public'),
    # Endpoints de autenticação chamados pelo NextAuth
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/login/', EmailLoginView.as_view(), name='auth_login'),
]
