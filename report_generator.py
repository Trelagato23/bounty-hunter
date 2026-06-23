"""
Report generator for bounty opportunities
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict
from database import BountyDatabase


class ReportGenerator:
    """Generates various reports from the database"""
    
    def __init__(self, config: Dict, db: BountyDatabase):
        self.config = config
        self.db = db
        self.reports_dir = config['output']['reports_dir']
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def generate_daily_digest(self):
        """Generate a daily digest of new opportunities"""
        opportunities = self.db.get_recent_opportunities(days=1)
        
        if not opportunities:
            print("No new opportunities in the last 24 hours")
            return
        
        # Sort by reward
        opportunities.sort(key=lambda x: x.get('reward_max') or 0, reverse=True)
        
        report_lines = [
            "# 🎯 Daily Bounty Digest",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            f"## Summary",
            f"- **Total New Opportunities**: {len(opportunities)}",
            f"- **High Value (>$10k)**: {len([o for o in opportunities if (o.get('reward_max') or 0) >= 10000])}",
            "",
            "---",
            ""
        ]
        
        # Group by platform
        by_platform = {}
        for opp in opportunities:
            platform = opp.get('platform', 'unknown')
            if platform not in by_platform:
                by_platform[platform] = []
            by_platform[platform].append(opp)
        
        # Generate sections for each platform
        for platform, opps in sorted(by_platform.items()):
            report_lines.extend([
                f"## {platform.upper().replace('_', ' ')} ({len(opps)})",
                ""
            ])
            
            for opp in opps:
                reward_text = self._format_reward(opp)
                deadline_text = self._format_deadline(opp)
                
                report_lines.extend([
                    f"### {opp['title']}",
                    f"- **Type**: {opp.get('type', 'N/A').replace('_', ' ').title()}",
                    f"- **Reward**: {reward_text}",
                    f"- **Deadline**: {deadline_text}",
                    f"- **URL**: {opp['url']}",
                ])
                
                if opp.get('tags'):
                    tags = ', '.join(opp['tags'][:5]) if isinstance(opp['tags'], list) else opp['tags']
                    report_lines.append(f"- **Tags**: {tags}")
                
                if opp.get('difficulty'):
                    report_lines.append(f"- **Difficulty**: {opp['difficulty']}")
                
                if opp.get('description'):
                    desc = opp['description'][:200]
                    if len(opp['description']) > 200:
                        desc += "..."
                    report_lines.append(f"- **Description**: {desc}")
                
                report_lines.extend(["", "---", ""])
        
        # Top opportunities
        top_opportunities = opportunities[:10]
        if top_opportunities:
            report_lines.extend([
                "",
                "## 🏆 Top 10 Opportunities by Reward",
                ""
            ])
            
            for i, opp in enumerate(top_opportunities, 1):
                reward = self._format_reward(opp)
                report_lines.append(
                    f"{i}. **{opp['title']}** ({opp['platform']}) - {reward} - [Link]({opp['url']})"
                )
        
        # Cursor AI viability assessment
        report_lines.extend([
            "",
            "## 🤖 Cursor AI Viability",
            ""
        ])
        
        high_viability = [o for o in opportunities if o.get('type') in [
            'audit_contest', 'ml_competition', 'bounty', 'hackathon'
        ]]
        
        report_lines.append(f"**High Viability Opportunities**: {len(high_viability)}/{len(opportunities)}")
        report_lines.append("")
        
        for opp in high_viability[:5]:
            report_lines.append(f"- **{opp['title']}** ({opp['platform']}) - {self._format_reward(opp)}")
        
        # Write report
        report_path = os.path.join(self.reports_dir, 'daily_digest.md')
        with open(report_path, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"Daily digest generated: {report_path}")
        
        # Also create a simple text version
        self._create_simple_summary(opportunities)
    
    def generate_weekly_summary(self):
        """Generate a weekly summary"""
        opportunities = self.db.get_recent_opportunities(days=7)
        
        report_lines = [
            "# 📊 Weekly Bounty Summary",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            f"## Statistics",
            f"- **Total Opportunities This Week**: {len(opportunities)}",
            ""
        ]
        
        # Calculate statistics
        total_potential = sum([o.get('reward_max', 0) or 0 for o in opportunities])
        avg_reward = total_potential / len(opportunities) if opportunities else 0
        
        report_lines.extend([
            f"- **Total Potential Rewards**: ${total_potential:,.0f}",
            f"- **Average Reward**: ${avg_reward:,.0f}",
            ""
        ])
        
        # By type
        by_type = {}
        for opp in opportunities:
            opp_type = opp.get('type', 'unknown')
            by_type[opp_type] = by_type.get(opp_type, 0) + 1
        
        report_lines.extend([
            "## By Type",
            ""
        ])
        
        for opp_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"- **{opp_type.replace('_', ' ').title()}**: {count}")
        
        report_lines.append("")
        
        # By platform
        by_platform = {}
        for opp in opportunities:
            platform = opp.get('platform', 'unknown')
            by_platform[platform] = by_platform.get(platform, 0) + 1
        
        report_lines.extend([
            "## By Platform",
            ""
        ])
        
        for platform, count in sorted(by_platform.items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"- **{platform.upper()}**: {count}")
        
        # Write report
        report_path = os.path.join(self.reports_dir, 'weekly_summary.md')
        with open(report_path, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"Weekly summary generated: {report_path}")
    
    def generate_statistics_report(self):
        """Generate a comprehensive statistics report"""
        stats = self.db.get_statistics()
        
        report_lines = [
            "# 📈 Bounty Hunter Statistics",
            f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "## Overall Statistics",
            f"- **Total Active Opportunities**: {stats['total_active']}",
            f"- **High Value (>$10k)**: {stats['high_value']}",
            f"- **Added in Last 7 Days**: {stats['last_7_days']}",
            "",
            "## By Platform",
            ""
        ]
        
        for platform, count in sorted(stats['by_platform'].items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"- **{platform.upper()}**: {count}")
        
        report_lines.extend([
            "",
            "## By Type",
            ""
        ])
        
        for opp_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
            report_lines.append(f"- **{opp_type.replace('_', ' ').title()}**: {count}")
        
        # Write report
        report_path = os.path.join(self.reports_dir, 'statistics.md')
        with open(report_path, 'w') as f:
            f.write('\n'.join(report_lines))
        
        print(f"Statistics report generated: {report_path}")
    
    def _format_reward(self, opp: Dict) -> str:
        """Format reward amount"""
        reward_min = opp.get('reward_min')
        reward_max = opp.get('reward_max')
        currency = opp.get('currency', 'USD')
        
        if reward_max and reward_min and reward_min != reward_max:
            return f"${reward_min:,.0f} - ${reward_max:,.0f} {currency}"
        elif reward_max:
            return f"${reward_max:,.0f} {currency}"
        elif reward_min:
            return f"${reward_min:,.0f} {currency}"
        else:
            return "Unknown"
    
    def _format_deadline(self, opp: Dict) -> str:
        """Format deadline"""
        deadline = opp.get('deadline')
        if not deadline:
            return "Not specified"
        
        try:
            # Try to parse and format
            dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except:
            return str(deadline)
    
    def _create_simple_summary(self, opportunities: List[Dict]):
        """Create a simple text summary for quick viewing"""
        lines = [
            "BOUNTY HUNTER - DAILY SUMMARY",
            "=" * 60,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"New Opportunities: {len(opportunities)}",
            "=" * 60,
            ""
        ]
        
        # Top 10 by reward
        sorted_opps = sorted(opportunities, key=lambda x: x.get('reward_max') or 0, reverse=True)
        
        for i, opp in enumerate(sorted_opps[:10], 1):
            reward = f"${opp.get('reward_max', 0):,.0f}" if opp.get('reward_max') else "?"
            lines.append(f"{i:2}. [{opp['platform']:15}] {reward:12} - {opp['title'][:50]}")
        
        summary_path = os.path.join(self.reports_dir, 'summary.txt')
        with open(summary_path, 'w') as f:
            f.write('\n'.join(lines))
        
        print(f"Simple summary: {summary_path}")




