from .base_scraper import BaseScraper
from config import SITE_CONFIGS
import logging

logger = logging.getLogger(__name__)

class AmazonScraper(BaseScraper):
    """Scraper spécialisé pour Amazon"""
    
    def __init__(self):
        super().__init__()
        # Headers spécifiques Amazon
        self.amazon_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _get_random_headers(self):
        """Override pour ajouter headers spécifiques Amazon"""
        headers = super()._get_random_headers()
        headers.update(self.amazon_headers)
        return headers
    
    def scrape_product(self, url, product_info=None):
        """Scrape un produit depuis Amazon"""
        response = self._make_request(url)
        if not response:
            raise Exception("Impossible de récupérer la page Amazon")
        
        soup = self._parse_html(response)
        if not soup:
            raise Exception("Impossible de parser le HTML Amazon")
        
        # Détection de blocage Amazon
        if self._is_blocked(soup):
            raise Exception("Requête bloquée par Amazon")
        
        selectors = SITE_CONFIGS['amazon']['selectors']
        
        # Extraction du titre
        title = self._extract_text(soup, selectors['title'])
        
        # Extraction du prix (Amazon a plusieurs formats)
        price = self._extract_amazon_price(soup)
        
        # Vérification de disponibilité
        availability = self._extract_amazon_availability(soup)
        
        # Extraction des avis Amazon
        rating_info = self._extract_amazon_reviews(soup)
        
        # Description (Amazon utilise souvent des bullet points)
        description = self._extract_amazon_description(soup)
        
        return {
            'title': title,
            'price': price,
            'availability': availability,
            'rating': rating_info['rating'],
            'review_count': rating_info['review_count'],
            'description': description
        }
    
    def _is_blocked(self, soup):
        """Vérifie si la requête a été bloquée par Amazon"""
        blocked_indicators = [
            'api-services-support@amazon.com',
            'Robot Check',
            'Enter the characters you see below',
            'Sorry, we just need to make sure you\'re not a robot'
        ]
        
        page_text = soup.get_text().lower()
        return any(indicator.lower() in page_text for indicator in blocked_indicators)
    
    def _extract_amazon_price(self, soup):
        """Extraction spécialisée du prix Amazon"""
        price_selectors = [
            '.a-price-whole',
            '#priceblock_dealprice',
            '#priceblock_ourprice',
            '.a-offscreen',
            '.a-price.a-text-price.a-size-medium.apexPriceToPay',
            '.a-price-range'
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                price_text = element.get_text(strip=True)
                price = self._clean_price(price_text)
                if price > 0:
                    return price
        
        return 0.0
    
    def _extract_amazon_availability(self, soup):
        """Extraction spécialisée de la disponibilité Amazon"""
        availability_selectors = [
            '#availability span',
            '.a-alert-content',
            '.availability-msg'
        ]
        
        availability_text = self._extract_text(soup, availability_selectors)
        
        if not availability_text:
            return 'Disponibilité inconnue'
        
        availability_lower = availability_text.lower()
        
        if any(phrase in availability_lower for phrase in ['en stock', 'in stock', 'disponible']):
            return 'En stock'
        elif any(phrase in availability_lower for phrase in ['temporairement', 'currently unavailable', 'indisponible']):
            return 'Temporairement indisponible'
        elif any(phrase in availability_lower for phrase in ['rupture', 'out of stock']):
            return 'Rupture de stock'
        
        return availability_text
    
    def _extract_amazon_reviews(self, soup):
        """Extraction spécialisée des avis Amazon"""
        rating = None
        review_count = None
        
        # Extraction de la note
        rating_elements = soup.select('[data-hook="average-star-rating"] .a-offscreen, .a-icon-alt')
        for element in rating_elements:
            text = element.get_text()
            if 'sur 5' in text or 'out of 5' in text:
                try:
                    rating = float(text.split()[0].replace(',', '.'))
                    break
                except:
                    continue
        
        # Extraction du nombre d'avis
        review_elements = soup.select('[data-hook="total-review-count"], #acrCustomerReviewText')
        for element in review_elements:
            text = element.get_text()
            import re
            match = re.search(r'([\d\s,]+)', text.replace('.', '').replace(' ', ''))
            if match:
                try:
                    review_count = int(match.group(1).replace(',', '').replace(' ', ''))
                    break
                except:
                    continue
        
        return {'rating': rating, 'review_count': review_count}
    
    def _extract_amazon_description(self, soup):
        """Extraction spécialisée de la description Amazon"""
        desc_selectors = [
            '#feature-bullets ul',
            '.product-description',
            '#productDescription'
        ]
        
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                # Pour les bullet points, on joint les éléments
                if element.name == 'ul':
                    bullets = element.find_all('li')
                    description = ' | '.join([li.get_text(strip=True) for li in bullets[:5]])
                else:
                    description = element.get_text(strip=True)
                
                if description:
                    return description[:500]
        
        return ''