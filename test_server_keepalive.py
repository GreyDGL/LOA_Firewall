#!/usr/bin/env python3
import requests
import time
import json
from datetime import datetime

SERVER_URL = "http://localhost:5000"

def ping_server():
    """Send periodic requests to keep server active"""
    request_count = 0
    
    print(f"Starting server keep-alive test at {datetime.now()}")
    print(f"Pinging server at {SERVER_URL} every 10 seconds...")
    print("-" * 50)
    
    while True:
        try:
            request_count += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            health_response = requests.get(f"{SERVER_URL}/health", timeout=5)
            health_status = health_response.json() if health_response.status_code == 200 else "Failed"
            
            stats_response = requests.get(f"{SERVER_URL}/stats", timeout=5)
            stats_data = stats_response.json() if stats_response.status_code == 200 else "Failed"
            
            print(f"[{timestamp}] Request #{request_count}")
            print(f"  Health: {health_status}")
            if isinstance(stats_data, dict):
                print(f"  Stats: Requests={stats_data.get('total_requests', 0)}, "
                      f"Blocked={stats_data.get('blocked_requests', 0)}")
            else:
                print(f"  Stats: {stats_data}")
            
            test_data = {
                "text": "This is a test message to keep the server active.",
                "user_id": "test_user",
                "session_id": "test_session"
            }
            check_response = requests.post(
                f"{SERVER_URL}/check",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if check_response.status_code == 200:
                result = check_response.json()
                print(f"  Content check: Allowed={result.get('allowed', False)}, "
                      f"Risk={result.get('risk_score', 0):.2f}")
            else:
                print(f"  Content check failed: {check_response.status_code}")
            
            print()
            
        except requests.exceptions.RequestException as e:
            print(f"[{timestamp}] Error: {e}")
            print("  Retrying in 10 seconds...")
            print()
        except KeyboardInterrupt:
            print("\nStopping keep-alive test...")
            break
        except Exception as e:
            print(f"[{timestamp}] Unexpected error: {e}")
            print()
        
        time.sleep(10)

if __name__ == "__main__":
    try:
        ping_server()
    except KeyboardInterrupt:
        print("\nTest stopped by user.")