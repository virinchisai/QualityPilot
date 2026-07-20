#!/usr/bin/env python3
"""Fail when Behave step expressions are duplicated."""

import ast
import sys
from collections import defaultdict
from pathlib import Path

expressions = defaultdict(list)
for path in Path("tests/bdd/steps").glob("*.py"):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Name)
                    and decorator.func.id in {"given", "when", "then", "step"}
                    and decorator.args
                    and isinstance(decorator.args[0], ast.Constant)
                ):
                    expressions[decorator.args[0].value].append(f"{path}:{node.lineno}")
duplicates = {key: value for key, value in expressions.items() if len(value) > 1}
if duplicates:
    print(duplicates)
    sys.exit(1)
print(f"No duplicate steps across {len(expressions)} expressions")
