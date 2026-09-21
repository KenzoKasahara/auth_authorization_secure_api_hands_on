# 検証記録

各章の手順を実際に実行した結果の一次記録。ドキュメントに載せた「期待結果」は、すべてこの記録から取っている。

## 検証環境

| 項目 | 値 |
|---|---|
| 実施日 | 2026-09-16（初回）/ 2026-09-21（スタック更新後の再検証） |
| ホスト OS | Windows 11 Pro 26200 |
| Docker | 29.7.2 |
| Docker Compose | v5.5.0 |
| Python（コンテナ内） | 3.14.7（`python:3.14-slim`） |
| uv（コンテナ内） | 0.12.17 |
| Django | 6.1.1 |
| djangorestframework | 3.18.1 |
| djangorestframework-simplejwt | 5.5.1 |
| django-cors-headers | 4.9.0 |
| psycopg | 3.3.6 |
| PostgreSQL | 17.11（`postgres:17-alpine`） |

すべての依存は `app/pyproject.toml` に宣言し、`app/uv.lock` で固定している。イメージのビルドは `uv sync --locked` なので、ロックと宣言がずれていればビルドが失敗する。

---

## スタック更新（2026-09-21）の再検証範囲

Python 3.12 → 3.14、PostgreSQL 16 → 17、依存を最新へ更新し、コンテナの実行を pip から uv へ切り替えた。この更新で再実行した項目は次のとおり。

| 項目 | 結果 | 状態 |
|---|---|:---:|
| `docker compose build`（`uv sync --locked`） | 9パッケージを解決しイメージ生成 | ✅ |
| `docker compose up -d` | `db` healthy 後に `api` 起動、Django 6.1.1 で起動 | ✅ |
| `migrate` | 20マイグレーションすべて適用 | ✅ |
| `makemigrations --check` | `No changes detected`（Django 6 でモデル定義に差分なし） | ✅ |
| `seed_demo` | alice=1 / bob=2 / root=3、doc 1・2 を固定IDで作成 | ✅ |
| `normal_test.sh` | PASS=6 FAIL=0 | ✅ |
| `attack_test.sh` | PASS=9 FAIL=0 | ✅ |

`djangorestframework-simplejwt` 5.5.1 は Django 6.1 を classifier に含んでいないが、上記のテストで発行・検証・Refresh とも期待どおり動作することを確認した。

PostgreSQL 16 のデータディレクトリは 17 では起動できない。更新時は `docker compose down -v` でボリュームを作り直し、`seed_demo` で再投入する。

下の章ごとの表のうち、上記以外の項目（Chapter 01〜10 の個別レスポンス確認）は 2026-09-16 の旧スタックでの結果であり、新スタックでは再実行していない。正常系・異常系スクリプトが両方 PASS しているため結論は変わらないと判断している。

---

## 検証状態の凡例

| 記号 | 意味 |
|---|---|
| ✅ | 実際にコマンドを実行し、出力を確認した |
| ⚠️ | 未検証、または環境依存で確認できていない |

---

## 章ごとの検証結果

| 章 | 検証項目 | 結果 | 状態 |
|---|---|---|:---:|
| 00 | `docker compose build` | 依存が解決しイメージ生成 | ✅ |
| 00 | `migrate` | accounts / documents のマイグレーション適用 | ✅ |
| 00 | `seed_demo` | alice=1 / bob=2 / root=3、doc 1・2 を固定IDで作成 | ✅ |
| 01 | `INSECURE_NO_AUTH=1` で Token なし GET | `200`・全ユーザーの全件 | ✅ |
| 01 | `INSECURE_NO_AUTH=0` で Token なし GET | `401` | ✅ |
| 02 | 正しい資格情報でログイン | `200` + access / refresh | ✅ |
| 02 | 誤ったパスワードでログイン | `401` `No active account found...` | ✅ |
| 02 | Token 改ざん | `401` `Token is invalid` | ✅ |
| 02 | `Bearer` プレフィックスなし | `401` `bad_authorization_header` | ✅ |
| 02 | `/api/auth/me/`（alice / root） | `{"id":1,...,"role":"user"}` / `{"id":3,...,"role":"admin"}` | ✅ |
| 03 | Access Token の payload デコード | `token_type` / `exp` / `iat` / `jti` / `user_id` | ✅ |
| 03 | 寿命1分・70秒後の再実行 | `401` `Token is expired` | ✅ |
| 03 | Refresh による再発行 | `200`、レスポンスは `access` のみ | ✅ |
| 03 | 再発行した Token での API | `200` | ✅ |
| 04 | alice（role=user）の DELETE | `403` | ✅ |
| 04 | root（role=admin）の DELETE | `204` | ✅ |
| 05 | 脆弱時 GET 他人の Document | `200`（bob のデータが返る） | ✅ |
| 05 | 脆弱時 PATCH 他人の Document | `200`（`hijacked by alice` に書き換わる） | ✅ |
| 05 | 脆弱時 一覧 | 全ユーザーの2件 | ✅ |
| 06 | 修正後 GET 他人の Document | `404` | ✅ |
| 06 | 修正後 PATCH 他人の Document | `404` | ✅ |
| 06 | 修正後 一覧 | 自分の1件のみ | ✅ |
| 06 | 防御2層の4通りの組み合わせ | 下表のとおり | ✅ |
| 07 | 脆弱時 POST `owner=2` | `201`、`owner=2` で保存 | ✅ |
| 07 | 脆弱時 PATCH `owner=2` | `200`、所有権が bob へ移る | ✅ |
| 07 | 修正後 POST `owner=2` | `201`、`owner=1` で保存 | ✅ |
| 07 | 修正後 PATCH `owner=2` | `200`、`owner=1` のまま | ✅ |
| 08 | ログイン連打（`5/min`） | 4〜6回目から `429` | ✅ |
| 08 | `429` の本文 | `Request was throttled. Expected available in 59 seconds.` | ✅ |
| 09 | 許可 Origin の preflight | `200` + `access-control-allow-origin` | ✅ |
| 09 | 未許可 Origin の preflight | `200`、CORS ヘッダなし | ✅ |
| 09 | curl + 未許可 Origin + 有効 Token | `200`、データが返る | ✅ |
| 09 | ブラウザ実機での遮断確認 | — | ⚠️ |
| 10 | 全イベント種別の出力 | 7種すべて出力を確認 | ✅ |
| 10 | password / token の混入 | 0件 | ✅ |
| 11 | `normal_test.sh` | PASS=6 FAIL=0 | ✅ |
| 11 | `attack_test.sh` | PASS=9 FAIL=0 | ✅ |
| 11 | 脆弱フラグ ON での `attack_test.sh` | PASS=7 FAIL=2（オブジェクト認可の2件） | ✅ |
| 12 | `docker compose down -v` | コンテナ・ボリューム・ネットワーク削除 | ✅ |

### ⚠️ 未検証の項目

**Chapter 09：ブラウザ実機での CORS 遮断**

curl で preflight のヘッダ有無は確認したが、実際のブラウザが未許可 Origin のレスポンスを JavaScript へ渡さないところまでは確認していない。CORS の遮断はブラウザの実装であり、この API の挙動ではないため、検証には別 Origin でホストしたページが必要になる。

章の主張（「CORS は API の認可機構ではない」）は Step 3 の curl で確認済みのため、結論には影響しない。

---

## Chapter 06：防御2層の組み合わせ

alice の Token で、一覧の件数と `GET /api/documents/2/` のステータスを測定した。各測定の前に `seed_demo` を実行している（初期状態：alice が1件、bob が1件）。

| # | QuerySet スコープ | Object Permission | 一覧の件数 | `GET /documents/2/` |
|---|---|---|---:|---|
| A | なし | なし | 2 | `200` |
| B | あり | なし | 1 | `404` |
| C | なし | あり | 2 | `403` |
| D | あり | あり | 1 | `404` |

C が要点になる。`has_object_permission` は詳細取得では機能する（`403`）が、一覧では呼ばれないため全件漏洩する。

---

## 実装中に見つかり、修正した問題

### 1. `resource_not_found` が一度も記録されなかった

**症状**：Chapter 10 でログを確認した際、他人のリソースへのアクセス（`404`）が監査ログに現れなかった。

**原因**：例外ハンドラが `rest_framework.exceptions.NotFound` だけを見ていた。DRF の `get_object()` は `get_object_or_404` を経由するため、送出されるのは `django.http.Http404` になる。DRF は `404` レスポンスへ変換するが、ハンドラに渡る `exc` は `Http404` のまま。

**影響**：Chapter 06 の QuerySet スコープによる拒否はすべて `404` のため、**オブジェクト認可による拒否が一切記録されない**状態だった。

**修正**：`isinstance(exc, (NotFound, Http404))` へ変更。

```python
# config/audit.py
elif isinstance(exc, (NotFound, Http404)):
    log_event(logging.WARNING, "resource_not_found", **common)
```

### 2. `INSECURE_MASS_ASSIGNMENT=1` で 500 エラー

**症状**：`AttributeError: 'NoneType' object has no attribute 'get'`

**原因**：`read_only` で生成済みの `PrimaryKeyRelatedField` に対し、`field.read_only = False` を代入して書き込み可能にしていた。read_only のリレーションフィールドは `queryset` を持たないため、入力の解決時に失敗する。

**修正**：フラグ有効時は、`queryset` を持つ新しいフィールドへ差し替える。

```python
# documents/serializers.py
fields["owner"] = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all())
```

### 3. `seed_demo` の再実行で既存 Token が無効になった

**症状**：再シード後、それまでの Token が `401` `{"detail":"User not found","code":"user_not_found"}` を返した。

**原因**：ユーザーを削除して再作成していたため、連番の主キーが 4・5・6 へずれた。JWT の `user_id` は発行時のIDを指すため、解決に失敗する。

**影響**：ドキュメントに `user_id=1` や `/api/documents/2/` を書く前提が崩れる。

**修正**：ユーザーと Document を明示的な主キーで作成し、そのあとシーケンスをリセットする。

```python
for table in ("accounts_user", "documents_document"):
    cursor.execute(
        f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
        f"COALESCE((SELECT MAX(id) FROM {table}), 1))"
    )
```

シーケンスのリセットを省くと、以降の `POST /api/documents/` が主キー重複で失敗する。

### 4. 起動時の `ValueError: Dependency on app with no migrations: accounts`

**症状**：初回起動時、開発サーバーがマイグレーションチェックで停止した。

**原因**：マイグレーションファイルが未生成の状態で `runserver` が起動していた。

**対処**：`makemigrations` → `migrate` のあと `docker compose restart api`。Chapter 00 に注記として記載した。

---

## 再現時の注意点

### ログインの Rate Limit

既定は `5/min`（IP単位）。検証中に Token を取り直す回数が多いと、意図せず `429` に当たる。Chapter 06 Step 3 のように複数回ログインする手順では、`LOGIN_RATE` を一時的に `1000/min` へ上げる。

**戻し忘れると、Chapter 08 と `attack_test.sh` の Rate Limit テストが失敗する**（実際に検証中に発生した）。

### 環境変数の反映

`.env` を変更したあとは `docker compose up -d api` を使う。`docker compose restart api` では環境変数が反映されない（コンテナが作り直されないため）。

### 日本語を含む JSON を curl で送る場合

Windows のシェル経由で日本語を含むリクエストボディを送ると、端末のコードページによっては UTF-8 として送信されず、次のエラーになる。

```json
{"detail":"JSON parse error - 'utf-8' codec can't decode byte 0x82 in position 49: invalid start byte"}
```

このため、ドキュメント中の `curl` で送るボディはすべて ASCII のみで構成している。日本語を送る必要がある場合は、`--data-binary @file.json` でファイルから渡す。

### `normal_test.sh` は Document 1 を削除する

admin の DELETE を検証するため。続けて `attack_test.sh` を実行する前に `seed_demo` を実行する。

### 2本のスクリプトを続けて実行するとログイン回数を共有する

`normal_test.sh` が3回ログインするため、直後に `attack_test.sh` を実行すると Rate Limit の残枠がほとんど無く、1回目から `429` になる。判定は「最初に `429` が出た回数」で行うため PASS するが、`401` → `429` の切り替わりを観察したい場合は1分あけて実行する。
