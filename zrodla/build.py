"""Buduje index.html (oraz sitemap.xml i robots.txt) z plików w zrodla/.

Godziny mszy i ogłoszenia bierze z zrodla/dane.json (kopia Arkusza Google,
odświeżana przez zrodla/pobierz_arkusz.py) i wpisuje je wprost w HTML,
żeby widziały je Google i asystenci AI, którzy nie uruchamiają JavaScriptu.
"""
import datetime, html, json, pathlib, re, unicodedata, zoneinfo

src = pathlib.Path(__file__).parent
strona = src.parent
ADRES_STRONY = "https://parafia-dabki.pl/"

FONTY = "Marcellus&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400"
ZNAK = '<svg viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="20" cy="20" r="17"/><circle cx="20" cy="20" r="14" opacity=".5"/><path d="M20 9v22M13 16h14" stroke-width="2.4" stroke-linecap="round"/></svg>'
ART = '<svg class="ornament" viewBox="0 0 360 26" fill="none" stroke="currentColor" aria-hidden="true"><path d="M0 13h150M210 13h150" stroke-width="1"/><path d="M0 17h140M220 17h140" stroke-width=".6" opacity=".6"/><path d="M180 2l3.2 7.8L191 13l-7.8 3.2L180 24l-3.2-7.8L169 13l7.8-3.2z" fill="currentColor" stroke="none"/><circle cx="160" cy="13" r="2" fill="currentColor" stroke="none"/><circle cx="200" cy="13" r="2" fill="currentColor" stroke="none"/></svg>'
TYTUL = "Parafia Dąbki – Matki Bożej z Góry Karmel | Msze święte, ogłoszenia"
OPIS = ("Parafia rzymskokatolicka Matki Bożej z Góry Karmel w Dąbkach (gmina Darłowo), "
        "ul. Darłowska 14. Godziny mszy świętych, ogłoszenia duszpasterskie, dojazd i kontakt.")

MIESIACE = ["sty", "lut", "mar", "kwi", "maj", "cze", "lip", "sie", "wrz", "paz", "lis", "gru"]
DNI_EN = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


# ===== te same reguły co w parafia.js =====
def norm(s):
    s = str(s or "").lower().replace("ł", "l")
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c)).strip()

def miesiac(s):
    try:
        n = int(str(s).strip())
        if 1 <= n <= 12:
            return n
    except ValueError:
        pass
    w = norm(s)[:3]
    return MIESIACE.index(w) + 1 if w in MIESIACE else None

def w_okresie(m, od, do):
    if od is None or do is None:
        return True
    return od <= m <= do if od <= do else (m >= od or m <= do)

def dzien(slowo):
    w = norm(slowo)
    for wzor, d in [(r"^pon", 1), (r"^wt", 2), (r"^sr", 3), (r"^cz", 4), (r"^(pi|pt)", 5), (r"^so", 6), (r"^(ni|nd)", 0)]:
        if re.match(wzor, w):
            return d
    return None

def dni_tygodnia(s):
    w = norm(s)
    if "codzien" in w:
        return list(range(7))
    if "powszedn" in w:
        return [1, 2, 3, 4, 5, 6]
    wynik = []
    for cz in re.split(r"[,;]| i ", w):
        zakres = re.split(r"\s*[–—-]\s*", cz.strip())
        a = dzien(zakres[0])
        if a is None:
            continue
        b = dzien(zakres[1]) if len(zakres) > 1 else None
        if b is None:
            wynik.append(a)
            continue
        d = a
        while True:
            wynik.append(d)
            if d == b:
                break
            d = (d + 1) % 7
    return wynik

def godziny(s):
    return [f"{h}:{m}" for h, m in re.findall(r"(\d{1,2})[:.](\d{2})", str(s))]

def wiersze(dane):
    return [r for r in dane if r and any(str(c or "").strip() for c in r)]

def kol(r, i):
    return str(r[i]).strip() if i < len(r) and r[i] is not None else ""


# ===== HTML =====
e = lambda s: html.escape(str(s), quote=True)

def html_msze(msze, m):
    grupy = {}
    for r in msze:
        d = dni_tygodnia(kol(r, 0))
        k = "Niedziele i święta" if d == [0] else "Dni powszednie"
        grupy.setdefault(k, []).append(r)
    out = []
    for k, rows in grupy.items():
        li = []
        for r in rows:
            teraz = w_okresie(m, miesiac(kol(r, 1)), miesiac(kol(r, 2)))
            okres = f"{e(kol(r, 1))} – {e(kol(r, 2))}" if kol(r, 1) or kol(r, 2) else "cały rok"
            li.append(
                f'<li class="okres{" teraz" if teraz else ""}">'
                f'<div class="okres-glowa"><span class="okres-nazwa">{okres}</span>'
                + ('<span class="znacznik">obowiązuje teraz</span>' if teraz else "") + "</div>"
                + (f'<p class="okres-dni">{e(kol(r, 0))}</p>' if k == "Dni powszednie" else "")
                + '<div class="godziny">' + "".join(f'<span class="godzina">{g}</span>' for g in godziny(kol(r, 3))) + "</div>"
                + (f'<p class="okres-uwagi">{e(kol(r, 4))}</p>' if kol(r, 4) else "") + "</li>")
        out.append(f'<article class="msze-karta"><h3>{e(k)}</h3><ul>{"".join(li)}</ul></article>')
    return "".join(out)

def podziel_ogloszenia(ogl):
    koniec = [r for r in ogl if norm(kol(r, 0)) == "zakonczenie"]
    zwykle = [r for r in ogl if norm(kol(r, 0)) != "zakonczenie"]
    return zwykle, koniec

def html_ogloszenia(ogl):
    zwykle, koniec = podziel_ogloszenia(ogl)
    data = kol(zwykle[0], 0) if zwykle else ""
    lista = "".join(f"<li>{e(kol(r, 1)).replace(chr(10), '<br>')}</li>" for r in zwykle) \
        or '<li class="brak">Brak ogłoszeń w tym tygodniu.</li>'
    return e(data), lista, "".join(f"<p>{e(kol(r, 1))}</p>" for r in koniec)


# ===== dane strukturalne (schema.org) =====
def msze_tekst(msze):
    return "; ".join(
        f"{kol(r, 0)}" + (f" ({kol(r, 1)}–{kol(r, 2)})" if kol(r, 1) or kol(r, 2) else "")
        + f": {', '.join(godziny(kol(r, 3)))}" + (f" – {kol(r, 4)}" if kol(r, 4) else "")
        for r in msze)

def json_ld(msze):
    dane = {
        "@context": "https://schema.org",
        "@type": "Church",
        "@id": ADRES_STRONY + "#parafia",
        "name": "Parafia Rzymskokatolicka pw. Matki Bożej z Góry Karmel w Dąbkach",
        "alternateName": ["Parafia Dąbki", "Kościół w Dąbkach", "Kościół Matki Bożej z Góry Karmel w Dąbkach"],
        "description": "Godziny mszy świętych: " + msze_tekst(msze) + ".",
        "url": ADRES_STRONY,
        "image": ADRES_STRONY + "img/kosciol-front.jpg",
        "telephone": "+48 94 314 86 08",
        "email": "dabki@koszalin.opoka.org.pl",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "ul. Darłowska 14",
            "postalCode": "76-156",
            "addressLocality": "Dąbki",
            "addressRegion": "zachodniopomorskie",
            "addressCountry": "PL",
        },
        "hasMap": "https://www.google.com/maps/search/?api=1&query=" + "Ko%C5%9Bci%C3%B3%C5%82%20Matki%20Bo%C5%BCej%20z%20G%C3%B3ry%20Karmel%2C%20Dar%C5%82owska%2014%2C%2076-156%20D%C4%85bki",
        "isAccessibleForFree": True,
    }
    return json.dumps(dane, ensure_ascii=False, indent=1).replace("</", "<\\/")


def zbuduj(dane, dzis):
    msze, ogl = wiersze(dane["msze"]), wiersze(dane["ogloszenia"])
    data, lista, koniec = html_ogloszenia(ogl)
    tresc = (src / "tresc.html").read_text()
    for k, v in {
        "{{ZNAK}}": ZNAK, "{{HERO_ART}}": ART,
        "{{NAJBLIZSZA_CZAS}}": "—", "{{NAJBLIZSZA_DZIEN}}": "Godziny mszy znajdziesz w rozkładzie poniżej.",
        "{{MSZE}}": html_msze(msze, dzis.month),
        "{{OGL_DATA}}": data, "{{OGLOSZENIA}}": lista, "{{OGL_KONIEC}}": koniec,
    }.items():
        tresc = tresc.replace(k, v)
    css = (src / "baza.css").read_text() + "\n" + (src / "klasyczna.css").read_text()
    js = (src / "parafia.js").read_text().replace("osadzMape: false", "osadzMape: true")
    js = re.sub(r"/\*DANE\*/.*?/\*KONIEC\*/",
                lambda _: json.dumps({"msze": msze, "ogloszenia": ogl}, ensure_ascii=False).replace("</", "<\\/"),
                js, flags=re.S)
    return ('<!doctype html>\n<html lang="pl">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f"<title>{e(TYTUL)}</title>\n"
            f'<meta name="description" content="{e(OPIS)}">\n'
            f'<link rel="canonical" href="{ADRES_STRONY}">\n'
            '<meta property="og:type" content="website">\n'
            '<meta property="og:locale" content="pl_PL">\n'
            f'<meta property="og:title" content="{e(TYTUL)}">\n'
            f'<meta property="og:description" content="{e(OPIS)}">\n'
            f'<meta property="og:url" content="{ADRES_STRONY}">\n'
            f'<meta property="og:image" content="{ADRES_STRONY}img/kosciol-front.jpg">\n'
            f'<script type="application/ld+json">\n{json_ld(msze)}\n</script>\n'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
            f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family={FONTY}&display=swap">\n'
            f"<style>\n{css}</style>\n"
            "</head>\n<body>\n" + tresc + f"\n<script>\n{js}</script>\n</body>\n</html>\n")


if __name__ == "__main__":
    dane = json.loads((src / "dane.json").read_text())
    dzis = datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Warsaw"))
    (strona / "index.html").write_text(zbuduj(dane, dzis))
    (strona / "CNAME").write_text("parafia-dabki.pl\n")
    (strona / ".nojekyll").write_text("")
    (strona / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {ADRES_STRONY}sitemap.xml\n")
    (strona / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{ADRES_STRONY}</loc></url>\n</urlset>\n")
    print("ok")
