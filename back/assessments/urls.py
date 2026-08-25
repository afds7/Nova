from django.urls import path
from .views import AssessmentCreateView, LastAssessmentView
from .auth_views import RegisterView, EmailLoginView
from .dashboard_views import DashboardView, MissionSuggestionsView
from .portfolio_views import (
    EvidenciaPortfolioDetailView,
    EvidenciaPortfolioFileView,
    EvidenciaPortfolioListCreateView,
    PortfolioUploadStartView,
)
from .mission_flow_views import EvidencePublishView, MissionCompleteView

urlpatterns = [
    path('submit/', AssessmentCreateView.as_view(), name='assessment-submit'),
    path('last/', LastAssessmentView.as_view(), name='assessment-last'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('missions/suggestions/', MissionSuggestionsView.as_view(), name='mission-suggestions'),
    path('missoes/<uuid:mission_id>/concluir/', MissionCompleteView.as_view(), name='mission-complete'),
    path('portfolio/evidencias/<uuid:evidence_id>/publicar/', EvidencePublishView.as_view(), name='portfolio-evidence-publish'),
    path('portfolio/upload/iniciar/', PortfolioUploadStartView.as_view(), name='portfolio-upload-start'),
    path('portfolio/evidencias/', EvidenciaPortfolioListCreateView.as_view(), name='portfolio-evidencias'),
    path('portfolio/evidencias/<uuid:evidence_id>/arquivo/', EvidenciaPortfolioFileView.as_view(), name='portfolio-evidence-file'),
    path('portfolio/evidencias/<uuid:evidence_id>/', EvidenciaPortfolioDetailView.as_view(), name='portfolio-evidence-detail'),
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/', EmailLoginView.as_view(), name='auth_login'),
]
