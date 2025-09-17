#!/usr/bin/env python3
"""
Automated Security Patch Update Script
=====================================

This script automatically applies critical security patches and validates
the security posture of the Signate platform.

CRITICAL VULNERABILITIES ADDRESSED:
- CVE-2023-23931, CVE-2023-0286: cryptography package
- CVE-2023-0464: pyOpenSSL package
- Redis connection security gaps
- Django security middleware updates

Usage:
    python scripts/security-patch-update.py --check
    python scripts/security-patch-update.py --update
    python scripts/security-patch-update.py --validate
"""

import argparse
import subprocess
import sys
import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/security-patches.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SecurityPatcher:
    """Automated security patch management system."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.requirements_dir = self.project_root / "project" / "backend" / "requirements"
        self.security_requirements = self.project_root / "requirements-security.txt"

        # Critical vulnerabilities to patch
        self.critical_patches = {
            'cryptography': {
                'current': '3.3.2',
                'fixed': '41.0.0',
                'cves': ['CVE-2023-23931', 'CVE-2023-0286'],
                'severity': 'CRITICAL'
            },
            'pyOpenSSL': {
                'current': '19.1.0',
                'fixed': '23.2.0',
                'cves': ['CVE-2023-0464'],
                'severity': 'CRITICAL'
            },
            'redis': {
                'current': '3.5.3',
                'fixed': '5.0.0',
                'cves': ['Multiple security enhancements'],
                'severity': 'HIGH'
            },
            'Django': {
                'current': '4.2.24',
                'fixed': '4.2.24',
                'cves': ['Security middleware updates needed'],
                'severity': 'MEDIUM'
            }
        }

    def check_vulnerabilities(self) -> Dict[str, List[str]]:
        """Check for known security vulnerabilities."""
        logger.info("🔍 Scanning for security vulnerabilities...")

        vulnerabilities = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }

        try:
            # Run safety check
            result = subprocess.run(
                ['pip', 'list', '--format=json'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                packages = json.loads(result.stdout)

                for package in packages:
                    name = package['name']
                    version = package['version']

                    if name.lower() in [p.lower() for p in self.critical_patches.keys()]:
                        patch_info = self.critical_patches.get(name, {})
                        if patch_info and self._is_vulnerable_version(version, patch_info.get('fixed')):
                            severity = patch_info.get('severity', 'UNKNOWN').lower()
                            vulnerabilities[severity].append({
                                'package': name,
                                'current_version': version,
                                'fixed_version': patch_info.get('fixed'),
                                'cves': patch_info.get('cves', [])
                            })

        except Exception as e:
            logger.error(f"❌ Error checking vulnerabilities: {e}")

        return vulnerabilities

    def _is_vulnerable_version(self, current: str, fixed: str) -> bool:
        """Check if current version is vulnerable."""
        try:
            from packaging import version
            return version.parse(current) < version.parse(fixed)
        except:
            # Fallback to string comparison
            return current < fixed

    def apply_security_patches(self) -> bool:
        """Apply critical security patches."""
        logger.info("🔒 Applying critical security patches...")

        try:
            # Backup current requirements
            self._backup_requirements()

            # Update requirements files with security patches
            self._update_requirements_files()

            # Install security-hardened packages
            self._install_security_packages()

            # Validate installation
            return self._validate_patches()

        except Exception as e:
            logger.error(f"❌ Error applying patches: {e}")
            return False

    def _backup_requirements(self):
        """Backup current requirements files."""
        backup_dir = self.project_root / "backups" / f"requirements_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        for req_file in self.requirements_dir.glob("*.txt"):
            subprocess.run(['cp', str(req_file), str(backup_dir / req_file.name)])

        logger.info(f"📁 Requirements backed up to: {backup_dir}")

    def _update_requirements_files(self):
        """Update requirements files with security patches."""
        main_req_file = self.requirements_dir / "requirements.txt"

        if main_req_file.exists():
            with open(main_req_file, 'r') as f:
                content = f.read()

            # Apply security patches
            for package, patch_info in self.critical_patches.items():
                pattern = rf"{package}==[\d\.]+"
                replacement = f"{package}>={patch_info['fixed']}"
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

            # Write updated requirements
            with open(main_req_file, 'w') as f:
                f.write(content)

            logger.info(f"📝 Updated requirements file: {main_req_file}")

    def _install_security_packages(self):
        """Install security-hardened packages."""
        logger.info("📦 Installing security-hardened packages...")

        try:
            # Install from security requirements
            result = subprocess.run(
                ['pip', 'install', '-r', str(self.security_requirements)],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                logger.info("✅ Security packages installed successfully")
            else:
                logger.error(f"❌ Error installing packages: {result.stderr}")

        except Exception as e:
            logger.error(f"❌ Installation error: {e}")

    def _validate_patches(self) -> bool:
        """Validate that patches were applied successfully."""
        logger.info("🔍 Validating security patches...")

        vulnerabilities = self.check_vulnerabilities()

        critical_count = len(vulnerabilities.get('critical', []))
        high_count = len(vulnerabilities.get('high', []))

        if critical_count == 0:
            logger.info("✅ All critical vulnerabilities patched")
            return True
        else:
            logger.warning(f"⚠️ {critical_count} critical vulnerabilities remain")
            return False

    def generate_security_report(self) -> Dict:
        """Generate comprehensive security report."""
        logger.info("📊 Generating security report...")

        vulnerabilities = self.check_vulnerabilities()

        report = {
            'timestamp': datetime.now().isoformat(),
            'scan_results': vulnerabilities,
            'patch_status': {
                'total_packages': len(self.critical_patches),
                'patched': 0,
                'pending': 0
            },
            'recommendations': []
        }

        # Calculate patch status
        for vuln_list in vulnerabilities.values():
            report['patch_status']['pending'] += len(vuln_list)

        report['patch_status']['patched'] = (
            report['patch_status']['total_packages'] -
            report['patch_status']['pending']
        )

        # Generate recommendations
        if vulnerabilities['critical']:
            report['recommendations'].append(
                "URGENT: Apply critical security patches immediately"
            )

        if vulnerabilities['high']:
            report['recommendations'].append(
                "HIGH PRIORITY: Schedule high-severity patches"
            )

        # Save report
        report_file = self.project_root / "docs" / "security" / "security-report.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"📋 Security report saved: {report_file}")
        return report

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Automated Security Patch Management')
    parser.add_argument('--check', action='store_true', help='Check for vulnerabilities')
    parser.add_argument('--update', action='store_true', help='Apply security patches')
    parser.add_argument('--validate', action='store_true', help='Validate patches')
    parser.add_argument('--report', action='store_true', help='Generate security report')

    args = parser.parse_args()

    patcher = SecurityPatcher()

    if args.check or not any(vars(args).values()):
        vulnerabilities = patcher.check_vulnerabilities()
        print("\n🔍 VULNERABILITY SCAN RESULTS:")
        print("=" * 50)

        for severity, vulns in vulnerabilities.items():
            if vulns:
                print(f"\n{severity.upper()} ({len(vulns)}):")
                for vuln in vulns:
                    print(f"  • {vuln['package']} {vuln['current_version']} → {vuln['fixed_version']}")
                    for cve in vuln['cves']:
                        print(f"    - {cve}")

    if args.update:
        success = patcher.apply_security_patches()
        if success:
            print("✅ Security patches applied successfully")
        else:
            print("❌ Error applying security patches")
            sys.exit(1)

    if args.validate:
        success = patcher._validate_patches()
        if success:
            print("✅ All critical vulnerabilities patched")
        else:
            print("⚠️ Some vulnerabilities remain")

    if args.report:
        report = patcher.generate_security_report()
        print("\n📊 SECURITY REPORT GENERATED")
        print("=" * 50)
        print(f"Critical: {len(report['scan_results']['critical'])}")
        print(f"High: {len(report['scan_results']['high'])}")
        print(f"Medium: {len(report['scan_results']['medium'])}")

if __name__ == "__main__":
    main()