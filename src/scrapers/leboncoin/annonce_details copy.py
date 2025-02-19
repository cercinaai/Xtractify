import logging
from datetime import datetime
from playwright.sync_api import Page
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from src.database.realStateLbc import save_annonce_to_db, annonce_exists, RealStateLBCModel
from playwright.sync_api import expect
from src.utils.human_behavior import human_like_delay_search

logger = logging.getLogger(__name__)

def scrape_annonce_details(page: Page, ad_url: str):
    """Scrape les détails d'une annonce sur Leboncoin et l'enregistre en base de données si elle n'existe pas encore."""
    try:
        # Attendre que la page soit complètement chargée
        title_element = page.locator("h1.text-headline-1-expanded.u-break-word")
        expect(title_element).to_be_visible(timeout=60000)
        human_like_delay_search(2, 3)
        logger.info("✅ Annonce ouverte avec succès")

        # Si un bouton "Voir plus" est présent, cliquer dessus pour charger la description complète
        voir_plus_button = page.locator("div[data-qa-id='adview_description_container'] button")
        if voir_plus_button.count() > 0:
            voir_plus_button.first.click()
            human_like_delay_search(2, 3)

        # Extraction du contenu HTML et création d'un objet BeautifulSoup
        html_content = page.content()
        soup = BeautifulSoup(html_content, "html.parser")
        logger.info("🔍 Extraction des détails de l'annonce...")

        # Récupération de l'ID de l'annonce depuis l'URL
        parsed_url = urlparse(ad_url)
        annonce_id = parsed_url.path.split("/")[-1]

        # Vérification si l'annonce existe déjà en base
        if annonce_exists(annonce_id):
            logger.info(f"🔁 L'annonce {annonce_id} existe déjà en base de données.")
            return None

        # Fonction d'extraction sécurisée
        def get_text(selector, default="Pas trouvé"):
            element = soup.select_one(selector)
            return element.get_text(strip=True) if element else default

        # Extraction des informations de base
        title = get_text("h1.text-headline-1-expanded.u-break-word", "Titre non disponible")
        price = get_text("div.flex p.text-headline-2")
        charges_comprises = get_text("div.flex p.text-caption.font-semi-bold.ml-md")
        date_publication = get_text("p.text-caption.opacity-dim-1")

         # Extraction des critères
        criteria_dict = {}
        criteria_sections = soup.select("div[data-test-id='criteria']")
        for criterion in criteria_sections:
            label_elem = criterion.select_one("p.text-caption")
            value_elem = criterion.select_one("p.font-bold")
            if label_elem and value_elem:
                label = label_elem.get_text(strip=True)
                value = value_elem.get_text(strip=True)
                criteria_dict[label] = value

        # Extraction de la localisation avec plusieurs alternatives
        # Extraction de la localisation avec le nouveau sélecteur
        location_anchor = soup.select_one("a.text-body-1[href='#map']")
        if location_anchor:
            location_text = location_anchor.get_text(strip=True)
            parts = location_text.rsplit(" ", 1)
            if len(parts) == 2:
                city = parts[0]
                postal_code = parts[1]
            else:
                city = location_text
                postal_code = "Pas trouvé"
        else:
            city = "Pas trouvé"
            postal_code = "Pas trouvé"
        logger.info(f"📍 Localisation extraite : {city} ({postal_code})")

        # Extraction des informations de l'agence avec le nouveau sélecteur
        agence_container = soup.select_one("div.flex.justify-between a.block.truncate")
        if agence_container:
            agence_nom = agence_container.get_text(strip=True)
        else:
            agence_nom = "Pas trouvé"

        # Extraction de la description complète
        description = get_text("div[data-qa-id='adview_description_container']", "Pas trouvé")

        # Extraction des critères complémentaires avec valeurs par défaut
        type_vente = criteria_dict.get("Type de vente", "Pas trouvé")
        type_bien = criteria_dict.get("Type de bien", "Pas trouvé")
        meuble = criteria_dict.get("Ce bien est :", "Pas trouvé")
        surface = criteria_dict.get("Surface habitable", "Pas trouvé")
        surface_terrain = criteria_dict.get("Surface totale du terrain", "Pas trouvé")
        nombre_pieces = criteria_dict.get("Nombre de pièces", "Pas trouvé")
        nombre_chambres = criteria_dict.get("Nombre de chambres", "Pas trouvé")
        nombre_salles_bain = criteria_dict.get("Nombre de salle de bain", "Pas trouvé")
        nombre_salles_eau = criteria_dict.get("Nombre de salle d'eau", "Pas trouvé")
        nombre_niveaux = criteria_dict.get("Nombre de niveaux", "Pas trouvé")
        # Extraction de la classe énergétique à partir de la liste d'icônes
        energy_criteria_container = soup.select_one("div[data-test-id='energy-criteria']")
        if energy_criteria_container:
            # Rechercher l'élément sélectionné (par exemple, celui qui contient "drop-shadow-sm")
            selected_energy = energy_criteria_container.find("div", class_="drop-shadow-sm")
            if selected_energy:
                classe_energetique = selected_energy.get_text(strip=True)
            else:
                # En l'absence d'un élément marqué, on prend le premier élément de la liste
                first_energy = energy_criteria_container.select_one("div")
                classe_energetique = first_energy.get_text(strip=True) if first_energy else "Pas trouvé"
        else:
            classe_energetique = "Pas trouvé"

        # Extraction du critère GES via criteria_dict
        ges = criteria_dict.get("GES", "Pas trouvé")
        ges = criteria_dict.get("GES", "Pas trouvé")
        annee_construction = criteria_dict.get("Année de construction", "Pas trouvé")
        charges_honoraires = criteria_dict.get("Charges honoraires", "Pas trouvé")
        charges_copropriete_annuelle = criteria_dict.get("Charges de copropriété annuelle", "Pas trouvé")
        depot_garantie = criteria_dict.get("Dépôt de garantie", "Pas trouvé")
        place_parking = criteria_dict.get("Places de parking", "Pas trouvé")
        exterieur = criteria_dict.get("Extérieur", "Pas trouvé")
        nature_bien = criteria_dict.get("Nature du bien", "Pas trouvé")
        caracteristiques = criteria_dict.get("Caractéristiques", "Pas trouvé")
        charges_incluses = criteria_dict.get("Charges incluses", "Pas trouvé")
        reference = criteria_dict.get("Référence", "Pas trouvé")
        
        # Création du modèle avec les données extraites
        annonce_data = RealStateLBCModel(
            id=str(annonce_id),
            title=title,
            price=price,
            charges_comprises=charges_comprises,
            date_publication=date_publication,
            location=location_text,
            code_postal=postal_code,
            city=city,
            surface=surface,
            surface_terrain=surface_terrain,
            nombre_pieces=nombre_pieces,
            nombre_chambres=nombre_chambres,
            nombre_salles_bain=nombre_salles_bain,
            nombre_salles_eau=nombre_salles_eau,
            nombre_niveaux=nombre_niveaux,
            description=description,
            type_vente=type_vente,
            type_bien=type_bien,
            meuble=meuble,
            classe_energetique=classe_energetique,
            ges=ges,
            annee_construction=annee_construction,
            charges_honoraires=charges_honoraires,
            charges_copropriete_annuelle=charges_copropriete_annuelle,
            depot_garantie=depot_garantie,
            place_parking=place_parking,
            exterieur=exterieur,
            nature_bien=nature_bien,
            caracteristiques=caracteristiques,
            charges_incluses=charges_incluses,
            reference=reference,
            agence_nom=agence_nom,
            # agence_siren=agence_siren,
            ad_url=str(ad_url),
            scraped_at=datetime.utcnow()
        )

        # Enregistrement en base de données
        save_annonce_to_db(annonce_data)
        logger.info(f"✅ Annonce enregistrée avec succès : {annonce_id}")
        
        return annonce_data

    except Exception as e:
        logger.error(f"🚨 Erreur lors du scraping : {str(e)}")
        return None