from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scrapers.scraper_base import ScraperBase

@dataclass
class RentalOffer:
    """Nabídka pronájmu bytu"""

    link: str
    """URL adresa na nabídku"""

    title: str
    """Popis nabídky (nejčastěji počet pokojů, výměra)"""

    location: str
    """Lokace bytu (městská část, ulice)"""

    price: int | str
    """Cena pronájmu za měsíc bez poplatků a energií"""

    image_url: str
    """Náhledový obrázek nabídky"""

    scraper: "ScraperBase"
    """Odkaz na instanci scrapera, ze kterého tato nabídka pochází"""
