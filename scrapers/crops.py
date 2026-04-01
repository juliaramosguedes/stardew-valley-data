"""
crops.py — extrai dados de cultivos da Stardew Valley Wiki

Fonte: https://stardewvalleywiki.com/Crops
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from base import (
    fetch_wikitext,
    parse_wikitext,
    meta,
    normalize_price,
    normalize_days,
    strip_wikilink,
    strip_markup,
    validate_and_save,
    Crop,
    CropCalc,
)

WIKI_PAGE = "Crops"

SEASONS = ["spring", "summer", "fall", "winter"]

# Campos esperados nas wikitables de cultivos
# A wiki pode variar os nomes — listamos aliases
HEADER_ALIASES = {
    "name": ["name", "crop"],
    "seedPrice": ["seed price", "seeds price", "price", "cost"],
    "growthDays": ["growth time", "days to grow", "growth", "days"],
    "regrowDays": ["regrowth time", "regrow time", "regrow", "re-grow time"],
    "sellPrice": ["sell price", "base price", "sale price", "value"],
    "source": ["source", "sold at", "where to buy"],
    "ccBundle": ["bundle", "cc bundle", "community center"],
    "trellis": ["trellis"],
    "notes": ["notes", "note"],
}


def normalize_header(raw: str) -> str | None:
    """Mapeia header da wikitable para chave canônica."""
    raw = raw.strip().lower()
    for key, aliases in HEADER_ALIASES.items():
        if raw in aliases:
            return key
    return None


def parse_crop_table(table_text: str, season: str) -> list[dict]:
    """
    Parseia uma wikitable de cultivos e retorna lista de dicts normalizados.
    Lida com variações de formatação da wiki.
    """
    lines = [l.rstrip() for l in table_text.split("\n")]

    headers_raw = []
    headers = []
    rows = []
    current_cells = []
    in_row = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("!"):
            # Linha de headers: pode ser "! Name !! Price !! ..."
            parts = re.split(r"!!|\|!", stripped.lstrip("!"))
            headers_raw = [p.strip() for p in parts]
            headers = [normalize_header(h) for h in headers_raw]

        elif stripped == "|-":
            # Separador de linha
            if in_row and current_cells:
                rows.append(current_cells)
            current_cells = []
            in_row = True

        elif stripped.startswith("|") and not stripped.startswith("|}") and not stripped.startswith("{|"):
            # Célula(s) de dados
            cell_content = stripped.lstrip("|")
            # Múltiplas células na mesma linha: "| val1 || val2 || val3"
            cells = re.split(r"\|\|", cell_content)
            current_cells.extend([c.strip() for c in cells])

    # Última linha
    if in_row and current_cells:
        rows.append(current_cells)

    # Montar objetos
    crops = []
    for cells in rows:
        if not cells:
            continue

        crop = {"season": season}

        for i, key in enumerate(headers):
            if key is None or i >= len(cells):
                continue
            raw_val = cells[i]

            if key == "name":
                crop["name"] = strip_wikilink(raw_val)

            elif key in ("seedPrice", "sellPrice"):
                crop[key] = normalize_price(strip_markup(raw_val))

            elif key in ("growthDays", "regrowDays"):
                crop[key] = normalize_days(strip_markup(raw_val))

            elif key == "trellis":
                val = strip_markup(raw_val).lower()
                crop["trellis"] = val in ("yes", "true", "✓")

            elif key == "ccBundle":
                val = strip_markup(raw_val)
                crop["ccBundle"] = val if val not in ("—", "-", "N/A", "") else None

            else:
                crop[key] = strip_markup(raw_val) or None

        # Só inclui se tiver nome
        if crop.get("name"):
            # Calcular lucro por dia (sem fertilizante, sem profissão)
            sell = crop.get("sellPrice")
            seed = crop.get("seedPrice")
            growth = crop.get("growthDays")
            regrow = crop.get("regrowDays")

            if sell and seed and growth:
                # Colheitas possíveis em 28 dias
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

            crops.append(crop)

    return crops


def scrape() -> dict:
    print(f"[crops] Buscando página: {WIKI_PAGE}")
    wikitext = fetch_wikitext(WIKI_PAGE)

    if not wikitext:
        raise RuntimeError(f"Falha ao buscar página {WIKI_PAGE}")

    # Dividir por seção de estação
    # Padrão wiki: == Spring == ... == Summer == ...
    section_pattern = re.compile(r"==\s*(Spring|Summer|Fall|Winter)\s*==", re.IGNORECASE)
    parts = section_pattern.split(wikitext)

    all_crops = []

    # parts = [texto_antes, "Spring", conteudo_spring, "Summer", conteudo_summer, ...]
    i = 1
    while i < len(parts) - 1:
        season_name = parts[i].lower()
        section_content = parts[i + 1]

        if season_name in SEASONS:
            print(f"  → Parseando {season_name}...")
            crops = parse_crop_table(section_content, season_name)
            print(f"     {len(crops)} cultivos encontrados")
            all_crops.extend(crops)

        i += 2

    return {
        "_meta": meta(WIKI_PAGE),
        "crops": all_crops,
    }


if __name__ == "__main__":
    data = scrape()
    validate_and_save("crops.json", data, "crops")
    print(f"\nTotal: {len(data['crops'])} cultivos")
