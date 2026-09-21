"""ハンズオン用のデモデータを作成する。

  alice (role=user)  -> Document 1
  bob   (role=user)  -> Document 2
  root  (role=admin) -> Document なし

何度実行しても同じ状態になる（べき等）。
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from accounts.models import Role
from documents.models import Document

DEMO_PASSWORD = "Handson-Passw0rd!"

USERS = [
    (1, "alice", Role.USER),
    (2, "bob", Role.USER),
    (3, "root", Role.ADMIN),
]

DOCUMENTS = [
    (1, "alice", "Alice Private Note", "alice しか読めないはずの内容"),
    (2, "bob", "Bob Private Note", "bob しか読めないはずの内容"),
]


class Command(BaseCommand):
    help = "ハンズオン用のユーザーと Document を作成する"

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        Document.objects.all().delete()
        User.objects.filter(username__in=[name for _, name, _ in USERS]).delete()

        created = {}
        for pk, username, role in USERS:
            # pk を固定することで、再実行してもドキュメント中の ID と一致させる
            user = User.objects.create_user(
                pk=pk,
                username=username,
                password=DEMO_PASSWORD,
                role=role,
            )
            created[username] = user
            self.stdout.write(f"user  id={user.id} username={username} role={role}")

        for pk, owner, title, content in DOCUMENTS:
            doc = Document.objects.create(
                pk=pk, owner=created[owner], title=title, content=content
            )
            self.stdout.write(f"doc   id={doc.id} owner={owner} title={title}")

        # 明示的な pk で作成したので、シーケンスを実データに合わせ直す。
        # これをしないと、この後の POST /api/documents/ が pk 重複で失敗する。
        with connection.cursor() as cursor:
            for table in ("accounts_user", "documents_document"):
                cursor.execute(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
                )

        self.stdout.write(self.style.SUCCESS(f"seed done (password: {DEMO_PASSWORD})"))
