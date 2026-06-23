#!/usr/bin/env python3
"""
Main Bounty Hunter application
Scrapes various platforms for bug bounties, competitions, and gig opportunities
"""
import yaml
import os
import sys
import time
from datetime import datetime
from typing import List, Dict
import argparse

from database import BountyDatabase
from scrapers import ScraperFactory
from notifications import NotificationManager
from report_generator import ReportGenerator


class BountyHunter:
    """Main application orchestrator"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self.load_config(config_path)
        self.db = BountyDatabase(self.config['database']['path'])
        self.notification_manager = NotificationManager(self.config)
        self.report_generator = ReportGenerator(self.config, self.db)
        
        # Ensure output directories exist
        for dir_path in [
            self.config['output']['reports_dir'],
            self.config['output']['data_dir'],
            self.config['output']['logs_dir']
        ]:
            os.makedirs(dir_path, exist_ok=True)
    
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def scrape_platform(self, platform_name: str, platform_config: Dict) -> tuple:
        """Scrape a single platform"""
        print(f"\n{'='*60}")
        print(f"Scraping {platform_name.upper()}...")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Create scraper
            scraper = ScraperFactory.create_scraper(platform_name, self.config)
            
            if not scraper:
                print(f"Skipping {platform_name} - no scraper available")
                return 0, 0, "No scraper implemented"
            
            # Scrape opportunities
            opportunities = scraper.scrape()
            
            if not opportunities:
                print(f"No opportunities found on {platform_name}")
                duration = time.time() - start_time
                self.db.log_scraping(platform_name, 'success', 0, 0, None, duration)
                return 0, 0, None
            
            # Filter opportunities
            filtered = self.filter_opportunities(opportunities)
            
            print(f"Found {len(opportunities)} total, {len(filtered)} after filtering")
            
            # Add to database
            new_count = 0
            for opp in filtered:
                if self.db.add_opportunity(opp):
                    new_count += 1
            
            duration = time.time() - start_time
            print(f"Added {new_count} new opportunities ({duration:.2f}s)")
            
            # Log the scraping
            self.db.log_scraping(
                platform_name, 
                'success', 
                len(opportunities), 
                new_count, 
                None, 
                duration
            )
            
            # Send notifications for high-value opportunities
            if new_count > 0:
                self.notify_new_opportunities(filtered)
            
            return len(opportunities), new_count, None
            
        except Exception as e:
            error_msg = str(e)
            print(f"ERROR scraping {platform_name}: {error_msg}")
            duration = time.time() - start_time
            self.db.log_scraping(platform_name, 'error', 0, 0, error_msg, duration)
            return 0, 0, error_msg
    
    def filter_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """Filter opportunities based on config criteria"""
        filters = self.config.get('filters', {})
        min_reward = filters.get('min_reward', 0)
        
        filtered = []
        
        for opp in opportunities:
            # Check minimum reward
            reward_max = opp.get('reward_max')
            if reward_max and reward_max < min_reward:
                continue
            
            # Check keywords (if provided)
            keywords_include = filters.get('keywords_include', [])
            keywords_exclude = filters.get('keywords_exclude', [])
            
            text = f"{opp.get('title', '')} {opp.get('description', '')}".lower()
            
            # Must include at least one keyword if specified
            if keywords_include:
                if not any(kw.lower() in text for kw in keywords_include):
                    continue
            
            # Must not include any excluded keywords
            if keywords_exclude:
                if any(kw.lower() in text for kw in keywords_exclude):
                    continue
            
            filtered.append(opp)
        
        return filtered
    
    def notify_new_opportunities(self, opportunities: List[Dict]):
        """Send notifications for new opportunities"""
        high_value = [
            opp for opp in opportunities 
            if opp.get('reward_max', 0) >= self.config['notifications']['desktop']['min_reward']
        ]
        
        if high_value:
            self.notification_manager.notify_high_value(high_value)
    
    def scrape_all(self, priority: int = None):
        """Scrape all enabled platforms"""
        platforms = self.config.get('platforms', {})
        
        total_found = 0
        total_new = 0
        errors = []
        
        for platform_name, platform_config in platforms.items():
            if not platform_config.get('enabled', False):
                print(f"Skipping {platform_name} (disabled)")
                continue
            
            # Check priority if specified
            if priority and platform_config.get('priority') != priority:
                continue
            
            found, new, error = self.scrape_platform(platform_name, platform_config)
            total_found += found
            total_new += new
            
            if error:
                errors.append(f"{platform_name}: {error}")
            
            # Be nice to servers
            time.sleep(2)
        
        print(f"\n{'='*60}")
        print(f"SCRAPING COMPLETE")
        print(f"{'='*60}")
        print(f"Total opportunities found: {total_found}")
        print(f"New opportunities added: {total_new}")
        
        if errors:
            print(f"\nErrors encountered:")
            for error in errors:
                print(f"  - {error}")
        
        return total_found, total_new
    
    def generate_report(self, report_type: str = 'daily'):
        """Generate a report of opportunities"""
        print(f"\nGenerating {report_type} report...")
        
        if report_type == 'daily':
            self.report_generator.generate_daily_digest()
        elif report_type == 'weekly':
            self.report_generator.generate_weekly_summary()
        elif report_type == 'stats':
            self.report_generator.generate_statistics_report()
        else:
            print(f"Unknown report type: {report_type}")
    
    def show_statistics(self):
        """Display database statistics"""
        stats = self.db.get_statistics()
        
        print(f"\n{'='*60}")
        print("DATABASE STATISTICS")
        print(f"{'='*60}")
        print(f"Total active opportunities: {stats['total_active']}")
        print(f"High value (>$10k): {stats['high_value']}")
        print(f"Added in last 7 days: {stats['last_7_days']}")
        
        print(f"\nBy Platform:")
        for platform, count in sorted(stats['by_platform'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {platform:20} {count:5}")
        
        print(f"\nBy Type:")
        for opp_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {opp_type:20} {count:5}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Bounty Hunter - Automated opportunity scraper')
    parser.add_argument('--scrape', action='store_true', help='Run scraping')
    parser.add_argument('--priority', type=int, choices=[1, 2, 3], help='Only scrape priority N platforms')
    parser.add_argument('--platform', type=str, help='Only scrape specific platform')
    parser.add_argument('--report', type=str, choices=['daily', 'weekly', 'stats'], help='Generate report')
    parser.add_argument('--stats', action='store_true', help='Show statistics')
    parser.add_argument('--config', type=str, default='config.yaml', help='Config file path')
    
    args = parser.parse_args()
    
    # Initialize
    hunter = BountyHunter(args.config)
    
    # Execute commands
    if args.scrape:
        if args.platform:
            platform_config = hunter.config['platforms'].get(args.platform)
            if platform_config:
                hunter.scrape_platform(args.platform, platform_config)
            else:
                print(f"Platform {args.platform} not found in config")
        else:
            hunter.scrape_all(priority=args.priority)
    
    if args.report:
        hunter.generate_report(args.report)
    
    if args.stats:
        hunter.show_statistics()
    
    # If no arguments, show help
    if not (args.scrape or args.report or args.stats):
        parser.print_help()
        print("\nExample usage:")
        print("  python bounty_hunter.py --scrape              # Scrape all platforms")
        print("  python bounty_hunter.py --scrape --priority 1 # Scrape only priority 1")
        print("  python bounty_hunter.py --platform hackerone  # Scrape HackerOne only")
        print("  python bounty_hunter.py --report daily        # Generate daily report")
        print("  python bounty_hunter.py --stats               # Show statistics")


if __name__ == '__main__':
    main()




