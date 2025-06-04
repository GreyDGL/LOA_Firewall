#!/usr/bin/env python3
"""
Binary Builder for LLM Firewall

Creates a standalone binary distribution that protects source code.
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path


def create_spec_file():
    """Create PyInstaller spec file for the firewall service"""
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Data files to include
datas = [
    ('config.json', '.'),
    ('blacklists', 'blacklists'),
    ('filters', 'filters'),
    ('guards', 'guards'),
]

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'flask',
    'cryptography',
    'cryptography.fernet',
    'requests',
    'ollama',
    'transformers',
    'torch',
    'numpy',
    'json',
    'logging',
    'threading',
    'datetime',
    'base64',
    'hashlib',
    'uuid',
    'subprocess',
    'socket',
    're',
]

a = Analysis(
    ['firewall_service.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='llm-firewall',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    with open('llm-firewall.spec', 'w') as f:
        f.write(spec_content)


def build_binary():
    """Build the binary using PyInstaller"""
    
    print("Installing PyInstaller...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
    
    print("Creating PyInstaller spec file...")
    create_spec_file()
    
    print("Building binary with PyInstaller...")
    result = subprocess.run([
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        'llm-firewall.spec'
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"PyInstaller failed: {result.stderr}")
        return False
    
    print("Binary built successfully!")
    return True


def create_secure_dockerfile():
    """Create a Dockerfile that uses the binary instead of source code"""
    
    dockerfile_content = '''# Secure client distribution Dockerfile using binary
FROM ubuntu:22.04 as base

ENV DEBIAN_FRONTEND=noninteractive

# Create non-root user
RUN groupadd -r firewall && useradd -r -g firewall firewall

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    ca-certificates \\
    && rm -rf /var/lib/apt/lists/* \\
    && apt-get clean

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Create app directories
RUN mkdir -p /app/logs /home/firewall/.ollama && \\
    chown -R firewall:firewall /app /home/firewall

WORKDIR /app

# Copy only the binary and essential files
COPY --chown=firewall:firewall dist/llm-firewall /app/
COPY --chown=firewall:firewall config.json /app/
RUN chmod +x /app/llm-firewall

# Switch to non-root user
USER firewall

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LLM_FIREWALL_CONFIG=/app/config.json
ENV LLM_FIREWALL_LICENSE=/app/license.key
ENV LLM_FIREWALL_HOST=0.0.0.0
ENV LLM_FIREWALL_PORT=5001

# Expose firewall API port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:5001/health || exit 1

# Run the binary
CMD ["/app/llm-firewall"]
'''
    
    with open('Dockerfile.binary', 'w') as f:
        f.write(dockerfile_content)


def main():
    print("Building secure binary distribution for LLM Firewall...")
    
    # Check if we're in the right directory
    if not os.path.exists('firewall_service.py'):
        print("Error: firewall_service.py not found. Run this script from the project root.")
        return 1
    
    # Build the binary
    if not build_binary():
        print("Failed to build binary")
        return 1
    
    # Create secure Dockerfile
    create_secure_dockerfile()
    
    print("\\nSecure distribution files created:")
    print("- dist/llm-firewall (binary executable)")
    print("- Dockerfile.binary (secure Dockerfile)")
    print("\\nTo build client image:")
    print("docker build -f Dockerfile.binary -t llm-firewall:secure .")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())