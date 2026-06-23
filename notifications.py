"""
Notification system for bounty opportunities
"""
import os
import subprocess
from typing import List, Dict
from datetime import datetime


class NotificationManager:
    """Manages notifications for new opportunities"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.notifications_config = config.get('notifications', {})
        self.enabled = self.notifications_config.get('enabled', False)
    
    def notify_high_value(self, opportunities: List[Dict]):
        """Send notifications for high-value opportunities"""
        if not self.enabled:
            return
        
        methods = self.notifications_config.get('methods', [])
        
        if 'desktop' in methods and self.notifications_config.get('desktop', {}).get('enabled', False):
            self.send_desktop_notifications(opportunities)
        
        if 'email' in methods and self.notifications_config.get('email', {}).get('enabled', False):
            self.send_email_notifications(opportunities)
    
    def send_desktop_notifications(self, opportunities: List[Dict]):
        """Send desktop notifications using notify-send"""
        min_reward = self.notifications_config['desktop'].get('min_reward', 1000)
        
        for opp in opportunities[:5]:  # Limit to 5 notifications
            reward_max = opp.get('reward_max', 0)
            
            if reward_max < min_reward:
                continue
            
            title = f"🎯 New High-Value Opportunity!"
            
            reward_text = f"${reward_max:,.0f}" if reward_max else "Unknown"
            message = (
                f"{opp['title']}\n"
                f"Platform: {opp['platform'].title()}\n"
                f"Reward: {reward_text}\n"
                f"Type: {opp['type']}"
            )
            
            try:
                subprocess.run([
                    'notify-send',
                    title,
                    message,
                    '-u', 'normal',
                    '-t', '10000',  # 10 seconds
                    '-i', 'dialog-information'
                ], check=False)
            except Exception as e:
                print(f"Failed to send desktop notification: {e}")
    
    def send_email_notifications(self, opportunities: List[Dict]):
        """Send email notifications (stub - implement with your email service)"""
        # TODO: Implement email sending using SMTP
        email_config = self.notifications_config.get('email', {})
        
        if not email_config.get('enabled', False):
            return
        
        print("Email notifications not yet implemented")
        # You would implement SMTP email sending here
        pass
    
    def create_summary_text(self, opportunities: List[Dict]) -> str:
        """Create a text summary of opportunities"""
        lines = [
            "New High-Value Opportunities",
            "=" * 50,
            ""
        ]
        
        for opp in opportunities:
            reward_text = f"${opp.get('reward_max', 0):,.0f}" if opp.get('reward_max') else "Unknown"
            
            lines.extend([
                f"Title: {opp['title']}",
                f"Platform: {opp['platform'].title()}",
                f"Type: {opp['type']}",
                f"Reward: {reward_text}",
                f"URL: {opp['url']}",
                ""
            ])
        
        return "\n".join(lines)




