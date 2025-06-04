import base64
import datetime
import hashlib
import json
import os
import sys
import uuid
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class LicenseManager:
    """
    License management system with encryption and validation.
    Uses Fernet symmetric encryption with a master key derived from a secret.
    """

    def __init__(self, master_secret=None):
        """
        Initialize the license manager with a master secret for key derivation.
        If not provided, attempts to load from environment variable.

        Args:
            master_secret (str, optional): Secret used to derive encryption key
        """
        # Load master secret from environment if not provided
        if not master_secret:
            master_secret = os.environ.get("LLM_FIREWALL_SECRET")

        # If still no secret, generate a machine-specific one
        if not master_secret:
            machine_id = self._get_machine_id()
            master_secret = f"llm-firewall-{machine_id}"

        # Generate key from master secret
        self.key = self._derive_key(master_secret)
        self.cipher = Fernet(self.key)

    def _derive_key(self, secret):
        """
        Derive a Fernet key from a secret using PBKDF2.

        Args:
            secret (str): Secret to derive key from

        Returns:
            bytes: Base64 encoded 32-byte key
        """
        # Use a fixed salt for reproducibility
        salt = b'LLM-Firewall-Salt-Value-Fixed'

        # Convert string secret to bytes
        if isinstance(secret, str):
            secret = secret.encode('utf-8')

        # Generate key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret))
        return key

    def _get_machine_id(self):
        """
        Get a unique identifier for the current machine.

        Returns:
            str: A unique machine identifier
        """
        # Try to get machine-specific identifiers
        machine_id = ''

        # On Linux
        if os.path.exists('/etc/machine-id'):
            with open('/etc/machine-id', 'r') as f:
                machine_id = f.read().strip()

        # On macOS
        elif sys.platform == 'darwin':
            try:
                import subprocess
                result = subprocess.run(['ioreg', '-rd1', '-c', 'IOPlatformExpertDevice'],
                                        capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'IOPlatformUUID' in line:
                        machine_id = line.split('"')[-2]
                        break
            except:
                pass

        # On Windows
        elif sys.platform == 'win32':
            try:
                import subprocess
                result = subprocess.run(['wmic', 'csproduct', 'get', 'uuid'],
                                        capture_output=True, text=True)
                machine_id = result.stdout.strip().split('\n')[1].strip()
            except:
                pass

        # Fallback to a hash of hostname if no machine ID found
        if not machine_id:
            import socket
            machine_id = hashlib.sha256(socket.gethostname().encode()).hexdigest()

        return machine_id

    def generate_license(self, customer_id, expiration_date, features=None, meta=None):
        """
        Generate an encrypted license key.

        Args:
            customer_id (str): Unique customer identifier
            expiration_date (str or datetime): License expiration date (YYYY-MM-DD)
            features (list, optional): List of licensed features
            meta (dict, optional): Additional metadata

        Returns:
            str: Encrypted license key
        """
        # Convert expiration date string to datetime if needed
        if isinstance(expiration_date, str):
            expiration_date = datetime.datetime.strptime(expiration_date, "%Y-%m-%d").date()
        elif isinstance(expiration_date, datetime.datetime):
            expiration_date = expiration_date.date()

        # Prepare license data
        license_data = {
            "license_id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "created_at": datetime.datetime.now().isoformat(),
            "expires_at": expiration_date.isoformat(),
            "features": features or ["basic"],
            "meta": meta or {}
        }

        # Add validation hash to prevent tampering
        content_str = json.dumps(license_data, sort_keys=True)
        license_data["hash"] = hashlib.sha256(content_str.encode()).hexdigest()

        # Encrypt the license data
        license_json = json.dumps(license_data)
        encrypted = self.cipher.encrypt(license_json.encode())

        # Return as base64 string for easier storage/transmission
        return base64.urlsafe_b64encode(encrypted).decode()

    def validate_license(self, license_key):
        """
        Validate a license key and check if it's expired.

        Args:
            license_key (str): Encrypted license key

        Returns:
            tuple: (is_valid, message, license_data)
        """
        try:
            # Decode from base64
            encrypted = base64.urlsafe_b64decode(license_key)

            # Decrypt the license
            decrypted = self.cipher.decrypt(encrypted)
            license_data = json.loads(decrypted)

            # Verify hash to detect tampering
            original_hash = license_data.pop("hash", None)
            content_str = json.dumps(license_data, sort_keys=True)
            computed_hash = hashlib.sha256(content_str.encode()).hexdigest()

            if original_hash != computed_hash:
                return False, "License has been tampered with", None

            # Check expiration
            expires_at = datetime.datetime.fromisoformat(license_data["expires_at"]).date()
            today = datetime.date.today()

            if today > expires_at:
                days_expired = (today - expires_at).days
                return False, f"License expired {days_expired} days ago", license_data

            days_left = (expires_at - today).days
            return True, f"License valid for {days_left} more days", license_data

        except Exception as e:
            return False, f"Invalid license key: {str(e)}", None

    def save_license_to_file(self, license_key, file_path):
        """
        Save license key to a file.

        Args:
            license_key (str): License key to save
            file_path (str): Path to save the license to

        Returns:
            bool: Success status
        """
        try:
            with open(file_path, 'w') as f:
                f.write(license_key)
            return True
        except Exception as e:
            print(f"Error saving license: {str(e)}")
            return False

    def load_license_from_file(self, file_path):
        """
        Load license key from a file.

        Args:
            file_path (str): Path to load the license from

        Returns:
            str or None: License key if successful, None otherwise
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return f.read().strip()
            return None
        except Exception as e:
            print(f"Error loading license: {str(e)}")
            return None


# License key generation utility
def generate_license_key(customer_id, expiration_date, secret_key, features=None):
    """
    Generate a license key for a customer.

    Args:
        customer_id (str): Customer identifier
        expiration_date (str): Expiration date in YYYY-MM-DD format
        secret_key (str): Secret key for encryption
        features (list, optional): List of licensed features

    Returns:
        str: License key
    """
    manager = LicenseManager(secret_key)
    return manager.generate_license(customer_id, expiration_date, features)


# Example usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LLM Firewall License Utility")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Generate license command
    gen_parser = subparsers.add_parser("generate", help="Generate a license key")
    gen_parser.add_argument("--customer", required=True, help="Customer ID")
    gen_parser.add_argument("--expires", required=True, help="Expiration date (YYYY-MM-DD)")
    gen_parser.add_argument("--secret", required=True, help="Secret key for encryption")
    gen_parser.add_argument("--output", help="Output file path")
    gen_parser.add_argument("--features", nargs="+", help="Licensed features")

    # Validate license command
    val_parser = subparsers.add_parser("validate", help="Validate a license key")
    val_parser.add_argument("--key", help="License key to validate")
    val_parser.add_argument("--file", help="License key file")
    val_parser.add_argument("--secret", required=True, help="Secret key for decryption")

    args = parser.parse_args()

    if args.command == "generate":
        license_key = generate_license_key(args.customer, args.expires, args.secret, args.features)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(license_key)
            print(f"License key saved to {args.output}")
        else:
            print(f"License key: {license_key}")

    elif args.command == "validate":
        manager = LicenseManager(args.secret)

        if args.file:
            key = manager.load_license_from_file(args.file)
        elif args.key:
            key = args.key
        else:
            print("Error: Either --key or --file must be provided")
            sys.exit(1)

        valid, message, data = manager.validate_license(key)
        print(f"Valid: {valid}")
        print(f"Message: {message}")
        if data:
            print("License data:")
            for k, v in data.items():
                print(f"  {k}: {v}")