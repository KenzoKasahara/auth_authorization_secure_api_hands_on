"""
セキュリティイベントの監査ログ。

記録するもの：誰が / いつ / どの操作を / どのリソースに対して試み / どう扱われたか
記録しないもの：password / access token / refresh token / secret

DRF の EXCEPTION_HANDLER として登録し、401 / 403 / 429 を一箇所で捕捉する。
各 View から個別に呼ぶ必要があるのは「成功イベント」だけになる。
"""

import logging

from django.http import Http404
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    Throttled,
)
from rest_framework.views import exception_handler

logger = logging.getLogger("security")

# 値に含まれてはいけないキー。渡された場合は握りつぶさず、明示的に落とす。
FORBIDDEN_FIELDS = {"password", "token", "access", "refresh", "secret", "authorization"}


def log_event(level: int, event: str, **fields) -> None:
    leaked = FORBIDDEN_FIELDS & set(fields)
    if leaked:
        raise ValueError(f"監査ログに秘密情報を渡そうとしました: {sorted(leaked)}")
    payload = " ".join(f"{key}={value}" for key, value in fields.items() if value is not None)
    logger.log(level, f"{event} {payload}".strip())


def client_ip(request) -> str:
    return request.META.get("REMOTE_ADDR", "-")


def user_id_of(request):
    user = getattr(request, "user", None)
    return getattr(user, "id", None) if getattr(user, "is_authenticated", False) else None


def audit_exception_handler(exc, context):
    response = exception_handler(exc, context)
    request = context.get("request")
    if request is None or response is None:
        return response

    # View 側ですでに記録済みのイベントは二重に出さない
    if getattr(request, "_audit_logged", False):
        return response

    common = {
        "user_id": user_id_of(request),
        "method": request.method,
        "path": request.path,
        "ip": client_ip(request),
        "status": response.status_code,
    }

    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        log_event(logging.WARNING, "authentication_failure", **common)
    elif isinstance(exc, PermissionDenied):
        log_event(logging.WARNING, "authorization_failure", **common)
    elif isinstance(exc, Throttled):
        log_event(logging.WARNING, "rate_limit_exceeded", retry_after=exc.wait, **common)
    elif isinstance(exc, (NotFound, Http404)):
        # DRF は get_object_or_404 の Django Http404 も 404 レスポンスへ変換するため、
        # 両方を捕捉しないと owner スコープによる 404 を取りこぼす。
        # owner スコープの QuerySet では、他人のリソースへのアクセスも 404 になる。
        # 攻撃の痕跡を失わないよう、404 も監査対象に含める。
        log_event(logging.WARNING, "resource_not_found", **common)

    return response
