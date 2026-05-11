from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scrapers.scraper_base import ScraperBase


def parse_monthly_price_czk(price: int | str) -> int | None:
    """Vrátí měsíční nájem v Kč jako celé číslo, nebo None pokud ho nejde spolehlivě určit."""

    if isinstance(price, int):
        return price if price > 0 else None
    text = str(price).strip()
    if not text:
        return None
    i = 0
    while i < len(text) and not text[i].isdigit():
        i += 1
    if i >= len(text):
        return None
    digits: list[str] = []
    while i < len(text) and (text[i].isdigit() or text[i].isspace()):
        if text[i].isdigit():
            digits.append(text[i])
        i += 1
    if not digits:
        return None
    return int("".join(digits))


def offer_matches_price_range(
    offer: "RentalOffer", price_min_kc: int | None, price_max_kc: int | None
) -> bool:
    """Vrátí True, pokud se nabídka má oznámit při daném filtru ceny.

    Není-li nastavena žádná mez, projde vždy. Je-li aspoň jedna mez nastavená
    a z ceny nepůjde vyčíst číslo, projde také (konzervativně). Jinak musí
    vyčtená měsíční cena splnit všechny nastavené meze (dolní včetně, horní
    včetně).
    """

    if price_min_kc is None and price_max_kc is None:
        return True
    parsed = parse_monthly_price_czk(offer.price)
    if parsed is None:
        return True
    if price_min_kc is not None and parsed < price_min_kc:
        return False
    if price_max_kc is not None and parsed > price_max_kc:
        return False
    return True


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
