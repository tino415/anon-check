#!/usr/bin/env bash
set -uo pipefail

root=$(dirname "$(dirname "$(readlink -f "$0")")")
wrapper=$root/bin/anon-check
sample='Ján Novák, r. č. 850101/1233, IBAN SK31 1200 0000 1987 4263 7541'
failures=0

expect() {
  local name=$1
  shift
  if "$@"; then
    echo "ok: $name"
  else
    echo "FAILED: $name"
    failures=$((failures + 1))
  fi
}

stderr=$(ANON_CHECK_IMAGE=localhost/anon-check-missing "$wrapper" </dev/null 2>&1 >/dev/null)
status=$?
expect "a missing image exits 2" [ "$status" -eq 2 ]
expect "a missing image names anon-check-build" grep -q anon-check-build <<<"$stderr"

stdout=$(ANON_CHECK_IMAGE=localhost/anon-check-rules "$wrapper" <<<"$sample")
status=$?
expect "the sample through the wrapper exits 1" [ "$status" -eq 1 ]
expect "the wrapper prints the rule findings" [ "$stdout" = $'1:18 11 RODNE_CISLO 1.00\n1:36 29 IBAN 1.00' ]

ANON_CHECK_IMAGE=localhost/anon-check-rules "$wrapper" --no-such-flag </dev/null 2>/dev/null
expect "an unknown flag exits 2" [ $? -eq 2 ]

((failures == 0))
