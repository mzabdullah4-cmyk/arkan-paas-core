#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${ARKAN_BASE_URL:-http://localhost:8080}"
API="${BASE_URL%/}/api"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

json_value() {
  python3 -c 'import json,sys; print(json.load(sys.stdin)[sys.argv[1]])' "$1"
}

curl_json() {
  curl --fail-with-body --silent --show-error --retry 5 --retry-delay 2 "$@"
}

curl_json "$BASE_URL/" >/dev/null
health="$(curl_json "$API/health")"
test "$(printf '%s' "$health" | json_value status)" = ok

project="$(curl_json -X POST "$API/projects" -H 'Content-Type: application/json' -d '{"name":"SQL smoke test","description":"temporary end-to-end test"}')"
project_id="$(printf '%s' "$project" | json_value id)"

printf 'SELECT customer_id FROM customers WHERE active = 1;\n' > "$TMP_DIR/sample.sql"
artifact="$(curl_json -X POST "$API/projects/$project_id/artifacts/upload?language=sql" -F "file=@$TMP_DIR/sample.sql;filename=sample.sql")"
artifact_id="$(printf '%s' "$artifact" | json_value id)"

job="$(curl_json -X POST "$API/jobs" -H 'Content-Type: application/json' -d "{\"project_id\":\"$project_id\",\"artifact_id\":\"$artifact_id\",\"engine\":\"sqlglot\"}")"
job_id="$(printf '%s' "$job" | json_value id)"

for _ in $(seq 1 30); do
  current="$(curl_json "$API/jobs/$job_id")"
  state="$(printf '%s' "$current" | json_value status)"
  if [ "$state" = completed ]; then
    printf '%s' "$current" | python3 -c 'import json,sys; r=json.load(sys.stdin)["result"]; assert r["engine"] == "sqlglot"; assert r["schema_version"] == "1.0"'
    echo "SQL vertical slice passed."
    exit 0
  fi
  if [ "$state" = failed ]; then
    echo "$current" >&2
    exit 1
  fi
  sleep 2
done

echo "Timed out waiting for job $job_id" >&2
exit 1
