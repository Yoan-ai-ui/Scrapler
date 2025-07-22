from .base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)

class FiverrScraper(BaseScraper):
    """Scraper spécialisé pour Fiverr"""
    
    def scrape_product(self, url, product_info=None):
        """Scrape un service depuis Fiverr"""
        response = self._make_request(url)
        if not response:
            raise Exception("Impossible de récupérer la page Fiverr")
        
        soup = self._parse_html(response)
        if not soup:
            raise Exception("Impossible de parser le HTML Fiverr")
        
        # Sélecteurs spécifiques à Fiverr
        title_selectors = [
            '[data-gig-title]',
            'h1.gig-page-title',
            '.gig-title',
            'h1'
        ]
        
        price_selectors = [
            '.price-value',
            '.starting-price',
            '[data-price]',
            '.price'
        ]
        
        rating_selectors = [
            '.gig-rating',
            '.rating-score',
            '.star-rating'
        ]
        
        description_selectors = [
            '.gig-desc-container',
            '.description',
            '.gig-description'
        ]
        
        # Extraction du titre
        title = self._extract_text(soup, title_selectors)
        
        # Extraction du prix (Fiverr affiche souvent "Starting at $X")
        price_text = self._extract_text(soup, price_selectors)
        price = self._clean_price(price_text)
        
        # Sur Fiverr, les gigs sont généralement disponibles s'ils sont en ligne
        availability = 'Disponible'
        
        # Extraction des évaluations Fiverr
        rating_info = self._extract_fiverr_reviews(soup)
        
        # Description
        description = self._extract_text(soup, description_selectors)
        
        return {
            'title': title,
            'price': price,
            'availability': availability,
            'rating': rating_info['rating'],
            'review_count': rating_info['review_count'],
            'description': description[:500] if description else ''
        }
    
    def _extract_fiverr_reviews(self, soup):
        """Extraction spécialisée des avis Fiverr"""
        rating = None
        review_count = None
        
        # Fiverr affiche souvent la note sous forme d'étoiles
        rating_elements = soup.select('.rating-score, [data-rating], .star-rating')
        for element in rating_elements:
            text = element.get_text(strip=True)
            if text:
                try:
                    rating = float(text.replace(',', '.'))
                    if rating <= 5:  # Fiverr utilise une échelle sur 5
                        break
                except:
                    continue
        
        # Nombre d'avis
        review_elements = soup.select('.reviews-count, [data-reviews], .review-count')
        for element in review_elements:
            text = element.get_text()
            import re
            match = re.search(r'(\d+)', text.replace(',', ''))
            if match:
                review_count = int(match.group(1))
                break
        
        return {'rating': rating, 'review_count': review_count}