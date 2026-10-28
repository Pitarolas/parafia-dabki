"""Pobiera zakładki Msze i Ogłoszenia z Arkusza Google i zapisuje je w zrodla/dane.json.

Gdy pobranie się nie uda (albo zakładka Msze jest pusta), zostawia poprzednią kopię,
żeby strona nigdy nie straciła godzin mszy.
"""
import csv, io, json, pathlib, re, sys, urllib.parse, urllib.request

src = pathlib.Path(__file__).parent
js = (src / "parafia.js").read_text()
ARKUSZ = re.search(r'arkuszId:\s*"([^"]*)"', js).group(1)
ZAKLADKI = {"msze": "Msze", "ogloszenia": "Ogłoszenia"}

def pobierz(zakladka):
    url = (f"https://docs.google.com/spreadsheets/d/{ARKUSZ}/gviz/tq?tqx=out:csv&headers=1&sheet="
           + urllib.parse.quote(zakladka))
    with urllib.request.urlopen(url, timeout=30) as r:
        tekst = r.read().decode("utf-8")
    wiersze = list(csv.reader(io.StringIO(tekst)))[1:]
    return [w for w in wiersze if any(c.strip() for c in w)]

try:
    dane = {k: pobierz(z) for k, z in ZAKLADKI.items()}
except Exception as blad:
    sys.exit(f"Nie udało się pobrać arkusza: {blad}")
if not dane["msze"]:
    sys.exit("Zakładka Msze jest pusta, zostawiam poprzednie dane.")
(src / "dane.json").write_text(json.dumps(dane, ensure_ascii=False, indent=1) + "\n")
print("Pobrano:", {k: len(v) for k, v in dane.items()})
