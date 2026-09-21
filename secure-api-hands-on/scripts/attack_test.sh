#!/usr/bin/env bash
# 異常系：境界を破ろうとする操作が、想定どおり拒否されることを確認する
cd "$(dirname "$0")" && . ./lib.sh

echo "=== 異常系テスト (API=${API}) ==="

ALICE="$(login alice)"
if [ -z "$ALICE" ]; then
  echo "  ログインに失敗しました。Rate Limit（既定 5/min）に達している可能性があります。" >&2
  exit 1
fi

echo
echo "--- 認証境界 ---"
expect "Token なし"                   "401" "$(status_of "${API}/api/documents/")"
expect "Token 改ざん"                 "401" "$(status_of "${API}/api/documents/" -H "Authorization: Bearer ${ALICE}tampered")"
expect "Bearer プレフィックスなし"    "401" "$(status_of "${API}/api/documents/" -H "Authorization: ${ALICE}")"
expect "パスワード誤り"               "401" "$(status_of -X POST "${API}/api/auth/token/" -H 'Content-Type: application/json' -d '{"username":"alice","password":"wrong-password"}')"

echo
echo "--- 認可境界（API Permission / RBAC） ---"
expect "role=user による DELETE"      "403" "$(status_of -X DELETE "${API}/api/documents/1/" -H "Authorization: Bearer ${ALICE}")"

echo
echo "--- 認可境界（Object-Level） ---"
expect "他人の Document を GET"       "403|404" "$(status_of "${API}/api/documents/2/" -H "Authorization: Bearer ${ALICE}")"
expect "他人の Document を PATCH"     "403|404" "$(status_of -X PATCH "${API}/api/documents/2/" -H "Authorization: Bearer ${ALICE}" -H 'Content-Type: application/json' -d '{"title":"hijacked"}')"

echo
echo "--- 入力の信頼（Mass Assignment） ---"
FORGED="$(curl -s -X POST "${API}/api/documents/" \
  -H "Authorization: Bearer ${ALICE}" -H 'Content-Type: application/json' \
  -d '{"title":"forged owner","content":"attempt","owner":2}' |
  python -c "import sys,json;print(json.load(sys.stdin).get('owner',''))" 2>/dev/null)"
expect "owner 指定が無視される (owner=1)" "1" "${FORGED}"

echo
echo "--- Rate Limit ---"
FIRST_429=""
for i in $(seq 1 12); do
  code="$(status_of -X POST "${API}/api/auth/token/" -H 'Content-Type: application/json' -d '{"username":"alice","password":"wrong-password"}')"
  printf '  attempt %-2s -> %s\n' "$i" "$code"
  if [ "$code" = "429" ] && [ -z "$FIRST_429" ]; then FIRST_429="$i"; fi
done
expect "連続ログインが 429 で遮断される" "[0-9]+" "${FIRST_429:-none}"

summary
