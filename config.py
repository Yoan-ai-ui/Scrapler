import os
from dotenv import load_dotenv

load_dotenv()

# Configuration générale
class Config:
    # Paramètres de scraping
    DEFAULT_TIMEOUT = 10
    MAX_RETRIES = 3
    DELAY_BETWEEN_REQUESTS = 2  # secondes
    
    # Headers par défaut
    DEFAULT_HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Configuration des rapports
    REPORTS_DIR = 'reports_output'
    DATA_DIR = 'data'
    LOGS_DIR = 'logs'
    
    # Configuration email (pour les alertes)
    EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'False').lower() == 'true'
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    EMAIL_USER = os.getenv('EMAIL_USER', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    EMAIL_RECIPIENTS = os.getenv('EMAIL_RECIPIENTS', '').split(',')
    
    # Configuration de surveillance
    PRICE_CHANGE_THRESHOLD = 5.0  # pourcentage de changement significatif
    
    # User agents pour rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
    ]

# Configuration spécifique par site
SITE_CONFIGS = {
    'shopify': {
        'selectors': {
            'title': ['h1.product-title', '.product__title', '.product-single__title', 'h1'],
            'price': ['.price', '.product-price', '.money', '.current_price'],
            'availability': ['.product-availability', '.inventory_quantity', '.stock-level'],
            'reviews': ['.reviews-summary', '.product-reviews', '.review-count'],
            'description': ['.product-description', '.product-single__description', '.rte']
        }
    },
    'amazon': {
        'selectors': {
            'title': ['#productTitle', '.product-title'],
            'price': ['#priceblock_dealprice', '#priceblock_ourprice', '.a-price-whole'],
            'availability': ['#availability span', '.availability-msg'],
            'reviews': ['#acrCustomerReviewText', '.review-count'],
            'description': ['#feature-bullets', '.product-description']
        }
    },
    'etsy': {
        'selectors': {
            'title': ['h1[data-test-id="listing-page-title"]', '.listing-page-title'],
            'price': ['.currency-value', '.notranslate'],
            'availability': ['.listing-page-availability', '.stock-level'],
            'reviews': ['.shop2-review-average', '.review-text'],
            'description': ['.listing-description', '.shop2-listing-description']
        }
    },
    'leboncoin': {
        'selectors': {
            'title': ['h1[data-qa-id="adview_title"]', '.ad-title'],
            'price': ['[data-qa-id="adview_price"]', '.price'],
            'availability': ['.availability', '.stock-info'],
            'reviews': ['.rating', '.review-count'],
            'description': ['[data-qa-id="adview_description_container"]', '.ad-description']
        }
    }
}