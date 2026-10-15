# Audit: facts and sources in globe/coffee_globe.html

Inventory only. Nothing here was checked online, and no file other than this one was changed. Line numbers refer to `globe/coffee_globe.html` (570 lines) as of commit `dbb3146`.

## Summary

- `python -m json.tool references/sources.json` **passes** (valid JSON, 12 entries). None of the 12 ledger entries covers any source used by the globe.
- **9 data blocks** hold factual statements (listed below).
  - **2 have a stated source**: `coe` and `COE_TEXT` (Cup of Excellence). The source is the code comment at lines 202–205 ("Based on the 2025 and 2026 auction calendars", plus the URL https://allianceforcoffeeexcellence.org). This comment is in the code only and is never shown on the page.
  - **1 has a partial source**: `IMPORTERS`. Only 1 of its 9 entries (NLD, line 253) names a source: "(ITC figures)".
  - **6 have no stated source**: `TYPES`, `coffee` (56 countries), `trade`, `P` (ports), `ROUTES`, and the facts written inline in functions (`introText()` and others).
- **One page-wide sources line** (lines 62–66) names 8 organisations: International Coffee Organization, USDA Foreign Agricultural Service, Cecafé, VICOFA, Vietnam Customs, Uganda Coffee Development Authority, Alliance for Coffee Excellence and ITC. It has **no links**, does not say which fact comes from which organisation, and is shown at 8px with 60% opacity (line 36).
- **About 70 individual figures** (volumes, values, percentages, years, counts; many repeated) appear in 41 rows of the step 5 table. On the page, only the 2 NLD values tagged "(ITC figures)" have a source. The "2025–26 calendar" label and the "11 active hosts" count are covered by the code comment only.
- **4 external resources** are loaded: the globe.gl library, two globe texture images and one countries GeoJSON file. There are no fonts, because the page uses the system `sans-serif`. None of the 4 states a licence in the file.

## Step 1: sources.json check

| Command | Result |
|---|---|
| `python -m json.tool references/sources.json` | Passes (exit 0). A top-level list of 12 entries. |

## Step 2–3: Data blocks

| # | Variable | Lines | What it holds | Entries | Source stated in the file |
|---|---|---|---|---|---|
| 1 | `TYPES` | 73–77 | Species categories and their legend labels | 3 | No source stated |
| 2 | `coffee` | 79–199 | Coffee-growing countries: name, type, regions, note | 56 (Americas 19, Africa 21, Asia 13, Oceania 3) | No source stated |
| 3 | `COE_TEXT` (with `COE_COLORS`) | 207–211 | Labels for active and past Cup of Excellence hosts | 2 | Yes. Comment at lines 202–205 (code only) |
| 4 | `coe` | 212–230 | Cup of Excellence host countries: status and note | 17 (11 active, 6 past) | Yes. Comment at lines 202–205 (code only) |
| 5 | `trade` | 235–240 | Export figures for producing countries | 4 | No source stated |
| 6 | `IMPORTERS` | 244–254 | Importing countries and their import text | 9 | Partial. NLD only, "(ITC figures)" at line 253 |
| 7 | `P` | 259–280 | Ports: name, location, coordinates, role | 19 (10 origin, 9 destination) | No source stated |
| 8 | `ROUTES` (with fallback `qual`) | 282–321 | Port-to-port trade routes and their text | 25 (14 with text, 11 `null` that use the fallback) | No source stated. The fallback text points to "ICO or USDA data" for numbers that are not shown |
| 9 | Inline text in functions | 347, 350, 373, 409–410, 423 | Facts written directly into HTML strings | 5 strings | No source stated |

Exact source text found in the file:

- Lines 202–205 (code comment, not shown on the page):
  > `// 2. CUP OF EXCELLENCE (competition and auction run by the`
  > `//    Alliance for Coffee Excellence). s = 'active' or 'past'.`
  > `//    Based on the 2025 and 2026 auction calendars. Update yearly:`
  > `//    https://allianceforcoffeeexcellence.org`
- Line 253 (inside the NLD importer text, shown on the page): `(ITC figures)`
- Lines 282–283 (code comment on `ROUTES`): `// [from, to, text]. A null text falls back to a generic line` / `// (no published figure available).`
- Line 318 (fallback route text, shown on the page): `No volume figure shown here; see ICO or USDA data for numbers.`

### Block 1: `TYPES` (lines 73–77), no source stated

| Key | Line | Label shown |
|---|---|---|
| arabica | 74 | Mainly arabica |
| robusta | 75 | Mainly robusta |
| both | 76 | Both / other species |

These are category definitions. The facts they carry come from which category each country in `coffee` is put in (block 2).

### Block 2: `coffee` (lines 79–199), no source stated

Every entry has `type`, `regions` and `note`. All three are factual claims, and none has a source. The last column gives a short summary of the factual claims in `note`.

| Code | Name | Line | Type | Main claims in note |
|---|---|---|---|---|
| BRA | Brazil | 81–82 | both | Largest producer "for well over a century"; mostly dry-processed; robusta called conilon |
| COL | Colombia | 83–84 | arabica | Washed arabica, small farms; Coffee Cultural Landscape is a UNESCO World Heritage Site; Juan Valdez brand |
| HND | Honduras | 85–86 | arabica | One of the biggest producers in Central America; Marcala was the first protected designation of origin in Honduras |
| PER | Peru | 87–88 | arabica | Leading source of organic and fair-trade coffee; cooperatives in the Andes |
| MEX | Mexico | 89–90 | arabica | Small, organic, shade-grown farms; major supplier to the USA |
| GTM | Guatemala | 91–92 | arabica | Volcanic soils; Antigua among best-known regions |
| NIC | Nicaragua | 93–94 | arabica | Maragogipe "elephant bean" |
| CRI | Costa Rica | 95–96 | arabica | Robusta prohibited by law; popularised "honey" process |
| SLV | El Salvador | 97–98 | arabica | Pacamara bred there in the 1950s (Pacas × Maragogipe) |
| PAN | Panama | 99–100 | arabica | Geisha from Boquete breaks auction price records |
| ECU | Ecuador | 101–102 | both | Arabica and robusta; coffee on the Galápagos |
| VEN | Venezuela | 103–104 | arabica | Historically a major exporter; Andean production |
| BOL | Bolivia | 105–106 | arabica | Small volumes from the Yungas |
| DOM | Dominican Republic | 107–108 | arabica | Much of the harvest drunk locally |
| HTI | Haiti | 109–110 | arabica | Supplied a large share of world coffee in the 1700s |
| CUB | Cuba | 111–112 | arabica | Eastern mountains; cafecito |
| JAM | Jamaica | 113–114 | arabica | Blue Mountain among the most expensive coffees; shipped in wooden barrels |
| PRI | Puerto Rico | 115–116 | arabica | Once a major exporter to Europe |
| USA | United States | 117–118 | arabica | Hawaii is the main producer; Kona on Hualālai and Mauna Loa (regions also list Puerto Rico) |
| ETH | Ethiopia | 121–122 | arabica | Birthplace of arabica; grows wild; coffee ceremony |
| UGA | Uganda | 123–124 | both | One of Africa's largest producers; mostly robusta, native to the region; arabica on Mount Elgon |
| KEN | Kenya | 125–126 | arabica | SL28 and SL34; weekly auction system |
| TZA | Tanzania | 127–128 | both | Kilimanjaro arabica, peaberry, robusta in the west |
| RWA | Rwanda | 129–130 | arabica | Bourbon; specialty sector grown since the 1990s |
| BDI | Burundi | 131–132 | arabica | Coffee is the main export; "hundreds of thousands" of smallholders |
| CMR | Cameroon | 133–134 | both | Arabica in the highlands, robusta in the lowlands |
| CIV | Ivory Coast | 135–136 | robusta | Major robusta producer in West Africa |
| COD | DR Congo | 137–138 | both | Arabica near Lake Kivu, robusta in the Congo basin |
| MDG | Madagascar | 139–140 | robusta | Mainly robusta, coastal |
| AGO | Angola | 141–142 | robusta | Once a major robusta exporter; fell during civil war |
| MWI | Malawi | 143–144 | arabica | Small amounts, northern highlands |
| ZMB | Zambia | 145–146 | arabica | Small-scale; growing specialty sector |
| ZWE | Zimbabwe | 147–148 | arabica | Eastern highlands along the Mozambique border |
| TGO | Togo | 149–150 | robusta | Smallholders alongside cocoa |
| GIN | Guinea | 151–152 | robusta | Forested southeast |
| SLE | Sierra Leone | 153–154 | robusta | Historically a main cash crop |
| LBR | Liberia | 155–156 | both | Gives its name to Liberica |
| CAF | Central African Republic | 157–158 | robusta | Once an important export |
| GHA | Ghana | 159–160 | robusta | Small producer, overshadowed by cocoa |
| NGA | Nigeria | 161–162 | robusta | Small-scale; domestic drinking growing |
| VNM | Vietnam | 165–166 | robusta | World's largest robusta producer, "generally ranked second overall"; cà phê sữa đá, egg coffee |
| IDN | Indonesia | 167–168 | both | One of the biggest producers; wet-hulling (giling basah); kopi luwak |
| IND | India | 169–170 | both | Western Ghats, shade-grown; Monsooned Malabar; Baba Budan legend, 1600s |
| YEM | Yemen | 171–172 | arabica | Among the first places coffee was cultivated; port of Mocha |
| LAO | Laos | 173–174 | both | Bolaven Plateau |
| THA | Thailand | 175–176 | both | Arabica promoted as an alternative to opium poppies |
| MMR | Myanmar | 177–178 | arabica | Growing specialty scene, Pyin Oo Lwin |
| CHN | China | 179–180 | arabica | Almost all from Yunnan (regions also list Hainan) |
| PHL | Philippines | 181–182 | both | Grows all four commercial species; kapeng barako |
| TLS | Timor-Leste | 183–184 | arabica | Coffee is the largest export crop; Hibrido de Timor |
| NPL | Nepal | 185–186 | arabica | Small producer, organic, Himalayan foothills |
| MYS | Malaysia | 187–188 | both | Liberica and robusta; Ipoh white coffee |
| TWN | Taiwan | 189–190 | arabica | Small amounts, high-priced, Alishan |
| PNG | Papua New Guinea | 193–194 | arabica | Smallholder crop; Typica and Bourbon descent |
| AUS | Australia | 195–196 | arabica | Mechanical harvesting; flat white |
| VUT | Vanuatu | 197–198 | arabica | Tanna island |

### Block 3: `COE_TEXT` / `COE_COLORS` (lines 207–211), source in code comment (lines 202–205)

| Key | Line | Text shown | Source |
|---|---|---|---|
| active | 209 | Active host, on the 2025–26 calendar | Comment at 202–205: "Based on the 2025 and 2026 auction calendars", https://allianceforcoffeeexcellence.org |
| past | 210 | Past host, not on the 2025–26 calendar | Same comment |

### Block 4: `coe` (lines 212–230), source in code comment (lines 202–205)

The comment covers which countries are active or past hosts. It does not say where the historical years in the notes come from.

| Code | Line | Status | Note (claims) | Source for the note |
|---|---|---|---|---|
| BRA | 213 | active | First competition in 1999, called "Best of Brazil" | Not stated (the comment names auction calendars only) |
| NIC | 214 | active | A long-running participant | Not stated |
| MEX | 215 | active | A long-running participant | Not stated |
| HND | 216 | active | A long-running participant | Not stated |
| CRI | 217 | active | Long-running, joined in 2007 | Not stated |
| GTM | 218 | active | A long-running participant | Not stated |
| SLV | 219 | active | A long-running participant | Not stated |
| PER | 220 | active | A long-running participant | Not stated |
| THA | 221 | active | Newcomer, first competition "within the last few years" | Not stated |
| TWN | 222 | active | Newcomer, as above | Not stated |
| IDN | 223 | active | Newcomer, as above | Not stated |
| COL | 224 | past | Took part every year 2005–2023 | Not stated |
| ETH | 225 | past | Held competitions 2020–2024 | Not stated |
| ECU | 226 | past | Three years, the last in 2023 | Not stated |
| RWA | 227 | past | First African host, first competition 2008 | Not stated |
| BDI | 228 | past | Second East African host, after Rwanda | Not stated |
| BOL | 229 | past | Hosted competitions in earlier years | Not stated |

### Block 5: `trade` (lines 235–240), no source stated

| Code | Line | Text | Source |
|---|---|---|---|
| BRA | 236 | About 40 million bags in 2025, roughly 20% down on the year before, sent to more than 120 countries. Germany (5.4 million bags) and the USA (5.3 million bags) were the biggest buyers, followed by Italy, Japan and Belgium. | No source stated |
| VNM | 237 | About 1.6 million tonnes in 2025, worth a record US$8.92 billion. Europe takes around half of it. Germany (13.7% of value), Italy (7.8%) and Spain (7.1%) are the top three markets, and robusta made up 73.8% of export value. | No source stated |
| COL | 238 | About 12 million 60-kg bags in 2024. The USA imported over US$1.5 billion of Colombian coffee in 2023. | No source stated |
| UGA | 239 | 8.7 million bags worth about US$2.5 billion in calendar 2025, up from 5.9 million bags worth US$1.4 billion in 2024. | No source stated |

### Block 6: `IMPORTERS` (lines 244–254), partial source (NLD only)

| Code | Name | Line | Main claims | Source |
|---|---|---|---|---|
| DEU | Germany | 245 | ~US$5.6 bn imports 2024, second after USA; biggest buyer of Brazilian (5.4 M bags, 2025) and Vietnamese (~US$1.23 bn) coffee; roasting and re-export hub | No source stated |
| USA | United States | 246 | World's largest importer; ~US$9 bn in 2024, ~17.7% of global imports; 5.3 M bags from Brazil in 2025, down 33% after tariffs | No source stated |
| ITA | Italy | 247 | Lavazza; buys robusta for espresso; major buyer of Brazilian coffee; ~7.8% of Vietnam's exports 2025 | No source stated |
| JPN | Japan | 248 | Almost no own production; Brazil and Vietnam main suppliers; canned and instant coffee market | No source stated |
| BEL | Belgium | 249 | Antwerp major EU entry port for green coffee; major buyer of Brazilian coffee | No source stated |
| ESP | Spain | 250 | Vietnam's third-largest market 2025, ~7.1% of export value | No source stated |
| DZA | Algeria | 251 | ~6.5% of Vietnam's export volume 2025, more than USA (5.9%) | No source stated |
| SAU | Saudi Arabia | 252 | Significant buyer of Ethiopian coffee | No source stated |
| NLD | Netherlands | 253 | Exported ~US$1.2 bn of coffee products in 2023; net trade deficit ~US$355 M; among Vietnam's top-10 markets | **"(ITC figures)"**, which covers the 2023 export and deficit figures. The top-10 claim has no source. |

### Block 7: `P` ports (lines 259–280), no source stated

The facts here are the port names, coordinates, and the claim that each origin port is "a main shipping port" or "a main outlet" for that country's coffee (text built at lines 409–410).

| Key | Line | Name, place | Serves | Lat, Lng | Role |
|---|---|---|---|---|---|
| santos | 260 | Santos, Brazil | Brazil | -23.96, -46.33 | origin |
| caimep | 261 | Cai Mep, Vietnam | Vietnam | 10.53, 107.03 | origin |
| cartagena | 262 | Cartagena, Colombia | Colombia | 10.39, -75.51 | origin |
| djibouti | 263 | Djibouti, Djibouti | Ethiopia | 11.59, 43.15 | origin |
| mombasa | 264 | Mombasa, Kenya | Uganda | -4.04, 39.67 | origin |
| belawan | 265 | Belawan (Medan), Indonesia | Indonesia | 3.78, 98.69 | origin |
| cortes | 266 | Puerto Cortés, Honduras | Honduras | 15.84, -87.95 | origin |
| quetzal | 267 | Puerto Quetzal, Guatemala | Guatemala | 13.93, -90.78 | origin |
| callao | 268 | Callao, Peru | Peru | -12.05, -77.15 | origin |
| kochi | 269 | Kochi, India | India | 9.97, 76.27 | origin |
| hamburg | 271 | Hamburg, Germany | Germany | 53.55, 9.97 | destination |
| newyork | 272 | New York, USA | USA | 40.67, -74.04 | destination |
| genoa | 273 | Genoa, Italy | Italy | 44.41, 8.92 | destination |
| antwerp | 274 | Antwerp, Belgium | Belgium | 51.23, 4.40 | destination |
| rotterdam | 275 | Rotterdam, Netherlands | Netherlands | 51.95, 4.14 | destination |
| barcelona | 276 | Barcelona, Spain | Spain | 41.35, 2.17 | destination |
| algiers | 277 | Algiers, Algeria | Algeria | 36.77, 3.06 | destination |
| jeddah | 278 | Jeddah, Saudi Arabia | Saudi Arabia | 21.49, 39.17 | destination |
| yokohama | 279 | Yokohama, Japan | Japan | 35.44, 139.64 | destination |

### Block 8: `ROUTES` (lines 284–315) and fallback `qual` (lines 317–318), no source stated

Fallback text for `null` routes (line 317–318): "*X* to *Y*: one of the regular trade flows for *X* coffee. No volume figure shown here; see ICO or USDA data for numbers." It points readers to ICO and USDA but gives no source for the claim that the flow is a "regular trade flow".

| Line | From → To | Text | Source |
|---|---|---|---|
| 285 | santos → hamburg | Brazil to Germany: 5.4 million bags in 2025 (13.5% of Brazil's exports), making Germany Brazil's biggest buyer that year. | No source stated |
| 286 | santos → newyork | Brazil to the USA: 5.3 million bags in 2025, down 33% on the year before after steep US import tariffs. | No source stated |
| 287 | santos → genoa | One of Brazil's major buyers after Germany and the USA. No volume figure. | No source stated |
| 288 | santos → yokohama | As above (Japan) | No source stated |
| 289 | santos → antwerp | As above (Belgium) | No source stated |
| 291 | caimep → hamburg | Vietnam's biggest coffee market in 2025, nearly US$1.23 billion (~13.7% of export value) | No source stated |
| 292 | caimep → genoa | ~7.8% of Vietnam's coffee export value in 2025 | No source stated |
| 293 | caimep → barcelona | ~7.1% of Vietnam's coffee export value in 2025 | No source stated |
| 294 | caimep → algiers | ~6.5% of Vietnam's coffee export volume in 2025, more than the USA | No source stated |
| 295 | caimep → newyork | ~5.9% of Vietnam's coffee export volume in 2025 | No source stated |
| 296 | caimep → rotterdam | Among Vietnam's top-10 coffee markets in 2025 | No source stated |
| 297 | caimep → yokohama | One of Vietnam's largest coffee buyers | No source stated |
| 299 | cartagena → newyork | USA imported over US$1.5 bn of Colombian coffee in 2023; Colombia exported ~12 M bags in 2024 | No source stated |
| 300 | cartagena → yokohama | `null` (fallback) | Fallback pointer only |
| 302 | djibouti → hamburg | `null` (fallback) | Fallback pointer only |
| 303 | djibouti → jeddah | `null` (fallback) | Fallback pointer only |
| 305 | mombasa → genoa | Ugandan robusta to European roasters; Uganda exported 8.7 M bags, ~US$2.5 bn in 2025 | No source stated |
| 307 | belawan → newyork | `null` (fallback) | Fallback pointer only |
| 308 | belawan → yokohama | `null` (fallback) | Fallback pointer only |
| 309 | cortes → hamburg | `null` (fallback) | Fallback pointer only |
| 310 | cortes → newyork | `null` (fallback) | Fallback pointer only |
| 311 | quetzal → newyork | `null` (fallback) | Fallback pointer only |
| 312 | callao → newyork | `null` (fallback) | Fallback pointer only |
| 313 | callao → hamburg | `null` (fallback) | Fallback pointer only |
| 314 | kochi → genoa | `null` (fallback) | Fallback pointer only |

### Block 9: Inline facts in functions, no source stated

| Line | Function | Text (fact part) | Source |
|---|---|---|---|
| 347 | `introText()` | "Cup of Excellence is a competition and online auction for the highest-scoring coffee lots, run by the Alliance for Coffee Excellence. Purple countries are active hosts (11 on the 2025–26 calendar)…" | No source stated on the page (the count of 11 matches the 11 `active` entries in `coe`) |
| 350 | `introText()` | "For scale, the world drank roughly 177 million 60-kg bags in 2023/24." | No source stated |
| 373 | `coeLine()` | "Not a Cup of Excellence host country." (shown for every coffee country not in `coe`) | No source stated |
| 409–410 | `showPort()` | "A main shipping port for *X* coffee." / "A main outlet for *X* coffee, located in *Y*." | No source stated |
| 423 | `showRoute()` | "The line shows a main trade flow between two countries, not the exact sea lane." | Disclaimer, not a fact claim |

## Step 4: Sources and citation text shown on the page

The only visible sources text is the `#sources` div, lines 62–66, quoted exactly:

> Sources: International Coffee Organization, USDA Foreign Agricultural Service, Cecafé (Brazil), VICOFA and Vietnam Customs,
> Uganda Coffee Development Authority, Alliance for Coffee Excellence, ITC. Figures are rounded and change every year, so check
> the original sources before quoting them.

Organisations named (8): International Coffee Organization; USDA Foreign Agricultural Service; Cecafé (Brazil); VICOFA; Vietnam Customs; Uganda Coffee Development Authority; Alliance for Coffee Excellence; ITC.

Links named: **none**. The div has no `<a>` tags and no URLs.

Other source text visible on the page:

- Line 253, NLD importer text: "(ITC figures)".
- Line 318, fallback route text: "see ICO or USDA data for numbers".
- Line 347: names the "Alliance for Coffee Excellence" as the organiser of Cup of Excellence. This describes the competition and is not presented as a citation.

Not visible on the page:

- Lines 202–205, the code comment with https://allianceforcoffeeexcellence.org. This is the only source URL in the file.

## Step 5: Statistics (numbers and dates)

"Source?" means a source is attached to that specific statement in the file. The general footer (lines 62–66) applies to the whole page and is not counted here.

| Entry | Line | Statistic | Source? |
|---|---|---|---|
| coffee BRA | 82 | Largest producer "for well over a century" | No |
| coffee SLV | 98 | Pacamara bred in the 1950s | No |
| coffee HTI | 110 | Large share of world coffee in the 1700s | No |
| coffee RWA | 130 | Specialty sector grown since the 1990s | No |
| coffee BDI | 132 | "hundreds of thousands of smallholders" | No |
| coffee VNM | 166 | Largest robusta producer; ranked second overall | No |
| coffee IND | 170 | Baba Budan seeds in the 1600s | No |
| coffee PHL | 182 | Grows all four commercial species | No |
| COE_TEXT | 209–210 | "2025–26 calendar" | Yes, code comment 202–205 |
| coe BRA | 213 | First competition 1999 | No |
| coe CRI | 217 | Joined 2007 | No |
| coe COL | 224 | Every year 2005–2023 | No |
| coe ETH | 225 | 2020–2024 | No |
| coe ECU | 226 | Three years, last in 2023 | No |
| coe RWA | 227 | First African host, 2008 | No |
| coe BDI | 228 | Second East African host | No |
| coe THA, TWN, IDN | 221–223 | First competition "within the last few years" | No |
| introText | 347 | 11 active hosts on the 2025–26 calendar | Code comment 202–205 only (not on the page) |
| introText | 350 | World drank ~177 M 60-kg bags in 2023/24 | No |
| trade BRA | 236 | ~40 M bags 2025; ~20% down y/y; >120 countries; Germany 5.4 M bags; USA 5.3 M bags | No |
| trade VNM | 237 | ~1.6 M tonnes 2025; record US$8.92 bn; Europe ~half; Germany 13.7%, Italy 7.8%, Spain 7.1% of value; robusta 73.8% of value | No |
| trade COL | 238 | ~12 M 60-kg bags 2024; USA imported >US$1.5 bn in 2023 | No |
| trade UGA | 239 | 8.7 M bags, ~US$2.5 bn, 2025; 5.9 M bags, US$1.4 bn, 2024 | No |
| IMPORTERS DEU | 245 | ~US$5.6 bn imports 2024; 2nd after USA; 5.4 M bags Brazil 2025; ~US$1.23 bn Vietnam | No |
| IMPORTERS USA | 246 | ~US$9 bn 2024; ~17.7% of global imports; 5.3 M bags Brazil 2025; down 33% | No |
| IMPORTERS ITA | 247 | ~7.8% of Vietnam's exports 2025 | No |
| IMPORTERS ESP | 250 | Vietnam's 3rd-largest market 2025, ~7.1% of value | No |
| IMPORTERS DZA | 251 | ~6.5% of Vietnam's volume 2025; USA 5.9% | No |
| IMPORTERS NLD | 253 | ~US$1.2 bn exports 2023; ~US$355 M net deficit | **Yes, "(ITC figures)"** |
| IMPORTERS NLD | 253 | Among Vietnam's top-10 markets | No |
| ROUTES santos→hamburg | 285 | 5.4 M bags 2025; 13.5% of Brazil's exports | No |
| ROUTES santos→newyork | 286 | 5.3 M bags 2025; down 33% | No |
| ROUTES caimep→hamburg | 291 | ~US$1.23 bn; ~13.7% of value, 2025 | No |
| ROUTES caimep→genoa | 292 | ~7.8% of value 2025 | No |
| ROUTES caimep→barcelona | 293 | ~7.1% of value 2025 | No |
| ROUTES caimep→algiers | 294 | ~6.5% of volume 2025 | No |
| ROUTES caimep→newyork | 295 | ~5.9% of volume 2025 | No |
| ROUTES caimep→rotterdam | 296 | Top-10 market 2025 | No |
| ROUTES cartagena→newyork | 299 | >US$1.5 bn 2023; ~12 M bags 2024 | No |
| ROUTES mombasa→genoa | 305 | 8.7 M bags, ~US$2.5 bn, 2025 | No |
| P (all ports) | 260–279 | Latitude and longitude of 19 ports | No |

Several figures are repeated in more than one place: Brazil→Germany 5.4 M, Brazil→USA 5.3 M, Vietnam shares 13.7, 7.8, 7.1, 6.5 and 5.9%, Colombia US$1.5 bn and 12 M bags, and Uganda 8.7 M bags and US$2.5 bn. Each one will need its source recorded only once, but all its copies must change together.

## Step 6: External resources loaded by the page

| Line | Kind | Exact URL as written | Notes from the file |
|---|---|---|---|
| 68 | Script (library) | `//unpkg.com/globe.gl` | Protocol-relative and no version pinned, so the latest version is always loaded. No licence stated. |
| 430 | Image (globe texture) | `//unpkg.com/three-globe/example/img/earth-blue-marble.jpg` | Loaded from the three-globe package's `example` folder. No licence or credit stated. |
| 431 | Image (bump map) | `//unpkg.com/three-globe/example/img/earth-topology.png` | Same as above. |
| 534 | Data file (fetch) | `https://raw.githubusercontent.com/vasturiano/globe.gl/master/example/datasets/ne_110m_admin_0_countries.geojson` | Country shapes. The code reads properties `ADM0_A3` (line 435) and `ADMIN` (line 461). Loaded from the `master` branch, so it can change. No licence stated. |
| 7 | Font | none loaded (`font-family: sans-serif`, the system font) | No web fonts. |
| 205 | Link in comment (not loaded) | `https://allianceforcoffeeexcellence.org` | The only source URL in the file. |

## Open questions

1. **Footer not tied to facts.** The footer lists 8 organisations but does not say which figure comes from which one. The names suggest some matches (for example Cecafé → Brazil exports, VICOFA/Vietnam Customs → Vietnam figures, UCDA → Uganda, ACE → Cup of Excellence, ITC → Netherlands). That is a guess and is not stated in the file. Every figure needs its real source confirmed before we write `sources.json` entries.
2. **No URLs, report titles or dates of access** for any of the 8 organisations. We will need these, and their licences, for `sources.json`. Until then they are "unknown".
3. **Acronyms not expanded.** "ITC" and "VICOFA" are never written out in the file, and "ICO" (line 318) is only expanded in the footer. We should not guess their full names. Confirm them when the sources are opened.
4. **Cup of Excellence history years** (1999, 2005–2023, 2007, 2008, 2020–2024, 2023) are not covered by the "2025 and 2026 auction calendars" comment. Where did they come from?
5. **"Within the last few years"** (THA, TWN, IDN, lines 221–223) and **"2025–26 calendar"** depend on the date. Which date were they true on? The comment says "Update yearly".
6. **The `coffee` block (56 notes, types and regions) has no source at all.** It includes history (1700s, 1600s, 1950s), legal claims (Costa Rica robusta ban), rankings ("largest", "one of the biggest") and UNESCO status. Do we source each claim, soften the wording, or mark the block as general background?
7. **Category choices in `type`** (arabica, robusta or both) for 56 countries have no stated rule or source. Is "mainly" by volume, and by whose data?
8. **Ambiguous measures.** Italy's 7.8% is "of export value" in `trade` (line 237) and on the route (line 292), but "of Vietnam's coffee exports" in `IMPORTERS` (line 247). Germany's US$1.23 bn (line 245) does not say a year, while the route text (line 291) says 2025.
9. **Bag size.** Some figures say "60-kg bags" (lines 238, 350) and others just "bags" (lines 236, 239, 245, 246, 285, 286, 305). Are they all 60-kg bags?
10. **Duplicate geography.** `USA` regions include "Puerto Rico" (line 117), and `PRI` is also its own entry (line 115). Is this intended?
11. **Port choices** (for example Djibouti for Ethiopia, Mombasa for Uganda) and their coordinates have no source. Should a port reference be added to the ledger?
12. **External resources.** The licences for globe.gl, the three-globe textures and the countries GeoJSON are not stated in the file. The file name `ne_110m_…` suggests Natural Earth, but the file does not say so. globe.gl may also load further libraries that are not visible in this file. All of this needs checking and ledger entries.
13. **Unpinned versions.** `//unpkg.com/globe.gl` (no version) and the GeoJSON on the `master` branch can change without notice. Should we pin them, or copy the data file into `globe/data/`?
14. **Footer readability.** The sources text is 8px at 60% opacity (line 36). This matters for the planned References button.
