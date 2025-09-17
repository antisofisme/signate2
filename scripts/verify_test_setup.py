#!/usr/bin/env python3
"""
Verification script for testing infrastructure setup.

This script validates that all testing components are properly configured
and can be used for running the Signate SaaS test suite.
"""

import os
import sys
import importlib.util
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and report status."""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NOT FOUND")
        return False

def check_directory_structure():
    """Verify testing directory structure."""
    print("\n🔍 Checking directory structure...")

    base_path = Path(__file__).parent.parent

    required_dirs = [
        "tests",
        "tests/utils",
        ".github/workflows",
        "docs/testing"
    ]

    all_dirs_exist = True
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists():
            print(f"✅ Directory: {dir_path}")
        else:
            print(f"❌ Directory: {dir_path} - NOT FOUND")
            all_dirs_exist = False

    return all_dirs_exist

def check_test_files():
    """Verify test files exist."""
    print("\n🔍 Checking test files...")

    base_path = Path(__file__).parent.parent

    test_files = [
        "pytest.ini",
        "tests/conftest.py",
        "tests/test_models.py",
        "tests/test_api.py",
        "tests/utils/tenant_test_utils.py",
        ".github/workflows/test.yml",
        "docs/testing/strategy.md",
        "docs/testing/multi-tenant-testing.md"
    ]

    all_files_exist = True
    for file_path in test_files:
        full_path = base_path / file_path
        if check_file_exists(str(full_path), f"Test file: {file_path}"):
            # Check file size to ensure it's not empty
            if full_path.stat().st_size > 0:
                print(f"   📄 Size: {full_path.stat().st_size} bytes")
            else:
                print(f"   ⚠️ File is empty")
        else:
            all_files_exist = False

    return all_files_exist

def check_pytest_config():
    """Verify pytest configuration."""
    print("\n🔍 Checking pytest configuration...")

    base_path = Path(__file__).parent.parent
    pytest_ini = base_path / "pytest.ini"

    if not pytest_ini.exists():
        print("❌ pytest.ini not found")
        return False

    try:
        with open(pytest_ini, 'r') as f:
            content = f.read()

        required_sections = [
            "[tool:pytest]",
            "testpaths",
            "addopts",
            "markers",
            "coverage"
        ]

        for section in required_sections:
            if section in content:
                print(f"✅ Configuration section: {section}")
            else:
                print(f"❌ Configuration section missing: {section}")
                return False

        return True

    except Exception as e:
        print(f"❌ Error reading pytest.ini: {e}")
        return False

def check_test_markers():
    """Verify test markers are properly defined."""
    print("\n🔍 Checking test markers...")

    base_path = Path(__file__).parent.parent

    test_files = [
        base_path / "tests/test_models.py",
        base_path / "tests/test_api.py"
    ]

    expected_markers = [
        "@pytest.mark.unit",
        "@pytest.mark.integration",
        "@pytest.mark.api",
        "@pytest.mark.tenant",
        "@pytest.mark.security",
        "@pytest.mark.performance"
    ]

    markers_found = set()

    for test_file in test_files:
        if test_file.exists():
            try:
                with open(test_file, 'r') as f:
                    content = f.read()

                for marker in expected_markers:
                    if marker in content:
                        markers_found.add(marker)

            except Exception as e:
                print(f"❌ Error reading {test_file}: {e}")

    for marker in expected_markers:
        if marker in markers_found:
            print(f"✅ Test marker found: {marker}")
        else:
            print(f"⚠️ Test marker not found: {marker}")

    return len(markers_found) >= len(expected_markers) * 0.8  # 80% coverage

def check_fixtures():
    """Verify pytest fixtures are defined."""
    print("\n🔍 Checking pytest fixtures...")

    base_path = Path(__file__).parent.parent
    conftest_file = base_path / "tests/conftest.py"

    if not conftest_file.exists():
        print("❌ conftest.py not found")
        return False

    try:
        with open(conftest_file, 'r') as f:
            content = f.read()

        expected_fixtures = [
            "@pytest.fixture",
            "django_db_setup",
            "tenant_context",
            "api_client",
            "asset_factory",
            "performance_monitor",
            "security_scanner"
        ]

        fixtures_found = 0
        for fixture in expected_fixtures:
            if fixture in content:
                print(f"✅ Fixture found: {fixture}")
                fixtures_found += 1
            else:
                print(f"⚠️ Fixture not found: {fixture}")

        return fixtures_found >= len(expected_fixtures) * 0.8  # 80% coverage

    except Exception as e:
        print(f"❌ Error reading conftest.py: {e}")
        return False

def check_ci_pipeline():
    """Verify CI/CD pipeline configuration."""
    print("\n🔍 Checking CI/CD pipeline...")

    base_path = Path(__file__).parent.parent
    workflow_file = base_path / ".github/workflows/test.yml"

    if not workflow_file.exists():
        print("❌ test.yml workflow not found")
        return False

    try:
        with open(workflow_file, 'r') as f:
            content = f.read()

        required_jobs = [
            "pre-flight",
            "code-quality",
            "unit-tests",
            "integration-tests",
            "api-tests",
            "multi-tenant-tests",
            "security-tests"
        ]

        jobs_found = 0
        for job in required_jobs:
            if job in content:
                print(f"✅ CI job found: {job}")
                jobs_found += 1
            else:
                print(f"⚠️ CI job not found: {job}")

        return jobs_found >= len(required_jobs) * 0.8  # 80% coverage

    except Exception as e:
        print(f"❌ Error reading test.yml: {e}")
        return False

def check_documentation():
    """Verify testing documentation."""
    print("\n🔍 Checking documentation...")

    base_path = Path(__file__).parent.parent

    doc_files = [
        base_path / "docs/testing/strategy.md",
        base_path / "docs/testing/multi-tenant-testing.md"
    ]

    all_docs_exist = True
    for doc_file in doc_files:
        if doc_file.exists():
            size = doc_file.stat().st_size
            print(f"✅ Documentation: {doc_file.name} ({size} bytes)")
            if size < 1000:  # Less than 1KB might be too small
                print(f"   ⚠️ File might be incomplete (< 1KB)")
        else:
            print(f"❌ Documentation missing: {doc_file.name}")
            all_docs_exist = False

    return all_docs_exist

def main():
    """Run all verification checks."""
    print("🧪 Signate SaaS Testing Infrastructure Verification")
    print("=" * 55)

    checks = [
        ("Directory Structure", check_directory_structure),
        ("Test Files", check_test_files),
        ("Pytest Configuration", check_pytest_config),
        ("Test Markers", check_test_markers),
        ("Pytest Fixtures", check_fixtures),
        ("CI/CD Pipeline", check_ci_pipeline),
        ("Documentation", check_documentation)
    ]

    results = []

    for check_name, check_func in checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Error during {check_name}: {e}")
            results.append((check_name, False))

    # Summary
    print("\n" + "="*55)
    print("🏁 VERIFICATION SUMMARY")
    print("="*55)

    passed = 0
    total = len(results)

    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
        if result:
            passed += 1

    print(f"\n📊 Results: {passed}/{total} checks passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 All checks passed! Testing infrastructure is ready.")
        return 0
    elif passed >= total * 0.8:
        print("\n⚠️  Most checks passed. Minor issues may need attention.")
        return 0
    else:
        print("\n❌ Significant issues detected. Please review and fix.")
        return 1

if __name__ == "__main__":
    sys.exit(main())