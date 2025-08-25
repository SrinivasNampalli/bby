import asyncio
import aiohttp
import time
import statistics
from datetime import datetime
import json

class LoadTester:
    def __init__(self, url, concurrent_users=10, test_duration=60):
        self.url = url
        self.concurrent_users = concurrent_users
        self.test_duration = test_duration
        self.results = []
        
    async def make_request(self, session, user_id):
        """Make a single HTTP request and record metrics"""
        start_time = time.time()
        try:
            async with session.get(self.url) as response:
                await response.read()  # Ensure full response is received
                end_time = time.time()
                
                result = {
                    'user_id': user_id,
                    'timestamp': datetime.now().isoformat(),
                    'response_time': end_time - start_time,
                    'status_code': response.status,
                    'success': response.status == 200
                }
                self.results.append(result)
                return result
                
        except Exception as e:
            end_time = time.time()
            result = {
                'user_id': user_id,
                'timestamp': datetime.now().isoformat(),
                'response_time': end_time - start_time,
                'status_code': 0,
                'success': False,
                'error': str(e)
            }
            self.results.append(result)
            return result
    
    async def simulate_user(self, session, user_id):
        """Simulate a single user making requests during test duration"""
        end_time = time.time() + self.test_duration
        request_count = 0
        
        while time.time() < end_time:
            await self.make_request(session, user_id)
            request_count += 1
            # Small delay between requests (1-3 seconds)
            await asyncio.sleep(1 + (user_id % 3))
            
        return request_count
    
    async def run_test(self):
        """Run the load test with concurrent users"""
        print(f"Starting load test for {self.url}")
        print(f"Concurrent users: {self.concurrent_users}")
        print(f"Test duration: {self.test_duration} seconds")
        print("-" * 50)
        
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Start all concurrent users
            tasks = []
            for user_id in range(self.concurrent_users):
                task = asyncio.create_task(self.simulate_user(session, user_id))
                tasks.append(task)
            
            # Wait for all users to complete
            start_time = time.time()
            await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
        self.generate_report(total_time)
    
    def generate_report(self, total_test_time):
        """Generate and display test results"""
        if not self.results:
            print("No results to report")
            return
            
        successful_requests = [r for r in self.results if r['success']]
        failed_requests = [r for r in self.results if not r['success']]
        response_times = [r['response_time'] for r in successful_requests]
        
        print("\n" + "="*60)
        print("LOAD TEST RESULTS")
        print("="*60)
        print(f"Total requests: {len(self.results)}")
        print(f"Successful requests: {len(successful_requests)}")
        print(f"Failed requests: {len(failed_requests)}")
        print(f"Success rate: {(len(successful_requests) / len(self.results)) * 100:.1f}%")
        print(f"Test duration: {total_test_time:.1f} seconds")
        print(f"Requests per second: {len(self.results) / total_test_time:.2f}")
        
        if response_times:
            print(f"\nResponse Time Statistics:")
            print(f"  Average: {statistics.mean(response_times):.3f}s")
            print(f"  Median: {statistics.median(response_times):.3f}s")
            print(f"  Min: {min(response_times):.3f}s")
            print(f"  Max: {max(response_times):.3f}s")
            if len(response_times) > 1:
                print(f"  Std Dev: {statistics.stdev(response_times):.3f}s")
        
        # Status code breakdown
        status_codes = {}
        for result in self.results:
            code = result['status_code']
            status_codes[code] = status_codes.get(code, 0) + 1
        
        print(f"\nStatus Code Breakdown:")
        for code, count in sorted(status_codes.items()):
            print(f"  {code}: {count} requests")
        
        # Save detailed results
        self.save_results()
        print(f"\nDetailed results saved to: load_test_results.json")
    
    def save_results(self):
        """Save detailed results to JSON file"""
        report_data = {
            'test_config': {
                'url': self.url,
                'concurrent_users': self.concurrent_users,
                'test_duration': self.test_duration,
                'timestamp': datetime.now().isoformat()
            },
            'results': self.results
        }
        
        with open('load_test_results.json', 'w') as f:
            json.dump(report_data, f, indent=2)

async def main():
    # Test configuration
    URL = "https://posture-updated.vercel.app/"
    CONCURRENT_USERS = 5  # Start with 5 concurrent users
    TEST_DURATION = 30    # 30 second test
    
    # Create and run load test
    tester = LoadTester(URL, CONCURRENT_USERS, TEST_DURATION)
    await tester.run_test()

if __name__ == "__main__":
    asyncio.run(main())