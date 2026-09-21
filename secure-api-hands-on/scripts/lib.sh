#!/usr/bin/env bash
# 各テストスクリプトの共通処理
set -uo pipefail

API="${API:-http://localhost:8000}"
PASSWORD="${PASSWORD:-Handson-Passw0rd!}"

PASS=0
FAIL=0

login() {
  # $1: username -> access token を stdout へ
  curl -s -X POST "${API}/api/auth/token/" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$1\",\"password\":\"${PASSWORD}\"}" |
    python -c "import sys,json;print(json.load(sys.stdin).get('access',''))" 2>/dev/null
}

status_of() {
  # $@: curl の引数 -> HTTP ステータスコードを stdout へ
  curl -s -o /dev/null -w "%{http_code}" "$@"
}

expect() {
  # $1: ラベル / $2: 期待するステータス（| 区切りで複数可） / $3: 実際のステータス
  local label="$1" want="$2" got="$3"
  if echo "$got" | grep -qE "^(${want})$"; then
    printf '  [PASS] %-44s expected=%-9s actual=%s\n' "$label" "$want" "$got"
    PASS=$((PASS + 1))
  else
    printf '  [FAIL] %-44s expected=%-9s actual=%s\n' "$label" "$want" "$got"
    FAIL=$((FAIL + 1))
  fi
}

summary() {
  echo
  echo "--------------------------------------------------"
  echo "  PASS=${PASS}  FAIL=${FAIL}"
  echo "--------------------------------------------------"
  [ "$FAIL" -eq 0 ]
}
