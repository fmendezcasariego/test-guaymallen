"""
Test script for newspapers_scraper_v2.py
Tests individual scrapers and orchestrator functionality.
"""

import sys
import logging
from newspapers_scraper_v2 import (
    LosAndesScraper,
    DiarioUnoScraper,
    ElSolScraper,
    MDZScraper,
    NewspaperScraperOrchestrator
)

# Set logging to INFO to see progress
logging.basicConfig(level=logging.INFO)

def test_individual_scraper(scraper, max_articles=3):
    """Test an individual scraper with limited articles."""
    print(f"\n{'='*80}")
    print(f"Testing {scraper.name}")
    print(f"{'='*80}")
    
    # Limit to first URL only for testing
    original_urls = scraper.urls
    scraper.urls = [scraper.urls[0]]
    
    try:
        results = scraper.scrape()
        
        if not results:
            print(f"⚠️  No articles found for {scraper.name}")
            return False
        
        print(f"✅ Successfully scraped {len(results)} articles from {scraper.name}")
        
        # Display first article
        first_url = list(results.keys())[0]
        first_article = results[first_url]
        
        print(f"\nSample article:")
        print(f"  URL: {first_url}")
        print(f"  Headline: {first_article.get('headline', 'N/A')[:80]}")
        print(f"  Date: {first_article.get('date', 'N/A')}")
        print(f"  Author: {first_article.get('author', 'N/A')}")
        print(f"  Summary length: {len(first_article.get('summary', ''))}")
        print(f"  Body length: {len(first_article.get('body', ''))}")
        
        # Check for empty fields
        empty_fields = [k for k, v in first_article.items() if v == '']
        if empty_fields:
            print(f"  ⚠️  Empty fields: {', '.join(empty_fields)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing {scraper.name}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        scraper.urls = original_urls


def test_orchestrator():
    """Test the orchestrator with limited scraping."""
    print(f"\n{'='*80}")
    print(f"Testing Orchestrator")
    print(f"{'='*80}")
    
    try:
        orchestrator = NewspaperScraperOrchestrator()
        
        # Limit each scraper to first URL only for testing
        for scraper in orchestrator.scrapers:
            scraper.urls = [scraper.urls[0]]
        
        results = orchestrator.scrape_all()
        
        if not results:
            print("⚠️  No articles found by orchestrator")
            return False
        
        print(f"\n✅ Orchestrator successfully scraped {len(results)} total articles")
        
        # Check distribution
        df = orchestrator.to_dataframe()
        print(f"\nArticles per newspaper:")
        print(df['newspaper'].value_counts())
        
        # Test exports
        print(f"\nTesting exports...")
        orchestrator.export_csv("test_news_data.csv")
        orchestrator.export_json("test_news_data.json")
        print(f"✅ Exports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing orchestrator: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*80)
    print("NEWSPAPER SCRAPER V2 - TEST SUITE")
    print("="*80)
    print("\nNote: Testing with limited URLs to avoid long execution times")
    
    results = {}
    
    # Test individual scrapers
    print("\n" + "="*80)
    print("PHASE 1: Testing Individual Scrapers")
    print("="*80)
    
    scrapers = [
        LosAndesScraper(),
        DiarioUnoScraper(),
        ElSolScraper(),
        MDZScraper()
    ]
    
    for scraper in scrapers:
        results[scraper.name] = test_individual_scraper(scraper)
    
    # Test orchestrator
    print("\n" + "="*80)
    print("PHASE 2: Testing Orchestrator")
    print("="*80)
    
    results['Orchestrator'] = test_orchestrator()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check logs above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
