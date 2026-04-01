# Sources & Data Validation Log

Todos os dados deste repositório são derivados de fontes públicas creditadas abaixo.
Cada arquivo JSON inclui um campo `_meta` com atribuição automática.

## Fontes primárias

| Dataset | Página da wiki | Método | Status |
|---|---|---|---|
| `crops.json` | [Crops](https://stardewvalleywiki.com/Crops) | MediaWiki API + parser | ✓ automatizado |
| `events.json` | [Festivals](https://stardewvalleywiki.com/Festivals) | Dados estruturados + validação via API | ✓ automatizado |
| `community_center.json` | [Community Center Bundles](https://stardewvalleywiki.com/Community_Center_Bundles) | Dados estruturados + validação via API | ✓ automatizado |

## Licença dos dados

**Stardew Valley Wiki** é licenciada sob
[Creative Commons Attribution-NonCommercial-ShareAlike 3.0](https://creativecommons.org/licenses/by-nc-sa/3.0/).

Este projeto não é afiliado à ConcernedApe, ao Stardew Valley Wiki ou à Fandom.
Todo conteúdo de jogo é propriedade de Eric Barone (ConcernedApe).

## Referências secundárias

- [polarstoat/stardew-crop-data](https://github.com/polarstoat/stardew-crop-data) — MIT
  Usado como referência de schema para cultivos (versão 1.5.4)

## Validação manual

Campos que requerem validação manual a cada update do jogo:

- Preços das sementes no Pierre (podem mudar entre versões)
- Disponibilidade por ano (ex: Red Cabbage só no Ano 2)
- Novos cultivos adicionados em updates (1.6 adicionou Carrot, Summer Squash, Broccoli, Powdermelon)
- Bundles do Centro Comunitário (estrutura estável, mas itens podem mudar)
