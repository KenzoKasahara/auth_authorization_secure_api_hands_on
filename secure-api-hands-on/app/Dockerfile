FROM python:3.14-slim

# uv は公式イメージからバイナリだけ取り込む。タグを固定して再現性を保つ
COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /uvx /usr/local/bin/

# UV_PROJECT_ENVIRONMENT: compose が ./app を /app にバインドマウントするため、
#   仮想環境は /app の外（/opt/venv）に作らないとマウントで隠れてしまう
# UV_NO_SYNC: 実行時に uv が勝手に再同期しないようにする（依存はビルド時に確定）
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_NO_SYNC=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# 依存だけ先に入れてレイヤキャッシュを効かせる。--locked で uv.lock との差異を検出する
COPY pyproject.toml uv.lock /app/
RUN uv sync --locked --no-dev

COPY . /app

EXPOSE 8000
