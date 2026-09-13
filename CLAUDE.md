# CLAUDE.md — deníček projektu

Shrnutí toho, co se v projektu udělalo, proč, a na co si dát pozor. Výzkumný
design (RQs, metodologie, fáze) je v `MasterOutline.md` — tenhle soubor je
spíš technický/vývojářský deníček a rychlý kontext pro (příště i sebe).

## Co projekt dělá

Analýza morfologie uličních sítí českých měst (orientace/bearing, topologické
metriky, shlukování) — inspirováno posterem Geoffa Boeinga. Postaveno na
research-template (notebooky orchestrují, logika v `src/`).

## Architektura (`src/streets/`)

- `registry.py` — registr ~6 259 obcí ČR, migrováno z `GeoGram_sufix-ice`
  (RÚIAN + ČSÚ). Používá se k disambiguaci sídel se stejným jménem a jako
  zdroj `status_code` (viz `MasterOutline.md` §6 — kódovník 1–6 odvozený
  empiricky, oficiální RÚIAN číselník se online nedohledal).
- `osm.py` — stahování grafů přes OSMnx/Overpass. `download_graph()` (jedno
  sídlo, cache + retry) a `download_all()` (dávka, jedno selhání nezastaví
  zbytek). Viz sekce "Overpass problémy" níže.
- `metrics.py` — `extract_metrics()` (orientation entropy, circuity, stupeň
  uzlu, hustota křižovatek, clustering coefficient, betweenness centrality)
  + `build_metrics_table()`/`compute_metrics()` (offline, cachované do CSV).
- `clustering.py` — K-Means přes standardizované metriky, `sweep_k()` pro
  volbu k přes silhouette score, PCA pro 2D vizualizaci.
- `viz.py` — polar (rose) ploty orientace, poster mřížka, cluster scatter.
- `local_data.py` — **alternativní** pipeline, co obchází OSMnx/Overpass
  úplně (čte Geofabrik shapefile export přes čistě pythonovou `pyshp`).
  Postavená, funkční, ale **není zapojená do hlavního pipeline** — viz níže.

## Notebooky

- `00_pilot.ipynb` — Fáze 0, malý testovací vzorek (7 sídel), rozhodnutí o
  `network_type` (`drive` vs `all`).
- `01_full_sample.ipynb` — Fáze 1, kurátorovaný vzorek 33 sídel
  (`sample_seed.csv`).
- `02_all_czech_towns.ipynb` — Fáze 1.5, rozšířeno na všech 610 měst ČR
  (`all_czech_towns.csv`, status_code 3/4/5).

Všechny mají stejnou strukturu: **"Stáhni vše"** (jediná síťová buňka) →
**"Spočítej metriky"** (čistě offline, bezpečné opakovat).

## Klíčová rozhodnutí a proč

- **`network_type="drive"`** (finální, po zvratu). Krátce jsme zkusili
  `"all"` (hustší síť u malých měst), ale opakovaně to padalo na velkých
  městech (Brno) — `"all"` je řádově těžší dotaz a Overpass ho tiše ořezal.
  Riziko na velkých městech převážilo benefit u malých. Viz
  `MasterOutline.md` §5.
- **K-Means, ne DBSCAN/hierarchické** — zatím jediná implementovaná metoda,
  zvážit srovnání až bude víc dat (aktuálně ~27–33 bodů bylo na hraně
  spolehlivosti pro shlukování se 7 metrikami — proto rozšíření na 610 měst).
- **Betweenness centrality aproximovaná** (`k=min(500, n)` zdrojových uzlů),
  ne přesná — exaktní výpočet byl na velkých městech řádově pomalý (minuty
  na město).

## Overpass problémy (hlavní zdroj bolesti celého projektu)

Opakovaně jsme narazili na nespolehlivost veřejného Overpass serveru
(`overpass-api.de`), stejný problém jako v sesterském `OptiCyclingTown`
(viz jeho `network-download-troubleshooting.md`):

1. **Tichý oříznutý výsledek** — Brno na `"all"` vrátilo graf s 0 hranami
   místo chyby (Overpass tiše ořízl moc velký dotaz). Fix: `MIN_EDGES`
   kontrola v `download_graph()`, špatný výsledek se vůbec neuloží.
2. **`ConnectTimeout` — TCP spojení se vůbec nenaváže.** Opakovaně, i po
   zvýšení `requests_timeout`/`overpass_memory`. Vypadá na škrcení podle
   objemu přenesených dat (stejný vzorec jako v `OptiCyclingTown`). Fix:
   retry s 90s cooldownem (až 4×) + 3s pauza po každém stažení. **Není to
   spolehlivá oprava** — někdy to i tak vyžadovalo desítky minut/hodiny a
   opakované spouštění buňky.
3. **Duplicitní název v dotazu** — města, co jsou sama sídlem svého okresu
   (Hradec Králové, Jihlava, Karlovy Vary, Olomouc, Pardubice, ...), dávala
   dotaz typu "Hradec Králové, Hradec Králové, Czech Republic", což
   Nominatim rozbilo (`TypeError`, ne `ValueError` — nebylo to zachytávané).
   Fix: přeskočit okres v dotazu, když `district_name == name`.
4. **Praha** má zvláštní pseudo-okres v RÚIAN (`district_code=9999`,
   "území Hlavního města Prahy") — stejný typ problému, řešeno stejně.

**Zkusili jsme obejít Overpass úplně** (`local_data.py`): stáhnout Geofabrik
`.osm.pbf`/shapefile export a číst lokálně. Fungovalo to stahování (žádné
výpadky, normální HTTPS), ale:
- GDAL (`pyogrio`) a `osmium` python knihovny **blokuje Windows Application
  Control Policy** na tomhle stroji (`Zásada řízení aplikací tento soubor
  zablokovala`) — pyshp (čistě python) funguje.
- Vlastní rekonstrukce grafu z shapefile dala **řidší síť** než živé OSMnx
  (49 vs. 97 uzlů pro Loštice) — Geofabrik shapefile export je kurátorovaná/
  ořezaná podmnožina OSM dat, chybí část propojovacích cest.
- Rozhodnutí: zůstat u OSMnx/Overpass, `local_data.py` nechat jako
  nezapojenou zálohu pro budoucnost.

**2026-09-13 update:** stahování na jiné WiFi síti běží výrazně lépe/
spolehlivěji než na původní síti — podporuje teorii, že jde o něco na
úrovni sítě/ISP/routeru, ne o server nebo náš kód. Stejný test doporučen i
`OptiCyclingTown` (viz jejich `network-download-troubleshooting.md`).

## Drobnosti k IDE/prostředí

- VS Code Jupyter kernel picker si občas nenačte nově vytvořený kernel do
  seznamu (i když `kernel.json` je v pořádku) — pomáhá "Developer: Reload
  Window" nebo přímý výběr interpretru přes cestu k `.venv/Scripts/python.exe`.
- Vícekrát se stalo omylem spuštění notebooku na **jiném projektu venv**
  (`urbanMAL`) — hlídej, který kernel je vybraný nahoře v notebooku.
- "notebook controller is DISPOSED" — pád/zahození Jupyter kernel procesu na
  straně VS Code rozšíření, ne bug v kódu; restart kernelu / reload window.

## Stav k 2026-09-13

- `sample_seed.csv` (33 měst): většina stažená a spočítaná.
- `all_czech_towns.csv` (610 měst): rozjeté, běží průběžně (viz Overpass
  problémy výše — očekávej, že to zabere dny, ne hodiny).
- Vizuální styl se sjednocuje s ostatními projekty přes `modules/dataviz_style/`
  (práce v procesu, viz `src/viz.py`, `src/streets/viz.py`, `src/config.py`).
