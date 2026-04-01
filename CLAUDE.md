# CLAUDE.md — stardew-data

## Contexto do projeto

Pipeline de dados para o site stardew-guide.
Extrai dados da Stardew Valley Wiki via MediaWiki API, estrutura em JSON e publica via GitHub Actions.

## Stack

- Python 3.12
- mwparserfromhell (parse de wikitext)
- requests (HTTP)
- jsonschema (validação de output)
- GitHub Actions (automação semanal)

## O que fazer primeiro

1. Criar o repositório no GitHub como `stardew-data` (público)
2. Copiar todos os arquivos desta pasta para o repo
3. Instalar dependências: `pip install -r requirements.txt`
4. Rodar os scrapers: `python scrapers/run_all.py`
5. Verificar os JSONs gerados em `data/`
6. Commitar tudo incluindo os JSONs gerados
7. Ativar o GitHub Actions (o workflow já está em `.github/workflows/scrape.yml`)

## Estrutura de arquivos

```
scrapers/base.py              — cliente MediaWiki API + TypedDicts Python + validate_and_save
scrapers/crops.py             — cultivos (parseia wikitable real da wiki)
scrapers/events.py            — festivais (dados estruturados + validação)
scrapers/community_center.py  — bundles do CC (dados estruturados)
scrapers/run_all.py           — executa todos
schemas/                      — JSON Schemas (contrato de dados entre os dois repos)
  crops.schema.json
  events.schema.json
  community_center.schema.json
data/                         — JSONs gerados (commitados no repo)
```

## Contrato de dados

Os JSON Schemas em `schemas/` são a fonte da verdade entre este repo e o `stardew-guide`.

- Python valida o output contra o schema antes de salvar (`validate_and_save` em `base.py`)
- O site `stardew-guide` define seus TypeScript types à mão, espelhando os schemas
- Se o schema mudar: atualizar o `.schema.json` aqui E os types em `stardew-guide/src/types/`

## Como a MediaWiki API funciona

```python
# Busca wikitext de qualquer página
GET https://stardewvalleywiki.com/mediawiki/api.php
  ?action=parse
  &page=Crops
  &prop=wikitext
  &format=json
```

O `base.py` já tem a função `fetch_wikitext(page)` que faz isso.

## Importante: respeitar o servidor

O `base.py` tem `REQUEST_DELAY = 1.0` — 1 request por segundo.
Não remover. A wiki é mantida por voluntários.

## Próximos scrapers a adicionar (depois do MVP)

- `scrapers/fish.py` — peixes por local/estação/condição
  Página: https://stardewvalleywiki.com/Fish
  
- `scrapers/buildings.py` — construções da fazenda
  Página: https://stardewvalleywiki.com/Farm_Buildings

- `scrapers/npcs.py` — NPCs, aniversários, presentes favoritos
  Página: https://stardewvalleywiki.com/Villagers

- `scrapers/upgrades.py` — melhorias de ferramentas
  Página: https://stardewvalleywiki.com/Tools

## Schema padrão de todo JSON gerado

```json
{
  "_meta": {
    "source": "https://stardewvalleywiki.com/Crops",
    "license": "CC BY-NC-SA 3.0",
    "credit": "Stardew Valley Wiki contributors",
    "gameVersion": "1.6",
    "generatedAt": "2026-04-01T..."
  },
  "crops": [...]
}
```

## URLs dos JSONs para o site consumir

Após commitar, os JSONs ficam disponíveis em:

```
https://raw.githubusercontent.com/juliaramosguedes/stardew-data/main/data/crops.json
https://raw.githubusercontent.com/juliaramosguedes/stardew-data/main/data/events.json
https://raw.githubusercontent.com/juliaramosguedes/stardew-data/main/data/community_center.json
```

O site `stardew-guide` vai consumir essas URLs diretamente.

## Validação esperada ao rodar run_all.py

```
==================================================
  CROPS
==================================================
[crops] Buscando página: Crops
  → Parseando spring...
     8+ cultivos encontrados
  → Parseando summer...
  → Parseando fall...
  → Parseando winter...
[OK] Salvo: data/crops.json

==================================================
  EVENTS
==================================================
[events] Usando dados estruturados + validação da wiki
  → Buscando Festivals para validação...
  [OK] Egg Festival validado
  [OK] Luau validado
  ...
[OK] Salvo: data/events.json

==================================================
  COMMUNITY_CENTER
==================================================
[OK] Salvo: data/community_center.json

==================================================
  RESULTADO
==================================================
  ✓ crops
  ✓ events
  ✓ community_center
```

## Se algo falhar

O parser de cultivos (`crops.py`) depende da estrutura da wikitable.
Se a wiki mudar o formato da tabela, o parser pode retornar 0 cultivos.

Nesse caso:
1. Buscar o wikitext real: `python -c "from scrapers.base import fetch_wikitext; print(fetch_wikitext('Crops')[:2000])"`
2. Verificar a estrutura das linhas `!` (headers) e `|` (dados)
3. Ajustar `HEADER_ALIASES` em `crops.py` se necessário
