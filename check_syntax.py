#!/usr/bin/env python
import ast

try:
    with open('orders/views.py', 'r') as f:
        code = f.read()
    
    ast.parse(code)
    print("No syntax errors found")
    
except SyntaxError as e:
    print(f"SyntaxError at line {e.lineno}")
    print(f"Message: {e.msg}")
    print(f"Text: {repr(e.text)}")
    print(f"Offset: {e.offset}")
    
    # Show context
    with open('orders/views.py', 'r') as f:
        lines = f.readlines()
    
    print("\nContext:")
    for i in range(max(0, e.lineno - 5), min(len(lines), e.lineno + 5)):
        marker = ">>>" if i + 1 == e.lineno else "   "
        print(f"{marker} {i+1:4d}: {lines[i].rstrip()}")