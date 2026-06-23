"""
Platform-specific scrapers for bounty opportunities
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import json
import time
import re
from urllib.parse import urljoin


class BaseScraper:
    """Base class for all scrapers"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.headers = {
            'User-Agent': config.get('browser', {}).get('user_agent', 
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
        }
        self.timeout = config.get('browser', {}).get('timeout', 30)
    
    def scrape(self) -> List[Dict]:
        """Override this method in child classes"""
        raise NotImplementedError
    
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a page"""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_reward(self, text: str) -> tuple:
        """Extract min and max reward from text"""
        # Remove currency symbols and commas
        text = text.replace(',', '').replace('$', '').replace('€', '').replace('£', '')
        
        # Look for patterns like "1000-5000" or "up to 10000"
        range_pattern = r'(\d+(?:\.\d+)?)\s*[-–to]\s*(\d+(?:\.\d+)?)'
        single_pattern = r'(\d+(?:\.\d+)?)'
        
        range_match = re.search(range_pattern, text)
        if range_match:
            return float(range_match.group(1)), float(range_match.group(2))
        
        single_match = re.search(single_pattern, text)
        if single_match:
            value = float(single_match.group(1))
            # If it says "up to X", use 0 as min
            if 'up to' in text.lower():
                return 0, value
            return value, value
        
        return None, None


class HackerOneScraper(BaseScraper):
    """Scraper for HackerOne bug bounty programs"""
    
    def scrape(self) -> List[Dict]:
        opportunities = []
        
        try:
            # HackerOne API endpoint with proper headers
            url = "https://hackerone.com/directory/programs.json"
            headers = self.headers.copy()
            headers['Accept'] = 'application/json'
            headers['X-Requested-With'] = 'XMLHttpRequest'
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            for program in data.get('results', []):
                if program.get('submission_state') != 'open':
                    continue
                
                reward_min, reward_max = None, None
                offers_bounties = program.get('offers_bounties', False)
                
                if offers_bounties:
                    # Try to extract bounty range
                    bounty_split = program.get('bounty_splitting', {})
                    if bounty_split:
                        reward_min = bounty_split.get('min', 100)
                        reward_max = bounty_split.get('max', 10000)
                
                opportunity = {
                    'external_id': f"hackerone_{program.get('handle')}",
                    'platform': 'hackerone',
                    'type': 'bug_bounty',
                    'title': program.get('name'),
                    'description': program.get('submission_state'),
                    'url': f"https://hackerone.com/{program.get('handle')}",
                    'reward_min': reward_min,
                    'reward_max': reward_max,
                    'currency': 'USD',
                    'posted_date': program.get('started_accepting_at'),
                    'tags': program.get('targets', [])[:3] if program.get('targets') else [],
                    'raw_data': program
                }
                
                opportunities.append(opportunity)
            
            print(f"HackerOne: Found {len(opportunities)} programs")
            
        except Exception as e:
            print(f"Error scraping HackerOne: {e}")
        
        return opportunities


class ImmunefiScraper(BaseScraper):
    """Scraper for Immunefi blockchain bounties"""
    
    def scrape(self) -> List[Dict]:
        opportunities = []
        
        try:
            url = "https://immunefi.com/bounty/"
            soup = self.get_page(url)
            
            if not soup:
                return opportunities
            
            # Immunefi lists bounties in cards
            bounty_cards = soup.find_all('a', class_=re.compile('bounty|card'))
            
            for card in bounty_cards[:50]:  # Limit to first 50
                try:
                    title_elem = card.find(['h2', 'h3', 'h4'])
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown"
                    
                    link = card.get('href', '')
                    if link and not link.startswith('http'):
                        link = urljoin(url, link)
                    
                    # Try to find reward info
                    reward_text = ''
                    reward_elem = card.find(text=re.compile(r'[$€£]\s*\d+|up to', re.I))
                    if reward_elem:
                        reward_text = reward_elem.strip()
                    
                    reward_min, reward_max = self.extract_reward(reward_text) if reward_text else (None, None)
                    
                    if link and title != "Unknown":
                        opportunity = {
                            'external_id': f"immunefi_{link.split('/')[-1]}",
                            'platform': 'immunefi',
                            'type': 'blockchain_bounty',
                            'title': title,
                            'description': reward_text,
                            'url': link,
                            'reward_min': reward_min,
                            'reward_max': reward_max,
                            'currency': 'USD',
                            'tags': ['blockchain', 'smart contract', 'defi'],
                            'raw_data': {}
                        }
                        opportunities.append(opportunity)
                
                except Exception as e:
                    print(f"Error parsing Immunefi card: {e}")
                    continue
            
            print(f"Immunefi: Found {len(opportunities)} bounties")
            
        except Exception as e:
            print(f"Error scraping Immunefi: {e}")
        
        return opportunities


class KaggleScraper(BaseScraper):
    """Scraper for Kaggle competitions"""
    
    def scrape(self) -> List[Dict]:
        opportunities = []
        
        try:
            # Kaggle public competitions page (HTML scraping)
            url = "https://www.kaggle.com/competitions"
            soup = self.get_page(url)
            
            if not soup:
                return opportunities
            
            # Find competition listings
            # Note: This is a simplified scraper - Kaggle's actual structure may vary
            competition_links = soup.find_all('a', href=re.compile(r'/competitions/[^/]+$'))
            
            for link in competition_links[:30]:  # Limit to 30
                try:
                    title = link.get_text(strip=True)
                    comp_url = urljoin(url, link.get('href', ''))
                    
                    if title and comp_url:
                        opportunity = {
                            'external_id': f"kaggle_{comp_url.split('/')[-1]}",
                            'platform': 'kaggle',
                            'type': 'ml_competition',
                            'title': title,
                            'description': '',
                            'url': comp_url,
                            'tags': ['machine learning', 'data science'],
                            'raw_data': {}
                        }
                        opportunities.append(opportunity)
                except:
                    continue
            
            # Fallback: Try old API method
            if not opportunities:
                url = "https://www.kaggle.com/api/v1/competitions/list"
                try:
                    response = requests.get(url, headers=self.headers, timeout=self.timeout)
                    if response.status_code == 200:
                        data = response.json()
                        
                        for comp in data:
                            if comp.get('reward') and float(comp.get('reward', 0)) > 0:
                                opportunity = {
                                    'external_id': f"kaggle_{comp.get('id')}",
                                    'platform': 'kaggle',
                                    'type': 'ml_competition',
                                    'title': comp.get('title'),
                                    'description': comp.get('description', '')[:500],
                                    'url': f"https://www.kaggle.com/c/{comp.get('url')}",
                                    'reward_min': float(comp.get('reward', 0)),
                                    'reward_max': float(comp.get('reward', 0)),
                                    'currency': 'USD',
                                    'deadline': comp.get('deadline'),
                                    'tags': ['machine learning', 'data science', comp.get('category', '')],
                                    'raw_data': comp
                                }
                                opportunities.append(opportunity)
                except:
                    pass
            
            print(f"Kaggle: Found {len(opportunities)} competitions")
            
        except Exception as e:
            print(f"Error scraping Kaggle: {e}")
        
        return opportunities


class DevpostScraper(BaseScraper):
    """Scraper for Devpost hackathons"""
    
    def scrape(self) -> List[Dict]:
        opportunities = []
        
        try:
            url = "https://devpost.com/api/hackathons"
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            for hackathon in data.get('hackathons', []):
                # Extract prize info
                prizes = hackathon.get('prizes', [])
                total_prize = sum([p.get('amount', 0) for p in prizes])
                
                opportunity = {
                    'external_id': f"devpost_{hackathon.get('id')}",
                    'platform': 'devpost',
                    'type': 'hackathon',
                    'title': hackathon.get('title'),
                    'description': hackathon.get('tagline', ''),
                    'url': hackathon.get('url'),
                    'reward_min': 0,
                    'reward_max': total_prize if total_prize > 0 else None,
                    'currency': 'USD',
                    'deadline': hackathon.get('submission_deadline'),
                    'posted_date': hackathon.get('published_at'),
                    'tags': hackathon.get('themes', [])[:5],
                    'raw_data': hackathon
                }
                opportunities.append(opportunity)
            
            print(f"Devpost: Found {len(opportunities)} hackathons")
            
        except Exception as e:
            # Fallback to HTML scraping
            try:
                url = "https://devpost.com/hackathons"
                soup = self.get_page(url)
                
                if soup:
                    hackathon_items = soup.find_all('div', class_=re.compile('hackathon|challenge'))
                    
                    for item in hackathon_items[:30]:
                        try:
                            title_elem = item.find(['h2', 'h3', 'a'])
                            title = title_elem.get_text(strip=True) if title_elem else None
                            
                            link_elem = item.find('a')
                            link = link_elem.get('href', '') if link_elem else None
                            
                            if title and link:
                                if not link.startswith('http'):
                                    link = urljoin(url, link)
                                
                                opportunity = {
                                    'external_id': f"devpost_{link.split('/')[-1]}",
                                    'platform': 'devpost',
                                    'type': 'hackathon',
                                    'title': title,
                                    'description': '',
                                    'url': link,
                                    'tags': ['hackathon'],
                                    'raw_data': {}
                                }
                                opportunities.append(opportunity)
                        except:
                            continue
                
                print(f"Devpost (HTML): Found {len(opportunities)} hackathons")
                
            except Exception as e2:
                print(f"Error scraping Devpost (fallback): {e2}")
        
        return opportunities


class Code4arenaScraper(BaseScraper):
    """Scraper for Code4rena audit contests"""
    
    def scrape(self) -> List[Dict]:
        opportunities = []
        
        try:
            url = "https://code4rena.com/contests"
            soup = self.get_page(url)
            
            if not soup:
                return opportunities
            
            # Find contest cards
            contests = soup.find_all(['div', 'article'], class_=re.compile('contest|card'))
            
            for contest in contests[:20]:
                try:
                    title_elem = contest.find(['h2', 'h3', 'a'])
                    title = title_elem.get_text(strip=True) if title_elem else None
                    
                    link_elem = contest.find('a')
                    link = link_elem.get('href', '') if link_elem else None
                    
                    if link and not link.startswith('http'):
                        link = urljoin(url, link)
                    
                    # Try to find prize pool
                    prize_text = ''
                    prize_elem = contest.find(text=re.compile(r'\$\s*\d+|prize', re.I))
                    if prize_elem:
                        prize_text = prize_elem.strip()
                    
                    reward_min, reward_max = self.extract_reward(prize_text) if prize_text else (5000, 50000)
                    
                    if title and link:
                        opportunity = {
                            'external_id': f"code4rena_{link.split('/')[-1]}",
                            'platform': 'code4rena',
                            'type': 'audit_contest',
                            'title': title,
                            'description': prize_text,
                            'url': link,
                            'reward_min': reward_min,
                            'reward_max': reward_max,
                            'currency': 'USD',
                            'tags': ['smart contract', 'security audit', 'solidity'],
                            'raw_data': {}
                        }
                        opportunities.append(opportunity)
                
                except Exception as e:
                    print(f"Error parsing Code4rena contest: {e}")
                    continue
            
            print(f"Code4rena: Found {len(opportunities)} contests")
            
        except Exception as e:
            print(f"Error scraping Code4rena: {e}")
        
        return opportunities


class GitcoinScraper(BaseScraper):
    """Scraper for Gitcoin bounties"""
    
    def scrape(self) -> List[Dict]:
        opportunities = []
        
        try:
            # Gitcoin Explorer API
            url = "https://gitcoin.co/api/v0.1/bounties/"
            params = {
                'network': 'mainnet',
                'order_by': '-web3_created',
                'idx_status': 'open'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            for bounty in data:
                try:
                    value_usd = float(bounty.get('value_in_usdt', 0))
                    
                    opportunity = {
                        'external_id': f"gitcoin_{bounty.get('id')}",
                        'platform': 'gitcoin',
                        'type': 'bounty',
                        'title': bounty.get('title'),
                        'description': bounty.get('issue_description', '')[:500],
                        'url': bounty.get('url'),
                        'reward_min': value_usd,
                        'reward_max': value_usd,
                        'currency': 'USD',
                        'deadline': bounty.get('expires_date'),
                        'tags': bounty.get('keywords', '').split(',')[:5] if bounty.get('keywords') else ['web3'],
                        'difficulty': bounty.get('experience_level'),
                        'raw_data': bounty
                    }
                    
                    opportunities.append(opportunity)
                
                except Exception as e:
                    print(f"Error parsing Gitcoin bounty: {e}")
                    continue
            
            print(f"Gitcoin: Found {len(opportunities)} bounties")
            
        except Exception as e:
            print(f"Error scraping Gitcoin: {e}")
        
        return opportunities


class ChallengeGovScraper(BaseScraper):
    """Scraper for Challenge.gov government challenges"""
    
    def scrape(self) -> List[Dict]:
        opportunities = []
        
        try:
            # Challenge.gov website scraping (API seems down)
            url = "https://www.challenge.gov/challenges/"
            soup = self.get_page(url)
            
            if not soup:
                return opportunities
            
            # Find challenge cards
            challenge_cards = soup.find_all(['div', 'article'], class_=re.compile('challenge|card'))
            
            for card in challenge_cards[:30]:
                try:
                    title_elem = card.find(['h2', 'h3', 'h4', 'a'])
                    title = title_elem.get_text(strip=True) if title_elem else None
                    
                    link_elem = card.find('a')
                    link = link_elem.get('href', '') if link_elem else None
                    
                    if link and not link.startswith('http'):
                        link = urljoin(url, link)
                    
                    if title and link:
                        opportunity = {
                            'external_id': f"challengegov_{link.split('/')[-1]}",
                            'platform': 'challenge_gov',
                            'type': 'government_challenge',
                            'title': title,
                            'description': '',
                            'url': link,
                            'tags': ['government'],
                            'raw_data': {}
                        }
                        opportunities.append(opportunity)
                except:
                    continue
            
            print(f"Challenge.gov: Found {len(opportunities)} challenges")
            
        except Exception as e:
            print(f"Error scraping Challenge.gov: {e}")
            
            # Fallback: Try old API
            try:
                url_api = "https://api.challenge.gov/challenges"
                response = requests.get(url_api, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                
                for challenge in data:
                    try:
                        prize_total = challenge.get('prize_total', 0)
                        
                        opportunity = {
                            'external_id': f"challengegov_{challenge.get('id')}",
                            'platform': 'challenge_gov',
                            'type': 'government_challenge',
                            'title': challenge.get('title'),
                            'description': challenge.get('description', '')[:500],
                            'url': challenge.get('url'),
                            'reward_min': 0,
                            'reward_max': prize_total if prize_total else None,
                            'currency': 'USD',
                            'deadline': challenge.get('submission_end'),
                            'posted_date': challenge.get('posted_date'),
                            'tags': challenge.get('agency_name', []) if isinstance(challenge.get('agency_name'), list) else [challenge.get('agency_name', 'government')],
                            'raw_data': challenge
                        }
                        
                        opportunities.append(opportunity)
                    
                    except Exception as e:
                        print(f"Error parsing Challenge.gov item: {e}")
                        continue
                
                print(f"Challenge.gov (API): Found {len(opportunities)} challenges")
            except:
                pass
        
        return opportunities
        
        return opportunities


class ScraperFactory:
    """Factory to create appropriate scraper for each platform"""
    
    SCRAPERS = {
        'hackerone': HackerOneScraper,
        'immunefi': ImmunefiScraper,
        'kaggle': KaggleScraper,
        'devpost': DevpostScraper,
        'code4rena': Code4arenaScraper,
        'gitcoin': GitcoinScraper,
        'challenge_gov': ChallengeGovScraper,
    }
    
    @staticmethod
    def create_scraper(platform: str, config: Dict):
        """Create a scraper instance for the given platform"""
        scraper_class = ScraperFactory.SCRAPERS.get(platform)
        
        if scraper_class:
            return scraper_class(config)
        else:
            print(f"Warning: No scraper implemented for {platform}")
            return None

