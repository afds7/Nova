from django.urls import path
from .views import AssessmentCreateView, LastAssessmentView
from .auth_views import RegisterView, EmailLoginView
from .dashboard_views import DashboardView, MissionSuggestionsView

urlpatterns = [
    path('submit/', AssessmentCreateView.as_view(), name='assessment-submit'),
    path('last/', LastAssessmentView.as_view(), name='assessment-last'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('missions/suggestions/', MissionSuggestionsView.as_view(), name='mission-suggestions'),
    path('auth/register/', RegisterView.as_view(), name='auth_register'),
    path('auth/login/', EmailLoginView.as_view(), name='auth_login'),
]
