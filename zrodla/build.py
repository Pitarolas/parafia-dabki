import pathlib, sys
src = pathlib.Path(__file__).parent
out = src.parent / "podglad"; out.mkdir(exist_ok=True)
FONTY = {
  "nadmorska": "Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=Figtree:ital,wght@0,400;0,600;0,700;1,400",
  "klasyczna": "Marcellus&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400",
}
ZNAK = {
  "nadmorska": '<svg viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M20 5v18M13 11h14"/><path d="M5 28c3-2.5 6-2.5 9 0s6 2.5 9 0 6-2.5 9 0 3 1.5 4 1"/><path d="M5 34c3-2.5 6-2.5 9 0s6 2.5 9 0 6-2.5 9 0 3 1.5 4 1" opacity=".55"/></svg>',
  "klasyczna": '<svg viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="20" cy="20" r="17"/><circle cx="20" cy="20" r="14" opacity=".5"/><path d="M20 9v22M13 16h14" stroke-width="2.4" stroke-linecap="round"/></svg>',
}
ART = {
  "nadmorska": '<svg class="fale" viewBox="0 0 1440 120" preserveAspectRatio="none" aria-hidden="true"><path class="f1" d="M0 46c120 22 240 22 360 0s240-22 360 0 240 22 360 0 240-22 360 0v74H0z"/><path class="f2" d="M0 70c160 18 320 18 480 0s320-18 480 0 320 18 480 0v50H0z"/><path class="f3" d="M0 92c180 14 360 14 540 0s360-14 540 0 270 10 360 4v24H0z"/></svg>',
  "klasyczna": '<svg class="ornament" viewBox="0 0 360 26" fill="none" stroke="currentColor" aria-hidden="true"><path d="M0 13h150M210 13h150" stroke-width="1"/><path d="M0 17h140M220 17h140" stroke-width=".6" opacity=".6"/><path d="M180 2l3.2 7.8L191 13l-7.8 3.2L180 24l-3.2-7.8L169 13l7.8-3.2z" fill="currentColor" stroke="none"/><circle cx="160" cy="13" r="2" fill="currentColor" stroke="none"/><circle cx="200" cy="13" r="2" fill="currentColor" stroke="none"/></svg>',
}
NAZWA = {"nadmorska": "wersja nadmorska", "klasyczna": "wersja klasyczna"}
TYTUL = {"nadmorska": "Parafia Dąbki · nadmorska", "klasyczna": "Parafia Matki Bożej z Góry Karmel w Dąbkach"}

def zbuduj(wersja, pelny=False):
    tresc = (src / "tresc.html").read_text()
    tresc = tresc.replace("{{ZNAK}}", ZNAK[wersja]).replace("{{HERO_ART}}", ART[wersja]).replace("{{WERSJA}}", NAZWA[wersja])
    css = (src / "baza.css").read_text() + "\n" + (src / f"{wersja}.css").read_text()
    js = (src / "parafia.js").read_text()
    if pelny:
        js = js.replace("osadzMape: false", "osadzMape: true")
    glowa = (f'<title>{TYTUL[wersja]}</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
             '<meta name="description" content="Parafia Matki Bożej z Góry Karmel w Dąbkach: godziny mszy świętych, ogłoszenia duszpasterskie, intencje i dojazd.">\n'
             '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
             f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={FONTY[wersja]}&display=swap">\n'
             f"<style>\n{css}</style>\n")
    cialo = f"{tresc}\n<script>\n{js}</script>\n"
    if pelny:
        return ('<!doctype html>\n<html lang="pl">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                + glowa + "</head>\n<body>\n" + cialo + "</body>\n</html>\n")
    return glowa + cialo

(out / "klasyczna.html").write_text(zbuduj("klasyczna"))
strona = src.parent
(strona / "index.html").write_text(zbuduj("klasyczna", pelny=True))
(strona / "CNAME").write_text("parafia-dabki.pl\n")
(strona / ".nojekyll").write_text("")
print("ok")
