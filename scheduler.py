#!/usr/bin/env python3
"""
Scheduler for automated bounty scraping
"""
import schedule
import time
import yaml
from datetime import datetime
from bounty_hunter import BountyHunter


def load_config(config_path: str = "config.yaml"):
    """Load configuration"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def scrape_priority_1(hunter):
    """Scrape priority 1 platforms (daily)"""
    print(f"\n{'='*60}")
    print(f"SCHEDULED SCRAPE - PRIORITY 1 (DAILY)")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    hunter.scrape_all(priority=1)
    hunter.generate_report('daily')


def scrape_priority_2(hunter):
    """Scrape priority 2 platforms (weekly)"""
    print(f"\n{'='*60}")
    print(f"SCHEDULED SCRAPE - PRIORITY 2 (WEEKLY)")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    hunter.scrape_all(priority=2)
    hunter.generate_report('weekly')


def scrape_priority_3(hunter):
    """Scrape priority 3 platforms (monthly)"""
    print(f"\n{'='*60}")
    print(f"SCHEDULED SCRAPE - PRIORITY 3 (MONTHLY)")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    hunter.scrape_all(priority=3)


def main():
    """Main scheduler loop"""
    print("Starting Bounty Hunter Scheduler...")
    
    # Initialize
    hunter = BountyHunter()
    
    # Schedule jobs
    schedule.every().day.at("09:00").do(scrape_priority_1, hunter)
    schedule.every().sunday.at("10:00").do(scrape_priority_2, hunter)
    schedule.every(30).days.at("11:00").do(scrape_priority_3, hunter)
    
    print("\nScheduled jobs:")
    print("  - Priority 1 (daily): Every day at 09:00")
    print("  - Priority 2 (weekly): Every Sunday at 10:00")
    print("  - Priority 3 (monthly): Every 30 days at 11:00")
    print("\nScheduler is running. Press Ctrl+C to stop.")
    
    # Run an initial scrape
    print("\nRunning initial scrape...")
    scrape_priority_1(hunter)
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScheduler stopped by user.")
    except Exception as e:
        print(f"\n\nScheduler error: {e}")




