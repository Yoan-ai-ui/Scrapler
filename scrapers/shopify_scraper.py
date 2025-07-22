from .base_scraper import BaseScraper
from config import SITE_CONFIGS
import logging

logger = logging.getLogger(__name__)

class ShopifyScraper(BaseScraper):
    """Scraper spécialisé pour les sites Shopify"""
    
    def scrape_product(self, url, product_info=None):
        """Scrape un produit depuis un site Shopify"""
        response = self._make_request(url)
        if not response:
            raise Exception("Impossible de récupérer la page")
        
        soup = self._parse_html(response)
        if not soup:
            raise Exception("Impossible de parser le HTML")
        
        selectors = SITE_CONFIGS['shopify']['selectors']
        
        # Extraction du titre
        title = self._extract_text(soup, selectors['title'])
        
        # Extraction du prix
        price_text = self._extract_text(soup, selectors['price'])
        price = self._clean_price(price_text)
        
        # Vérification de disponibilité
        availability_text = self._extract_text(soup, selectors['availability'])
        availability = self._determine_availability(availability_text, soup)
        
        # Extraction des avis
        reviews_text = self._extract_text(soup, selectors['reviews'])
        rating_info = self._extract_rating(reviews_text)
        
        # Description
        description = self._extract_text(soup, selectors['description'])
        
        return {
            'title': title,
            'price': price,
            'availability': availability,
            'rating': rating_info['rating'],
            'review_count': rating_info['review_count'],
            'description': description[:500] if description else ''  # Limite la description
        }
    
    def _determine_availability(self, availability_text, soup):
        """Détermine la disponibilité du produit Shopify"""
        availability_text = availability_text.lower()
        
        # Mots-clés pour "en stock"
        in_stock_keywords = ['en stock', 'disponible', 'in stock', 'available']
        
        # Mots-clés pour "rupture de stock"
        out_of_stock_keywords = ['rupture', 'épuisé', 'indisponible', 'out of stock', 'sold out']
        
        if any(keyword in availability_text for keyword in out_of_stock_keywords):
            return 'Rupture de stock'
        elif any(keyword in availability_text for keyword in in_stock_keywords):
            return 'En stock'
        
        # Vérification via les boutons d'ajout au panier
        add_to_cart_buttons = soup.find_all(['button', 'input'], attrs={
            'class': lambda x: x and any(cls in x.lower() for cls in ['add-to-cart', 'btn-cart', 'product-submit'])
        })
        
        for button in add_to_cart_buttons:
            if button.get('disabled') or 'disabled' in button.get('class', []):
                return 'Rupture de stock'
            
            button_text = button.get_text(strip=True).lower()
            if any(keyword in button_text for keyword in out_of_stock_keywords):
                return 'Rupture de stock'
        
        return 'Disponibilité inconnue'