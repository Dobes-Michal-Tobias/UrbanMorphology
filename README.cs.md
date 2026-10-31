# Morfologie uličních sítí českých měst

Výzkumný projekt prostorové analýzy, který zkoumá uliční sítě českých měst
a obcí optikou urbánní morfologie: orientaci ulic (bearing), topologické
vlastnosti grafu a morfologické shlukování. Postaveno na
[OSMnx](https://osmnx.readthedocs.io/), NetworkX a scikit-learn.

**Výsledky:** [Doprava a rovně! Orientace ulic českých měst](https://dobes-michal-tobias.github.io/michal-tobias-dobes.cz/projekty/urban-morphology.html) (článek na webu)

English version: [README.md](README.md)

Přímou inspirací je poster/článek Geoffa Boeinga *"Urban spatial order:
street network orientation, configuration, and entropy"* (viz
`Geoff-Boeing_Motivation_Picture.png` v tomto repozitáři) — cílem je
obdobné vizuální a statistické zpracování pro česká sídla, nejprve jako
článek na osobní web, případně později rozšířené do odborného textu.

Kompletní výzkumný design (otázky, metodologie, fáze pipeline) je v
[`MasterOutline.md`](MasterOutline.md) — to je zdroj pravdy pro "proč" a
"co"; tenhle README popisuje "jak to spustit."

## Výzkumné otázky (stručně)

1. Jak se liší **orientace** uliční sítě (distribuce bearingu, entropie)
   napříč českými městy a souvisí to s věkem, velikostí nebo historií
   plánování města?
2. Jak se liší **topologické vlastnosti** (circuity, hustota křižovatek,
   průměrný stupeň uzlu, clustering coefficient) mezi historickými centry
   a okrajovou/suburbánní zástavbou?
3. Tvoří česká města rozlišitelné **morfologické shluky**, a pokud ano,
   co je pro jednotlivé shluky charakteristické?

Detaily, hypotézy a fázovaný plán sběru dat: `MasterOutline.md`.

## Struktura projektu

```
data/           raw/ interim/ processed/ external/  — gitignored
notebooks/      orchestrační notebooky — logika je v src/, ne tady
src/            jádro znovupoužitelného kódu (config.py, viz.py, io_utils.py)
                + src/streets/ — doménová logika tohoto projektu (viz níže)
modules/        volitelný doménový kód převzatý ze šablony
models/         natrénované modely — gitignored
reports/figures/  uložené grafy (polar orientation plots atd.) — gitignored
scripts/        skripty pro nastavení prostředí
```

`src/streets/` (vlastní balíček tohoto projektu) obsahuje:
- `osm.py` — stahování/cachování uličních sítí per město přes OSMnx
- `metrics.py` — bearing/orientace, circuity, hustota křižovatek,
  clustering coefficient pro každý graf
- `clustering.py` — sestavení feature matice + shlukování scikit-learn
  (KMeans / hierarchické) nad morfologickými metrikami měst
- `viz.py` — polar (rose) grafy orientace ulic, ve stylu `src/viz.py`

(Tahle struktura je návrh z `MasterOutline.md` §7 — může se změnit, až se
shodneme na architektuře.)

## Setup

```powershell
.\scripts\setup_env.ps1          # Windows
```
```bash
./scripts/setup_env.sh           # macOS/Linux
```

Vytvoří `.venv`, nainstaluje `requirements.txt` (obsahuje `osmnx`,
`networkx`, `geopandas`, `scikit-learn`) a zaregistruje Jupyter kernel
pojmenovaný podle složky projektu.

## Volitelné moduly převzaté ze šablony

| Modul | K čemu slouží |
|---|---|
| [`modules/network_viz`](modules/network_viz) | Vykreslování networkx grafů v barevném stylu projektu — pro obrázky uličních sítí |
| [`modules/ml_model`](modules/ml_model) | OOP obal nad modely + trénovací smyčka; ponecháno pro případnou budoucí klasifikaci morfologických typů (metriky tam cílí na klasifikátory, ne shlukování — upravit až/pokud se použije) |

## Konvence

Stejné jako v rodičovské šabloně (`principles.md`, necommitovaný — viz
poznámka tam): notebooky orchestrují, logika je v `.py` souborech; grafy
jdou přes sdílený styl `src/viz.py`; dlouhé smyčky (stahování stovek měst)
vždy s progress barem a průběžným zápisem výsledků, aby pád neztratil
hotovou práci — viz `MasterOutline.md` pro ponaučení o rate-limitingu
OSMnx z předchozího projektu.

## Licence

MIT — viz [LICENSE](LICENSE).
