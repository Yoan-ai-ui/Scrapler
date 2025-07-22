# 🕷️ Bot de Veille Concurrentielle E-commerce

Un bot Python professionnel pour surveiller automatiquement les prix et la disponibilité des produits concurrents sur les principales plateformes e-commerce.

## 🎯 Fonctionnalités Principales

### ✅ Sites Supportés
- **Shopify** (tous les sites .myshopify.com)
- **Amazon** (Amazon.fr, Amazon.com, etc.)
- **Etsy** (marketplace créateurs)
- **Leboncoin** (petites annonces)
- **Beacon.by** (services freelances)
- **Fiverr** (services freelances)

### 📊 Données Collectées
- Titre du produit
- Prix actuel
- Disponibilité (en stock/rupture)
- Note et nombre d'avis
- Description courte
- Historique des changements

### 🚀 Modes d'Utilisation
- **Scraping ponctuel** : Analyse immédiate
- **Surveillance périodique** : Contrôle automatique (cron job intégré)
- **Alertes intelligentes** : Notifications par email des changements

## 🛠️ Installation

### Pré-requis
- Python 3.8+
- pip (gestionnaire de paquets Python)

### Installation des dépendances
```bash
python -m pip install -r requirements.txt
```

### Configuration (optionnel)
Copiez le fichier de configuration :
```bash
cp .env.example .env
```

Éditez `.env` pour configurer les alertes email :
```env
EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=votre_email@gmail.com
EMAIL_PASSWORD=votre_mot_de_passe_app
EMAIL_RECIPIENTS=destinataire@email.com
```

## 📋 Utilisation

### 1. Préparer le fichier d'URLs

Créez un fichier CSV avec vos URLs à surveiller :

```csv
url,name,category
https://www.amazon.fr/dp/B08N5WRWNW,Echo Dot,Électronique
https://www.etsy.com/listing/123456789/custom-mug,Mug Personnalisé,Maison
https://example-shop.myshopify.com/products/t-shirt,T-Shirt Mode,Vêtements
```

Ou un simple fichier TXT :
```txt
https://www.amazon.fr/dp/B08N5WRWNW
https://www.etsy.com/listing/123456789/custom-mug
https://example-shop.myshopify.com/products/t-shirt
```

### 2. Lancer le scraping

#### Scraping unique
```bash
python main.py -f data/input_urls.csv
```

#### Scraping avec résumé email
```bash
python main.py -f data/input_urls.csv --summary
```

#### Surveillance continue (toutes les 6 heures)
```bash
python main.py -f data/input_urls.csv --schedule 6
```

#### Mode verbose (détaillé)
```bash
python main.py -f data/input_urls.csv --verbose
```

### 3. Consulter les sites supportés
```bash
python main.py --sites
```

## 📁 Structure du Projet

```
competitive_scraper/
├── main.py                    # Point d'entrée principal
├── config.py                  # Configuration globale
├── requirements.txt           # Dépendances Python
├── README.md                  # Documentation
├── .env.example              # Template de configuration
├── 
├── utils/                     # Utilitaires
│   ├── __init__.py
│   └── file_loader.py        # Chargement des URLs
├── 
├── scrapers/                  # Modules de scraping
│   ├── __init__.py
│   ├── base_scraper.py       # Classe de base
│   ├── scraper_factory.py    # Factory pattern
│   ├── shopify_scraper.py    # Scraper Shopify
│   ├── amazon_scraper.py     # Scraper Amazon
│   ├── etsy_scraper.py       # Scraper Etsy
│   ├── leboncoin_scraper.py  # Scraper Leboncoin
│   ├── beacon_scraper.py     # Scraper Beacon
│   └── fiverr_scraper.py     # Scraper Fiverr
├── 
├── reports/                   # Génération de rapports
│   ├── __init__.py
│   └── report_generator.py   # Rapports CSV et analyses
├── 
├── alerts/                    # Système d'alertes
│   ├── __init__.py
│   └── notifier.py          # Notifications email
├── 
└── data/                     # Données
    └── input_urls.csv        # Exemple d'URLs
```

## 📊 Rapports Générés

### Rapport Principal (CSV)
- Toutes les données collectées
- Métadonnées de scraping (durée, succès/échec)
- Horodatage précis

### Rapport de Comparaison
- Changements de prix (avec pourcentages)
- Modifications de disponibilité
- Nouveaux/anciens produits

### Résumé Exécutif
- Statistiques globales
- Prix moyens par site
- Taux de succès du scraping

## 🔔 Système d'Alertes

### Alertes Prix
- Seuil de changement configurable (défaut: 5%)
- Détection hausse/baisse
- Historique des variations

### Alertes Stock
- Passages en rupture de stock
- Retour en disponibilité
- Changements de statut

### Notifications
- Email HTML formaté
- Résumés périodiques
- Rapports d'erreurs

## ⚙️ Configuration Avancée

### Paramètres de Scraping
```python
# Dans config.py
DEFAULT_TIMEOUT = 10          # Timeout requêtes (secondes)
MAX_RETRIES = 3              # Nombre de tentatives
DELAY_BETWEEN_REQUESTS = 2   # Délai entre requêtes
PRICE_CHANGE_THRESHOLD = 5.0 # Seuil d'alerte prix (%)
```

### Anti-détection
- Rotation automatique des User-Agents
- Délais aléatoires entre requêtes
- Headers HTTP réalistes
- Gestion des codes d'erreur 403/429

## 🎛️ Personnalisation

### Ajouter un nouveau site
1. Créer un nouveau scraper dans `scrapers/`
2. Hériter de `BaseScraper`
3. Implémenter `scrape_product()`
4. Ajouter au `ScraperFactory`

```python
class MonSiteScraper(BaseScraper):
    def scrape_product(self, url, product_info=None):
        response = self._make_request(url)
        soup = self._parse_html(response)
        
        return {
            'title': self._extract_text(soup, ['h1', '.title']),
            'price': self._clean_price(price_text),
            'availability': 'En stock',
            'rating': None,
            'review_count': None,
            'description': ''
        }
```

### Personnaliser les sélecteurs
Modifiez `SITE_CONFIGS` dans `config.py` :

```python
SITE_CONFIGS = {
    'monsite': {
        'selectors': {
            'title': ['h1.product-name', '.title'],
            'price': ['.price', '.cost'],
            'availability': ['.stock'],
            'reviews': ['.rating'],
            'description': ['.desc']
        }
    }
}
```

## 🚀 Déploiement en Production

### Serveur Linux
```bash
# Crontab pour exécution automatique toutes les 6h
0 */6 * * * /usr/bin/python /path/to/main.py -f /path/to/urls.csv --summary
```

### Docker (optionnel)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py", "-f", "data/input_urls.csv", "--schedule", "6"]
```

### Variables d'environnement
```bash
export EMAIL_ENABLED=true
export SMTP_SERVER=smtp.gmail.com
export EMAIL_USER=bot@monentreprise.com
export EMAIL_PASSWORD=mot_de_passe_application
```

## 📈 Cas d'Usage

### Pour Dropshippers
- Surveiller les prix fournisseurs
- Détecter les ruptures de stock
- Ajuster automatiquement les marges

### Pour E-commerçants
- Analyser la concurrence directe
- Optimiser le pricing
- Identifier les opportunités de marché

### Pour Agences Marketing
- Rapports clients automatisés
- Veille sectorielle
- Analyses comparatives

## 🐛 Dépannage

### Erreurs communes
```bash
# Erreur 403/429 (blocage)
# Solution: Augmenter les délais dans config.py
DELAY_BETWEEN_REQUESTS = 5

# Timeout sur requêtes
# Solution: Augmenter le timeout
DEFAULT_TIMEOUT = 20

# Sélecteurs obsolètes
# Solution: Mettre à jour SITE_CONFIGS
```

### Logs détaillés
```bash
python main.py -f data/input_urls.csv --verbose
```

Les logs sont sauvegardés dans `logs/scraper_YYYYMMDD.log`

## 📄 Licence

Ce projet est sous licence MIT. Voir `LICENSE` pour plus de détails.

## 🤝 Contribution

Les contributions sont les bienvenues ! 

1. Fork le projet
2. Créer une branche feature
3. Commit vos changements
4. Push vers la branche
5. Ouvrir une Pull Request

## 📞 Support

- **Issues GitHub** : Pour les bugs et demandes de fonctionnalités
- **Email** : support@bot-veille.com
- **Documentation** : https://docs.bot-veille.com

---

**⚡ Développé avec passion pour les entrepreneurs du e-commerce ⚡**