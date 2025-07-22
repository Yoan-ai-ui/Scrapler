import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from config import Config
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailNotifier:
    """Gestionnaire d'alertes par email"""
    
    def __init__(self):
        self.config = Config()
        
    def send_alert(self, subject: str, message: str, recipients: List[str] = None) -> bool:
        """
        Envoie une alerte par email
        
        Args:
            subject: Sujet de l'email
            message: Corps du message
            recipients: Liste des destinataires (optionnel)
            
        Returns:
            True si envoi réussi, False sinon
        """
        if not self.config.EMAIL_ENABLED:
            logger.info("Alertes email désactivées")
            return False
        
        if not recipients:
            recipients = self.config.EMAIL_RECIPIENTS
        
        if not recipients or not self.config.EMAIL_USER or not self.config.EMAIL_PASSWORD:
            logger.error("Configuration email incomplète")
            return False
        
        try:
            # Création du message
            msg = MIMEMultipart()
            msg['From'] = self.config.EMAIL_USER
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Ajout du corps du message
            msg.attach(MIMEText(message, 'html' if '<html>' in message else 'plain'))
            
            # Connexion et envoi
            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                server.starttls()
                server.login(self.config.EMAIL_USER, self.config.EMAIL_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Alerte envoyée à {len(recipients)} destinataires")
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
            return False
    
    def send_price_change_alert(self, price_changes: List[Dict]) -> bool:
        """
        Envoie une alerte pour les changements de prix
        
        Args:
            price_changes: Liste des changements de prix
            
        Returns:
            True si envoi réussi, False sinon
        """
        if not price_changes:
            return True
        
        subject = f"🔔 Alerte Prix - {len(price_changes)} changements détectés"
        
        # Construction du message HTML
        message = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #f8f9fa; padding: 20px; }}
                .alert {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 10px 0; }}
                .price-up {{ color: #e74c3c; font-weight: bold; }}
                .price-down {{ color: #27ae60; font-weight: bold; }}
                .product {{ margin: 15px 0; padding: 10px; border-left: 4px solid #3498db; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🔔 Alerte Changements de Prix</h2>
                <p>Détection de {len(price_changes)} changements de prix significatifs</p>
                <p><strong>Date:</strong> {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
            </div>
            
            <div class="alert">
                <h3>Changements détectés:</h3>
        """
        
        for change in price_changes:
            price_class = "price-up" if change['change_percent'] > 0 else "price-down"
            arrow = "📈" if change['change_percent'] > 0 else "📉"
            
            message += f"""
            <div class="product">
                <h4>{change['title']}</h4>
                <p><strong>Prix précédent:</strong> {change['old_price']:.2f}€</p>
                <p><strong>Prix actuel:</strong> <span class="{price_class}">{change['new_price']:.2f}€</span></p>
                <p><strong>Variation:</strong> <span class="{price_class}">{arrow} {change['change_percent']:.1f}%</span></p>
                <p><a href="{change['url']}" target="_blank">Voir le produit</a></p>
            </div>
            """
        
        message += """
            </div>
        </body>
        </html>
        """
        
        return self.send_alert(subject, message)
    
    def send_availability_alert(self, availability_changes: List[Dict]) -> bool:
        """
        Envoie une alerte pour les changements de disponibilité
        
        Args:
            availability_changes: Liste des changements de disponibilité
            
        Returns:
            True si envoi réussi, False sinon
        """
        if not availability_changes:
            return True
        
        subject = f"📦 Alerte Stock - {len(availability_changes)} changements détectés"
        
        # Construction du message HTML
        message = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #f8f9fa; padding: 20px; }}
                .alert {{ background-color: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; margin: 10px 0; }}
                .in-stock {{ color: #27ae60; font-weight: bold; }}
                .out-of-stock {{ color: #e74c3c; font-weight: bold; }}
                .product {{ margin: 15px 0; padding: 10px; border-left: 4px solid #17a2b8; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📦 Alerte Changements de Stock</h2>
                <p>Détection de {len(availability_changes)} changements de disponibilité</p>
                <p><strong>Date:</strong> {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
            </div>
            
            <div class="alert">
                <h3>Changements détectés:</h3>
        """
        
        for change in availability_changes:
            status_class = "in-stock" if "stock" in change['new_availability'].lower() else "out-of-stock"
            icon = "✅" if "stock" in change['new_availability'].lower() else "❌"
            
            message += f"""
            <div class="product">
                <h4>{change['title']}</h4>
                <p><strong>Ancien statut:</strong> {change['old_availability']}</p>
                <p><strong>Nouveau statut:</strong> <span class="{status_class}">{icon} {change['new_availability']}</span></p>
                <p><a href="{change['url']}" target="_blank">Voir le produit</a></p>
            </div>
            """
        
        message += """
            </div>
        </body>
        </html>
        """
        
        return self.send_alert(subject, message)
    
    def send_summary_report(self, summary_data: Dict) -> bool:
        """
        Envoie un rapport de synthèse par email
        
        Args:
            summary_data: Données de synthèse
            
        Returns:
            True si envoi réussi, False sinon
        """
        subject = f"📊 Rapport de Veille Concurrentielle - {summary_data.get('total_products', 0)} produits"
        
        message = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #e9ecef; padding: 20px; }}
                .stats {{ background-color: #f8f9fa; padding: 15px; margin: 10px 0; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; background: white; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📊 Rapport de Veille Concurrentielle</h2>
                <p><strong>Généré le:</strong> {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
            </div>
            
            <div class="stats">
                <h3>Statistiques Générales</h3>
                <div class="metric">
                    <strong>Produits analysés:</strong><br>
                    {summary_data.get('total_products', 0)}
                </div>
                <div class="metric">
                    <strong>Scraping réussi:</strong><br>
                    {summary_data.get('successful_scrapes', 0)}
                </div>
                <div class="metric">
                    <strong>Sites analysés:</strong><br>
                    {summary_data.get('sites_scraped', 0)}
                </div>
                <div class="metric">
                    <strong>Prix moyen:</strong><br>
                    {summary_data.get('average_price', 0):.2f}€
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_alert(subject, message)