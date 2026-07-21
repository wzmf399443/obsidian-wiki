# Shared 10-Color Graph Palette

Canonical color palette used by `wiki-export` (graph.html community colors) and
`graph-colorize` (Obsidian graph.json colorGroups). Both skills must draw from
this table so the browser visualization and Obsidian's graph view stay visually
consistent. Use in order; if more groups than colors, cycle.

| # | Hex | rgb (packed int) | Role |
|---|---|---|---|
| 0 | `#4E79A7` | `5142951` | blue |
| 1 | `#F28E2B` | `15896107` | orange |
| 2 | `#E15759` | `14767961` | red |
| 3 | `#76B7B2` | `7780786` | teal |
| 4 | `#59A14F` | `5873999` | green |
| 5 | `#EDC948` | `15583048` | yellow |
| 6 | `#B07AA1` | `11565217` | purple |
| 7 | `#FF9DA7` | `16751527` | pink |
| 8 | `#9C755F` | `10253663` | brown |
| 9 | `#BAB0AC` | `12234924` | gray |

- `wiki-export` uses the **Hex** column (JS array order 0–9).
- `graph-colorize` uses the **rgb (packed int)** column, wrapped as
  `{"a": 1, "rgb": <int>}` in `graph.json`.
