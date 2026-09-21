from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ["id", "title", "content", "owner", "created_at"]
        # owner はサーバー側（View の perform_create）で決定する。
        # read_only にしないと、クライアントが owner を指定できてしまう（Mass Assignment）。
        read_only_fields = ["id", "owner", "created_at"]

    def get_fields(self):
        fields = super().get_fields()
        if settings.INSECURE_MASS_ASSIGNMENT:
            # Chapter 07 で攻撃を再現するための学習用フラグ。本番では使わない。
            # read_only を外すだけでは queryset が無いため、書き込み可能な field へ差し替える。
            fields["owner"] = serializers.PrimaryKeyRelatedField(
                queryset=get_user_model().objects.all()
            )
        return fields
