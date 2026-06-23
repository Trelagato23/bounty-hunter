"""
Database module for storing bounty opportunities
"""
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import json
import os


class BountyDatabase:
    def __init__(self, db_path: str = "./data/bounties.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Opportunities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id TEXT UNIQUE,
                platform TEXT NOT NULL,
                type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT NOT NULL,
                reward_min REAL,
                reward_max REAL,
                currency TEXT DEFAULT 'USD',
                deadline TEXT,
                posted_date TEXT,
                discovered_date TEXT NOT NULL,
                last_checked TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                tags TEXT,
                difficulty TEXT,
                requirements TEXT,
                raw_data TEXT
            )
        ''')
        
        # Scraping logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraping_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                items_found INTEGER DEFAULT 0,
                new_items INTEGER DEFAULT 0,
                errors TEXT,
                duration_seconds REAL
            )
        ''')
        
        # Notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id INTEGER,
                notification_type TEXT NOT NULL,
                sent_date TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_opportunity(self, opportunity: Dict) -> bool:
        """Add a new opportunity or update if exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            now = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT OR REPLACE INTO opportunities (
                    external_id, platform, type, title, description, url,
                    reward_min, reward_max, currency, deadline, posted_date,
                    discovered_date, last_checked, status, tags, difficulty,
                    requirements, raw_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                opportunity.get('external_id'),
                opportunity.get('platform'),
                opportunity.get('type'),
                opportunity.get('title'),
                opportunity.get('description'),
                opportunity.get('url'),
                opportunity.get('reward_min'),
                opportunity.get('reward_max'),
                opportunity.get('currency', 'USD'),
                opportunity.get('deadline'),
                opportunity.get('posted_date'),
                opportunity.get('discovered_date', now),
                now,
                opportunity.get('status', 'active'),
                json.dumps(opportunity.get('tags', [])),
                opportunity.get('difficulty'),
                opportunity.get('requirements'),
                json.dumps(opportunity.get('raw_data', {}))
            ))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding opportunity: {e}")
            return False
        finally:
            conn.close()
    
    def get_recent_opportunities(self, days: int = 7, platform: Optional[str] = None) -> List[Dict]:
        """Get opportunities discovered in the last N days"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM opportunities 
            WHERE datetime(discovered_date) > datetime('now', '-' || ? || ' days')
            AND status = 'active'
        '''
        params = [days]
        
        if platform:
            query += ' AND platform = ?'
            params.append(platform)
        
        query += ' ORDER BY discovered_date DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_high_value_opportunities(self, min_reward: float = 1000) -> List[Dict]:
        """Get opportunities with rewards above threshold"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM opportunities 
            WHERE (reward_min >= ? OR reward_max >= ?)
            AND status = 'active'
            ORDER BY reward_max DESC
        ''', (min_reward, min_reward))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_opportunities_by_type(self, opp_type: str) -> List[Dict]:
        """Get opportunities of a specific type"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM opportunities 
            WHERE type = ? AND status = 'active'
            ORDER BY discovered_date DESC
        ''', (opp_type,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def log_scraping(self, platform: str, status: str, items_found: int = 0, 
                     new_items: int = 0, errors: str = None, duration: float = 0):
        """Log a scraping run"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO scraping_logs (
                platform, timestamp, status, items_found, 
                new_items, errors, duration_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            platform,
            datetime.now().isoformat(),
            status,
            items_found,
            new_items,
            errors,
            duration
        ))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total opportunities
        cursor.execute('SELECT COUNT(*) FROM opportunities WHERE status = "active"')
        stats['total_active'] = cursor.fetchone()[0]
        
        # By platform
        cursor.execute('''
            SELECT platform, COUNT(*) as count 
            FROM opportunities 
            WHERE status = 'active'
            GROUP BY platform
        ''')
        stats['by_platform'] = dict(cursor.fetchall())
        
        # By type
        cursor.execute('''
            SELECT type, COUNT(*) as count 
            FROM opportunities 
            WHERE status = 'active'
            GROUP BY type
        ''')
        stats['by_type'] = dict(cursor.fetchall())
        
        # High value (>$10k)
        cursor.execute('''
            SELECT COUNT(*) FROM opportunities 
            WHERE status = 'active' AND (reward_max >= 10000 OR reward_min >= 10000)
        ''')
        stats['high_value'] = cursor.fetchone()[0]
        
        # Last 7 days
        cursor.execute('''
            SELECT COUNT(*) FROM opportunities 
            WHERE status = 'active' 
            AND datetime(discovered_date) > datetime('now', '-7 days')
        ''')
        stats['last_7_days'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def mark_as_closed(self, external_id: str):
        """Mark an opportunity as closed"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE opportunities 
            SET status = 'closed' 
            WHERE external_id = ?
        ''', (external_id,))
        
        conn.commit()
        conn.close()
    
    def search_opportunities(self, keywords: List[str], exclude: List[str] = None) -> List[Dict]:
        """Search opportunities by keywords"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build search query
        include_conditions = []
        for keyword in keywords:
            include_conditions.append(f"(title LIKE '%{keyword}%' OR description LIKE '%{keyword}%')")
        
        query = f'''
            SELECT * FROM opportunities 
            WHERE status = 'active' AND ({' OR '.join(include_conditions)})
        '''
        
        if exclude:
            exclude_conditions = []
            for keyword in exclude:
                exclude_conditions.append(f"(title NOT LIKE '%{keyword}%' AND description NOT LIKE '%{keyword}%')")
            query += f" AND {' AND '.join(exclude_conditions)}"
        
        query += ' ORDER BY discovered_date DESC'
        
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]




