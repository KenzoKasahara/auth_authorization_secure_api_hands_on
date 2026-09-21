from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):
    """role=admin のユーザーだけを許可する。"""

    message = "この操作には admin ロールが必要です。"

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_admin_role)
