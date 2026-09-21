import logging

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from config.audit import client_ip, log_event

from .serializers import MeSerializer


class AuditedTokenObtainPairView(TokenObtainPairView):
    """ログインエンドポイント。

    - ScopedRateThrottle の対象（Brute Force 対策 / Chapter 08）
    - 成功・失敗の両方を監査ログへ記録する（Chapter 10）
    - password はログに出さない。username は攻撃調査に必要なので記録する。
    """

    throttle_scope = "login"

    def post(self, request, *args, **kwargs):
        username = request.data.get("username", "-")
        try:
            response = super().post(request, *args, **kwargs)
        except AuthenticationFailed:
            # exception handler 側の二重記録を避ける
            request._audit_logged = True
            log_event(
                logging.WARNING,
                "login_failure",
                username=username,
                ip=client_ip(request),
                path=request.path,
                status=401,
            )
            raise

        log_event(
            logging.INFO,
            "login_success",
            username=username,
            ip=client_ip(request),
            path=request.path,
            status=response.status_code,
        )
        return response


class AuditedTokenRefreshView(TokenRefreshView):
    """Refresh Token から Access Token を再発行する（Chapter 03）。"""

    throttle_scope = "login"


class MeView(APIView):
    """現在の Token がどのユーザー・どの role として解決されたかを返す。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)
