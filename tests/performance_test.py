#!/usr/bin/env python3
"""
Performance test program to measure the theoretical maximum token handling
capacity of the LoAFirewall system.

This test runs for approximately 1 minute and measures:
- Total tokens processed
- Requests per second
- Average processing time
- Token throughput (tokens per second)
"""

import time
import threading
import statistics
import requests
import json
import argparse
from datetime import datetime
import concurrent.futures


class FirewallPerformanceTest:
    def __init__(self, base_url="http://localhost:5001", num_threads=10, test_duration=60):
        """
        Initialize the performance test
        
        Args:
            base_url (str): Base URL of the firewall API
            num_threads (int): Number of concurrent threads
            test_duration (int): Test duration in seconds
        """
        self.base_url = base_url
        self.num_threads = num_threads
        self.test_duration = test_duration
        
        # Test data with varying complexity
        self.test_texts = [
            "Hello world, this is a simple test message.",  # ~10 tokens
            "Can you help me understand how machine learning algorithms work in practice? I'm particularly interested in neural networks and their applications.",  # ~25 tokens
            "The quick brown fox jumps over the lazy dog. This is a classic pangram used for testing text processing systems and measuring performance characteristics.",  # ~25 tokens
            "Write a detailed explanation of quantum computing principles, including superposition, entanglement, and quantum gates. How do these concepts contribute to quantum advantage?",  # ~30 tokens
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",  # ~75 tokens
        ]
        
        # Metrics tracking
        self.results = []
        self.start_time = None
        self.end_time = None
        self.stop_event = threading.Event()
        
    def check_firewall_health(self):
        """Check if the firewall is running and healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Firewall is healthy: {health_data}")
                return True
            else:
                print(f"❌ Firewall health check failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ Failed to connect to firewall: {e}")
            return False
    
    def get_initial_token_count(self):
        """Get the initial token count from the firewall"""
        try:
            response = requests.get(f"{self.base_url}/stats", timeout=5)
            if response.status_code == 200:
                stats_data = response.json()
                return stats_data.get("total_tokens_processed", 0)
            else:
                print(f"Warning: Could not get initial token count: {response.status_code}")
                return 0
        except requests.RequestException as e:
            print(f"Warning: Could not get initial token count: {e}")
            return 0
    
    def send_single_request(self, text):
        """
        Send a single request to the firewall and measure performance
        
        Args:
            text (str): Text to send for checking
            
        Returns:
            dict: Result with timing and response information
        """
        start_time = time.time()
        
        try:
            payload = {"text": text}
            response = requests.post(
                f"{self.base_url}/check",
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if response.status_code == 200:
                result_data = response.json()
                return {
                    "success": True,
                    "processing_time": processing_time,
                    "tokens_processed": result_data.get("tokens_processed", 0),
                    "total_tokens_processed": result_data.get("total_tokens_processed", 0),
                    "is_safe": result_data.get("is_safe", True),
                    "text_length": len(text),
                    "response_time_api": result_data.get("processing_time_ms", 0) / 1000.0,
                }
            else:
                return {
                    "success": False,
                    "processing_time": processing_time,
                    "error": f"HTTP {response.status_code}",
                    "text_length": len(text),
                }
                
        except requests.RequestException as e:
            end_time = time.time()
            processing_time = end_time - start_time
            return {
                "success": False,
                "processing_time": processing_time,
                "error": str(e),
                "text_length": len(text),
            }
    
    def worker_thread(self, thread_id):
        """
        Worker thread function that continuously sends requests
        
        Args:
            thread_id (int): ID of the worker thread
        """
        request_count = 0
        
        while not self.stop_event.is_set():
            # Cycle through test texts
            text = self.test_texts[request_count % len(self.test_texts)]
            
            result = self.send_single_request(text)
            result["thread_id"] = thread_id
            result["request_id"] = request_count
            result["timestamp"] = time.time()
            
            self.results.append(result)
            request_count += 1
            
            # Small delay to prevent overwhelming the system
            time.sleep(0.01)
    
    def run_performance_test(self):
        """Run the main performance test"""
        print(f"🚀 Starting performance test...")
        print(f"   Duration: {self.test_duration} seconds")
        print(f"   Threads: {self.num_threads}")
        print(f"   Target: {self.base_url}")
        print()
        
        # Check firewall health
        if not self.check_firewall_health():
            print("❌ Cannot proceed - firewall is not healthy")
            return
        
        # Get initial token count
        initial_tokens = self.get_initial_token_count()
        print(f"📊 Initial token count: {initial_tokens:,}")
        print()
        
        # Start worker threads
        self.start_time = time.time()
        threads = []
        
        print(f"⏱️  Starting {self.num_threads} worker threads...")
        
        for i in range(self.num_threads):
            thread = threading.Thread(target=self.worker_thread, args=(i,))
            thread.daemon = True
            thread.start()
            threads.append(thread)
        
        # Run for specified duration
        print(f"🔄 Running test for {self.test_duration} seconds...")
        time.sleep(self.test_duration)
        
        # Stop all threads
        print("🛑 Stopping test...")
        self.stop_event.set()
        self.end_time = time.time()
        
        # Wait for threads to finish
        for thread in threads:
            thread.join(timeout=5)
        
        # Get final token count
        final_tokens = self.get_initial_token_count()
        
        print("✅ Test completed!")
        print()
        
        # Analyze results
        self.analyze_results(initial_tokens, final_tokens)
    
    def analyze_results(self, initial_tokens, final_tokens):
        """
        Analyze and display the test results
        
        Args:
            initial_tokens (int): Initial token count
            final_tokens (int): Final token count
        """
        if not self.results:
            print("❌ No results to analyze")
            return
        
        # Filter successful requests
        successful_results = [r for r in self.results if r.get("success", False)]
        failed_results = [r for r in self.results if not r.get("success", False)]
        
        total_requests = len(self.results)
        successful_requests = len(successful_results)
        failed_requests = len(failed_results)
        
        if successful_requests == 0:
            print("❌ No successful requests to analyze")
            return
        
        # Calculate metrics
        actual_duration = self.end_time - self.start_time
        requests_per_second = total_requests / actual_duration
        successful_rps = successful_requests / actual_duration
        
        processing_times = [r["processing_time"] for r in successful_results]
        avg_processing_time = statistics.mean(processing_times)
        median_processing_time = statistics.median(processing_times)
        p95_processing_time = sorted(processing_times)[int(0.95 * len(processing_times))]
        
        # Token metrics
        total_tokens_in_requests = sum(r.get("tokens_processed", 0) for r in successful_results)
        tokens_per_second = total_tokens_in_requests / actual_duration
        firewall_total_tokens = final_tokens - initial_tokens
        
        # Text length metrics
        text_lengths = [r.get("text_length", 0) for r in successful_results]
        avg_text_length = statistics.mean(text_lengths) if text_lengths else 0
        
        # Print comprehensive results
        print("📈 PERFORMANCE TEST RESULTS")
        print("=" * 50)
        print()
        
        print("🎯 Test Configuration:")
        print(f"   Duration: {actual_duration:.2f} seconds")
        print(f"   Threads: {self.num_threads}")
        print(f"   Test texts: {len(self.test_texts)} variants")
        print()
        
        print("📊 Request Metrics:")
        print(f"   Total requests: {total_requests:,}")
        print(f"   Successful: {successful_requests:,} ({successful_requests/total_requests*100:.1f}%)")
        print(f"   Failed: {failed_requests:,} ({failed_requests/total_requests*100:.1f}%)")
        print(f"   Requests/second: {requests_per_second:.2f}")
        print(f"   Successful RPS: {successful_rps:.2f}")
        print()
        
        print("⏱️  Timing Metrics:")
        print(f"   Average processing time: {avg_processing_time*1000:.2f} ms")
        print(f"   Median processing time: {median_processing_time*1000:.2f} ms")
        print(f"   95th percentile: {p95_processing_time*1000:.2f} ms")
        print()
        
        print("🔤 Token Metrics:")
        print(f"   Tokens processed (by requests): {total_tokens_in_requests:,}")
        print(f"   Tokens processed (by firewall): {firewall_total_tokens:,}")
        print(f"   Tokens per second: {tokens_per_second:.2f}")
        print(f"   Average text length: {avg_text_length:.1f} characters")
        print(f"   Average tokens per request: {total_tokens_in_requests/successful_requests:.1f}")
        print()
        
        print("🎯 Theoretical Maximum Capacity:")
        # Calculate theoretical maximum assuming optimal conditions
        min_processing_time = min(processing_times)
        theoretical_max_rps = 1 / min_processing_time
        theoretical_max_tokens_per_sec = theoretical_max_rps * (total_tokens_in_requests/successful_requests)
        
        print(f"   Fastest request: {min_processing_time*1000:.2f} ms")
        print(f"   Theoretical max RPS: {theoretical_max_rps:.2f}")
        print(f"   Theoretical max tokens/sec: {theoretical_max_tokens_per_sec:.2f}")
        print()
        
        # Error analysis
        if failed_requests > 0:
            print("❌ Error Analysis:")
            error_types = {}
            for result in failed_results:
                error = result.get("error", "Unknown")
                error_types[error] = error_types.get(error, 0) + 1
            
            for error, count in error_types.items():
                print(f"   {error}: {count} ({count/failed_requests*100:.1f}%)")
            print()
        
        print("💡 Summary:")
        print(f"   The firewall processed {firewall_total_tokens:,} tokens in {actual_duration:.1f} seconds")
        print(f"   Peak throughput: {tokens_per_second:.1f} tokens/second")
        print(f"   Average response time: {avg_processing_time*1000:.1f} ms")
        print(f"   Success rate: {successful_requests/total_requests*100:.1f}%")


def main():
    parser = argparse.ArgumentParser(description="LoAFirewall Performance Test")
    parser.add_argument("--url", default="http://localhost:5001", 
                       help="Base URL of the firewall API (default: http://localhost:5001)")
    parser.add_argument("--threads", type=int, default=10,
                       help="Number of concurrent threads (default: 10)")
    parser.add_argument("--duration", type=int, default=60,
                       help="Test duration in seconds (default: 60)")
    
    args = parser.parse_args()
    
    # Create and run the performance test
    test = FirewallPerformanceTest(
        base_url=args.url,
        num_threads=args.threads,
        test_duration=args.duration
    )
    
    try:
        test.run_performance_test()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")


if __name__ == "__main__":
    main()