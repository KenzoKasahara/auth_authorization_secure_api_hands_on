from django.conf import settings
from rest_framework.permissions import SAFE_METHODS, BasePermission


class DocumentAccessPolicy(BasePermission):
    """Document に対する API 認可 + オブジェクト認可。

    レイヤーを分けている点が重要：

    has_permission        : 「この種類の操作をしてよいか」（API Permission / RBAC）
    has_object_permission : 「この 1 件を操作してよいか」（Object-Level Authorization）

    has_permission だけでは BOLA / IDOR は防げない。
    """

    def has_permission(self, request, view):
        if settings.INSECURE_NO_AUTH:
            # Chapter 01 の「認証なし API」を再現するための学習用フラグ
            return True

        user = request.user
        if not (user and user.is_authenticated):
            return False

        # DELETE は admin ロールのみ（Chapter 04）
        if request.method == "DELETE":
            self.message = "DELETE には admin ロールが必要です。"
            return user.is_admin_role

        return True

    def has_object_permission(self, request, view, obj):
        if settings.INSECURE_NO_AUTH or settings.INSECURE_OBJECT_PERMISSION:
            # Chapter 05 で BOLA を再現するための学習用フラグ
            return True

        user = request.user
        if user.is_admin_role:
            return True

        allowed = obj.owner_id == user.id
        if not allowed and request.method in SAFE_METHODS:
            self.message = "このリソースの所有者ではありません。"
        return allowed
