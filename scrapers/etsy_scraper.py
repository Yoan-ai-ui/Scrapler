from .base_scraper import BaseScraper
from config import SITE_CONFIGS
import logging

logger = logging.getLogger(__name__)

class EtsyScraper(BaseScraper):
    """Scraper spécialisé pour Etsy"""
    
    def scrape_product(self, url, product_info=None):
        """Scrape un produit depuis Etsy"""
        response = self._make_request(url)
        if not response:
            raise Exception("Impossible de récupérer la page Etsy")
        
        soup = self._parse_html(response)
        if not soup:
            raise Exception("Impossible de parser le HTML Etsy")
        
        selectors = SITE_CONFIGS['etsy']['selectors']
        
        # Extraction du titre
        title = self._extract_text(soup, selectors['title'])
        
        # Extraction du prix Etsy
        price = self._extract_etsy_price(soup)
        
        # Vérification de disponibilité
        availability = self._extract_etsy_availability(soup)
        
        # Extraction des avis Etsy
        rating_info = self._extract_etsy_reviews(soup)
        
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
    
    def _extract_etsy_price(self, soup):
        """Extraction spécialisée du prix Etsy"""
        price_selectors = [
            '[data-test-id="listing-page-price"] .currency-value',
            '.currency-value',
            '.notranslate',
            '.shop2-listing-price'
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                price_text = element.get_text(strip=True)
                price = self._clean_price(price_text)
                if price > 0:
                    return price
        
        return 0.0
    
    def _extract_etsy_availability(self, soup):
        """Extraction spécialisée de la disponibilité Etsy"""
        # Etsy affiche souvent le stock restant
        stock_selectors = [
            '[data-test-id="listing-page-inventory"]',
            '.listing-page-availability',
            '.stock-level'
        ]
        
        stock_text = self._extract_text(soup, stock_selectors)
        
        if stock_text:
            stock_lower = stock_text.lower()
            if 'en stock' in stock_lower or any(word in stock_lower for word in ['disponible', 'available']):
                return 'En stock'
            elif any(word in stock_lower for word in ['épuisé', 'sold out', 'unavailable']):
                return 'Rupture de stock'
            elif any(char.isdigit() for char in stock_text):
                return f'En stock ({stock_text})'
        
        # Vérifier le bouton d'ajout au panier
        add_button = soup.select_one('[data-test-id="add-to-cart-button"]')
        if add_button:
            if add_button.get('disabled') or 'disabled' in add_button.get('class', []):
                return 'Rupture de stock'
            else:
                return 'En stock'
        
        return 'Disponibilité inconnue'
    
    def _extract_etsy_reviews(self, soup):
        """Extraction spécialisée des avis Etsy"""
        rating = None
        review_count = None
        
        # Extraction de la note
        rating_selectors = [
            '[data-test-id="review-star-rating"]',
            '.shop2-review-average',
            '.rating-text'
        ]
        
        for selector in rating_selectors:
            element = soup.select_one(selector)
            if element:
                rating_text = element.get_text(strip=True)
                rating_info = self._extract_rating(rating_text)
                if rating_info['rating']:
                    rating = rating_info['rating']
                    break
        
        # Extraction du nombre d'avis
        review_selectors = [
            '[data-test-id="review-count"]',
            '.review-count',
            '[data-review-count]'
        ]
        
        for selector in review_selectors:
            element = soup.select_one(selector)
            if element:
                review_text = element.get_text(strip=True)
                import re
                match = re.search(r'(\d+)', review_text.replace(',', ''))
                if match:
                    review_count = int(match.group(1))
                    break
        
        return {'rating': rating, 'review_count': review_count}