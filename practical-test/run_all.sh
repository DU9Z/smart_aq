#!/usr/bin/env bash
set -e
for d in q11_tasks_api q15_form q26_registration q27_discount q28_orders q29_auth_regression; do
  echo "== $d"; (cd "$d" && python3 -m unittest 2>&1 | tail -3)
done
