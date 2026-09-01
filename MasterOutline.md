# MasterOutline: Morfologie uličních sítí českých měst a obcí

> Pracovní dokument k experimentálnímu designu. Živý dokument – aktualizovat průběžně.

---

## 1. Motivace

Vzorem je poster/práce Geoffa Boeinga *"Urban spatial order: street network
orientation, configuration, and entropy"* (viz `Geoff-Boeing_Motivation_Picture.png`
v tomto repozitáři) — mřížka polar (rose) plotů orientace ulic pro desítky měst
světa, doplněná srovnáním topologických metrik sítě. Cílem je obdobné zpracování
pro **česká sídla**, primárně jako článek na osobní web, s otevřenou možností
rozšířit později (po konzultaci s kolegy) do odborného textu.

---

## 2. Výzkumné otázky (RQs)

**RQ1 — Deskriptivní:** Existují viditelné prostorové vzorce (polar histogramy
orientace ulic) typické pro historická jádra a plánovaná průmyslová/socialistická
města (Zlín, Havířov) v ČR?

**RQ2 — Klasifikační / shlukování:** Lze na základě síťových a prostorových metrik
(spatial/orientation entropy, průměrný stupeň uzlu, hustota křižovatek, podíl
čtyřcestných křižovatek) algoritmicky shlukovat česká sídla do smysluplných
morfologických typů?

**RQ3 — Explorativní:** Odpovídají shluky z RQ2 nějakému rozpoznatelnému
geografickému nebo historickému vzorci (Čechy vs. Morava, hory vs. nížiny,
kraj/region), nebo je morfologický typ na geografii nezávislý? Otevřená,
zkoumaná nad výsledky shlukování — bez apriorně vybraných párů konkrétních
obcí (viz §5 — příklady typologie půdorysu jako okrouhlice/ulicovka se ukázaly
být téměř vždy zaniklé místní části jiných obcí, ne samostatné obce, takže by
narušovaly konzistenci vzorku "jen celé obce").

---

## 3. Metodologie

### 3.1 Zdroj dat a vzorek
- **OpenStreetMap** přes **OSMnx** — stažení uliční sítě jako `networkx.MultiDiGraph`
  pro každé sídlo (`network_type='drive'` nebo `'all'` — rozhodnout v pilotu, viz §5).
- **Vzorek (aktuálně 33 sídel, `data/processed/sample_seed.csv`):** všech 13 krajských
  měst + Praha, a regionální klastr měst v pomezí Pardubického/Olomouckého kraje
  (Šumpersko, Svitavsko, Ústeckoorlicko: Loštice, Mohelnice, Štíty, Šumperk, Zábřeh,
  Březová nad Svitavou, Jevíčko, Litomyšl, Moravská Třebová, Polička, Svitavy, Česká
  Třebová, Choceň, Králíky, Lanškroun, Letohrad, Ústí nad Orlicí, Vysoké Mýto, Žamberk)
  + Havířov (socialistické sídliště, RQ1). Zlín je už v seznamu jako krajské město.
  Vzorek je omezen na **celé samostatné obce** (žádné katastrální části/místní
  části) kvůli konzistenci dat — viz §5 pro důvod (vyřazení Terezína/Josefova).
  Sídla jsou disambiguovaná přes RÚIAN kód (`src/streets/registry.py`,
  `data/processed/cz_municipalities.csv` — kompletní registr 6 259 obcí ČR
  migrovaný z projektu `GeoGram_sufix-ice`, s populací/okresem/krajem/souřadnicemi).
  Vzorek se dá dál rozšířit (viz Fáze 1, ~50–100 sídel).
- **Ukládání surových dat:** stažené grafy se ukládají lokálně (`.graphml` do
  `data/raw/`), aby se při opakovaném běhu/analýze nezatěžovalo OSM API opakovanými
  dotazy — viz ponaučení v §5.

### 3.2 Feature engineering

**Orientace (RQ1):**
- `osmnx.bearing` — bearing (azimut) každé hrany grafu, symetrizovaný na 0–180°.
- **Orientation/spatial entropy** (Shannonova entropie přes bin distribuci bearingů) —
  míra toho, jak moc jsou ulice náhodně rozházené (vysoká entropie, organický půdorys)
  vs. uspořádané do gridu (nízká entropie).

**Topologie (RQ2, přes NetworkX / `osmnx.stats`):**
- **Betweenness centrality** (identifikace hlavních tepen sítě)
- **Clustering coefficient** (transitivita grafu)
- Průměrná délka ulice/hrany (edge length)
- Průměrný stupeň uzlu, hustota křižovatek, podíl čtyřcestných křižovatek

### 3.3 Strojové učení (RQ2, RQ3 — scikit-learn)
- Sestavit feature matici: řádek = jedno sídlo, sloupce = standardizované metriky
  z 3.2 (`StandardScaler`).
- **Unsupervised learning:** K-Means, DBSCAN, případně hierarchické shlukování —
  srovnat, které dává interpretovatelnější shluky.
- **PCA** pro redukci do 2D a vizualizaci shluků (a kontrolu multikolinearity metrik).
- Validace: silhouette score; pro RQ3 srovnat výsledné shluky proti geografickým/
  historickým proměnným z registru obcí (kraj, okres, populace) — žádné apriorní
  párování konkrétních obcí.

### 3.4 Vizualizace
- **Polar (rose) ploty** orientace ulic — hlavní vizuální prvek, vykreslené pro
  reprezentativní sídla z každého shluku (podle vzoru Boeingova posteru).
- Barevné kódování shluků konzistentní napříč vizualizacemi (`src/viz.py::PALETTE`).
- 2D PCA scatter shluků, vykreslení samotných sítí (`modules/network_viz`) pro
  vybrané kontrastní páry v rámci vzorku (historické jádro krajského města vs.
  Havířov, apod.).

---

## 4. Fáze pipeline

### FÁZE 0 — Pilot (pár sídel)
**Cíl:** Ověřit technický pipeline (stažení, metriky, polar plot) na malém, ručně
vybraném vzorku, než se škáluje na plný vzorek.

- [ ] Vybrat ~6–10 kontrastních sídel ze vzorku (Zlín, Havířov, historické centrum
  velkého města, menší region. město)
- [ ] Stáhnout přes OSMnx (`network_type` k rozhodnutí), uložit `.graphml`
- [ ] Spočítat orientaci (bearing, entropie) + topologické metriky
- [ ] Vykreslit polar ploty vedle sebe → ověřit, že rozdíly vizuálně dávají smysl
- [ ] Rozhodnout: binning bearing histogramu, `network_type`, definici hranic sídla

**Výstup:** `notebooks/00_pilot.ipynb`

### FÁZE 1 — Plný vzorek (~50–100 sídel)
**Cíl:** Systematické srovnání a shlukování napříč celým vzorkem.

- Stáhnout/spočítat metriky pro každé sídlo, ukládat inkrementálně (progress bar +
  průběžný zápis CSV — viz §5, ponaučení o rate-limitingu).
- Shlukování (3.3), interpretace shluků vzhledem k RQ2 a RQ3.
- Sestavit finální "poster" vizualizaci (mřížka polar plotů) pro web.

**Výstup:** `notebooks/01_full_sample.ipynb`, `reports/figures/cz_orientation_poster.png`

### FÁZE 2 (volitelná, budoucí) — Rozšíření / publikace
Pokud výsledky budou po konzultaci s kolegy zajímavé: rozšířit vzorek, přidat
statistické testování rozdílů mezi shluky/typy, případně mezinárodní srovnání pro
kontext, a připravit jako odborný text.

---

## 5. Ponaučení a otevřená rozhodnutí

### Ponaučení z `urbanMAL`: OSMnx / Overpass rate-limiting
Na předchozím projektu (`urbanMAL`, Menzerath-Altmannův zákon v urbánní morfologii)
došlo při stahování stovek měst přes veřejný Overpass server (`overpass-api.de`) po
~60 dotazech k patologickému chování (opakované connect timeouty), stahování
zpomalilo na ~56 min/město. Řešení tam bylo stáhnout celostátní `.osm.pbf` extrakt
z Geofabriku jednou a číst lokálně přes GDAL OSM driver (`geopandas.read_file`).

**Rozdíl oproti tomuto projektu:** ten trik dával jen plochý `GeoDataFrame` hran
(dobré pro délky segmentů), ne routovatelný `networkx` graf s uzly, který tady
potřebujeme pro topologické metriky (betweenness centrality, clustering coefficient,
stupeň uzlu) i pro `osmnx.bearing`. Pro náš vzorek (~50–100 sídel, o řád menší než
843 měst v `urbanMAL`) by ale mělo stačit jednodušší řešení:
- `ox.graph_from_place()` / `ox.graph_from_point()` per sídlo, s **diskovou cache**
  (`.graphml` v `data/raw/`) — jednou stažené sídlo se nikdy nestahuje znovu, ani při
  opakovaných bězích notebooku,
- pokud i tak narazíme na rate-limit: rozestupy mezi requesty (`ox.settings.pause`/
  retry) nebo přechod na lokální `.osm.pbf` + rekonstrukci grafu z něj (technicky
  složitější, zatím ve `urbanMAL` nevyzkoušené pro plný graf, jen pro ploché hrany) —
  řešit až pokud se to reálně ukáže jako problém při daném řádu velikosti vzorku.

Detailní rozhodnutí o strategii stahování je součástí kroku 4 (architektura) před
psaním kódu. Zvolené řešení: `ox.graph_from_place()` per sídlo + disková cache
(`data/raw/graphs/<slug>.graphml`, kontrola existence před každým stažením) —
při pádu/přerušení běhu se sídla, co už mají soubor na disku, nikdy nestahují
znovu, takže navazování na přerušený běh je zadarmo díky samotné cache, ne jen
díky incremental CSV zápisu metrik.

### Rešerše: typologie půdorysu vesnic (okrouhlice/ulicovka)
Typologie je v české sídelní geografii zavedená (Máčel 1955, Černý 1979,
Frolec–Vařeka 1983) — okrouhlice (návesní ves okrouhlého půdorysu, gotická
kolonizace) a ulicovka (řadová ves podél cesty). Konkrétní citované příklady
(Lipnice, Jablečno, Beranov, Šerchov, Kýšovice, Sobětice, Třebíška, Byšičky,
Terešov) jsou ale téměř všechny dnes **místní části** jiných obcí, ne
samostatné obce — stejný problém jako u Josefova/Jaroměře. Proto (rozhodnuto
2026-08-31) **RQ3 nepoužívá apriorně vybrané páry konkrétních obcí** a je
místo toho explorativní otázkou nad výsledky shlukování (§3.3). Zdroje:
[Okrouhlice — lidová architektura](https://www.lidova-architektura.cz/sidla/vesnice-okrouhle-okrouhlice/),
[Ulicová vesnice — Wikipedie](https://cs.wikipedia.org/wiki/Ulicov%C3%A1_vesnice),
[Terešov (Hlubočany) — Wikipedie](https://cs.wikipedia.org/wiki/Tere%C5%A1ov_(Hlubo%C4%8Dany)).

### Otevřená rozhodnutí

| Rozhodnutí | Možnosti | Status |
|---|---|---|
| `network_type` | `'drive'` / `'all'` | → rozhodnout v pilotu (Fáze 0) |
| Binning bearingu | 16 / 32 / 36 binů | → rozhodnout v pilotu, srovnat s Boeingovou metodou |
| Shlukovací algoritmus | K-Means / DBSCAN / hierarchické | → vyzkoušet víc, srovnat interpretovatelnost |
| Definice hranice sídla | admin. boundary / okolí bodu (radius) | → admin. boundary (aktuální vzorek jsou samá města s jasnou OSM hranicí) |
| Velikost vzorku | 33 (aktuální seed) vs. rozšíření na 50–100 | → rozšířit ve Fázi 1, pokud pilot ukáže, že stahování/výpočet zvládá dané tempo |

---

## 6. Datové zdroje

| Zdroj | Data | Poznámka |
|---|---|---|
| **OpenStreetMap / OSMnx** | Uliční síť (graf), hranice sídel | Hlavní zdroj |
| **RÚIAN + ČSÚ** (`data/processed/cz_municipalities.csv`) | Kód obce, okres, kraj, populace, souřadnice pro všech 6 259 obcí ČR | Migrováno z projektu `GeoGram_sufix-ice` (`src/streets/registry.py`) — používá se k disambiguaci sídel se shodným názvem a jako kontext pro RQ3 |

---

## 7. Architektura kódu (návrh — k odsouhlasení v kroku 4)

### Princip
- **Notebooky** (`notebooks/`) jsou čistě orchestrátory: načtou data, zavolají funkce
  z `src`, zobrazí výsledky. Žádná analytická logika přímo v notebooku.
- Veškerá logika žije v `src/streets/`.

### Struktura `src/streets/`

```
src/streets/
├── __init__.py
├── osm.py           # stahování/cachování grafů (.graphml) + hranic sídel přes OSMnx
├── metrics.py        # bearing/orientace, entropie, betweenness, clustering coeff, ...
├── clustering.py      # feature matice + K-Means/DBSCAN/hierarchické (scikit-learn) + PCA
└── viz.py             # polar ploty orientace, poster mřížka (styl přes src/viz.py)
```

### Ukládání dat
- `data/raw/` — surové stažené grafy (`.graphml` per sídlo) a hranice (GeoJSON)
- `data/processed/` — feature matice metrik (`sample_metrics.csv`), výsledky shlukování
- `reports/figures/` — polar ploty, poster mřížka, PCA scatter shluků

---

## 8. Potenciální výstupy

- Článek na osobní web s posterovou vizualizací (hlavní, blízký cíl)
- Případně (po konzultaci s kolegy) rozšíření do odborného textu
- Replikační balíček (kód na GitHubu)
