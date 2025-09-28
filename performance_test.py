#!/usr/bin/env python3
"""
Performance test comparing multiple instances vs singleton pattern.
"""
import time
from scrapers.harris_county_scraper import get_scraper, HarrisCountyScraper


def test_multiple_instances():
    """Test creating multiple scraper instances (old way)."""
    print("🔄 Testing Multiple Instances (Old Way)")
    start_time = time.time()
    
    # Simulate creating multiple instances
    scrapers = []
    for i in range(5):
        scraper = HarrisCountyScraper()
        scrapers.append(scraper)
    
    end_time = time.time()
    print(f"⏱️  Time to create 5 instances: {(end_time - start_time)*1000:.2f}ms")
    print(f"📊 Memory: {len(scrapers)} scraper instances created")
    return scrapers


def test_singleton_pattern():
    """Test using singleton pattern (new way)."""
    print("\n🚀 Testing Singleton Pattern (New Way)")
    start_time = time.time()
    
    # Simulate getting scraper multiple times
    scrapers = []
    for i in range(5):
        scraper = get_scraper()  # Same instance returned
        scrapers.append(scraper)
    
    end_time = time.time()
    print(f"⏱️  Time to get 5 references: {(end_time - start_time)*1000:.2f}ms")
    print(f"📊 Memory: {len(set(id(s) for s in scrapers))} unique instance(s)")
    return scrapers


def test_actual_scraping_performance():
    """Test actual scraping performance with singleton."""
    print("\n🔍 Testing Actual Scraping Performance")
    
    scraper = get_scraper()
    
    # Test multiple scraping operations
    start_time = time.time()
    
    for i in range(3):
        print(f"  Scraping batch {i+1}/3...")
        df = scraper.scrape_records("DEED", "01/01/2025", "01/02/2025")
        print(f"    Found {len(df)} records")
    
    end_time = time.time()
    total_time = end_time - start_time
    print(f"⏱️  Total scraping time: {total_time:.2f}s")
    print(f"📊 Average per batch: {total_time/3:.2f}s")


def main():
    """Run performance tests."""
    print("🧪 Harris County Scraper Performance Test")
    print("=" * 50)
    
    # Test instance creation
    old_scrapers = test_multiple_instances()
    new_scrapers = test_singleton_pattern()
    
    # Verify singleton works
    print(f"\n✅ Singleton verification:")
    print(f"  All references point to same instance: {all(s is new_scrapers[0] for s in new_scrapers)}")
    print(f"  Instance ID: {id(new_scrapers[0])}")
    
    # Test actual performance
    test_actual_scraping_performance()
    
    print("\n🎉 Performance test completed!")
    print("\n💡 Benefits of Singleton Pattern:")
    print("  ✅ Single instance = less memory usage")
    print("  ✅ Faster initialization = better performance")
    print("  ✅ Consistent state = more reliable")
    print("  ✅ Resource efficiency = better scalability")


if __name__ == "__main__":
    main()
