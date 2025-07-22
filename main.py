#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot de Veille Concurrentielle E-commerce
=========================================

Ce bot scrape automatiquement les prix et informations des produits concurrents
sur diverses plateformes e-commerce et génère des rapports détaillés.

Auteur: Bot de Veille Concurrentielle
Version: 1.0.0
"""

import argparse
import logging
import schedule
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import colorama
from colorama import Fore, Style

# Import des modules locaux
from config import Config
from utils.file_loader import FileLoader
from scrapers.scraper_factory import ScraperFactory
from reports.report_generator import ReportGenerator
from alerts.notifier import EmailNotifier

# Initialisation
colorama.init(autoreset=True)
logger = logging.getLogger(__name__)

class CompetitiveScraper:
    """Classe principale du bot de veille concurrentielle"""
    
    def __init__(self):
        self.config = Config()
        self.file_loader = FileLoader()
        self.report_generator = ReportGenerator()
        self.notifier = EmailNotifier()
        
        # Configuration du logging
        self._setup_logging()
        
        # Création des dossiers nécessaires
        self._create_directories()
        
    def _setup_logging(self):
        """Configure le système de logging"""
        logs_dir = Path(self.config.LOGS_DIR)
        logs_dir.mkdir(exist_ok=True)
        
        # Format des logs
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Handler pour fichier
        file_handler = logging.FileHandler(
            logs_dir / f"scraper_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setFormatter(formatter)
        
        # Handler pour console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Configuration du logger principal
        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, console_handler]
        )
        
        # Suppression des logs excessifs de requests
        logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    def _create_directories(self):
        """Crée les répertoires nécessaires"""
        directories = [
            self.config.REPORTS_DIR,
            self.config.DATA_DIR,
            self.config.LOGS_DIR
        ]
        
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def load_urls(self, file_path: str) -> List[Dict]:
        """
        Charge les URLs depuis un fichier
        
        Args:
            file_path: Chemin vers le fichier d'URLs
            
        Returns:
            Liste des URLs avec métadonnées
        """
        logger.info(f"Chargement des URLs depuis: {file_path}")
        urls_data = self.file_loader.load_urls(file_path)
        
        if not urls_data:
            logger.error("Aucune URL valide trouvée")
            return []
        
        # Vérification de la compatibilité des sites
        supported_sites = ScraperFactory.get_supported_sites()
        supported_urls = []
        unsupported_count = 0
        
        for url_data in urls_data:
            if ScraperFactory.is_site_supported(url_data['site']):
                supported_urls.append(url_data)
            else:
                unsupported_count += 1
                logger.warning(f"Site non supporté: {url_data['site']} - {url_data['url']}")
        
        logger.info(f"URLs supportées: {len(supported_urls)}")
        if unsupported_count > 0:
            logger.warning(f"URLs non supportées: {unsupported_count}")
        
        return supported_urls
    
    def scrape_products(self, urls_data: List[Dict]) -> List[Dict]:
        """
        Scrape tous les produits de la liste
        
        Args:
            urls_data: Liste des URLs avec métadonnées
            
        Returns:
            Liste des données scrapées
        """
        logger.info(f"Démarrage du scraping de {len(urls_data)} produits")
        
        scraped_data = []
        success_count = 0
        
        for i, url_data in enumerate(urls_data, 1):
            print(f"\n{Fore.CYAN}[{i}/{len(urls_data)}] Scraping: {url_data['url'][:60]}...{Style.RESET_ALL}")
            
            try:
                # Récupération du scraper approprié
                scraper = ScraperFactory.get_scraper(url_data['site'])
                
                if not scraper:
                    logger.error(f"Scraper non disponible pour: {url_data['site']}")
                    continue
                
                # Scraping du produit
                product_data = scraper.get_product_data(url_data['url'], url_data)
                scraped_data.append(product_data)
                
                if product_data['success']:
                    success_count += 1
                    print(f"{Fore.GREEN}✓ Succès: {product_data['title'][:40]}...{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}✗ Échec: {product_data['error_message']}{Style.RESET_ALL}")
                
                # Délai entre les requêtes
                if i < len(urls_data):
                    time.sleep(self.config.DELAY_BETWEEN_REQUESTS)
                
            except Exception as e:
                logger.error(f"Erreur scraping {url_data['url']}: {e}")
                scraped_data.append({
                    'url': url_data['url'],
                    'success': False,
                    'error_message': str(e),
                    'scraped_at': datetime.now().isoformat()
                })
        
        print(f"\n{Fore.YELLOW}Résumé du scraping:{Style.RESET_ALL}")
        print(f"  • Total: {len(scraped_data)} produits")
        print(f"  • Réussis: {success_count}")
        print(f"  • Échoués: {len(scraped_data) - success_count}")
        
        return scraped_data
    
    def generate_reports(self, scraped_data: List[Dict]) -> Dict[str, str]:
        """
        Génère les rapports à partir des données scrapées
        
        Args:
            scraped_data: Données scrapées
            
        Returns:
            Dictionnaire avec les chemins des rapports générés
        """
        logger.info("Génération des rapports")
        
        reports_generated = {}
        
        # Rapport CSV principal
        csv_report = self.report_generator.generate_csv_report(scraped_data)
        if csv_report:
            reports_generated['csv'] = csv_report
            print(f"{Fore.GREEN}✓ Rapport CSV généré: {csv_report}{Style.RESET_ALL}")
        
        # Rapport de synthèse
        summary = self.report_generator.generate_summary_report(scraped_data)
        if summary:
            print(f"\n{Fore.CYAN}Synthèse:{Style.RESET_ALL}")
            print(f"  • Produits analysés: {summary['total_products']}")
            print(f"  • Scraping réussi: {summary['successful_scrapes']}")
            print(f"  • Sites différents: {summary['sites_scraped']}")
            print(f"  • Prix moyen: {summary['average_price']:.2f}€")
        
        # Sauvegarde des données historiques
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        historical_file = Path(self.config.DATA_DIR) / f"historical_data_{timestamp}.csv"
        self.file_loader.save_historical_data(scraped_data, str(historical_file))
        
        return reports_generated
    
    def check_changes_and_alert(self, current_data: List[Dict]):
        """
        Vérifie les changements par rapport aux données historiques et envoie des alertes
        
        Args:
            current_data: Données actuelles
        """
        logger.info("Vérification des changements")
        
        # Recherche du fichier historique le plus récent
        data_dir = Path(self.config.DATA_DIR)
        historical_files = list(data_dir.glob("historical_data_*.csv"))
        
        if len(historical_files) < 2:
            logger.info("Pas assez de données historiques pour comparaison")
            return
        
        # Tri par date (le plus récent en premier)
        historical_files.sort(reverse=True)
        previous_file = historical_files[1]  # Le fichier précédent (pas le plus récent)
        
        # Chargement des données historiques
        historical_df = self.file_loader.load_historical_data(str(previous_file))
        
        if historical_df is None:
            logger.error("Impossible de charger les données historiques")
            return
        
        historical_data = historical_df.to_dict('records')
        
        # Génération du rapport de comparaison
        comparison_report = self.report_generator.generate_comparison_report(
            current_data, historical_data
        )
        
        if not comparison_report:
            return
        
        # Sauvegarde du rapport de comparaison
        comparison_file = self.report_generator.save_comparison_report(comparison_report)
        if comparison_file:
            print(f"{Fore.GREEN}✓ Rapport de comparaison: {comparison_file}{Style.RESET_ALL}")
        
        # Envoi des alertes
        if comparison_report.get('price_changes'):
            self.notifier.send_price_change_alert(comparison_report['price_changes'])
            print(f"{Fore.YELLOW}📧 Alerte prix envoyée: {len(comparison_report['price_changes'])} changements{Style.RESET_ALL}")
        
        if comparison_report.get('availability_changes'):
            self.notifier.send_availability_alert(comparison_report['availability_changes'])
            print(f"{Fore.YELLOW}📧 Alerte stock envoyée: {len(comparison_report['availability_changes'])} changements{Style.RESET_ALL}")
    
    def run_single_scraping(self, urls_file: str, send_summary: bool = False):
        """
        Exécute un scraping unique
        
        Args:
            urls_file: Fichier contenant les URLs
            send_summary: Si True, envoie un résumé par email
        """
        print(f"{Fore.BLUE}🚀 Démarrage du scraping unique{Style.RESET_ALL}")
        print(f"Fichier d'URLs: {urls_file}")
        
        # Chargement des URLs
        urls_data = self.load_urls(urls_file)
        if not urls_data:
            print(f"{Fore.RED}❌ Aucune URL valide trouvée{Style.RESET_ALL}")
            return
        
        # Scraping
        scraped_data = self.scrape_products(urls_data)
        
        # Génération des rapports
        reports = self.generate_reports(scraped_data)
        
        # Vérification des changements et alertes
        self.check_changes_and_alert(scraped_data)
        
        # Envoi du résumé par email si demandé
        if send_summary:
            summary = self.report_generator.generate_summary_report(scraped_data)
            self.notifier.send_summary_report(summary)
            print(f"{Fore.GREEN}📧 Résumé envoyé par email{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}✅ Scraping terminé avec succès{Style.RESET_ALL}")
    
    def schedule_periodic_scraping(self, urls_file: str, interval_hours: int):
        """
        Programme un scraping périodique
        
        Args:
            urls_file: Fichier contenant les URLs
            interval_hours: Intervalle en heures entre chaque scraping
        """
        print(f"{Fore.BLUE}⏰ Configuration du scraping périodique{Style.RESET_ALL}")
        print(f"Fichier d'URLs: {urls_file}")
        print(f"Intervalle: {interval_hours} heures")
        
        def scheduled_job():
            print(f"\n{Fore.CYAN}🔄 Démarrage du scraping programmé - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
            self.run_single_scraping(urls_file, send_summary=True)
        
        # Première exécution immédiate
        scheduled_job()
        
        # Programmation des exécutions suivantes
        schedule.every(interval_hours).hours.do(scheduled_job)
        
        print(f"{Fore.GREEN}✅ Scraping périodique configuré{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Appuyez sur Ctrl+C pour arrêter{Style.RESET_ALL}")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Vérification chaque minute
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}🛑 Arrêt du scraping périodique{Style.RESET_ALL}")

def main():
    """Fonction principale avec interface en ligne de commande"""
    
    parser = argparse.ArgumentParser(
        description="Bot de Veille Concurrentielle E-commerce",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python main.py -f data/input_urls.csv                    # Scraping unique
  python main.py -f data/input_urls.csv --summary          # Scraping avec résumé email  
  python main.py -f data/input_urls.csv --schedule 6       # Scraping toutes les 6h
  python main.py --sites                                   # Liste des sites supportés
        """
    )
    
    parser.add_argument(
        '-f', '--file',
        help='Fichier CSV/TXT contenant les URLs des produits à scraper'
    )
    
    parser.add_argument(
        '--schedule',
        type=int,
        metavar='HOURS',
        help='Active le scraping périodique avec intervalle en heures'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Envoie un résumé par email après le scraping'
    )
    
    parser.add_argument(
        '--sites',
        action='store_true',
        help='Affiche la liste des sites supportés'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mode verbose (affichage détaillé)'
    )
    
    args = parser.parse_args()
    
    # Configuration du niveau de logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Affichage des sites supportés
    if args.sites:
        sites = ScraperFactory.get_supported_sites()
        print(f"\n{Fore.CYAN}Sites supportés:{Style.RESET_ALL}")
        for site in sorted(sites):
            print(f"  • {site.capitalize()}")
        print(f"\nTotal: {len(sites)} sites supportés")
        return
    
    # Vérification des arguments
    if not args.file:
        print(f"{Fore.RED}❌ Fichier d'URLs requis. Utilisez -f ou --file{Style.RESET_ALL}")
        print("Exemple: python main.py -f data/input_urls.csv")
        sys.exit(1)
    
    if not Path(args.file).exists():
        print(f"{Fore.RED}❌ Fichier introuvable: {args.file}{Style.RESET_ALL}")
        sys.exit(1)
    
    # Initialisation du scraper
    try:
        scraper = CompetitiveScraper()
        
        # Exécution selon les arguments
        if args.schedule:
            scraper.schedule_periodic_scraping(args.file, args.schedule)
        else:
            scraper.run_single_scraping(args.file, args.summary)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠️  Arrêt demandé par l'utilisateur{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}❌ Erreur critique: {e}{Style.RESET_ALL}")
        logger.exception("Erreur critique")
        sys.exit(1)

if __name__ == "__main__":
    main()