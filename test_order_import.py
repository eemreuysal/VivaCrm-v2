#!/usr/bin/env python
"""
Order import test
"""
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import pandas as pd
from orders.excel_validators import OrderExcelValidator

# Test data oluştur
test_data = {
    'customer_email': ['test@example.com', 'test2@example.com'],
    'product_sku': ['TEST-001', 'TEST-002'],
    'quantity': [1, 2]
}

# DataFrame oluştur
df = pd.DataFrame(test_data)

# Validator'ı test et
validator = OrderExcelValidator()

# File validation
print("File validation:")
result = validator.validate_file(df)
print(f"Result: {result}")
print(f"Has errors: {validator.error_collector.has_errors()}")
if validator.error_collector.has_errors():
    print("Errors:")
    print(validator.error_collector.to_list())

# Row validation
print("\nRow validation:")
for index, row in df.iterrows():
    print(f"\nRow {index}:")
    result = validator.validate_row(row.to_dict(), index)
    print(f"Result: {result}")

print(f"\nFinal has_errors: {validator.has_errors()}")
if validator.error_collector.has_errors():
    print("All errors:")
    print(validator.error_collector.to_list())