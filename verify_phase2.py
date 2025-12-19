"""Verification script for Phase 2 implementation.

This script verifies that all Phase 2 modules are properly implemented
without requiring runtime execution (syntax and structure checks only).
"""

import ast
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())


def check_file_syntax(filepath: Path) -> tuple[bool, str]:
    """Check if a Python file has valid syntax."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        return True, "OK"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def check_module_structure(filepath: Path, expected_classes: list[str]) -> tuple[bool, str]:
    """Check if a module contains expected classes."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())

        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

        missing = set(expected_classes) - set(classes)
        if missing:
            return False, f"Missing classes: {missing}"

        return True, f"Found classes: {', '.join(expected_classes)}"

    except Exception as e:
        return False, f"Error: {e}"


def main():
    """Run verification checks."""
    print("=" * 70)
    print("PHASE 2 IMPLEMENTATION VERIFICATION")
    print("=" * 70)

    base_dir = Path(__file__).parent
    src_dir = base_dir / "src" / "reelsbot"

    # Define checks
    checks = [
        {
            "name": "models.py",
            "path": src_dir / "models.py",
            "classes": ["ReelPlan", "ReelMetadata"],
        },
        {
            "name": "planner.py",
            "path": src_dir / "planner.py",
            "classes": ["Planner", "PlannerError"],
        },
        {
            "name": "policy_gate.py",
            "path": src_dir / "policy_gate.py",
            "classes": ["PolicyGate", "PolicyViolationError"],
        },
        {
            "name": "caption_generator.py",
            "path": src_dir / "caption_generator.py",
            "classes": ["CaptionGenerator", "CaptionGeneratorError"],
        },
        {
            "name": "storage/runs.py",
            "path": src_dir / "storage" / "runs.py",
            "classes": ["RunStorage", "RunStorageError"],
        },
        {
            "name": "publisher/base.py",
            "path": src_dir / "publisher" / "base.py",
            "classes": ["BasePublisher", "PublisherError"],
        },
        {
            "name": "publisher/dry_run.py",
            "path": src_dir / "publisher" / "dry_run.py",
            "classes": ["DryRunPublisher"],
        },
    ]

    all_passed = True

    print("\n1. SYNTAX CHECKS")
    print("-" * 70)

    for check in checks:
        filepath = check["path"]
        is_valid, message = check_file_syntax(filepath)

        status = "✓" if is_valid else "✗"
        print(f"{status} {check['name']}: {message}")

        if not is_valid:
            all_passed = False

    print("\n2. STRUCTURE CHECKS")
    print("-" * 70)

    for check in checks:
        filepath = check["path"]
        is_valid, message = check_module_structure(filepath, check["classes"])

        status = "✓" if is_valid else "✗"
        print(f"{status} {check['name']}: {message}")

        if not is_valid:
            all_passed = False

    print("\n3. FILE SIZE CHECKS")
    print("-" * 70)

    total_lines = 0
    for check in checks:
        filepath = check["path"]
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
                total_lines += lines
                print(f"  {check['name']}: {lines} lines")

    print(f"\nTotal Phase 2 code: {total_lines} lines")

    print("\n4. DEPENDENCY CHECKS")
    print("-" * 70)

    # Check __init__.py exports
    init_file = src_dir / "__init__.py"
    if init_file.exists():
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()

        expected_exports = [
            "ReelPlan", "ReelMetadata",
            "Planner", "PlannerError",
            "PolicyGate", "PolicyViolationError",
            "CaptionGenerator", "CaptionGeneratorError",
            "RunStorage", "RunStorageError",
            "BasePublisher", "PublisherError", "DryRunPublisher",
        ]

        for export in expected_exports:
            if export in content:
                print(f"  ✓ {export} exported")
            else:
                print(f"  ✗ {export} NOT exported")
                all_passed = False
    else:
        print("  ✗ __init__.py not found")
        all_passed = False

    print("\n5. PROMPT/POLICY FILES")
    print("-" * 70)

    required_files = [
        ("prompts/planner_system.txt", "Planner system prompt"),
        ("prompts/policy_system.txt", "Policy system prompt"),
        ("prompts/caption_en.txt", "Caption template"),
        ("policies/blocked_terms.txt", "Blocked terms list"),
    ]

    for filepath, description in required_files:
        full_path = base_dir / filepath
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  ✓ {description}: {size} bytes")
        else:
            print(f"  ✗ {description}: NOT FOUND")
            all_passed = False

    # Summary
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL VERIFICATION CHECKS PASSED")
        print("=" * 70)
        print("\nPhase 2 implementation is complete and ready:")
        print("  - All modules have valid syntax")
        print("  - All expected classes are present")
        print("  - All exports are configured")
        print("  - All required files exist")
        print("\nNext: Run test_phase2.py with Python 3.11+ to test functionality")
        return 0
    else:
        print("✗ SOME CHECKS FAILED")
        print("=" * 70)
        print("\nPlease review the failed checks above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
