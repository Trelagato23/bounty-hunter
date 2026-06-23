# 🚀 Bounty Hunter - Quick Start Guide

## 5-Minute Setup

### Step 1: Run Setup Script

```bash
cd /home/pjtre/Documents/notes/zk-vault/projects/bounty-hunter
chmod +x setup.sh
./setup.sh
```

### Step 2: First Scrape

```bash
source venv/bin/activate
python bounty_hunter.py --scrape --priority 1
```

This will scrape the highest priority platforms (usually completes in 2-3 minutes).

### Step 3: View Results

```bash
# Quick text summary
cat reports/summary.txt

# Full report
cat reports/daily_digest.md

# Database stats
python bounty_hunter.py --stats
```

## What Gets Scraped?

### Priority 1 (Daily) ⭐⭐⭐
These are scraped by default and have the best opportunities:

- **HackerOne** - Bug bounties ($500 - $1M+)
- **Immunefi** - Blockchain bounties ($1K - $10M)
- **Kaggle** - ML competitions ($5K - $1M)
- **Devpost** - Hackathons ($500 - $500K)
- **Code4rena** - Smart contract audits ($5K - $500K)
- **Gitcoin** - Web3 bounties ($50 - $100K)

### Priority 2 (Weekly) ⭐⭐
Scraped weekly for less frequent updates:

- **Challenge.gov** - Government challenges ($10K - $10M)
- **Topcoder** - Coding challenges ($100 - $50K)
- **HeroX** - Innovation competitions ($1K - $1M)
- **X Prize** - Grand challenges ($1M - $100M)

## Understanding the Reports

### Daily Digest (`reports/daily_digest.md`)
- Formatted markdown with all new opportunities
- Grouped by platform
- Top 10 by reward amount
- Cursor AI viability assessment

### Summary (`reports/summary.txt`)
- Quick text format
- Top 10 opportunities by reward
- Easy to view in terminal

### Statistics
```bash
python bounty_hunter.py --stats
```
Shows:
- Total active opportunities
- Breakdown by platform
- Breakdown by type
- Recent additions

## Filtering Results

Edit `config.yaml`:

```yaml
filters:
  min_reward: 100          # Only show $100+ rewards
  keywords_include:
    - "remote"
    - "software"
    - "AI"
```

Then re-run the scraper to apply filters.

## Best Opportunities for Cursor AI

After scraping, check the "Cursor AI Viability" section in reports:

### ✅ HIGHEST VIABILITY
1. **Smart Contract Auditing** (Code4rena, Immunefi)
   - $5K - $500K per contest
   - Cursor excels at code analysis
   - Clear vulnerability patterns

2. **Kaggle Competitions** (Kaggle)
   - $5K - $1M prizes
   - AI-assisted model building
   - Data analysis automation

3. **Web3 Bounties** (Gitcoin)
   - $50 - $100K per task
   - Well-defined requirements
   - Open-source contributions

4. **Hackathons** (Devpost)
   - $500 - $500K prizes
   - Rapid prototyping
   - 24-72 hour sprints

### ⚠️ MEDIUM VIABILITY
- Traditional bug bounties (need security expertise)
- Government challenges (varies by domain)

## Automation

### Option 1: Cron Job

```bash
# Edit crontab
crontab -e

# Add this line (scrape daily at 9 AM)
0 9 * * * cd /home/pjtre/Documents/notes/zk-vault/projects/bounty-hunter && venv/bin/python bounty_hunter.py --scrape --priority 1 --report daily
```

### Option 2: Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/bounty-hunter.service

# Paste from README.md, then:
sudo systemctl daemon-reload
sudo systemctl enable bounty-hunter
sudo systemctl start bounty-hunter
```

### Option 3: Manual Scheduler

```bash
# Run the built-in scheduler
python scheduler.py
```

This keeps running and scrapes on schedule.

## Desktop Notifications

Get notified for high-value opportunities ($1K+):

1. Make sure `notify-send` is installed:
```bash
# Arch Linux
sudo pacman -S libnotify

# Ubuntu/Debian
sudo apt install libnotify-bin
```

2. Enable in `config.yaml`:
```yaml
notifications:
  desktop:
    enabled: true
    min_reward: 1000  # $1K minimum
```

3. Run scraper - you'll get notifications automatically!

## Typical Workflow

### Morning Routine (5 minutes)
```bash
# 1. Quick scrape
python bounty_hunter.py --scrape --priority 1

# 2. Check summary
cat reports/summary.txt

# 3. Read full digest if interesting
cat reports/daily_digest.md | less
```

### Weekly Review (15 minutes)
```bash
# 1. Scrape all platforms
python bounty_hunter.py --scrape

# 2. Generate weekly report
python bounty_hunter.py --report weekly

# 3. Review statistics
python bounty_hunter.py --stats

# 4. Open promising opportunities in browser
# (URLs are in the reports)
```

### Targeting an Opportunity
```bash
# 1. Search database for specific type
python -c "from database import BountyDatabase; \
  db = BountyDatabase(); \
  opps = db.get_opportunities_by_type('audit_contest'); \
  print(f'Found {len(opps)} audit contests')"

# 2. Use Cursor to analyze requirements
# 3. Build solution with AI assistance
# 4. Submit and profit! 💰
```

## Common Commands

```bash
# Scrape everything
python bounty_hunter.py --scrape

# Scrape just HackerOne
python bounty_hunter.py --platform hackerone --scrape

# High priority only (fast)
python bounty_hunter.py --scrape --priority 1

# Generate reports
python bounty_hunter.py --report daily
python bounty_hunter.py --report weekly

# Check what's in database
python bounty_hunter.py --stats

# Run scheduler
python scheduler.py
```

## Troubleshooting

### "No module named..."
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "No opportunities found"
- Check your internet connection
- Some platforms may have changed HTML structure
- Try a different platform: `python bounty_hunter.py --platform kaggle --scrape`

### Notifications not showing
```bash
# Test notify-send
notify-send "Test" "If you see this, notifications work!"

# If it doesn't work, install:
sudo pacman -S libnotify  # Arch
sudo apt install libnotify-bin  # Ubuntu
```

## Next Steps

1. ✅ Complete setup
2. ✅ Run first scrape
3. ✅ Review reports
4. ⏳ Set up automation (cron or systemd)
5. ⏳ Start hunting bounties!
6. ⏳ Make money! 💰

## Pro Tips

🔥 **High ROI Targets**: Smart contract audits (Code4rena, Immunefi) have the best reward/effort ratio

🤖 **Use Cursor**: Let AI handle boilerplate, focus on unique logic

⏰ **Be Quick**: Many platforms are first-come-first-served

📚 **Learn as You Go**: Start with easier bounties to build skills

🎯 **Specialize**: Pick 2-3 platforms and become an expert

💰 **Volume + Quality**: Apply to many, but do quality work

## Resources

- **Full Documentation**: See `README.md`
- **Platform Details**: See `BOUNTY_PLATFORMS_REPORT.md`
- **Config Options**: Edit `config.yaml`

---

**Happy Hunting! 🎯**




