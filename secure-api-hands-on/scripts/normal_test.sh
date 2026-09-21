#!/usr/bin/env bash
# 正常系：想定どおりの操作が想定どおりに通ることを確認する
cd "$(dirname "$0")" && . ./lib.sh

echo "=== 正常系テスト (API=${API}) ==="

ALICE="$(login alice)"
ROOT="$(login root)"
if [ -z "$ALICE" ] || [ -z "$ROOT" ]; then
  echo "  ログインに失敗しました。Rate Limit（既定 5/min）に達している可能性があります。" >&2
  exit 1
fi

expect "ログイン成功"                 "200" "$(status_of -X POST "${API}/api/auth/token/" -H 'Content-Type: application/json' -d "{\"username\":\"alice\",\"password\":\"${PASSWORD}\"}")"
expect "自分の識別情報を取得"         "200" "$(status_of "${API}/api/auth/me/" -H "Authorization: Bearer ${ALICE}")"
expect "自分の Document 一覧"         "200" "$(status_of "${API}/api/documents/" -H "Authorization: Bearer ${ALICE}")"
expect "自分の Document 取得"         "200" "$(status_of "${API}/api/documents/1/" -H "Authorization: Bearer ${ALICE}")"
expect "Document 作成"                "201" "$(status_of -X POST "${API}/api/documents/" -H "Authorization: Bearer ${ALICE}" -H 'Content-Type: application/json' -d '{"title":"normal test","content":"created by normal_test.sh"}')"
expect "admin による DELETE"          "204" "$(status_of -X DELETE "${API}/api/documents/1/" -H "Authorization: Bearer ${ROOT}")"

summary
