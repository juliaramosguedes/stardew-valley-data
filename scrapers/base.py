"""
base.py — cliente MediaWiki API + utilitários compartilhados

Fonte: https://stardewvalleywiki.com
Licença: CC BY-NC-SA 3.0
"""

import re
import json
import time
import requests
import mwparserfromhell
import jsonschema
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict, Literal, NotRequired

WIKI_API = "https://stardewvalleywiki.com/mediawiki/api.php"
GAME_VERSION = "1.6"
DATA_DIR = Path(__file__).parent.parent / "data"
SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"

# Respeitar o servidor: 1 request por segundo
REQUEST_DELAY = 1.0

# ─── Python types (TypedDicts) ────────────────────────────────────────────────
# Espelham os JSON Schemas em schemas/*.schema.json
# Usados para type hints nos scrapers — não são exportados para o site
# O site (stardew-guide) define seus próprios tipos TypeScript à mão

Season = Literal["spring", "summer", "fall", "winter"]
Quality = Literal["normal", "silver", "gold", "iridium"]
StrategicValue = Literal["critical", "high", "medium", "low"]


class Meta(TypedDict):
    source: str
    license: str
    credit: str
    gameVersion: str
    generatedAt: str


class CropCalc(TypedDict):
    estimatedHarvests28days: int
    estimatedNetProfit28days: int
    profitPerDay: float


class Crop(TypedDict):
    name: str
    season: Season
    seedPrice: int | None
    growthDays: int | None
    regrowDays: int | None
    sellPrice: int | None
    source: str | None
    ccBundle: str | None
    trellis: NotRequired[bool]
    notes: NotRequired[str | None]
    _calc: NotRequired[CropCalc]


class ShopItem(TypedDict):
    item: str
    price: int | None
    note: str


class Festival(TypedDict):
    name: str
    season: Season
    day: int
    dayEnd: NotRequired[int]
    location: str
    time: str
    highlights: list[str]
    shopItems: list[ShopItem]
    strategicValue: StrategicValue
    year1Notes: str


class BundleItem(TypedDict):
    item: str
    quantity: int
    quality: NotRequired[Quality]
    season: NotRequired[str]
    source: NotRequired[str]
    location: NotRequired[str]


class Bundle(TypedDict):
    name: str
    reward: str
    items: list[BundleItem]
    year1Strategy: NotRequired[str]
    note: NotRequired[str]


class CCRoom(TypedDict):
    room: str
    roomReward: str
    roomRewardNote: NotRequired[str]
    bundles: list[Bundle]
    note: NotRequired[str]


class CCStats(TypedDict):
    totalRooms: int
    totalBundles: int
    totalItems: int


def fetch_wikitext(page: str) -> str:
    """
    Busca o wikitext de uma página via MediaWiki API.
    Retorna string vazia se a página não existir.
    """
    params = {
        "action": "parse",
        "page": page,
        "prop": "wikitext",
        "format": "json",
        "redirects": True,
    }

    headers = {
        "User-Agent": "stardew-data/1.0 (https://github.com/juliaramosguedes/stardew-data)"
    }

    time.sleep(REQUEST_DELAY)

    resp = requests.get(WIKI_API, params=params, headers=headers, timeout=15)
    resp.raise_for_status()

    data = resp.json()

    if "error" in data:
        print(f"[WARN] Página não encontrada: {page} — {data['error']}")
        return ""

    return data["parse"]["wikitext"]["*"]


def parse_wikitext(raw: str):
    """Retorna objeto mwparserfromhell parseado."""
    return mwparserfromhell.parse(raw)


def meta(source_page: str) -> dict:
    """Gera o bloco _meta padrão para todo JSON gerado."""
    return {
        "source": f"https://stardewvalleywiki.com/{source_page.replace(' ', '_')}",
        "license": "CC BY-NC-SA 3.0",
        "credit": "Stardew Valley Wiki contributors",
        "gameVersion": GAME_VERSION,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }


def normalize_price(val: str) -> int | None:
    """'80g' -> 80, '1,000g' -> 1000, 'N/A' -> None"""
    if not val:
        return None
    val = val.strip().replace(",", "")
    if val in ("N/A", "—", "-", "n/a", ""):
        return None
    val = re.sub(r"g$", "", val, flags=re.IGNORECASE)
    try:
        return int(val)
    except ValueError:
        return None


def normalize_days(val: str) -> int | None:
    """'4 days' -> 4, '1 day' -> 1, 'N/A' -> None"""
    if not val:
        return None
    val = val.strip()
    if val in ("N/A", "—", "-", ""):
        return None
    val = re.sub(r"\s*days?$", "", val, flags=re.IGNORECASE)
    try:
        return int(val)
    except ValueError:
        return None


def strip_wikilink(text: str) -> str:
    """'[[Parsnip|Pastinaga]]' -> 'Parsnip', '[[Parsnip]]' -> 'Parsnip'"""
    text = text.strip()
    match = re.match(r"\[\[([^\|\]]+)(?:\|[^\]]+)?\]\]", text)
    return match.group(1) if match else re.sub(r"\[\[|\]\]", "", text)


def strip_markup(text: str) -> str:
    """Remove qualquer markup wiki restante de uma string."""
    wikicode = mwparserfromhell.parse(text)
    return wikicode.strip_code().strip()


def validate_and_save(filename: str, data: dict, schema_name: str) -> None:
    """Valida o JSON contra o schema antes de salvar. Falha ruidosamente se inválido."""
    schema_path = SCHEMAS_DIR / f"{schema_name}.schema.json"

    if schema_path.exists():
        schema = json.loads(schema_path.read_text())
        try:
            jsonschema.validate(instance=data, schema=schema)
            print(f"  [schema] {schema_name} validado com sucesso")
        except jsonschema.ValidationError as e:
            raise RuntimeError(
                f"Schema inválido para {schema_name}: {e.message}\n"
                f"Caminho: {' → '.join(str(p) for p in e.absolute_path)}"
            )
    else:
        print(f"  [schema] {schema_name}.schema.json não encontrado — pulando validação")

    save_json(filename, data)


def save_json(filename: str, data: dict) -> None:
    """Salva JSON em data/ com indentação e encoding corretos."""
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Salvo: {path}")
