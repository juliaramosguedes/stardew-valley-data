# stardew-data

Pipeline de dados para o [stardew-guide](https://github.com/juliaramosguedes/stardew-guide).

Extrai dados da [Stardew Valley Wiki](https://stardewvalleywiki.com) via MediaWiki API,
estrutura em JSON e publica automaticamente via GitHub Actions.

## Fontes

- **Primária**: [Stardew Valley Wiki](https://stardewvalleywiki.com) — CC BY-NC-SA 3.0
- **Secundária**: [polarstoat/stardew-crop-data](https://github.com/polarstoat/stardew-crop-data) — MIT

Todo arquivo JSON gerado inclui um campo `_meta` com atribuição da fonte.

## Estrutura

```
stardew-data/
├── scrapers/
│   ├── base.py             # cliente MediaWiki API + TypedDicts + validate_and_save
│   ├── crops.py            # cultivos por estação
│   ├── events.py           # festivais e eventos
│   ├── community_center.py # bundles do Centro Comunitário
│   └── run_all.py          # executa todos os scrapers
├── schemas/                # JSON Schemas — contrato de dados entre os dois repos
│   ├── crops.schema.json
│   ├── events.schema.json
│   └── community_center.schema.json
├── data/                   # JSONs gerados (commitados)
│   ├── crops.json
│   ├── events.json
│   └── community_center.json
├── .github/workflows/
│   └── scrape.yml          # atualiza dados toda segunda-feira
├── SOURCES.md              # log de validação por campo
└── requirements.txt
```

## Uso local

```fish
git clone https://github.com/juliaramosguedes/stardew-data
cd stardew-data
pip install -r requirements.txt
python scrapers/run_all.py
```

Os JSONs são gerados em `data/`.

## GitHub Actions

O workflow `scrape.yml` roda toda segunda-feira às 08h UTC.
Se houver mudanças nos dados, cria um commit automático com diff do que mudou.

## Consumindo os dados

Os JSONs ficam disponíveis via raw do GitHub:

```
https://raw.githubusercontent.com/juliaramosguedes/stardew-data/main/data/crops.json
https://raw.githubusercontent.com/juliaramosguedes/stardew-data/main/data/events.json
...
```

O site `stardew-guide` consome essas URLs diretamente — sem servidor, sem custo.
