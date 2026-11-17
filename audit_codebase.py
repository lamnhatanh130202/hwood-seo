import os
import sys
import ast
import py_compile
import traceback

def check_syntax():
    print("=== 1. KIEM TRA CU PHAP (SYNTAX CHECK) ===")
    has_error = False
    for root, dirs, files in os.walk("."):
        if ".git" in root or "__pycache__" in root or ".gemini" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                try:
                    py_compile.compile(path, doraise=True)
                    print(f"  [OK] {path}")
                except Exception as e:
                    print(f"  [SYNTAX ERROR] {path}: {e}")
                    has_error = True
    return not has_error

def find_undefined_names_ast(filepath):
    """Phan tich AST de tim cac bien/ham dung ma khong import hoac khai bao"""
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source, filepath)
    except Exception as e:
        return [f"AST parse error: {e}"]

    builtins = set(dir(__builtins__)) | {
        "__file__", "__name__", "__doc__", "__package__", "True", "False", "None"
    }

    # Collect imports and top-level definitions
    defined = set(builtins)
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                defined.add(alias.asname or alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                defined.add(alias.asname or alias.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    defined.add(target.id)

    # Walk all Name nodes and look for undefined globals
    errors = []
    
    # Simple check for obvious globals used in functions without being imported or defined
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            name = node.id
            if name in ["os", "sys", "time", "json", "re", "random", "requests", "st", "pd", "datetime", "CURRENT_DIR"]:
                if name not in defined:
                    errors.append(f"Line {node.lineno}: Undefined variable '{name}'")

    return list(set(errors))

def check_undefined_variables():
    print("\n=== 2. KIEM TRA BIEN CHUA KHAI BAO HOAC THIEU IMPORT ===")
    has_error = False
    for root, dirs, files in os.walk("."):
        if ".git" in root or "__pycache__" in root or ".gemini" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                errs = find_undefined_names_ast(path)
                if errs:
                    has_error = True
                    print(f"  [THIEU IMPORT/BIEN] {path}:")
                    for err in sorted(errs):
                        print(f"    - {err}")
    if not has_error:
        print("  [OK] Tat ca cac file deu import day du cac thu vien co ban!")
    return not has_error

if __name__ == "__main__":
    s_ok = check_syntax()
    u_ok = check_undefined_variables()
    if s_ok and u_ok:
        print("\n===> KET QUA: TOAN BO FILE PYTHON DEU HOP LE VA CHUAN XAC!")
    else:
        print("\n===> KET QUA: CO LOI CAN FIX!")
