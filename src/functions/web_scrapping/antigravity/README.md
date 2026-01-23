# Newspaper Scraper v2 - Modular Architecture

A modular, OOP-based newspaper scraper supporting 4 Mendoza news portals with duplicate detection, comprehensive logging, and multiple export formats.

## Features

✅ **Modular OOP Architecture**
- Abstract base class (`BaseNewspaperScraper`) with shared functionality
- Portal-specific scrapers with custom XPath selectors
- Easy to extend with new portals

✅ **Supported Portals**
- Los Andes (https://www.losandes.com.ar)
- Diario UNO (https://www.diariouno.com.ar)
- El Sol (https://www.elsol.com.ar)
- MDZ (https://www.mdzol.com)

✅ **Advanced Features**
- Duplicate detection by URL
- Comprehensive logging with progress tracking
- Configurable delays (1s between requests, 2s between portals)
- Export to CSV and JSON
- Timestamp field (`scraped_at`) for each article

## Installation

### Requirements

```bash
pip install requests lxml pandas
```

### Dependencies

- Python 3.7+
- requests
- lxml
- pandas

## Quick Start

### Using the Orchestrator (Recommended)

```python
from newspapers_scraper_v2 import NewspaperScraperOrchestrator

# Initialize and scrape all portals
orchestrator = NewspaperScraperOrchestrator()
results = orchestrator.scrape_all()

# Export to CSV and JSON
orchestrator.export_csv("news_data.csv")
orchestrator.export_json("news_data.json")

# View as DataFrame
df = orchestrator.to_dataframe()
print(df.head())
```

### Using Individual Scrapers

```python
from newspapers_scraper_v2 import LosAndesScraper

# Scrape only Los Andes
scraper = LosAndesScraper()
results = scraper.scrape()

print(f"Scraped {len(results)} articles")
```

### Using the Jupyter Notebook

Open `newspapers_scraper_v2.ipynb` for an interactive demonstration with examples and data analysis.

## Architecture

### Class Hierarchy

```
BaseNewspaperScraper (Abstract)
├── LosAndesScraper
├── DiarioUnoScraper
├── ElSolScraper
└── MDZScraper

NewspaperScraperOrchestrator
```

### Base Class Methods

Each scraper inherits from `BaseNewspaperScraper` and implements:

- `extract_article_links(tree, base_url)` - Extract article URLs from listing page
- `extract_article_data(tree, url)` - Extract article data (headline, summary, body, date, author)

Shared methods:
- `get_tree(url)` - Fetch and parse HTML
- `scrape()` - Main orchestration method

### Data Structure

Each article contains:
- `url` - Article URL
- `newspaper` - Source newspaper name
- `headline` - Article title
- `summary` - Article summary/lead
- `body` - Full article text
- `date` - Publication date
- `author` - Author name
- `scraped_at` - ISO timestamp of when the article was scraped

## Configuration

Edit `SCRAPER_CONFIG` in `newspapers_scraper_v2.py`:

```python
SCRAPER_CONFIG = {
    "request_delay": 1,      # seconds between requests
    "portal_delay": 2,       # seconds between portals
    "timeout": 10,           # request timeout
    "portals": {
        "Los Andes": [...],  # list of URLs to scrape
        # ...
    }
}
```

## Adding New Portals

1. Create a new scraper class inheriting from `BaseNewspaperScraper`
2. Implement `extract_article_links()` and `extract_article_data()`
3. Add portal URLs to `SCRAPER_CONFIG`
4. Add the scraper to `NewspaperScraperOrchestrator.__init__()`

Example:

```python
class NewPortalScraper(BaseNewspaperScraper):
    def __init__(self):
        super().__init__("New Portal", SCRAPER_CONFIG["portals"]["New Portal"])
    
    def extract_article_links(self, tree, base_url):
        # Your XPath logic here
        return tree.xpath('//a[@class="article-link"]/@href')
    
    def extract_article_data(self, tree, url):
        return {
            "headline": tree.xpath('//h1/text()')[0],
            "summary": tree.xpath('//p[@class="summary"]/text()')[0],
            # ... etc
        }
```

## Logging

The scraper uses Python's `logging` module. Adjust the log level:

```python
import logging
logging.getLogger('newspapers_scraper_v2').setLevel(logging.DEBUG)
```

## Troubleshooting

### No articles found

- Check if the portal's HTML structure has changed
- Verify XPath selectors using browser DevTools
- Check network connectivity and timeouts

### Missing data fields

- Some articles may not have all fields (e.g., author)
- The scraper handles missing data gracefully with empty strings
- Check logs for extraction errors

### Rate limiting / Blocked requests

- Increase delays in `SCRAPER_CONFIG`
- Verify `User-Agent` header is set correctly
- Some portals may require additional headers or cookies

## Output Examples

### CSV Format

```csv
url,newspaper,headline,summary,body,date,author,scraped_at
https://www.losandes.com.ar/...,Los Andes,Title,Summary,Body text...,2026-01-20,Author Name,2026-01-20T10:30:00
```

### JSON Format

```json
{
  "https://www.losandes.com.ar/...": {
    "headline": "Title",
    "summary": "Summary",
    "body": "Body text...",
    "date": "2026-01-20",
    "author": "Author Name",
    "newspaper": "Los Andes",
    "scraped_at": "2026-01-20T10:30:00"
  }
}
```

## License

This project is provided as-is for educational and research purposes.

## Notes

- Respect robots.txt and terms of service of each portal
- Use appropriate delays to avoid overloading servers
- Some portals may change their HTML structure over time
- The scraper preserves the original Los Andes XPath logic from the initial implementation
