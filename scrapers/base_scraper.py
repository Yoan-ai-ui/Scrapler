import requests
import time
import random
import logging
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
from fake_useragent import UserAgent
from config import Config

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Classe de base pour tous les scrapers avec fonctionnalités communes"""
    
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.config = Config()
        
    def _get_random_headers(self) -> Dict[str, str]:
        """Génère des headers aléatoires pour éviter la détection"""
        headers = self.config.DEFAULT_HEADERS.copy()
        headers['User-Agent'] = random.choice(self.config.USER_AGENTS)
        return headers
    
    def _make_request(self, url: str, max_retries: int = None) -> Optional[requests.Response]:
        """
        Effectue une requête HTTP avec gestion des erreurs et retry
        
        Args:
            url: URL à requêter
            max_retries: Nombre maximum de tentatives
            
        Returns:
            Response object ou None si échec
        """
        max_retries = max_retries or self.config.MAX_RETRIES
        
        for attempt in range(max_retries):
            try:
                # Délai aléatoire entre les requêtes
                if attempt > 0:
                    delay = self.config.DELAY_BETWEEN_REQUESTS + random.uniform(1, 3)
                    time.sleep(delay)
                
                headers = self._get_random_headers()
                
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=self.config.DEFAULT_TIMEOUT,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    logger.debug(f"Requête réussie: {url}")
                    return response
                elif response.status_code in [403, 429]:
                    logger.warning(f"Blocage détecté ({response.status_code}): {url}")
                    time.sleep(random.uniform(5, 10))  # Attente plus longue
                else:
                    logger.warning(f"Code d'erreur {response.status_code}: {url}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur requête (tentative {attempt + 1}): {e}")
                
        logger.error(f"Échec définitif pour: {url}")
        return None
    
    def _parse_html(self, response: requests.Response) -> Optional[BeautifulSoup]:
        """Parse le HTML avec BeautifulSoup"""
        try:
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            logger.error(f"Erreur parsing HTML: {e}")
            return None
    
    def _extract_text(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """
        Extrait le texte en essayant plusieurs sélecteurs
        
        Args:
            soup: Objet BeautifulSoup
            selectors: Liste de sélecteurs CSS à essayer
            
        Returns:
            Texte extrait ou chaîne vide
        """
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text:
                        return text
            except Exception as e:
                logger.debug(f"Erreur sélecteur '{selector}': {e}")
                continue
        return ""
    
    def _clean_price(self, price_text: str) -> float:
        """
        Nettoie et convertit un prix en float
        
        Args:
            price_text: Texte contenant le prix
            
        Returns:
            Prix en float ou 0.0 si échec
        """
        if not price_text:
            return 0.0
        
        # Supprime les caractères non numériques sauf . et ,
        import re
        price_clean = re.sub(r'[^\d.,]', '', price_text)
        
        # Gère les formats européens (1.234,56) et américains (1,234.56)
        if ',' in price_clean and '.' in price_clean:
            if price_clean.rfind(',') > price_clean.rfind('.'):
                # Format européen: 1.234,56
                price_clean = price_clean.replace('.', '').replace(',', '.')
            else:
                # Format américain: 1,234.56
                price_clean = price_clean.replace(',', '')
        elif ',' in price_clean:
            # Peut être 1,50 ou 1234,56
            if len(price_clean.split(',')[-1]) <= 2:
                price_clean = price_clean.replace(',', '.')
            else:
                price_clean = price_clean.replace(',', '')
        
        try:
            return float(price_clean)
        except ValueError:
            logger.warning(f"Impossible de convertir le prix: {price_text}")
            return 0.0
    
    def _extract_rating(self, rating_text: str) -> Dict[str, Optional[float]]:
        """
        Extrait note et nombre d'avis depuis le texte
        
        Args:
            rating_text: Texte contenant les informations d'évaluation
            
        Returns:
            Dictionnaire avec 'rating' et 'review_count'
        """
        import re
        
        result = {'rating': None, 'review_count': None}
        
        if not rating_text:
            return result
        
        # Cherche une note (format: 4.5/5, 4.5 sur 5, 4,5★, etc.)
        rating_patterns = [
            r'(\d+[.,]\d+)\s*[/sur]\s*5',
            r'(\d+[.,]\d+)\s*★',
            r'(\d+[.,]\d+)\s*étoiles?',
            r'(\d+[.,]\d+)\s*stars?'
        ]
        
        for pattern in rating_patterns:
            match = re.search(pattern, rating_text.lower())
            if match:
                try:
                    result['rating'] = float(match.group(1).replace(',', '.'))
                    break
                except ValueError:
                    continue
        
        # Cherche le nombre d'avis
        review_patterns = [
            r'(\d+)\s*avis',
            r'(\d+)\s*reviews?',
            r'(\d+)\s*évaluations?'
        ]
        
        for pattern in review_patterns:
            match = re.search(pattern, rating_text.lower())
            if match:
                try:
                    result['review_count'] = int(match.group(1))
                    break
                except ValueError:
                    continue
        
        return result
    
    @abstractmethod
    def scrape_product(self, url: str, product_info: Dict = None) -> Dict[str, any]:
        """
        Méthode abstraite à implémenter par chaque scraper spécialisé
        
        Args:
            url: URL du produit à scraper
            product_info: Informations additionnelles sur le produit
            
        Returns:
            Dictionnaire avec les données du produit
        """
        pass
    
    def get_product_data(self, url: str, product_info: Dict = None) -> Dict[str, any]:
        """
        Point d'entrée principal pour récupérer les données d'un produit
        
        Args:
            url: URL du produit
            product_info: Informations additionnelles
            
        Returns:
            Données du produit avec métadonnées
        """
        logger.info(f"Scraping: {url}")
        
        start_time = time.time()
        
        # Structure de base des données
        product_data = {
            'url': url,
            'title': '',
            'price': 0.0,
            'availability': '',
            'rating': None,
            'review_count': None,
            'description': '',
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'scraping_duration': 0.0,
            'success': False,
            'error_message': ''
        }
        
        if product_info:
            product_data.update({
                'product_name': product_info.get('name', ''),
                'category': product_info.get('category', ''),
                'site': product_info.get('site', '')
            })
        
        try:
            # Appel de la méthode spécialisée
            scraped_data = self.scrape_product(url, product_info)
            product_data.update(scraped_data)
            product_data['success'] = True
            
        except Exception as e:
            logger.error(f"Erreur scraping {url}: {e}")
            product_data['error_message'] = str(e)
        
        product_data['scraping_duration'] = round(time.time() - start_time, 2)
        
        return product_data