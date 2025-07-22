from .shopify_scraper import ShopifyScraper
from .amazon_scraper import AmazonScraper
from .etsy_scraper import EtsyScraper
from .leboncoin_scraper import LeboncoinScraper
from .beacon_scraper import BeaconScraper
from .fiverr_scraper import FiverrScraper
import logging

logger = logging.getLogger(__name__)

class ScraperFactory:
    """Factory pour créer le bon scraper selon le site"""
    
    SCRAPERS = {
        'shopify': ShopifyScraper,
        'amazon': AmazonScraper,
        'etsy': EtsyScraper,
        'leboncoin': LeboncoinScraper,
        'beacon': BeaconScraper,
        'fiverr': FiverrScraper
    }
    
    @classmethod
    def get_scraper(cls, site_type: str):
        """
        Retourne une instance du scraper approprié
        
        Args:
            site_type: Type de site (shopify, amazon, etsy, etc.)
            
        Returns:
            Instance du scraper ou None si non supporté
        """
        scraper_class = cls.SCRAPERS.get(site_type.lower())
        
        if scraper_class:
            return scraper_class()
        else:
            logger.warning(f"Scraper non supporté pour: {site_type}")
            return None
    
    @classmethod
    def get_supported_sites(cls):
        """Retourne la liste des sites supportés"""
        return list(cls.SCRAPERS.keys())
    
    @classmethod
    def is_site_supported(cls, site_type: str):
        """Vérifie si un site est supporté"""
        return site_type.lower() in cls.SCRAPERS