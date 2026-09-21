from django.urls import path

from .views import AuditedTokenObtainPairView, AuditedTokenRefreshView, MeView

urlpatterns = [
    path("token/", AuditedTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", AuditedTokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
]
