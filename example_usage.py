#!/usr/bin/env python3
"""
Example usage of Bounty Hunter API
"""

from database import BountyDatabase
from scrapers import ScraperFactory
import yaml


def example_direct_scraping():
    """Example: Directly use a scraper"""
    print("Example 1: Direct Scraping")
    print("-" * 40)
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Create a scraper
    scraper = ScraperFactory.create_scraper('hackerone', config)
    
    # Scrape
    opportunities = scraper.scrape()
    
    print(f"Found {len(opportunities)} opportunities")
    
    # Show first 3
    for opp in opportunities[:3]:
        print(f"\n  {opp['title']}")
        print(f"  Reward: ${opp.get('reward_max', 0):,.0f}")
        print(f"  URL: {opp['url']}")


def example_database_queries():
    """Example: Query the database"""
    print("\n\nExample 2: Database Queries")
    print("-" * 40)
    
    db = BountyDatabase()
    
    # Get high-value opportunities
    high_value = db.get_high_value_opportunities(min_reward=10000)
    print(f"\nHigh-value opportunities (>$10k): {len(high_value)}")
    
    for opp in high_value[:5]:
        print(f"  - {opp['title']} (${opp.get('reward_max', 0):,.0f})")
    
    # Get recent opportunities
    recent = db.get_recent_opportunities(days=7)
    print(f"\nRecent opportunities (last 7 days): {len(recent)}")
    
    # Get by type
    ml_comps = db.get_opportunities_by_type('ml_competition')
    print(f"\nML Competitions: {len(ml_comps)}")
    
    # Search by keywords
    blockchain = db.search_opportunities(['blockchain', 'smart contract'])
    print(f"\nBlockchain opportunities: {len(blockchain)}")
    
    # Statistics
    stats = db.get_statistics()
    print(f"\nTotal active opportunities: {stats['total_active']}")
    print("\nBy platform:")
    for platform, count in sorted(stats['by_platform'].items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {platform}: {count}")


def example_filtering():
    """Example: Filter opportunities"""
    print("\n\nExample 3: Custom Filtering")
    print("-" * 40)
    
    db = BountyDatabase()
    
    # Get all opportunities
    all_opps = db.get_recent_opportunities(days=30)
    
    # Custom filter: High-viability for Cursor AI
    cursor_viable = [
        opp for opp in all_opps
        if opp.get('type') in ['audit_contest', 'ml_competition', 'bounty', 'hackathon']
        and (opp.get('reward_max', 0) or 0) >= 1000
    ]
    
    print(f"Total opportunities: {len(all_opps)}")
    print(f"Cursor AI viable (>$1k): {len(cursor_viable)}")
    
    # Show top 5
    cursor_viable.sort(key=lambda x: x.get('reward_max', 0) or 0, reverse=True)
    
    print("\nTop 5 Cursor-viable opportunities:")
    for i, opp in enumerate(cursor_viable[:5], 1):
        print(f"{i}. {opp['title']}")
        print(f"   Platform: {opp['platform']} | Type: {opp['type']}")
        print(f"   Reward: ${opp.get('reward_max', 0):,.0f}")
        print()


def example_adding_opportunity():
    """Example: Manually add an opportunity"""
    print("\n\nExample 4: Manually Add Opportunity")
    print("-" * 40)
    
    db = BountyDatabase()
    
    # Create a custom opportunity
    opportunity = {
        'external_id': 'custom_test_123',
        'platform': 'custom',
        'type': 'bug_bounty',
        'title': 'Test Custom Opportunity',
        'description': 'This is a test opportunity added manually',
        'url': 'https://example.com/bounty/123',
        'reward_min': 500,
        'reward_max': 5000,
        'currency': 'USD',
        'tags': ['test', 'example'],
        'status': 'active'
    }
    
    # Add to database
    success = db.add_opportunity(opportunity)
    
    if success:
        print("✓ Opportunity added successfully!")
        print(f"  Title: {opportunity['title']}")
        print(f"  Reward: ${opportunity['reward_min']} - ${opportunity['reward_max']}")
    else:
        print("✗ Failed to add opportunity")


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("BOUNTY HUNTER - EXAMPLE USAGE")
    print("=" * 50)
    
    # Run examples
    try:
        # Example 1: Scraping (may fail without internet)
        # example_direct_scraping()
        print("Example 1 skipped (requires internet)")
        
        # Example 2: Database queries
        example_database_queries()
        
        # Example 3: Filtering
        example_filtering()
        
        # Example 4: Adding manually
        example_adding_opportunity()
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("Make sure you've run setup.sh and at least one scrape first!")
    
    print("\n" + "=" * 50)
    print("Examples complete!")
    print("=" * 50)




