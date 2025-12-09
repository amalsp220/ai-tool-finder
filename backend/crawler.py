"""Web crawler for toolify.ai that respects robots.txt and crawl delay."""

import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import logging
import os
from dotenv import load_dotenv
from database import SessionLocal, init_db
from models import Tool, Category
import xml.etree.ElementTree as ET

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "https://www.toolify.ai"
CRAWL_DELAY = int(os.getenv("CRAWL_DELAY", 5))  # Default 5 seconds from robots.txt
MAX_TOOLS = int(os.getenv("MAX_TOOLS", 1000))
USER_AGENT = "AIToolFinderBot/1.0 (+https://github.com/amalsp220/ai-tool-finder)"

class ToolifyCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.robot_parser = RobotFileParser()
        self.robot_parser.set_url(f"{BASE_URL}/robots.txt")
        self.robot_parser.read()
        self.tools_crawled = 0
        self.last_request_time = 0
        
    def can_fetch(self, url):
        """Check if URL can be fetched according to robots.txt"""
        return self.robot_parser.can_fetch(USER_AGENT, url)
    
    def respect_crawl_delay(self):
        """Respect the crawl delay from robots.txt"""
        elapsed = time.time() - self.last_request_time
        if elapsed < CRAWL_DELAY:
            time.sleep(CRAWL_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def fetch_url(self, url):
        """Fetch URL with proper delay and error handling"""
        if not self.can_fetch(url):
            logger.warning(f"Robots.txt disallows: {url}")
            return None
        
        self.respect_crawl_delay()
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def get_sitemap_urls(self):
        """Get URLs from toolify.ai sitemaps"""
        sitemap_url = f"{BASE_URL}/sitemap.xml"
        response = self.fetch_url(sitemap_url)
        
        if not response:
            return []
        
        tool_sitemaps = []
        try:
            root = ET.fromstring(response.content)
            for sitemap in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
                url = sitemap.text
                # Only get tool sitemaps (sitemap_tools_1.xml through sitemap_tools_4.xml)
                if "sitemap_tools_" in url:
                    tool_sitemaps.append(url)
        except ET.ParseError as e:
            logger.error(f"Error parsing sitemap: {e}")
        
        return tool_sitemaps[:4]  # Only first 4 tool sitemaps
    
    def extract_tool_urls_from_sitemap(self, sitemap_url):
        """Extract individual tool URLs from a sitemap"""
        response = self.fetch_url(sitemap_url)
        
        if not response:
            return []
        
        tool_urls = []
        try:
            root = ET.fromstring(response.content)
            for url in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
                tool_urls.append(url.text)
        except ET.ParseError as e:
            logger.error(f"Error parsing sitemap {sitemap_url}: {e}")
        
        return tool_urls
    
    def extract_tool_data(self, url, html):
        """Extract tool information from HTML"""
        soup = BeautifulSoup(html, 'lxml')
        
        tool_data = {
            'url': url,
            'name': '',
            'description': '',
            'pricing': 'Unknown',
            'categories': [],
            'features': [],
            'rating': None
        }
        
        # Extract tool name (from h1 or title)
        title_tag = soup.find('h1') or soup.find('title')
        if title_tag:
            tool_data['name'] = title_tag.get_text(strip=True)
        
        # Extract description (from meta description or first paragraph)
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            tool_data['description'] = meta_desc['content']
        else:
            first_p = soup.find('p')
            if first_p:
                tool_data['description'] = first_p.get_text(strip=True)[:500]
        
        # Extract categories (from links or tags)
        category_links = soup.find_all('a', class_=lambda x: x and ('category' in x.lower() or 'tag' in x.lower()))
        tool_data['categories'] = [link.get_text(strip=True) for link in category_links[:5]]
        
        # Extract pricing info
        pricing_text = soup.find(text=lambda t: t and any(word in t.lower() for word in ['free', 'paid', 'pricing', 'price']))
        if pricing_text:
            parent = pricing_text.find_parent()
            if parent:
                tool_data['pricing'] = parent.get_text(strip=True)[:100]
        
        return tool_data
    
    def save_tool(self, tool_data, db):
        """Save tool to database"""
        try:
            # Check if tool already exists
            existing = db.query(Tool).filter(Tool.url == tool_data['url']).first()
            if existing:
                logger.info(f"Tool already exists: {tool_data['name']}")
                return
            
            # Create tool
            tool = Tool(
                name=tool_data['name'],
                description=tool_data['description'],
                url=tool_data['url'],
                pricing=tool_data['pricing'],
                rating=tool_data.get('rating')
            )
            
            # Add categories
            for cat_name in tool_data['categories']:
                category = db.query(Category).filter(Category.name == cat_name).first()
                if not category:
                    category = Category(name=cat_name)
                    db.add(category)
                tool.categories.append(category)
            
            db.add(tool)
            db.commit()
            logger.info(f"Saved tool: {tool_data['name']}")
            self.tools_crawled += 1
            
        except Exception as e:
            logger.error(f"Error saving tool {tool_data.get('name', 'Unknown')}: {e}")
            db.rollback()
    
    def crawl(self):
        """Main crawl function"""
        logger.info("Starting crawl of toolify.ai...")
        logger.info(f"Respecting {CRAWL_DELAY} second crawl delay")
        
        # Initialize database
        init_db()
        db = SessionLocal()
        
        try:
            # Get sitemaps
            sitemap_urls = self.get_sitemap_urls()
            logger.info(f"Found {len(sitemap_urls)} tool sitemaps")
            
            for sitemap_url in sitemap_urls:
                if self.tools_crawled >= MAX_TOOLS:
                    logger.info(f"Reached maximum of {MAX_TOOLS} tools")
                    break
                
                logger.info(f"Processing sitemap: {sitemap_url}")
                tool_urls = self.extract_tool_urls_from_sitemap(sitemap_url)
                logger.info(f"Found {len(tool_urls)} tool URLs in sitemap")
                
                for tool_url in tool_urls:
                    if self.tools_crawled >= MAX_TOOLS:
                        break
                    
                    response = self.fetch_url(tool_url)
                    if response:
                        tool_data = self.extract_tool_data(tool_url, response.text)
                        if tool_data['name']:
                            self.save_tool(tool_data, db)
            
            logger.info(f"Crawl complete. Total tools crawled: {self.tools_crawled}")
            
        finally:
            db.close()

if __name__ == "__main__":
    crawler = ToolifyCrawler()
    crawler.crawl()
