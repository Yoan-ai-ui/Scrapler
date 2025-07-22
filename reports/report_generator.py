import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Générateur de rapports pour les données scrapées"""
    
    def __init__(self):
        self.config = Config()
        self.reports_dir = Path(self.config.REPORTS_DIR)
        self.reports_dir.mkdir(exist_ok=True)
    
    def generate_csv_report(self, data: List[Dict], filename: Optional[str] = None) -> str:
        """
        Génère un rapport CSV des données scrapées
        
        Args:
            data: Liste des données de produits
            filename: Nom du fichier (optionnel, auto-généré si non fourni)
            
        Returns:
            Chemin du fichier généré
        """
        if not data:
            logger.warning("Aucune donnée à rapporter")
            return ""
        
        # Génération automatique du nom de fichier
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"competitive_report_{timestamp}.csv"
        
        filepath = self.reports_dir / filename
        
        try:
            # Création du DataFrame
            df = pd.DataFrame(data)
            
            # Réorganisation des colonnes pour plus de lisibilité
            preferred_columns = [
                'product_name', 'title', 'url', 'site', 'category',
                'price', 'availability', 'rating', 'review_count',
                'description', 'scraped_at', 'success', 'error_message'
            ]
            
            # Garder seulement les colonnes qui existent
            available_columns = [col for col in preferred_columns if col in df.columns]
            remaining_columns = [col for col in df.columns if col not in available_columns]
            
            final_columns = available_columns + remaining_columns
            df = df[final_columns]
            
            # Nettoyage et formatage
            df = self._clean_dataframe(df)
            
            # Sauvegarde
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            logger.info(f"Rapport CSV généré: {filepath}")
            logger.info(f"Nombre de produits: {len(df)}")
            logger.info(f"Produits réussis: {sum(df['success'])}")
            logger.info(f"Produits échoués: {sum(~df['success'])}")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Erreur génération rapport CSV: {e}")
            return ""
    
    def generate_summary_report(self, data: List[Dict]) -> Dict:
        """
        Génère un rapport de synthèse des données
        
        Args:
            data: Liste des données de produits
            
        Returns:
            Dictionnaire avec statistiques de synthèse
        """
        if not data:
            return {}
        
        df = pd.DataFrame(data)
        
        summary = {
            'total_products': len(df),
            'successful_scrapes': sum(df.get('success', [])),
            'failed_scrapes': sum(~df.get('success', [])) if 'success' in df.columns else 0,
            'sites_scraped': df['site'].nunique() if 'site' in df.columns else 0,
            'average_price': df['price'].mean() if 'price' in df.columns else 0,
            'price_range': {
                'min': df['price'].min() if 'price' in df.columns else 0,
                'max': df['price'].max() if 'price' in df.columns else 0
            },
            'availability_stats': df['availability'].value_counts().to_dict() if 'availability' in df.columns else {},
            'sites_breakdown': df['site'].value_counts().to_dict() if 'site' in df.columns else {},
            'average_rating': df['rating'].mean() if 'rating' in df.columns else None,
            'generated_at': datetime.now().isoformat()
        }
        
        return summary
    
    def generate_comparison_report(self, current_data: List[Dict], historical_data: List[Dict]) -> Dict:
        """
        Génère un rapport de comparaison entre données actuelles et historiques
        
        Args:
            current_data: Données actuelles
            historical_data: Données historiques
            
        Returns:
            Rapport de comparaison avec changements détectés
        """
        if not current_data or not historical_data:
            return {}
        
        current_df = pd.DataFrame(current_data)
        historical_df = pd.DataFrame(historical_data)
        
        # Jointure sur l'URL pour comparer
        if 'url' not in current_df.columns or 'url' not in historical_df.columns:
            return {}
        
        comparison_results = {
            'price_changes': [],
            'availability_changes': [],
            'new_products': [],
            'removed_products': [],
            'summary': {}
        }
        
        # URLs communes
        common_urls = set(current_df['url']).intersection(set(historical_df['url']))
        
        for url in common_urls:
            current_product = current_df[current_df['url'] == url].iloc[0]
            historical_product = historical_df[historical_df['url'] == url].iloc[-1]  # Dernière entrée
            
            # Changements de prix
            current_price = current_product.get('price', 0)
            historical_price = historical_product.get('price', 0)
            
            if current_price > 0 and historical_price > 0:
                price_change_pct = ((current_price - historical_price) / historical_price) * 100
                
                if abs(price_change_pct) >= self.config.PRICE_CHANGE_THRESHOLD:
                    comparison_results['price_changes'].append({
                        'url': url,
                        'title': current_product.get('title', ''),
                        'old_price': historical_price,
                        'new_price': current_price,
                        'change_percent': round(price_change_pct, 2)
                    })
            
            # Changements de disponibilité
            current_availability = current_product.get('availability', '')
            historical_availability = historical_product.get('availability', '')
            
            if current_availability != historical_availability:
                comparison_results['availability_changes'].append({
                    'url': url,
                    'title': current_product.get('title', ''),
                    'old_availability': historical_availability,
                    'new_availability': current_availability
                })
        
        # Nouveaux produits
        new_urls = set(current_df['url']) - set(historical_df['url'])
        for url in new_urls:
            product = current_df[current_df['url'] == url].iloc[0]
            comparison_results['new_products'].append({
                'url': url,
                'title': product.get('title', ''),
                'price': product.get('price', 0)
            })
        
        # Produits supprimés/non trouvés
        removed_urls = set(historical_df['url']) - set(current_df['url'])
        for url in removed_urls:
            product = historical_df[historical_df['url'] == url].iloc[-1]
            comparison_results['removed_products'].append({
                'url': url,
                'title': product.get('title', ''),
                'last_price': product.get('price', 0)
            })
        
        # Résumé
        comparison_results['summary'] = {
            'total_price_changes': len(comparison_results['price_changes']),
            'total_availability_changes': len(comparison_results['availability_changes']),
            'new_products_count': len(comparison_results['new_products']),
            'removed_products_count': len(comparison_results['removed_products']),
            'generated_at': datetime.now().isoformat()
        }
        
        return comparison_results
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Nettoie et formate le DataFrame"""
        # Formatage des prix
        if 'price' in df.columns:
            df['price'] = df['price'].round(2)
        
        # Nettoyage des descriptions (suppression des retours à la ligne)
        if 'description' in df.columns:
            df['description'] = df['description'].str.replace('\n', ' ').str.replace('\r', ' ')
        
        # Formatage des colonnes booléennes
        if 'success' in df.columns:
            df['success'] = df['success'].map({True: 'Oui', False: 'Non'})
        
        return df
    
    def save_comparison_report(self, comparison_data: Dict, filename: Optional[str] = None) -> str:
        """Sauvegarde un rapport de comparaison en CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comparison_report_{timestamp}.csv"
        
        filepath = self.reports_dir / filename
        
        try:
            # Création d'un DataFrame à partir des changements
            all_changes = []
            
            # Changements de prix
            for change in comparison_data.get('price_changes', []):
                all_changes.append({
                    'type': 'Prix',
                    'url': change['url'],
                    'titre': change['title'],
                    'ancienne_valeur': f"{change['old_price']}€",
                    'nouvelle_valeur': f"{change['new_price']}€",
                    'details': f"{change['change_percent']}%"
                })
            
            # Changements de disponibilité
            for change in comparison_data.get('availability_changes', []):
                all_changes.append({
                    'type': 'Disponibilité',
                    'url': change['url'],
                    'titre': change['title'],
                    'ancienne_valeur': change['old_availability'],
                    'nouvelle_valeur': change['new_availability'],
                    'details': ''
                })
            
            if all_changes:
                df = pd.DataFrame(all_changes)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
                logger.info(f"Rapport de comparaison sauvegardé: {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde rapport comparaison: {e}")
            return ""