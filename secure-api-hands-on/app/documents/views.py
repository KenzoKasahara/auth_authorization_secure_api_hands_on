import logging

from django.conf import settings
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from config.audit import client_ip, log_event

from .models import Document
from .permissions import DocumentAccessPolicy
from .serializers import DocumentSerializer


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [DocumentAccessPolicy]

    def get_authenticators(self):
        if settings.INSECURE_NO_AUTH:
            return []
        return super().get_authenticators()

    def get_permissions(self):
        if settings.INSECURE_NO_AUTH:
            return [AllowAny()]
        return super().get_permissions()

    def get_queryset(self):
        """データ取得の時点でユーザー単位へ絞り込む（防御の 1 段目）。

        Permission クラス（防御の 2 段目）だけに頼らないのは、
        一覧 API では has_object_permission が呼ばれないため。
        """
        if settings.INSECURE_NO_AUTH or settings.INSECURE_OBJECT_ACCESS:
            # Chapter 01 / Chapter 05 で BOLA を再現するための学習用フラグ
            return Document.objects.all()

        user = self.request.user
        if user.is_admin_role:
            return Document.objects.all()
        return Document.objects.filter(owner=user)

    def perform_create(self, serializer):
        if settings.INSECURE_MASS_ASSIGNMENT:
            # Chapter 07 で攻撃を再現するための学習用フラグ。本番では使わない。
            serializer.save()
            return
        # owner はリクエストボディではなく、認証済みユーザーから決める
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        log_event(
            logging.INFO,
            "admin_delete",
            user_id=getattr(self.request.user, "id", None),
            resource=f"document:{instance.pk}",
            ip=client_ip(self.request),
        )
        super().perform_destroy(instance)
