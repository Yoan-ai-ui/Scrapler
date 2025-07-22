from .base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)

class BeaconScraper(BaseScraper):
    """Scraper spécialisé pour Beacon.by"""
    
    def scrape_product(self, url, product_info=None):
        """Scrape un service depuis Beacon.by"""
        response = self._make_request(url)
        if not response:
            raise Exception("Impossible de récupérer la page Beacon")
        
        soup = self._parse_html(response)
        if not soup:
            raise Exception("Impossible de parser le HTML Beacon")
        
        # Sélecteurs spécifiques à Beacon
        title_selectors = [
            'h1.service-title',
            '.service-name',
            'h1',
            '.title'
        ]
        
        price_selectors = [
            '.price',
            '.service-price',
            '.pricing',
            '[data-price]'
        ]
        
        availability_selectors = [
            '.availability',
            '.service-status',
            '.status'
        ]
        
        description_selectors = [
            '.service-description',
            '.description',
            '.service-details'
        ]
        
        # Extraction du titre
        title = self._extract_text(soup, title_selectors)
        
        # Extraction du prix
        price_text = self._extract_text(soup, price_selectors)
        price = self._clean_price(price_text)
        
        # Vérification de disponibilité
        availability_text = self._extract_text(soup, availability_selectors)
        availability = availability_text if availability_text else 'Disponible'
        
        # Description
        description = self._extract_text(soup, description_selectors)
        
        return {
            'title': title,
            'price': price,
            'availability': availability,
            'rating': None,  # Beacon peut ne pas avoir de système de notation
            'review_count': None,
            'description': description[:500] if description else ''
        }