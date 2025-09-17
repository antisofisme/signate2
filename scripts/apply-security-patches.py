#!/usr/bin/env python3
"""
Security Patches Implementation Script
Apply critical security patches identified in Phase 1 analysis during migration
"""

import os
import sys
import subprocess
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/security_patches.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SecurityPatch:
    """Security patch definition"""
    name: str
    description: str
    cve_ids: List[str]
    package: str
    current_version: str
    target_version: str
    priority: str  # critical, high, medium, low
    commands: List[str]
    verification_commands: List[str]

@dataclass
class PatchResult:
    """Security patch application result"""
    patch_name: str
    success: bool
    applied: bool
    error_message: str = ''
    duration: float = 0.0
    verification_passed: bool = False

class SecurityPatcher:
    """Security patches management and application"""

    def __init__(self):
        self.patches = self._load_security_patches()
        self.patch_session_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    def _load_security_patches(self) -> List[SecurityPatch]:
        """Load security patches from Phase 1 analysis"""
        patches = [
            SecurityPatch(
                name="cryptography_update",
                description="Update cryptography package to fix CVE-2023-* vulnerabilities",
                cve_ids=["CVE-2023-23931", "CVE-2023-49083"],
                package="cryptography",
                current_version="3.4.8",
                target_version=">=41.0.4",
                priority="critical",
                commands=[
                    "pip install --upgrade 'cryptography>=41.0.4'",
                    "pip install --upgrade 'pyOpenSSL>=23.2.0'"
                ],
                verification_commands=[
                    "python -c 'import cryptography; print(cryptography.__version__)'",
                    "python -c 'import OpenSSL; print(OpenSSL.__version__)'"
                ]
            ),
            SecurityPatch(
                name="pyopenssl_update",
                description="Update pyOpenSSL to address dependency vulnerabilities",
                cve_ids=["CVE-2023-0286", "CVE-2023-0215"],
                package="pyOpenSSL",
                current_version="20.0.1",
                target_version=">=23.2.0",
                priority="high",
                commands=[
                    "pip install --upgrade 'pyOpenSSL>=23.2.0'"
                ],
                verification_commands=[
                    "python -c 'import OpenSSL; print(OpenSSL.__version__)'"
                ]
            ),
            SecurityPatch(
                name="redis_connection_security",
                description="Update Redis connection configuration to fix vulnerability",
                cve_ids=["CVE-2023-28425"],
                package="redis",
                current_version="3.5.3",
                target_version=">=4.5.5",
                priority="high",
                commands=[
                    "pip install --upgrade 'redis>=4.5.5'",
                    "pip install --upgrade 'redis-py-cluster>=2.1.3'"
                ],
                verification_commands=[
                    "python -c 'import redis; print(redis.__version__)'"
                ]
            ),
            SecurityPatch(
                name="django_security_updates",
                description="Update Django and related security middleware",
                cve_ids=["CVE-2023-31047", "CVE-2023-36053"],
                package="django",
                current_version="3.2.18",
                target_version=">=3.2.20",
                priority="high",
                commands=[
                    "pip install --upgrade 'Django>=3.2.20,<4.0'",
                    "pip install --upgrade 'django-cors-headers>=4.2.0'",
                    "pip install --upgrade 'djangorestframework>=3.14.0'"
                ],
                verification_commands=[
                    "python -c 'import django; print(django.VERSION)'",
                    "python manage.py check --deploy"
                ]
            ),
            SecurityPatch(
                name="pillow_security_update",
                description="Update Pillow to fix image processing vulnerabilities",
                cve_ids=["CVE-2023-44271", "CVE-2023-50447"],
                package="Pillow",
                current_version="8.3.2",
                target_version=">=10.0.1",
                priority="medium",
                commands=[
                    "pip install --upgrade 'Pillow>=10.0.1'"
                ],
                verification_commands=[
                    "python -c 'from PIL import Image; print(Image.__version__)'"
                ]
            ),
            SecurityPatch(
                name="requests_security_update",
                description="Update requests and urllib3 for security fixes",
                cve_ids=["CVE-2023-32681", "CVE-2023-43804"],
                package="requests",
                current_version="2.25.1",
                target_version=">=2.31.0",
                priority="medium",
                commands=[
                    "pip install --upgrade 'requests>=2.31.0'",
                    "pip install --upgrade 'urllib3>=1.26.17'"
                ],
                verification_commands=[
                    "python -c 'import requests; print(requests.__version__)'",
                    "python -c 'import urllib3; print(urllib3.__version__)'"
                ]
            )
        ]

        return patches

    def check_current_versions(self) -> Dict[str, str]:
        """Check current versions of packages to be patched"""
        logger.info("Checking current package versions...")

        current_versions = {}
        packages = [patch.package.lower() for patch in self.patches]

        try:
            # Get installed packages
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                check=True
            )

            installed_packages = json.loads(result.stdout)
            package_dict = {pkg['name'].lower(): pkg['version'] for pkg in installed_packages}

            for package in packages:
                current_versions[package] = package_dict.get(package, "Not installed")

            logger.info(f"Current versions: {current_versions}")
            return current_versions

        except Exception as e:
            logger.error(f"Failed to check current versions: {e}")
            return {}

    def create_backup_requirements(self) -> bool:
        """Create backup of current requirements before patching"""
        logger.info("Creating backup of current requirements...")

        try:
            # Create backup directory
            backup_dir = f"/tmp/security_patch_backup_{self.patch_session_id}"
            os.makedirs(backup_dir, exist_ok=True)

            # Backup current requirements
            result = subprocess.run(
                ["pip", "freeze"],
                capture_output=True,
                text=True,
                check=True
            )

            backup_file = os.path.join(backup_dir, "requirements_backup.txt")
            with open(backup_file, 'w') as f:
                f.write(result.stdout)

            logger.info(f"Requirements backed up to: {backup_file}")

            # Also backup current Django settings if available
            settings_paths = [
                "/mnt/g/khoirul/signate2/project/backend/anthias_django/settings.py",
                "/app/anthias_django/settings.py"
            ]

            for settings_path in settings_paths:
                if os.path.exists(settings_path):
                    backup_settings = os.path.join(backup_dir, "settings_backup.py")
                    subprocess.run(["cp", settings_path, backup_settings])
                    logger.info(f"Settings backed up to: {backup_settings}")
                    break

            return True

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False

    def apply_patch(self, patch: SecurityPatch) -> PatchResult:
        """Apply a single security patch"""
        logger.info(f"Applying patch: {patch.name}")

        start_time = datetime.now()
        result = PatchResult(
            patch_name=patch.name,
            success=False,
            applied=False
        )

        try:
            # Apply patch commands
            for command in patch.commands:
                logger.info(f"Executing: {command}")

                process = subprocess.run(
                    command.split(),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )

                if process.returncode != 0:
                    result.error_message = f"Command failed: {command}\nError: {process.stderr}"
                    logger.error(result.error_message)
                    return result

                logger.info(f"Command completed successfully: {command}")

            result.applied = True

            # Run verification commands
            verification_passed = True
            for verify_command in patch.verification_commands:
                logger.info(f"Verifying: {verify_command}")

                try:
                    process = subprocess.run(
                        verify_command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if process.returncode != 0:
                        verification_passed = False
                        logger.warning(f"Verification failed: {verify_command}")
                    else:
                        logger.info(f"Verification passed: {process.stdout.strip()}")

                except Exception as e:
                    verification_passed = False
                    logger.warning(f"Verification error: {e}")

            result.verification_passed = verification_passed
            result.success = True

            duration = (datetime.now() - start_time).total_seconds()
            result.duration = duration

            logger.info(f"Patch {patch.name} applied successfully in {duration:.2f}s")
            return result

        except subprocess.TimeoutExpired:
            result.error_message = f"Patch {patch.name} timed out"
            logger.error(result.error_message)
            return result

        except Exception as e:
            result.error_message = f"Patch {patch.name} failed: {e}"
            logger.error(result.error_message)
            return result

    def apply_all_patches(self, priority_filter: Optional[str] = None) -> List[PatchResult]:
        """Apply all security patches"""
        logger.info("Starting security patches application...")

        # Filter patches by priority if specified
        patches_to_apply = self.patches
        if priority_filter:
            patches_to_apply = [p for p in self.patches if p.priority == priority_filter]

        # Sort by priority (critical first)
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        patches_to_apply.sort(key=lambda p: priority_order.get(p.priority, 4))

        results = []

        for patch in patches_to_apply:
            logger.info(f"Processing patch: {patch.name} (Priority: {patch.priority})")

            # Log CVE information
            if patch.cve_ids:
                logger.info(f"Addresses CVEs: {', '.join(patch.cve_ids)}")

            result = self.apply_patch(patch)
            results.append(result)

            if not result.success and patch.priority == "critical":
                logger.error(f"Critical patch {patch.name} failed! Stopping patch application.")
                break

        return results

    def generate_patch_report(self, results: List[PatchResult]) -> str:
        """Generate detailed patch application report"""
        report_path = f"/tmp/security_patch_report_{self.patch_session_id}.json"

        report_data = {
            "patch_session_id": self.patch_session_id,
            "timestamp": datetime.now().isoformat(),
            "total_patches": len(results),
            "successful_patches": sum(1 for r in results if r.success),
            "failed_patches": sum(1 for r in results if not r.success),
            "patches_applied": sum(1 for r in results if r.applied),
            "verification_passed": sum(1 for r in results if r.verification_passed),
            "results": [asdict(result) for result in results],
            "recommendations": self._generate_recommendations(results)
        }

        try:
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)

            logger.info(f"Patch report saved: {report_path}")
            return report_path

        except Exception as e:
            logger.error(f"Failed to save patch report: {e}")
            return ""

    def _generate_recommendations(self, results: List[PatchResult]) -> List[str]:
        """Generate recommendations based on patch results"""
        recommendations = []

        failed_patches = [r for r in results if not r.success]
        if failed_patches:
            recommendations.append("Review and manually apply failed patches")
            recommendations.append("Check dependency conflicts that may have caused failures")

        verification_failed = [r for r in results if r.applied and not r.verification_passed]
        if verification_failed:
            recommendations.append("Manual verification required for patches with failed checks")

        critical_failed = [r for r in results if not r.success and any(p.priority == "critical" for p in self.patches if p.name == r.patch_name)]
        if critical_failed:
            recommendations.append("URGENT: Critical security patches failed - immediate manual intervention required")

        if all(r.success for r in results):
            recommendations.append("All patches applied successfully - restart application services")
            recommendations.append("Run comprehensive security scan to verify patch effectiveness")

        return recommendations

    def rollback_patches(self, backup_session_id: str) -> bool:
        """Rollback patches using backup requirements"""
        logger.info(f"Rolling back patches from session: {backup_session_id}")

        try:
            backup_dir = f"/tmp/security_patch_backup_{backup_session_id}"
            backup_file = os.path.join(backup_dir, "requirements_backup.txt")

            if not os.path.exists(backup_file):
                logger.error(f"Backup file not found: {backup_file}")
                return False

            # Reinstall from backup requirements
            result = subprocess.run(
                ["pip", "install", "-r", backup_file, "--force-reinstall"],
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode != 0:
                logger.error(f"Rollback failed: {result.stderr}")
                return False

            logger.info("Patches rolled back successfully")
            return True

        except Exception as e:
            logger.error(f"Rollback error: {e}")
            return False

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Security Patches Application Tool')
    parser.add_argument('--priority', choices=['critical', 'high', 'medium', 'low'],
                       help='Apply only patches with specified priority')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be patched without applying')
    parser.add_argument('--check-versions', action='store_true',
                       help='Check current package versions only')
    parser.add_argument('--rollback', help='Rollback patches using backup session ID')
    parser.add_argument('--list-patches', action='store_true',
                       help='List all available patches')

    args = parser.parse_args()

    patcher = SecurityPatcher()

    if args.list_patches:
        print("\nAvailable Security Patches:")
        print("=" * 50)
        for patch in patcher.patches:
            print(f"Name: {patch.name}")
            print(f"Priority: {patch.priority}")
            print(f"Package: {patch.package}")
            print(f"CVEs: {', '.join(patch.cve_ids)}")
            print(f"Description: {patch.description}")
            print("-" * 30)
        sys.exit(0)

    if args.check_versions:
        current_versions = patcher.check_current_versions()
        print("\nCurrent Package Versions:")
        print("=" * 30)
        for package, version in current_versions.items():
            print(f"{package}: {version}")
        sys.exit(0)

    if args.rollback:
        success = patcher.rollback_patches(args.rollback)
        sys.exit(0 if success else 1)

    if args.dry_run:
        print("\nDRY RUN: Security patches that would be applied:")
        print("=" * 50)
        patches_to_apply = patcher.patches
        if args.priority:
            patches_to_apply = [p for p in patcher.patches if p.priority == args.priority]

        for patch in patches_to_apply:
            print(f"✓ {patch.name} ({patch.priority} priority)")
            print(f"  Package: {patch.package}")
            print(f"  CVEs: {', '.join(patch.cve_ids)}")
            print(f"  Commands: {len(patch.commands)} command(s)")
            print()
        sys.exit(0)

    # Apply patches
    logger.info("Starting security patches application...")

    # Create backup
    if not patcher.create_backup_requirements():
        logger.error("Failed to create backup - aborting patch application")
        sys.exit(1)

    # Check current versions
    current_versions = patcher.check_current_versions()

    # Apply patches
    results = patcher.apply_all_patches(args.priority)

    # Generate report
    report_path = patcher.generate_patch_report(results)

    # Print summary
    successful = sum(1 for r in results if r.success)
    total = len(results)

    print(f"\nSecurity Patches Summary:")
    print(f"Patches applied: {successful}/{total}")
    print(f"Session ID: {patcher.patch_session_id}")

    if report_path:
        print(f"Detailed report: {report_path}")

    failed_patches = [r for r in results if not r.success]
    if failed_patches:
        print(f"\nFailed patches:")
        for result in failed_patches:
            print(f"  - {result.patch_name}: {result.error_message}")

    verification_issues = [r for r in results if r.applied and not r.verification_passed]
    if verification_issues:
        print(f"\nPatches with verification issues:")
        for result in verification_issues:
            print(f"  - {result.patch_name}: Verification failed")

    sys.exit(0 if successful == total else 1)

if __name__ == '__main__':
    main()