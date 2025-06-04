#!/usr/bin/env python3
"""
LLM Firewall License Generator

This script generates license keys for LLM Firewall customers.
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
import secrets
import string
from src.licensing.license_manager import LicenseManager


def generate_secret_key(length=32):
    """Generate a random secret key"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def main():
    parser = argparse.ArgumentParser(description="LLM Firewall License Generator")
    parser.add_argument("--customer", required=True, help="Customer ID or name")
    parser.add_argument("--days", type=int, default=365, help="License validity in days")
    parser.add_argument("--features", nargs="+", default=["basic"], help="Licensed features")
    parser.add_argument("--output", default="license.key", help="Output file for license key")
    parser.add_argument("--secret", default=None, help="Secret key for encryption (will generate if not provided)")
    parser.add_argument("--generate-only", action="store_true",
                        help="Only generate the license key, don't save to file")

    args = parser.parse_args()

    # Generate or use provided secret key
    secret_key = args.secret or generate_secret_key()
    if not args.secret:
        print(f"Generated secret key: {secret_key}")
        print("IMPORTANT: Store this key securely! You'll need it to validate licenses.")

    # Calculate expiration date
    expiration_date = (datetime.now() + timedelta(days=args.days)).strftime("%Y-%m-%d")

    # Create license manager
    manager = LicenseManager(secret_key)

    # Generate license key
    license_key = manager.generate_license(
        args.customer,
        expiration_date,
        args.features,
        {"generated_at": datetime.now().isoformat()}
    )

    if args.generate_only:
        print(f"\nLicense Key:\n{license_key}")
    else:
        # Save license key to file
        try:
            with open(args.output, 'w') as f:
                f.write(license_key)
            print(f"\nLicense key saved to: {args.output}")
            print(f"Expiration date: {expiration_date}")
            print(f"Features: {', '.join(args.features)}")
        except Exception as e:
            print(f"Error saving license key: {str(e)}")
            print(f"\nLicense Key:\n{license_key}")

    # Print validation command
    print("\nTo validate this license, run:")
    print(f"python3 license_manager.py validate --file {args.output} --secret \"{secret_key}\"")

    return 0


if __name__ == "__main__":
    sys.exit(main())