# 🎯 Bounty Hunter

An automated scraper and tracker for bug bounties, competitions, and remote gig opportunities.

## Overview

Bounty Hunter monitors multiple platforms for:
- 🐛 Bug bounty programs (HackerOne, Bugcrowd, Immunefi, etc.)
- 🏆 Prize competitions (X Prize, Kaggle, HeroX)
- 💻 Coding challenges (Gitcoin, Devpost, Code4rena)
- 🏛️ Government challenges (Challenge.gov)
- 🌐 Web3 bounties (Immunefi, Code4rena, Sherlock)

**Perfect for AI-assisted development with Cursor!**

## Features

✅ **Automated Scraping** - Daily, weekly, and monthly scraping schedules  
✅ **Smart Filtering** - Filter by reward amount, keywords, and more  
✅ **Database Storage** - SQLite database for tracking opportunities  
✅ **Reports** - Daily digests, weekly summaries, and statistics  
✅ **Notifications** - Desktop notifications for high-value opportunities  
✅ **Cursor AI Ready** - Identifies opportunities perfect for AI-assisted coding  

## Quick Start

### 1. Installation

```bash
cd /home/pjtre/Documents/notes/zk-vault/projects/bounty-hunter

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Make scripts executable
chmod +x bounty_hunter.py scheduler.py
```

### 2. Configuration

Edit `config.yaml` to customize:
- Platforms to scrape
- Scraping schedules
- Filter criteria (minimum rewards, keywords)
- Notification settings

### 3. First Run

```bash
# Scrape all platforms
python bounty_hunter.py --scrape

# Generate daily report
python bounty_hunter.py --report daily

# Show statistics
python bounty_hunter.py --stats
```

### 4. Automated Scheduling

```bash
# Run the scheduler (keeps running)
python scheduler.py

# Or use cron (add to crontab)
0 9 * * * cd /home/pjtre/Documents/notes/zk-vault/projects/bounty-hunter && venv/bin/python bounty_hunter.py --scrape --priority 1 --report daily
0 10 * * 0 cd /home/pjtre/Documents/notes/zk-vault/projects/bounty-hunter && venv/bin/python bounty_hunter.py --scrape --priority 2 --report weekly
```

## Usage

### Command-Line Interface

```bash
# Scrape all platforms
python bounty_hunter.py --scrape

# Scrape only priority 1 platforms (daily)
python bounty_hunter.py --scrape --priority 1

# Scrape a specific platform
python bounty_hunter.py --scrape --platform hackerone

# Generate reports
python bounty_hunter.py --report daily
python bounty_hunter.py --report weekly
python bounty_hunter.py --report stats

# Show statistics
python bounty_hunter.py --stats
```

### Running as a Service

Create a systemd service file at `/etc/systemd/system/bounty-hunter.service`:

```ini
[Unit]
Description=Bounty Hunter Scheduler
After=network.target

[Service]
Type=simple
User=pjtre
WorkingDirectory=/home/pjtre/Documents/notes/zk-vault/projects/bounty-hunter
ExecStart=/home/pjtre/Documents/notes/zk-vault/projects/bounty-hunter/venv/bin/python scheduler.py
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable bounty-hunter
sudo systemctl start bounty-hunter
sudo systemctl status bounty-hunter
```

## Supported Platforms

### Bug Bounty Platforms
- ✅ **HackerOne** - API-based scraping
- ✅ **Immunefi** - Blockchain/DeFi bounties
- ⚠️ **Bugcrowd** - Needs implementation
- ⚠️ **Intigriti** - Needs implementation
- ⚠️ **YesWeHack** - Needs implementation

### Competition Platforms
- ✅ **Kaggle** - Data science competitions
- ✅ **Devpost** - Hackathons
- ✅ **Code4rena** - Smart contract audits
- ✅ **Gitcoin** - Web3 bounties
- ✅ **Challenge.gov** - Government challenges
- ⚠️ **Topcoder** - Needs implementation
- ⚠️ **HeroX** - Needs implementation
- ⚠️ **X Prize** - Needs implementation

**Legend**: ✅ Implemented | ⚠️ Planned

## Database Schema

The SQLite database (`data/bounties.db`) contains:

**opportunities** - All discovered opportunities
- Platform, type, title, description
- Reward range, currency, deadline
- Tags, difficulty, requirements
- Status tracking

**scraping_logs** - History of scraping runs
- Platform, timestamp, status
- Items found, errors, duration

**notifications** - Notification history
- Which opportunities triggered notifications
- When and how they were sent

## Reports

Reports are generated in `./reports/`:

- **daily_digest.md** - Detailed daily report
- **weekly_summary.md** - Weekly statistics
- **statistics.md** - Overall database stats
- **summary.txt** - Quick text summary

## Filtering

Configure in `config.yaml`:

```yaml
filters:
  min_reward: 100  # Minimum reward in USD
  max_age_days: 30  # Only recent opportunities
  keywords_include:
    - "software"
    - "AI"
    - "security"
  keywords_exclude:
    - "on-site only"
    - "hardware required"
```

## Cursor AI Integration

### High Viability Opportunities

Bounty Hunter automatically identifies opportunities ideal for Cursor-assisted development:

1. **Smart Contract Auditing** (Code4rena, Immunefi, Sherlock)
   - Cursor excels at code analysis
   - Pattern recognition for vulnerabilities
   - Automated test generation

2. **Kaggle Competitions**
   - AI-assisted model building
   - Feature engineering
   - Code optimization

3. **Gitcoin Bounties**
   - Well-defined coding tasks
   - Open-source contributions
   - Clear acceptance criteria

4. **Devpost Hackathons**
   - Rapid prototyping
   - Full-stack development
   - AI integration features

### Workflow Example

```bash
# 1. Run scraper
python bounty_hunter.py --scrape --priority 1

# 2. Check daily digest
cat reports/daily_digest.md

# 3. Filter for AI-viable opportunities
cat reports/daily_digest.md | grep -A 10 "Cursor AI Viability"

# 4. Pick an opportunity and use Cursor to:
#    - Analyze requirements
#    - Generate boilerplate code
#    - Find vulnerabilities (bug bounties)
#    - Optimize solutions (competitions)
```

## Notifications

### Desktop Notifications

Automatically shows desktop notifications for high-value opportunities:

```yaml
notifications:
  desktop:
    enabled: true
    min_reward: 1000  # Only notify for $1k+ rewards
```

### Email Notifications (Coming Soon)

```yaml
notifications:
  email:
    enabled: true
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    smtp_user: "your-email@gmail.com"
    smtp_password: "your-app-password"
    recipients:
      - "you@example.com"
```

## Advanced Usage

### Custom Scrapers

Add your own scrapers in `scrapers.py`:

```python
class MyPlatformScraper(BaseScraper):
    def scrape(self) -> List[Dict]:
        opportunities = []
        # Your scraping logic here
        return opportunities

# Register in ScraperFactory
ScraperFactory.SCRAPERS['myplatform'] = MyPlatformScraper
```

### Querying Database Directly

```python
from database import BountyDatabase

db = BountyDatabase()

# Get high-value opportunities
high_value = db.get_high_value_opportunities(min_reward=10000)

# Search by keywords
blockchain = db.search_opportunities(['blockchain', 'smart contract'])

# Get by type
ml_comps = db.get_opportunities_by_type('ml_competition')
```

## Troubleshooting

### No opportunities found

- Check if platforms changed their HTML structure
- Verify internet connection
- Check scraping logs in `logs/`

### Import errors

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Desktop notifications not working

```bash
# Install notify-send (if not already installed)
sudo pacman -S libnotify  # Arch Linux
sudo apt install libnotify-bin  # Ubuntu/Debian
```

## Project Structure

```
bounty-hunter/
├── bounty_hunter.py       # Main application
├── scrapers.py           # Platform scrapers
├── database.py           # Database management
├── notifications.py      # Notification system
├── report_generator.py   # Report generation
├── scheduler.py          # Automated scheduling
├── config.yaml          # Configuration
├── requirements.txt     # Python dependencies
├── data/               # SQLite database
│   └── bounties.db
├── reports/            # Generated reports
│   ├── daily_digest.md
│   ├── weekly_summary.md
│   └── statistics.md
└── logs/              # Scraping logs
```

## Roadmap

### Phase 1 (Current)
- ✅ Core scraping framework
- ✅ Database storage
- ✅ Basic reporting
- ✅ Desktop notifications

### Phase 2 (In Progress)
- ⏳ Complete all platform scrapers
- ⏳ Email notifications
- ⏳ Web dashboard
- ⏳ ML-based opportunity ranking

### Phase 3 (Planned)
- 📋 Browser extension
- 📋 Mobile app
- 📋 Team collaboration features
- 📋 Automatic application submission

## Contributing

Want to add more platforms or features? Pull requests welcome!

### Adding a New Platform

1. Add platform config to `config.yaml`
2. Create scraper class in `scrapers.py`
3. Register in `ScraperFactory.SCRAPERS`
4. Test: `python bounty_hunter.py --platform yourplatform`

## Resources

- **Platform Report**: See `BOUNTY_PLATFORMS_REPORT.md` for detailed analysis
- **Learning**: HackTheBox, TryHackMe, Ethernaut
- **Communities**: Twitter Security, Discord servers, r/bugbounty
- **Tools**: Burp Suite, Slither, Cursor AI

## License

MIT License - Use freely for personal or commercial projects

## Support

For issues or questions:
- Check `BOUNTY_PLATFORMS_REPORT.md` for platform details
- Review logs in `logs/`
- Check database with `python bounty_hunter.py --stats`

---

**Happy Bounty Hunting! 🎯**

*Built with ❤️ and Cursor AI*




