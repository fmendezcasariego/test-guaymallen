"""
Modular Newspaper Scraper v2
Supports multiple Mendoza news portals with OOP architecture.

Author: Refactored from original newpapers_scrapping.ipynb
Date: 2026-01-20
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import requests
from lxml import html
import json
import time
import pandas as pd
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

SCRAPER_CONFIG = {
    "request_delay": 1,  # seconds between requests
    "portal_delay": 2,   # seconds between portals
    "headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    },
    "timeout": 10,
    "portals": {
        "Los Andes": [
            "https://www.losandes.com.ar/temas/mendoza",
            "https://www.losandes.com.ar/temas/mendoza/1",
            "https://www.losandes.com.ar/temas/mendoza/2"
        ],
        "Diario UNO": ["https://www.diariouno.com.ar/politica"],
        "El Sol": ["https://www.elsol.com.ar/mendoza/"],
        "MDZ": ["https://www.mdzol.com/politica"]
    }
}


# ============================================================================
# Base Abstract Class
# ============================================================================

class BaseNewspaperScraper(ABC):
    """
    Abstract base class for newspaper scrapers.
    Each concrete scraper must implement portal-specific extraction logic.
    """
    
    def __init__(self, name: str, urls: List[str]):
        """
        Initialize the scraper.
        
        Args:
            name: Name of the newspaper
            urls: List of URLs to scrape
        """
        self.name = name
        self.urls = urls
        self.headers = SCRAPER_CONFIG["headers"]
        self.timeout = SCRAPER_CONFIG["timeout"]
        self.request_delay = SCRAPER_CONFIG["request_delay"]
        
    def get_tree(self, url: str) -> Optional[html.HtmlElement]:
        """
        Fetch and parse HTML from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Parsed HTML tree or None if error
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                # Explicitly decode content as UTF-8 to handle special characters
                return html.fromstring(response.content.decode('utf-8'))
            else:
                logger.warning(f"HTTP {response.status_code} for {url}")
        except Exception as e:
            logger.error(f"Error loading {url}: {e}")
        return None
    
    @abstractmethod
    def extract_article_links(self, tree: html.HtmlElement, base_url: str) -> List[str]:
        """
        Extract article links from a listing page.
        
        Args:
            tree: Parsed HTML tree
            base_url: Base URL for resolving relative links
            
        Returns:
            List of article URLs
        """
        pass
    
    @abstractmethod
    def extract_article_data(self, tree: html.HtmlElement, url: str) -> Dict[str, str]:
        """
        Extract article data from an article page.
        
        Args:
            tree: Parsed HTML tree
            url: Article URL
            
        Returns:
            Dictionary with keys: headline, summary, body, date, author
        """
        pass
    
    def scrape(self) -> Dict[str, Dict[str, str]]:
        """
        Main scraping method that orchestrates the entire process.
        
        Returns:
            Dictionary mapping article URLs to their data
        """
        results = {}
        
        logger.info(f"Starting scrape for {self.name}")
        
        for page_url in self.urls:
            logger.info(f"Scraping listing page: {page_url}")
            
            # Get listing page
            tree_main = self.get_tree(page_url)
            if tree_main is None:
                logger.warning(f"Skipping {page_url} - failed to load")
                continue
            
            time.sleep(self.request_delay)
            
            # Extract article links
            try:
                article_links = self.extract_article_links(tree_main, page_url)
                logger.info(f"Found {len(article_links)} articles on {page_url}")
            except Exception as e:
                logger.error(f"Error extracting links from {page_url}: {e}")
                continue
            
            # Scrape each article
            for article_url in article_links:
                if article_url in results:
                    logger.debug(f"Skipping duplicate: {article_url}")
                    continue
                
                logger.debug(f"Scraping article: {article_url}")
                
                # Get article page
                tree_article = self.get_tree(article_url)
                if tree_article is None:
                    logger.warning(f"Skipping {article_url} - failed to load")
                    continue
                
                time.sleep(self.request_delay)
                
                # Extract article data
                try:
                    article_data = self.extract_article_data(tree_article, article_url)
                    article_data["newspaper"] = self.name
                    article_data["scraped_at"] = datetime.now().isoformat()
                    results[article_url] = article_data
                    logger.debug(f"Successfully scraped: {article_data.get('headline', 'N/A')[:50]}")
                except Exception as e:
                    logger.error(f"Error extracting data from {article_url}: {e}")
                    continue
        
        logger.info(f"Completed scrape for {self.name}: {len(results)} articles")
        return results


# ============================================================================
# Concrete Scraper Implementations
# ============================================================================

class LosAndesScraper(BaseNewspaperScraper):
    """Scraper for Los Andes newspaper (preserves original XPath logic)."""
    
    def __init__(self):
        super().__init__("Los Andes", SCRAPER_CONFIG["portals"]["Los Andes"])
    
    def extract_article_links(self, tree: html.HtmlElement, base_url: str) -> List[str]:
        """Extract article links from Los Andes listing page."""
        links = []
        
        try:
            main_container = tree.xpath('/html/body/main/div[1]/div[1]')
            if not main_container:
                return links
            
            row_grouper_news = main_container[0].xpath(
                './/section[contains(@class, "grouper-simple-news") and contains(@class, "news-article-wrapper")]'
            )
            
            for grouper in row_grouper_news:
                cols_news = grouper.xpath('.//div[contains(@class, "col") and contains(@class, "col-lg-4")]')
                
                for col in cols_news:
                    href_list = col.xpath('.//a/@href')
                    if href_list:
                        full_link = href_list[0]
                        if not full_link.startswith('http'):
                            full_link = f"https://www.losandes.com.ar{full_link}"
                        links.append(full_link)
        except Exception as e:
            logger.error(f"Error in extract_article_links for Los Andes: {e}")
        
        return links
    
    def extract_article_data(self, tree: html.HtmlElement, url: str) -> Dict[str, str]:
        """Extract article data from Los Andes article page."""
        data = {
            "headline": "",
            "summary": "",
            "body": "",
            "date": "",
            "author": ""
        }
        
        try:
            article_root = tree.xpath('/html/body/main/div[2]/div[1]')[0]
            
            # Headline
            try:
                headlines = article_root.xpath('./header/h1/text()')
                if headlines:
                    data["headline"] = headlines[0].strip()
            except Exception as e:
                logger.debug(f"Error extracting headline: {e}")
            
            # Summary
            try:
                topics_date = article_root.xpath('./div[1]/p//text()')
                data["summary"] = " ".join(topics_date).strip()
            except Exception as e:
                logger.debug(f"Error extracting summary: {e}")
            
            # Date
            try:
                news_date_elements = article_root.xpath('./header/div/span/text()')
                if news_date_elements:
                    data["date"] = news_date_elements[0].strip()
            except Exception as e:
                logger.debug(f"Error extracting date: {e}")
            
            # Author
            try:
                author_elements = article_root.xpath('./div[3]/div[1]/div[1]/div/div[2]/div/div/a/b/text()')
                if author_elements:
                    data["author"] = author_elements[0].strip()
            except Exception as e:
                logger.debug(f"Error extracting author: {e}")
            
            # Body
            try:
                body_divs = article_root.xpath('./div[3]')
                if body_divs:
                    body_article_texts = body_divs[0].xpath('.//article[starts-with(@class, "article-body")]//text()')
                    concatenated_text = " ".join([text.strip() for text in body_article_texts if text.strip()])
                    data["body"] = concatenated_text.strip()
            except Exception as e:
                logger.debug(f"Error extracting body: {e}")
        
        except Exception as e:
            logger.error(f"Error in extract_article_data for Los Andes: {e}")
        
        return data


class DiarioUnoScraper(BaseNewspaperScraper):
    """Scraper for Diario UNO newspaper."""
    
    def __init__(self):
        super().__init__("Diario UNO", SCRAPER_CONFIG["portals"]["Diario UNO"])
    
    def extract_article_links(self, tree: html.HtmlElement, base_url: str) -> List[str]:
        """Extract article links from Diario UNO listing page."""
        links = []
        
        try:
            # Get all article elements and extract the first link from each
            articles = tree.xpath('//article')
            for article in articles:
                href_list = article.xpath('.//a/@href')
                if href_list:
                    link = href_list[0]
                    if link.startswith('http'):
                        links.append(link)
        except Exception as e:
            logger.error(f"Error in extract_article_links for Diario UNO: {e}")
        
        return links
    
    def extract_article_data(self, tree: html.HtmlElement, url: str) -> Dict[str, str]:
        """Extract article data from Diario UNO article page."""
        data = {
            "headline": "",
            "summary": "",
            "body": "",
            "date": "",
            "author": ""
        }
        
        try:
            # Headline
            try:
                headline_elements = tree.xpath('//h1[contains(@class, "title")]/text()')
                if headline_elements:
                    data["headline"] = headline_elements[0].strip()
            except Exception as e:
                logger.debug(f"Error extracting headline: {e}")
            
            # Summary (try h2 first, then p.ignore-parser)
            try:
                summary_elements = tree.xpath('//h2/text()')
                if not summary_elements:
                    summary_elements = tree.xpath('//p[contains(@class, "ignore-parser")]/text()')
                if summary_elements:
                    data["summary"] = summary_elements[0].strip()
            except Exception as e:
                logger.debug(f"Error extracting summary: {e}")
            
            # Body
            try:
                body_texts = tree.xpath('//div[contains(@class, "article-body")]//p/text()')
                data["body"] = " ".join([text.strip() for text in body_texts if text.strip()])
            except Exception as e:
                logger.debug(f"Error extracting body: {e}")
            
            # Date
            try:
                date_elements = tree.xpath('//time/text()')
                if date_elements:
                    data["date"] = date_elements[0].strip()
            except Exception as e:
                logger.debug(f"Error extracting date: {e}")
            
            # Author
            try:
                author_elements = tree.xpath('//span[contains(@class, "author-name")]/text()')
                if author_elements:
                    data["author"] = author_elements[0].strip()
            except Exception as e:
                logger.debug(f"Error extracting author: {e}")
        
        except Exception as e:
            logger.error(f"Error in extract_article_data for Diario UNO: {e}")
        
        return data


class ElSolScraper(BaseNewspaperScraper):
    """Scraper for El Sol newspaper."""
    
    def __init__(self):
        super().__init__("El Sol", SCRAPER_CONFIG["portals"]["El Sol"])
    
    def extract_article_links(self, tree: html.HtmlElement, base_url: str) -> List[str]:
        """Extract article links from El Sol listing page."""
        links = []
        
        try:
            # Extract links from h2 and h3 article titles
            link_elements = tree.xpath('//article//h2/a/@href | //article//h3/a/@href')
            links = [link for link in link_elements if link.startswith('http')]
        except Exception as e:
            logger.error(f"Error in extract_article_links for El Sol: {e}")
        
        return links
    
    def extract_article_data(self, tree: html.HtmlElement, url: str) -> Dict[str, str]:
        """Extract article data from El Sol article page."""
        data = {
            "headline": "",
            "summary": "",
            "body": "",
            "date": "",
            "author": ""
        }
        
        try:
            # Headline
            try:
                headline_elements = tree.xpath('//h1/text()')
                if headline_elements:
                    data["headline"] = headline_elements[0].strip()
            except Exception as e:
                logger.debug(f"Error extracting headline: {e}")
            
            # Summary
            try:
                summary_elements = tree.xpath('//div[@class="newspack-post-subtitle"]/text()')
                if summary_elements:
                    data["summary"] = summary_elements[0].strip()
            except Exception as e:
                logger.debug(f"Error extracting summary: {e}")
            
            # Body
            try:
                body_texts = tree.xpath('//div[contains(@class, "entry-content")]//p/text()')
                data["body"] = " ".join([text.strip() for text in body_texts if text.strip()])
            except Exception as e:
                logger.debug(f"Error extracting body: {e}")
            
            # Date
            try:
                # Use datetime attribute for more reliable parsing
                date_elements = tree.xpath('//time/@datetime')
                if date_elements:
                    data["date"] = date_elements[0].strip()
                else:
                    # Fallback to text content
                    date_elements = tree.xpath('//time/text()')
                    if date_elements:
                        data["date"] = date_elements[0].strip()
            except Exception as e:
                logger.debug(f"Error extracting date: {e}")
            
            # Author
            try:
                author_elements = tree.xpath('//a[contains(@class, "url") and contains(@class, "fn")]/text()')
                if author_elements:
                    data["author"] = author_elements[0].strip()
            except Exception as e:
                logger.debug(f"Error extracting author: {e}")
        
        except Exception as e:
            logger.error(f"Error in extract_article_data for El Sol: {e}")
        
        return data


class MDZScraper(BaseNewspaperScraper):
    """Scraper for MDZ newspaper."""
    
    def __init__(self):
        super().__init__("MDZ", SCRAPER_CONFIG["portals"]["MDZ"])
    
    def extract_article_links(self, tree: html.HtmlElement, base_url: str) -> List[str]:
        """Extract article links from MDZ listing page."""
        links = []
        
        try:
            # Extract links with news-article__link class
            link_elements = tree.xpath('//a[contains(@class, "news-article__link")]/@href')
            links = [link for link in link_elements if link.startswith('http')]
        except Exception as e:
            logger.error(f"Error in extract_article_links for MDZ: {e}")
        
        return links
    
    def extract_article_data(self, tree: html.HtmlElement, url: str) -> Dict[str, str]:
        """Extract article data from MDZ article page."""
        data = {
            "headline": "",
            "summary": "",
            "body": "",
            "date": "",
            "author": ""
        }
        
        try:
            # Headline
            try:
                headline_elements = tree.xpath('//h1/text()')
                if headline_elements:
                    data["headline"] = headline_elements[0].strip()
            except Exception as e:
                logger.debug(f"Error extracting headline: {e}")
            
            # Summary
            try:
                # Get all text from the lead div, not just paragraphs
                summary_texts = tree.xpath('//div[contains(@class, "news-detail__lead")]//text()')
                if summary_texts:
                    data["summary"] = " ".join([text.strip() for text in summary_texts if text.strip()])
            except Exception as e:
                logger.debug(f"Error extracting summary: {e}")
            
            # Body
            try:
                body_texts = tree.xpath('//div[contains(@class, "news-detail__body")]//p//text()')
                data["body"] = " ".join([text.strip() for text in body_texts if text.strip()])
            except Exception as e:
                logger.debug(f"Error extracting body: {e}")
            
            # Date
            try:
                # Use datetime attribute for more reliable parsing
                date_elements = tree.xpath('//time/@datetime')
                if date_elements:
                    data["date"] = date_elements[0].strip()
                else:
                    # Fallback to text content
                    date_elements = tree.xpath('//time/text()')
                    if date_elements:
                        data["date"] = date_elements[0].strip()
            except Exception as e:
                logger.debug(f"Error extracting date: {e}")
            
            # Author
            try:
                author_elements = tree.xpath('//a[contains(@href, "/autor/")]/text()')
                if author_elements:
                    data["author"] = author_elements[0].strip()
            except Exception as e:
                logger.debug(f"Error extracting author: {e}")
        
        except Exception as e:
            logger.error(f"Error in extract_article_data for MDZ: {e}")
        
        return data


# ============================================================================
# Orchestrator
# ============================================================================

class NewspaperScraperOrchestrator:
    """
    Orchestrates scraping across multiple newspaper portals.
    Handles duplicate detection, aggregation, and export.
    """
    
    def __init__(self):
        """Initialize orchestrator with all scrapers."""
        self.scrapers = [
            LosAndesScraper(),
            DiarioUnoScraper(),
            ElSolScraper(),
            MDZScraper()
        ]
        self.portal_delay = SCRAPER_CONFIG["portal_delay"]
        self.results = {}
    
    def scrape_all(self) -> Dict[str, Dict[str, str]]:
        """
        Scrape all configured portals.
        
        Returns:
            Dictionary mapping article URLs to their data
        """
        logger.info("=" * 80)
        logger.info("Starting newspaper scraping orchestrator")
        logger.info("=" * 80)
        
        all_results = {}
        
        for i, scraper in enumerate(self.scrapers):
            # Scrape this portal
            portal_results = scraper.scrape()
            
            # Check for duplicates
            duplicates = 0
            for url, data in portal_results.items():
                if url in all_results:
                    duplicates += 1
                    logger.warning(f"Duplicate URL detected: {url}")
                else:
                    all_results[url] = data
            
            if duplicates > 0:
                logger.info(f"Removed {duplicates} duplicate(s) from {scraper.name}")
            
            # Delay between portals (except after the last one)
            if i < len(self.scrapers) - 1:
                logger.info(f"Waiting {self.portal_delay}s before next portal...")
                time.sleep(self.portal_delay)
        
        self.results = all_results
        
        logger.info("=" * 80)
        logger.info(f"Scraping complete! Total articles: {len(all_results)}")
        logger.info("=" * 80)
        
        return all_results
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert results to pandas DataFrame.
        
        Returns:
            DataFrame with article data
        """
        if not self.results:
            logger.warning("No results to convert. Run scrape_all() first.")
            return pd.DataFrame()
        
        df_data = []
        for url, data in self.results.items():
            row = {"url": url}
            row.update(data)
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        
        # Reorder columns for better readability
        column_order = ["url", "newspaper", "headline", "summary", "body", "date", "author", "scraped_at"]
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]
        
        return df
    
    def export_csv(self, filename: str = "news_data.csv") -> None:
        """
        Export results to CSV file.
        
        Args:
            filename: Output filename
        """
        df = self.to_dataframe()
        if df.empty:
            logger.warning("No data to export")
            return
        
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Exported {len(df)} articles to {filename}")
    
    def export_json(self, filename: str = "news_data.json") -> None:
        """
        Export results to JSON file.
        
        Args:
            filename: Output filename
        """
        if not self.results:
            logger.warning("No data to export")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported {len(self.results)} articles to {filename}")


# ============================================================================
# Main execution (for testing)
# ============================================================================

if __name__ == "__main__":
    # Example usage
    orchestrator = NewspaperScraperOrchestrator()
    results = orchestrator.scrape_all()
    
    # Export to both formats
    orchestrator.export_csv("news_data.csv")
    orchestrator.export_json("news_data.json")
    
    # Display summary
    df = orchestrator.to_dataframe()
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total articles scraped: {len(df)}")
    print("\nArticles per newspaper:")
    print(df['newspaper'].value_counts())
    print("\nFirst 5 articles:")
    print(df[['newspaper', 'headline', 'date']].head())
