"""
Platform-specific scrapers for bounty opportunities
"""
import json
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class BaseScraper:
    """Base class for all scrapers"""

    def __init__(self, config: Dict):
        self.config = config
        self.headers = {
            "User-Agent": config.get("browser", {}).get(
                "user_agent",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )
        }
        self.timeout = config.get("browser", {}).get("timeout", 30)

    def scrape(self) -> List[Dict]:
        raise NotImplementedError

    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def get_json(self, url: str, params: Optional[Dict] = None):
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching JSON {url}: {e}")
            return None

    def post_json(self, url: str, payload: Dict) -> Optional[Dict]:
        try:
            headers = self.headers.copy()
            headers["Content-Type"] = "application/json"
            headers["Accept"] = "application/json"
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error posting JSON {url}: {e}")
            return None

    @staticmethod
    def parse_money(value) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).replace(",", "").replace("$", "").replace("€", "").replace("£", "").strip()
        match = re.search(r"(\d+(?:\.\d+)?)", text)
        return float(match.group(1)) if match else None

    @staticmethod
    def slugify(text: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
        return slug or "unknown"

    def extract_reward(self, text: str) -> tuple:
        text = text.replace(",", "").replace("$", "").replace("€", "").replace("£", "")
        range_pattern = r"(\d+(?:\.\d+)?)\s*[-–to]\s*(\d+(?:\.\d+)?)"
        single_pattern = r"(\d+(?:\.\d+)?)"

        range_match = re.search(range_pattern, text)
        if range_match:
            return float(range_match.group(1)), float(range_match.group(2))

        single_match = re.search(single_pattern, text)
        if single_match:
            value = float(single_match.group(1))
            if "up to" in text.lower():
                return 0, value
            return value, value

        return None, None


class HackerOneScraper(BaseScraper):
    QUERY = """
    query($first: Int, $after: String) {
      teams(first: $first, after: $after, where: {submission_state: {_eq: open}, offers_bounties: {_eq: true}}) {
        pageInfo { hasNextPage endCursor }
        edges {
          node {
            handle
            name
            base_bounty
            currency
            about
          }
        }
      }
    }
    """

    def scrape(self) -> List[Dict]:
        opportunities = []
        cursor = None

        try:
            for _ in range(8):
                data = self.post_json(
                    "https://hackerone.com/graphql",
                    {"query": self.QUERY, "variables": {"first": 50, "after": cursor}},
                )
                if not data or data.get("errors"):
                    if data and data.get("errors"):
                        print(f"HackerOne GraphQL error: {data['errors'][0].get('message', data['errors'])}")
                    break

                teams = data.get("data", {}).get("teams", {})
                for edge in teams.get("edges", []):
                    program = edge.get("node", {})
                    handle = program.get("handle")
                    if not handle:
                        continue
                    base_bounty = self.parse_money(program.get("base_bounty")) or 100
                    opportunities.append(
                        {
                            "external_id": f"hackerone_{handle}",
                            "platform": "hackerone",
                            "type": "bug_bounty",
                            "title": program.get("name") or handle,
                            "description": (program.get("about") or "")[:500],
                            "url": f"https://hackerone.com/{handle}",
                            "reward_min": base_bounty,
                            "reward_max": max(base_bounty * 10, 1000),
                            "currency": (program.get("currency") or "USD").upper(),
                            "tags": ["security", "bug bounty"],
                            "raw_data": program,
                        }
                    )

                page_info = teams.get("pageInfo", {})
                if not page_info.get("hasNextPage"):
                    break
                cursor = page_info.get("endCursor")

            print(f"HackerOne: Found {len(opportunities)} programs")
        except Exception as e:
            print(f"Error scraping HackerOne: {e}")

        return opportunities


class BugcrowdScraper(BaseScraper):
    def scrape(self) -> List[Dict]:
        opportunities = []
        try:
            data = self.get_json("https://bugcrowd.com/engagements.json")
            if not data:
                return opportunities

            for engagement in data.get("engagements", []):
                if engagement.get("isPrivate") or engagement.get("isDemo"):
                    continue

                name = engagement.get("name")
                url = engagement.get("briefUrl") or engagement.get("subscriptionUrl")
                if not name or not url:
                    continue

                reward = engagement.get("rewardSummary") or {}
                reward_min = self.parse_money(reward.get("minReward"))
                reward_max = self.parse_money(reward.get("maxReward"))
                slug = url.rstrip("/").split("/")[-1]

                opportunities.append(
                    {
                        "external_id": f"bugcrowd_{slug}",
                        "platform": "bugcrowd",
                        "type": "bug_bounty",
                        "title": name,
                        "description": engagement.get("tagline") or reward.get("summary") or "",
                        "url": url,
                        "reward_min": reward_min,
                        "reward_max": reward_max or reward_min,
                        "currency": "USD",
                        "deadline": engagement.get("endsAt"),
                        "tags": ["security", "bug bounty", engagement.get("industryName") or ""],
                        "raw_data": engagement,
                    }
                )

            print(f"Bugcrowd: Found {len(opportunities)} programs")
        except Exception as e:
            print(f"Error scraping Bugcrowd: {e}")

        return opportunities


class IntigritiScraper(BaseScraper):
    def scrape(self) -> List[Dict]:
        opportunities = []
        try:
            programs = self.get_json("https://app.intigriti.com/api/core/public/programs")
            if not isinstance(programs, list):
                return opportunities

            for program in programs:
                if program.get("status") not in (3, 4):
                    continue

                handle = program.get("handle")
                company = program.get("companyHandle") or handle
                name = program.get("name")
                if not handle or not name:
                    continue

                min_bounty = program.get("minBounty") or {}
                max_bounty = program.get("maxBounty") or {}
                reward_min = self.parse_money(min_bounty.get("value"))
                reward_max = self.parse_money(max_bounty.get("value"))
                currency = (max_bounty.get("currency") or min_bounty.get("currency") or "EUR").upper()

                opportunities.append(
                    {
                        "external_id": f"intigriti_{program.get('programId') or handle}",
                        "platform": "intigriti",
                        "type": "bug_bounty",
                        "title": name,
                        "description": (program.get("description") or "")[:500],
                        "url": f"https://app.intigriti.com/programs/{company}/{handle}",
                        "reward_min": reward_min,
                        "reward_max": reward_max or reward_min,
                        "currency": currency,
                        "tags": ["security", "bug bounty", program.get("industry") or ""],
                        "raw_data": program,
                    }
                )

            print(f"Intigriti: Found {len(opportunities)} programs")
        except Exception as e:
            print(f"Error scraping Intigriti: {e}")

        return opportunities


class YesWeHackScraper(BaseScraper):
    def scrape(self) -> List[Dict]:
        opportunities = []
        try:
            page = 1
            while page <= 10:
                data = self.get_json(
                    "https://api.yeswehack.com/programs",
                    params={"page": page, "results_per_page": 42},
                )
                if not data:
                    break

                for program in data.get("items", []):
                    slug = program.get("slug")
                    title = program.get("title")
                    if not slug or not title:
                        continue

                    reward_min = self.parse_money(program.get("bounty_reward_min"))
                    reward_max = self.parse_money(program.get("bounty_reward_max"))

                    opportunities.append(
                        {
                            "external_id": f"yeswehack_{slug}",
                            "platform": "yeswehack",
                            "type": "bug_bounty",
                            "title": title,
                            "description": program.get("description") or "",
                            "url": f"https://yeswehack.com/programs/{slug}",
                            "reward_min": reward_min,
                            "reward_max": reward_max or reward_min,
                            "currency": "EUR",
                            "tags": ["security", "bug bounty", program.get("activity_area") or ""],
                            "raw_data": program,
                        }
                    )

                pagination = data.get("pagination") or {}
                if page >= pagination.get("nb_pages", page):
                    break
                page += 1

            print(f"YesWeHack: Found {len(opportunities)} programs")
        except Exception as e:
            print(f"Error scraping YesWeHack: {e}")

        return opportunities


class ImmunefiScraper(BaseScraper):
    PROJECT_PATTERN = re.compile(r'maxBounty\\":(\d+).*?\\"project\\":\\"([^\\]+)\\"')

    def scrape(self) -> List[Dict]:
        opportunities = []
        try:
            response = requests.get(
                "https://immunefi.com/explore/",
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            seen = set()

            for reward_max_raw, project in self.PROJECT_PATTERN.findall(response.text):
                if project in seen:
                    continue
                seen.add(project)

                reward_max = float(reward_max_raw)
                slug = self.slugify(project)
                opportunities.append(
                    {
                        "external_id": f"immunefi_{slug}",
                        "platform": "immunefi",
                        "type": "blockchain_bounty",
                        "title": f"{project} Immunefi Bounty",
                        "description": f"Web3 bug bounty program with up to ${reward_max:,.0f} max payout.",
                        "url": f"https://immunefi.com/bounty/{slug}/",
                        "reward_min": 1000,
                        "reward_max": reward_max,
                        "currency": "USD",
                        "tags": ["blockchain", "smart contract", "defi", "security"],
                        "raw_data": {"project": project, "maxBounty": reward_max},
                    }
                )

            print(f"Immunefi: Found {len(opportunities)} bounties")
        except Exception as e:
            print(f"Error scraping Immunefi: {e}")

        return opportunities


class KaggleScraper(BaseScraper):
    def scrape(self) -> List[Dict]:
        opportunities = []
        try:
            url = "https://www.kaggle.com/competitions"
            soup = self.get_page(url)
            if soup:
                competition_links = soup.find_all("a", href=re.compile(r"/competitions/[^/]+$"))
                for link in competition_links[:30]:
                    title = link.get_text(strip=True)
                    comp_url = urljoin(url, link.get("href", ""))
                    if title and comp_url:
                        opportunities.append(
                            {
                                "external_id": f"kaggle_{comp_url.split('/')[-1]}",
                                "platform": "kaggle",
                                "type": "ml_competition",
                                "title": title,
                                "description": "",
                                "url": comp_url,
                                "tags": ["machine learning", "data science"],
                                "raw_data": {},
                            }
                        )

            if not opportunities:
                response = requests.get(
                    "https://www.kaggle.com/api/v1/competitions/list",
                    headers=self.headers,
                    timeout=self.timeout,
                )
                if response.status_code == 200:
                    for comp in response.json():
                        reward = self.parse_money(comp.get("reward"))
                        if not reward:
                            continue
                        opportunities.append(
                            {
                                "external_id": f"kaggle_{comp.get('id')}",
                                "platform": "kaggle",
                                "type": "ml_competition",
                                "title": comp.get("title"),
                                "description": comp.get("description", "")[:500],
                                "url": f"https://www.kaggle.com/c/{comp.get('url')}",
                                "reward_min": reward,
                                "reward_max": reward,
                                "currency": "USD",
                                "deadline": comp.get("deadline"),
                                "tags": ["machine learning", "data science", comp.get("category", "")],
                                "raw_data": comp,
                            }
                        )

            print(f"Kaggle: Found {len(opportunities)} competitions")
        except Exception as e:
            print(f"Error scraping Kaggle: {e}")

        return opportunities


class DevpostScraper(BaseScraper):
    def scrape(self) -> List[Dict]:
        opportunities = []
        try:
            response = requests.get(
                "https://devpost.com/api/hackathons",
                headers=self.headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            for hackathon in data.get("hackathons", []):
                prizes = hackathon.get("prizes", [])
                total_prize = sum((p.get("amount") or 0) for p in prizes)

                opportunities.append(
                    {
                        "external_id": f"devpost_{hackathon.get('id')}",
                        "platform": "devpost",
                        "type": "hackathon",
                        "title": hackathon.get("title"),
                        "description": hackathon.get("tagline", ""),
                        "url": hackathon.get("url"),
                        "reward_min": 0,
                        "reward_max": total_prize if total_prize > 0 else None,
                        "currency": "USD",
                        "deadline": hackathon.get("submission_deadline"),
                        "posted_date": hackathon.get("published_at"),
                        "tags": hackathon.get("themes", [])[:5],
                        "raw_data": hackathon,
                    }
                )

            print(f"Devpost: Found {len(opportunities)} hackathons")
        except Exception as e:
            print(f"Error scraping Devpost API: {e}")
            try:
                url = "https://devpost.com/hackathons"
                soup = self.get_page(url)
                if soup:
                    for item in soup.find_all("div", class_=re.compile("hackathon|challenge"))[:30]:
                        title_elem = item.find(["h2", "h3", "a"])
                        title = title_elem.get_text(strip=True) if title_elem else None
                        link_elem = item.find("a")
                        link = link_elem.get("href", "") if link_elem else None
                        if title and link:
                            if not link.startswith("http"):
                                link = urljoin(url, link)
                            opportunities.append(
                                {
                                    "external_id": f"devpost_{link.split('/')[-1]}",
                                    "platform": "devpost",
                                    "type": "hackathon",
                                    "title": title,
                                    "description": "",
                                    "url": link,
                                    "tags": ["hackathon"],
                                    "raw_data": {},
                                }
                            )
                print(f"Devpost (HTML): Found {len(opportunities)} hackathons")
            except Exception as e2:
                print(f"Error scraping Devpost fallback: {e2}")

        return opportunities


class Code4arenaScraper(BaseScraper):
    def scrape(self) -> List[Dict]:
        opportunities = []
        try:
            url = "https://code4rena.com/contests"
            soup = self.get_page(url)
            if not soup:
                return opportunities

            contests = soup.find_all(["div", "article"], class_=re.compile("contest|card"))
            for contest in contests[:20]:
                try:
                    title_elem = contest.find(["h2", "h3", "a"])
                    title = title_elem.get_text(strip=True) if title_elem else None
                    link_elem = contest.find("a")
                    link = link_elem.get("href", "") if link_elem else None
                    if link and not link.startswith("http"):
                        link = urljoin(url, link)

                    prize_text = ""
                    prize_elem = contest.find(string=re.compile(r"\$\s*\d+|prize", re.I))
                    if prize_elem:
                        prize_text = prize_elem.strip()

                    reward_min, reward_max = self.extract_reward(prize_text) if prize_text else (5000, 50000)
                    if title and link:
                        opportunities.append(
                            {
                                "external_id": f"code4rena_{link.split('/')[-1]}",
                                "platform": "code4rena",
                                "type": "audit_contest",
                                "title": title,
                                "description": prize_text,
                                "url": link,
                                "reward_min": reward_min,
                                "reward_max": reward_max,
                                "currency": "USD",
                                "tags": ["smart contract", "security audit", "solidity"],
                                "raw_data": {},
                            }
                        )
                except Exception as e:
                    print(f"Error parsing Code4rena contest: {e}")

            print(f"Code4rena: Found {len(opportunities)} contests")
        except Exception as e:
            print(f"Error scraping Code4rena: {e}")

        return opportunities


class GitcoinScraper(BaseScraper):
    """Legacy Gitcoin bounties are deprecated; fall back to GitHub open bounty issues."""

    def scrape(self) -> List[Dict]:
        opportunities = []
        try:
            response = requests.get(
                "https://api.github.com/search/issues",
                headers={
                    **self.headers,
                    "Accept": "application/vnd.github+json",
                },
                params={
                    "q": "org:gitcoinco label:bounty state:open",
                    "sort": "updated",
                    "per_page": 30,
                },
                timeout=self.timeout,
            )
            if response.status_code != 200:
                print(f"Gitcoin fallback GitHub search failed: {response.status_code}")
                return opportunities

            for item in response.json().get("items", []):
                title = item.get("title")
                url = item.get("html_url")
                if not title or not url:
                    continue
                opportunities.append(
                    {
                        "external_id": f"gitcoin_{item.get('id')}",
                        "platform": "gitcoin",
                        "type": "bounty",
                        "title": title,
                        "description": (item.get("body") or "")[:500],
                        "url": url,
                        "reward_min": None,
                        "reward_max": None,
                        "currency": "USD",
                        "tags": ["web3", "open source", "github"],
                        "raw_data": item,
                    }
                )

            print(f"Gitcoin: Found {len(opportunities)} GitHub bounty issues")
        except Exception as e:
            print(f"Error scraping Gitcoin: {e}")

        return opportunities


class ChallengeGovScraper(BaseScraper):
    def scrape(self) -> List[Dict]:
        opportunities = []
        try:
            url = "https://www.challenge.gov/challenges/"
            soup = self.get_page(url)
            if soup:
                for card in soup.find_all(["div", "article"], class_=re.compile("challenge|card"))[:30]:
                    try:
                        title_elem = card.find(["h2", "h3", "h4", "a"])
                        title = title_elem.get_text(strip=True) if title_elem else None
                        link_elem = card.find("a")
                        link = link_elem.get("href", "") if link_elem else None
                        if link and not link.startswith("http"):
                            link = urljoin(url, link)
                        if title and link:
                            opportunities.append(
                                {
                                    "external_id": f"challengegov_{link.split('/')[-1]}",
                                    "platform": "challenge_gov",
                                    "type": "government_challenge",
                                    "title": title,
                                    "description": "",
                                    "url": link,
                                    "tags": ["government"],
                                    "raw_data": {},
                                }
                            )
                    except Exception:
                        continue

            if not opportunities:
                data = self.get_json("https://api.challenge.gov/challenges")
                if isinstance(data, list):
                    for challenge in data:
                        prize_total = challenge.get("prize_total", 0)
                        opportunities.append(
                            {
                                "external_id": f"challengegov_{challenge.get('id')}",
                                "platform": "challenge_gov",
                                "type": "government_challenge",
                                "title": challenge.get("title"),
                                "description": challenge.get("description", "")[:500],
                                "url": challenge.get("url"),
                                "reward_min": 0,
                                "reward_max": prize_total if prize_total else None,
                                "currency": "USD",
                                "deadline": challenge.get("submission_end"),
                                "posted_date": challenge.get("posted_date"),
                                "tags": [challenge.get("agency_name", "government")],
                                "raw_data": challenge,
                            }
                        )

            print(f"Challenge.gov: Found {len(opportunities)} challenges")
        except Exception as e:
            print(f"Error scraping Challenge.gov: {e}")

        return opportunities


class ScraperFactory:
    SCRAPERS = {
        "hackerone": HackerOneScraper,
        "bugcrowd": BugcrowdScraper,
        "intigriti": IntigritiScraper,
        "yeswehack": YesWeHackScraper,
        "immunefi": ImmunefiScraper,
        "kaggle": KaggleScraper,
        "devpost": DevpostScraper,
        "code4rena": Code4arenaScraper,
        "gitcoin": GitcoinScraper,
        "challenge_gov": ChallengeGovScraper,
    }

    @staticmethod
    def create_scraper(platform: str, config: Dict):
        scraper_class = ScraperFactory.SCRAPERS.get(platform)
        if scraper_class:
            return scraper_class(config)
        print(f"Warning: No scraper implemented for {platform}")
        return None
