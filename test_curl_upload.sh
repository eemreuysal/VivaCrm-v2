#!/bin/bash

# Get CSRF token from the form page
CSRF_TOKEN=$(curl -s http://127.0.0.1:8000/orders/import/ | grep -oP 'name="csrfmiddlewaretoken" value="\K[^"]+')

echo "CSRF Token: $CSRF_TOKEN"

# Upload the file
curl -X POST http://127.0.0.1:8000/orders/import/ \
  -H "X-Requested-With: XMLHttpRequest" \
  -F "csrfmiddlewaretoken=$CSRF_TOKEN" \
  -F "excel_file=@test_excel_file.xlsx" \
  -F "update_existing=off" \
  -c cookies.txt \
  -b cookies.txt \
  -v