import csv
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class FileLoader:
    """Gestionnaire de chargement et sauvegarde des fichiers de données"""
    
    @staticmethod
    def load_urls(file_path: str) -> List[Dict[str, str]]:
        """
        Charge les URLs depuis un fichier CSV ou TXT
        
        Args:
            file_path: Chemin vers le fichier d'URLs
            
        Returns:
            Liste de dictionnaires contenant les URLs et métadonnées
        """
        urls_data = []
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"Fichier introuvable: {file_path}")
            return []
        
        try:
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
                
                # Colonnes attendues: url, name (optionnel), category (optionnel)
                required_cols = ['url']
                if not all(col in df.columns for col in required_cols):
                    logger.error(f"Colonnes manquantes. Colonnes requises: {required_cols}")
                    return []
                
                for _, row in df.iterrows():
                    url_data = {
                        'url': row['url'].strip(),
                        'name': row.get('name', '').strip(),
                        'category': row.get('category', '').strip(),
                        'site': FileLoader._detect_site(row['url'])
                    }
                    urls_data.append(url_data)
                    
            elif file_path.suffix.lower() == '.txt':
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line_num, line in enumerate(file, 1):
                        url = line.strip()
                        if url and not url.startswith('#'):  # Ignore empty lines and comments
                            url_data = {
                                'url': url,
                                'name': f'Product_{line_num}',
                                'category': '',
                                'site': FileLoader._detect_site(url)
                            }
                            urls_data.append(url_data)
            
            logger.info(f"Chargé {len(urls_data)} URLs depuis {file_path}")
            return urls_data
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement de {file_path}: {e}")
            return []
    
    @staticmethod
    def _detect_site(url: str) -> str:
        """Détecte le type de site à partir de l'URL"""
        url_lower = url.lower()
        
        if 'amazon.' in url_lower:
            return 'amazon'
        elif 'shopify' in url_lower or '.myshopify.com' in url_lower:
            return 'shopify'
        elif 'etsy.com' in url_lower:
            return 'etsy'
        elif 'leboncoin.fr' in url_lower:
            return 'leboncoin'
        elif 'beacon.by' in url_lower:
            return 'beacon'
        elif 'fiverr.com' in url_lower:
            return 'fiverr'
        else:
            return 'unknown'
    
    @staticmethod
    def save_historical_data(data: List[Dict], filename: str) -> bool:
        """
        Sauvegarde les données historiques pour comparaison future
        
        Args:
            data: Données à sauvegarder
            filename: Nom du fichier de sauvegarde
            
        Returns:
            True si sauvegarde réussie, False sinon
        """
        try:
            df = pd.DataFrame(data)
            df['scraped_at'] = pd.Timestamp.now()
            df.to_csv(filename, index=False)
            logger.info(f"Données historiques sauvegardées: {filename}")
            return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde historique: {e}")
            return False
    
    @staticmethod
    def load_historical_data(filename: str) -> Optional[pd.DataFrame]:
        """Charge les données historiques si disponibles"""
        try:
            if Path(filename).exists():
                return pd.read_csv(filename)
            return None
        except Exception as e:
            logger.error(f"Erreur chargement historique: {e}")
            return None