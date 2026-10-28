# Strona parafii Matki Bożej z Góry Karmel w Dąbkach

Strona: https://parafia-dabki.pl

- `index.html`, `img/`, `sitemap.xml`, `robots.txt` – gotowa strona publikowana przez GitHub Pages.
- `zrodla/` – pliki źródłowe. Po zmianie uruchom `python3 zrodla/build.py`, który odtworzy `index.html`.
- Ogłoszenia i godziny mszy pochodzą z Arkusza Google (ustawienie `arkuszId` w `zrodla/parafia.js`):
  - co 3 godziny GitHub Action (`.github/workflows/aktualizuj.yml`) pobiera arkusz do `zrodla/dane.json`
    i wpisuje dane wprost w `index.html`, żeby widziały je Google i asystenci AI;
  - w przeglądarce strona dodatkowo odświeża dane z arkusza na żywo.
- Aktualizację można wymusić od razu: zakładka **Actions** → „Aktualizuj stronę z arkusza” → **Run workflow**.
