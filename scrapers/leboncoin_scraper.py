from .base_scraper import BaseScraper
from config import SITE_CONFIGS
import logging

logger = logging.getLogger(__name__)

class LeboncoinScraper(BaseScraper):
    """Scraper spécialisé pour Leboncoin"""
    
    def scrape_product(self, url, product_info=None):
        """Scrape une annonce depuis Leboncoin"""
        response = self._make_request(url)
        if not response:
            raise Exception("Impossible de récupérer la page Leboncoin")
        
        soup = self._parse_html(response)
        if not soup:
            raise Exception("Impossible de parser le HTML Leboncoin")
        
        selectors = SITE_CONFIGS['leboncoin']['selectors']
        
        # Extraction du titre
        title = self._extract_text(soup, selectors['title'])
        
        # Extraction du prix
        price_text = self._extract_text(soup, selectors['price'])
        price = self._clean_price(price_text)
        
        # Sur Leboncoin, les annonces sont généralement disponibles si elles sont en ligne
        availability = self._extract_leboncoin_availability(soup)
        
        # Leboncoin n'a pas de système d'avis classique
        rating_info = {'rating': None, 'review_count': None}
        
        # Description
        description = self._extract_text(soup, selectors['description'])
        
        return {
            'title': title,
            'price': price,
            'availability': availability,
            'rating': rating_info['rating'],
            'review_count': rating_info['review_count'],
            'description': description[:500] if description else ''
        }
    
    def _extract_leboncoin_availability(self, soup):
        """Extraction spécialisée de la disponibilité Leboncoin"""
        # Vérifier si l'annonce est toujours active
        unavailable_indicators = [
            'Cette annonce n\'est plus disponible',
            'Annonce expirée',
            'Cette annonce a été supprimée'
        ]
        
        page_text = soup.get_text()
        for indicator in unavailable_indicators:
            if indicator in page_text:
                return 'Annonce expirée'
        
        # Si on arrive à accéder à l'annonce normalement, elle est disponible
        return 'Disponible'