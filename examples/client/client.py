# client.py
# !/usr/bin/env python3
"""
LLM Firewall - Example Client

This script demonstrates how to use the LLM Firewall API.
"""

import requests
import json
import argparse
import sys


def check_content(api_url, text):
    """
    Check content safety using the LLM Firewall API

    Args:
        api_url (str): API base URL
        text (str): Text to check

    Returns:
        dict: API response
    """
    url = f"{api_url}/check"
    headers = {"Content-Type": "application/json"}
    data = {"text": text}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with API: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            try:
                print(f"Response: {e.response.json()}")
            except:
                print(f"Response: {e.response.text}")
        sys.exit(1)


def health_check(api_url):
    """
    Check API health

    Args:
        api_url (str): API base URL

    Returns:
        dict: API response
    """
    url = f"{api_url}/health"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with API: {str(e)}")
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="LLM Firewall API Client")
    parser.add_argument("--api-url", default="http://localhost:5001", help="API base URL")
    parser.add_argument("--health", action="store_true", help="Check API health")
    parser.add_argument("--text", help="Text to check")
    parser.add_argument("--file", help="File containing text to check")

    args = parser.parse_args()

    if args.health:
        result = health_check(args.api_url)
        print(json.dumps(result, indent=2))
        sys.exit(0)

    # Get text to check
    if args.file:
        try:
            with open(args.file, "r") as f:
                text = f.read()
        except Exception as e:
            print(f"Error reading file: {str(e)}")
            sys.exit(1)
    elif args.text:
        text = args.text
    else:
        print("Please provide text to check using --text or --file")
        sys.exit(1)

    # Check content
    result = check_content(args.api_url, text)

    # Print result
    print(json.dumps(result, indent=2))

    # Print summary
    print("\nSummary:")
    print(f"Is safe: {result['is_safe']}")
    print(f"Reason: {result['overall_reason']}")

    if not result["is_safe"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
