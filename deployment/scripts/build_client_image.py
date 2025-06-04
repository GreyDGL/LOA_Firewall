#!/usr/bin/env python3
"""
Client Image Builder for LLM Firewall

This script builds a Docker image with an embedded license for client distribution.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
import sys
sys.path.append('../../')
from src.licensing.license_manager import LicenseManager


def generate_client_license(customer_id, duration_days, secret_key, features=None):
    """Generate a license for the client"""
    manager = LicenseManager(secret_key)
    expiration_date = (datetime.now() + timedelta(days=duration_days)).strftime("%Y-%m-%d")
    
    license_key = manager.generate_license(
        customer_id=customer_id,
        expiration_date=expiration_date,
        features=features or ["basic"],
        meta={
            "generated_at": datetime.now().isoformat(),
            "client_build": True,
            "duration_days": duration_days
        }
    )
    
    return license_key, expiration_date


def create_client_dockerfile(base_dockerfile, license_key, secret_key):
    """Create a secure Dockerfile with embedded license and no source code"""
    
    with open(base_dockerfile, 'r') as f:
        dockerfile_content = f.read()
    
    # Add license embedding to the Dockerfile
    license_embed = f"""
# Embed client license (before switching to non-root user)
RUN echo '{license_key}' > /app/license.key && \\
    chmod 600 /app/license.key && \\
    chown firewall:firewall /app/license.key

# Set the secret key as environment variable
ENV LLM_FIREWALL_SECRET="{secret_key}"
"""
    
    # Insert before USER firewall instruction
    dockerfile_lines = dockerfile_content.split('\n')
    user_index = -1
    for i, line in enumerate(dockerfile_lines):
        if line.strip().startswith('USER firewall'):
            user_index = i
            break
    
    if user_index != -1:
        dockerfile_lines.insert(user_index, license_embed)
    else:
        # Fallback: insert before CMD
        cmd_index = -1
        for i, line in enumerate(dockerfile_lines):
            if line.strip().startswith('CMD'):
                cmd_index = i
                break
        if cmd_index != -1:
            dockerfile_lines.insert(cmd_index, license_embed)
        else:
            dockerfile_lines.append(license_embed)
    
    return '\n'.join(dockerfile_lines)


def build_client_image(customer_id, tag, secret_key, duration_days=180, features=None):
    """Build a client-specific Docker image with embedded license"""
    
    print(f"Building client image for: {customer_id}")
    print(f"License duration: {duration_days} days")
    print(f"Image tag: {tag}")
    
    # Generate license
    license_key, expiration_date = generate_client_license(
        customer_id, duration_days, secret_key, features
    )
    
    print(f"License expires: {expiration_date}")
    
    # Create temporary Dockerfile with embedded license (use secure client Dockerfile)
    client_dockerfile_path = 'deployment/docker/Dockerfile.client'
    base_dockerfile_path = 'deployment/docker/Dockerfile'
    base_dockerfile = client_dockerfile_path if os.path.exists(client_dockerfile_path) else base_dockerfile_path
    with tempfile.NamedTemporaryFile(mode='w', suffix='.Dockerfile', delete=False) as f:
        client_dockerfile = create_client_dockerfile(base_dockerfile, license_key, secret_key)
        f.write(client_dockerfile)
        temp_dockerfile = f.name
    
    try:
        # Build Docker image
        build_cmd = [
            'docker', 'build',
            '-f', temp_dockerfile,
            '-t', tag,
            '.'
        ]
        
        print(f"Building Docker image: {' '.join(build_cmd)}")
        result = subprocess.run(build_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Docker build failed: {result.stderr}")
            return False
        
        print(f"Successfully built image: {tag}")
        
        # Create client info file
        client_info = {
            "customer_id": customer_id,
            "image_tag": tag,
            "license_expires": expiration_date,
            "features": features or ["basic"],
            "build_date": datetime.now().isoformat()
        }
        
        info_filename = f"client_info_{customer_id.replace(' ', '_')}.json"
        with open(info_filename, 'w') as f:
            json.dump(client_info, f, indent=2)
        
        print(f"Client info saved to: {info_filename}")
        return True
        
    finally:
        # Clean up temporary file
        os.unlink(temp_dockerfile)


def create_client_docker_compose(customer_id, image_tag, output_file=None):
    """Create a docker-compose.yml file for the client"""
    
    if not output_file:
        output_file = f"docker-compose.{customer_id.replace(' ', '_')}.yml"
    
    compose_content = f"""version: '3.8'

services:
  llm-firewall:
    image: {image_tag}
    container_name: llm-firewall-{customer_id.replace(' ', '_').lower()}
    restart: unless-stopped

    # Port mapping
    ports:
      - "5001:5001"   # LLM Firewall API
      - "11434:11434" # Ollama API (optional)

    # Environment configuration
    environment:
      - LLM_FIREWALL_HOST=0.0.0.0
      - LLM_FIREWALL_PORT=5001
      - LLM_FIREWALL_LOG_LEVEL=INFO
      - LLM_FIREWALL_DEBUG=false
      - OLLAMA_HOST=0.0.0.0:11434
      - PYTHONUNBUFFERED=1

    # Volume mounts for logs
    volumes:
      - ./logs:/app/logs
      - ollama-models:/home/firewall/.ollama

    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

    # Resource limits
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'

    # Security settings
    user: firewall
    tmpfs:
      - /tmp:size=512M,mode=1777

    # Network isolation
    networks:
      - firewall-network

networks:
  firewall-network:
    driver: bridge

volumes:
  ollama-models:
    driver: local
"""
    
    with open(output_file, 'w') as f:
        f.write(compose_content)
    
    print(f"Client docker-compose saved to: {output_file}")
    return output_file


def main():
    parser = argparse.ArgumentParser(description="Build client-specific LLM Firewall Docker images")
    parser.add_argument("--customer", required=True, help="Customer ID or name")
    parser.add_argument("--tag", required=True, help="Docker image tag (e.g., llm-firewall:client-abc)")
    parser.add_argument("--secret", required=True, help="Master secret key for license encryption")
    parser.add_argument("--days", type=int, default=180, help="License duration in days (default: 180)")
    parser.add_argument("--features", nargs="+", default=["basic"], help="Licensed features")
    parser.add_argument("--compose", action="store_true", help="Generate docker-compose.yml for client")
    parser.add_argument("--push", help="Docker registry to push image to (optional)")
    
    args = parser.parse_args()
    
    # Validate inputs
    dockerfile_path = 'deployment/docker/Dockerfile'
    if not os.path.exists(dockerfile_path):
        print("Error: Dockerfile not found at deployment/docker/Dockerfile")
        sys.exit(1)
    
    # Build the client image
    success = build_client_image(
        customer_id=args.customer,
        tag=args.tag,
        secret_key=args.secret,
        duration_days=args.days,
        features=args.features
    )
    
    if not success:
        print("Failed to build client image")
        sys.exit(1)
    
    # Generate docker-compose if requested
    if args.compose:
        create_client_docker_compose(args.customer, args.tag)
    
    # Push to registry if requested
    if args.push:
        registry_tag = f"{args.push}/{args.tag}"
        print(f"Tagging image for registry: {registry_tag}")
        
        tag_cmd = ['docker', 'tag', args.tag, registry_tag]
        result = subprocess.run(tag_cmd)
        
        if result.returncode == 0:
            print(f"Pushing to registry: {registry_tag}")
            push_cmd = ['docker', 'push', registry_tag]
            result = subprocess.run(push_cmd)
            
            if result.returncode == 0:
                print(f"Successfully pushed: {registry_tag}")
            else:
                print("Failed to push to registry")
                sys.exit(1)
        else:
            print("Failed to tag image for registry")
            sys.exit(1)
    
    print("\nClient deployment ready!")
    print(f"Image: {args.tag}")
    print(f"License expires in {args.days} days")
    print("\nNext steps for client:")
    print("1. Load the Docker image or pull from registry")
    print("2. Use the provided docker-compose.yml to deploy")
    print("3. Access the firewall API at http://localhost:5001")


if __name__ == "__main__":
    main()