"""
crops.py — extrai dados de cultivos da Stardew Valley Wiki

Fonte: https://stardewvalleywiki.com/Crops

A wiki reestruturou a página de cultivos: antes era uma wikitable por estação,
agora cada cultivo tem sua própria subseção ===CropName=== com uma wikitable interna.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base import (
    fetch_wikitext,
    meta,
    strip_wikilink,
    validate_and_save,
    Crop,
    CropCalc,
)

WIKI_PAGE = "Crops"
SEASONS = ["spring", "summer", "fall", "winter"]
TRELLIS_CROPS = {"Green Bean", "Hops", "Grape"}


def extract_crop_name(header: str) -> str | None:
    """Extrai nome do cultivo do header ===[[File:X.png]] [[CropName]]===."""
    # Remove [[File:...]] e extrai o wikilink do nome
    cleaned = re.sub(r"\[\[File:[^\]]+\]\]\s*", "", header)
    name = strip_wikilink(cleaned.strip())
    return name if name else None


def parse_crop_section(section_text: str, name: str, season: str) -> dict:
    """
    Parseia a subseção de um único cultivo e extrai os dados chave.
    A nova estrutura da wiki tem templates {{Qualityprice}} e {{Price}} em vez de colunas de tabela.
    """
    crop: dict = {"name": name, "season": season, "ccBundle": None}

    # Preço de venda: {{Qualityprice|CropName|PRICE|...}}
    sell_match = re.search(r"\{\{Qualityprice\|[^|]+\|(\d+)", section_text)
    crop["sellPrice"] = int(sell_match.group(1)) if sell_match else None

    # Preço da semente: primeiro {{Price|X}} da seção (coluna Seeds)
    price_matches = re.findall(r"\{\{Price\|(\d+)\}\}", section_text)
    crop["seedPrice"] = int(price_matches[0]) if price_matches else None

    # Dias de crescimento: "Total: X days"
    total_match = re.search(r"Total:\s*(\d+)\s*days?", section_text, re.IGNORECASE)
    crop["growthDays"] = int(total_match.group(1)) if total_match else None

    # Dias de rebrota: "Regrowth: X days" ou "Regrowth:\nX days"
    regrow_match = re.search(
        r"Regrowth:.*?(\d+)\s*days?", section_text, re.IGNORECASE | re.DOTALL
    )
    crop["regrowDays"] = int(regrow_match.group(1)) if regrow_match else None

    # Fonte/loja: [[Store|Name]]: {{Price  ou  [[Store]]: {{Price
    source_matches = re.findall(
        r"\[\[(?:File:[^\]]+\|[^\]]+|[^\]|]+)(?:\|([^\]]+))?\]\]:\s*\{\{Price",
        section_text,
    )
    # Extrai o nome do link mais próximo antes de cada ": {{Price"
    source_links = re.findall(
        r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]:\s*\{\{Price", section_text
    )
    sources = [(display or full).strip() for full, display in source_links if (display or full).strip()]
    crop["source"] = ", ".join(sources) if sources else None

    # Trellis: cultivos conhecidos que precisam de treliça
    if name in TRELLIS_CROPS:
        crop["trellis"] = True

    return crop


def scrape() -> dict:
    print(f"[crops] Buscando página: {WIKI_PAGE}")
    wikitext = fetch_wikitext(WIKI_PAGE)

    if not wikitext:
        raise RuntimeError(f"Falha ao buscar página {WIKI_PAGE}")

    # Nova estrutura: == Spring Crops ==, == Summer Crops ==, etc.
    section_pattern = re.compile(
        r"==\s*(Spring|Summer|Fall|Winter)\s+Crops\s*==", re.IGNORECASE
    )
    parts = section_pattern.split(wikitext)

    all_crops = []

    # parts = [antes, "Spring", conteudo_spring, "Summer", conteudo_summer, ...]
    i = 1
    while i < len(parts) - 1:
        season_name = parts[i].lower()
        section_content = parts[i + 1]

        if season_name in SEASONS:
            print(f"  → Parseando {season_name}...")

            # Divide por subseções ===[[File:CropName.png]] [[CropName]]===
            crop_blocks = re.split(r"(?====\[\[File:)", section_content)

            season_crops = []
            for block in crop_blocks:
                header_match = re.match(r"===(.+?)===", block)
                if not header_match:
                    continue

                name = extract_crop_name(header_match.group(1))
                if not name:
                    continue

                crop = parse_crop_section(block, name, season_name)

                sell = crop.get("sellPrice")
                seed = crop.get("seedPrice")
                growth = crop.get("growthDays")
                regrow = crop.get("regrowDays")

                if sell and seed and growth:
                    days_remaining_after_first = 28 - growth
                    if regrow and days_remaining_after_first > 0:
                        extra_harvests = days_remaining_after_first // regrow
                        total_harvests = 1 + extra_harvests
                    else:
                        total_harvests = max(1, 28 // (growth + 1))

                    total_revenue = sell * total_harvests
                    net_profit = total_revenue - seed
                    crop["_calc"] = {
                        "estimatedHarvests28days": total_harvests,
                        "estimatedNetProfit28days": net_profit,
                        "profitPerDay": round(net_profit / 28, 1),
                    }

                season_crops.append(crop)

            print(f"     {len(season_crops)} cultivos encontrados")
            all_crops.extend(season_crops)

        i += 2

    return {
        "_meta": meta(WIKI_PAGE),
        "crops": all_crops,
    }


if __name__ == "__main__":
    data = scrape()
    validate_and_save("crops.json", data, "crops")
    print(f"\nTotal: {len(data['crops'])} cultivos")
