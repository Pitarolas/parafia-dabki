(function () {
  // ===== USTAWIENIA =====
  // arkuszId: identyfikator Arkusza Google z adresu
  //   https://docs.google.com/spreadsheets/d/<TU_JEST_ID>/edit
  // Arkusz musi być udostępniony "Każdy, kto ma link, może wyświetlać".
  // Puste = strona pokazuje tylko kopię danych wpisaną w stronę.
  var KONFIG = {
    arkuszId: "16jOSdoO5qnS31DFOOotpNGsSqQRZVqqqgYlffLeZCVU",
    zakladki: { msze: "Msze", ogloszenia: "Ogłoszenia" },
    celMapy: "Kościół Matki Bożej z Góry Karmel, Darłowska 14, 76-156 Dąbki",
    osadzMape: false
  };

  // Ostatnia kopia danych z arkusza, wpisywana przez zrodla/build.py.
  // Strona pokazuje ją od razu, a potem odświeża z Arkusza Google.
  // Msze: Dni | Od miesiąca | Do miesiąca | Godziny | Uwagi
  // Ogłoszenia: Niedziela | Treść (wiersz "Zakończenie" = słowo na koniec, bez numeru)
  var DANE = /*DANE*/{ msze: [], ogloszenia: [] }/*KONIEC*/;

  var MIESIACE = ["sty", "lut", "mar", "kwi", "maj", "cze", "lip", "sie", "wrz", "paz", "lis", "gru"];
  var MIESIACE_DOP = ["stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca", "sierpnia", "września", "października", "listopada", "grudnia"];
  var DNI_KIEDY = ["W niedzielę", "W poniedziałek", "We wtorek", "W środę", "W czwartek", "W piątek", "W sobotę"];

  function $(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function norm(s) {
    return String(s || "").toLowerCase().replace(/ł/g, "l").normalize("NFD").replace(/[̀-ͯ]/g, "").trim();
  }

  // "wrzesień" / "wrz" / "9" -> 9
  function miesiac(s) {
    var n = parseInt(s, 10);
    if (n >= 1 && n <= 12) return n;
    var w = norm(s).slice(0, 3);
    var i = MIESIACE.indexOf(w);
    return i >= 0 ? i + 1 : null;
  }
  function wOkresie(m, od, doM) {
    if (od == null || doM == null) return true;
    return od <= doM ? (m >= od && m <= doM) : (m >= od || m <= doM);
  }

  function dzien(slowo) {
    var w = norm(slowo);
    if (/^pon/.test(w)) return 1;
    if (/^wt/.test(w)) return 2;
    if (/^sr/.test(w)) return 3;
    if (/^cz/.test(w)) return 4;
    if (/^(pi|pt)/.test(w)) return 5;
    if (/^so/.test(w)) return 6;
    if (/^(ni|nd)/.test(w)) return 0;
    return null;
  }
  // "Wtorek–sobota", "Niedziele i święta", "pon, śr, pt", "codziennie" -> [dni tygodnia]
  function dniTygodnia(s) {
    var w = norm(s);
    if (/codzien/.test(w)) return [0, 1, 2, 3, 4, 5, 6];
    if (/powszedn/.test(w)) return [1, 2, 3, 4, 5, 6];
    var wynik = [];
    w.split(/[,;]| i /).forEach(function (cz) {
      var zakres = cz.split(/\s*[–—-]\s*/);
      var a = dzien(zakres[0]);
      if (a == null) return;
      if (zakres.length > 1) {
        var b = dzien(zakres[1]);
        if (b == null) { wynik.push(a); return; }
        for (var d = a; ; d = (d + 1) % 7) { wynik.push(d); if (d === b) break; }
      } else {
        wynik.push(a);
      }
    });
    return wynik;
  }
  function godziny(s) {
    var out = [], re = /(\d{1,2})[:.](\d{2})/g, m;
    while ((m = re.exec(String(s)))) out.push({ h: +m[1], m: +m[2], txt: m[1] + ":" + m[2] });
    return out;
  }

  function wiersze(dane) {
    return dane.filter(function (r) { return r && r.some(function (c) { return String(c || "").trim(); }); });
  }

  function najblizsza(msze, teraz) {
    for (var d = 0; d < 8; d++) {
      var data = new Date(teraz.getFullYear(), teraz.getMonth(), teraz.getDate() + d);
      var dt = data.getDay(), m = data.getMonth() + 1, kandydaci = [];
      msze.forEach(function (r) {
        if (dniTygodnia(r[0]).indexOf(dt) < 0) return;
        if (!wOkresie(m, miesiac(r[1]), miesiac(r[2]))) return;
        godziny(r[3]).forEach(function (g) {
          var t = new Date(data); t.setHours(g.h, g.m, 0, 0);
          if (t > teraz) kandydaci.push({ t: t, txt: g.txt });
        });
      });
      if (kandydaci.length) {
        kandydaci.sort(function (a, b) { return a.t - b.t; });
        var kiedy = d === 0 ? "Dziś" : d === 1 ? "Jutro" : DNI_KIEDY[dt];
        return { czas: kandydaci[0].txt, dzien: kiedy + ", " + data.getDate() + " " + MIESIACE_DOP[data.getMonth()] };
      }
    }
    return null;
  }

  function rysujMsze(msze) {
    var teraz = new Date(), m = teraz.getMonth() + 1, grupy = [], mapa = {};
    msze.forEach(function (r) {
      var d = dniTygodnia(r[0]);
      var k = d.length === 1 && d[0] === 0 ? "Niedziele i święta" : "Dni powszednie";
      if (!mapa[k]) { mapa[k] = []; grupy.push(k); }
      mapa[k].push(r);
    });
    $("msze-lista").innerHTML = grupy.map(function (k) {
      return '<article class="msze-karta"><h3>' + esc(k) + "</h3><ul>" + mapa[k].map(function (r) {
        var teraz = wOkresie(m, miesiac(r[1]), miesiac(r[2]));
        var okres = r[1] || r[2] ? esc(r[1]) + " – " + esc(r[2]) : "cały rok";
        return '<li class="okres' + (teraz ? " teraz" : "") + '">' +
          '<div class="okres-glowa"><span class="okres-nazwa">' + okres + "</span>" +
          (teraz ? '<span class="znacznik">obowiązuje teraz</span>' : "") + "</div>" +
          (k === "Dni powszednie" ? '<p class="okres-dni">' + esc(r[0]) + "</p>" : "") +
          '<div class="godziny">' + godziny(r[3]).map(function (g) { return '<span class="godzina">' + g.txt + "</span>"; }).join("") + "</div>" +
          (r[4] ? '<p class="okres-uwagi">' + esc(r[4]) + "</p>" : "") + "</li>";
      }).join("") + "</ul></article>";
    }).join("");
    $("msze-opis").textContent = "Rozkład zmienia się z sezonem letnim. Zaznaczyliśmy godziny obowiązujące dziś, " +
      teraz.getDate() + " " + MIESIACE_DOP[teraz.getMonth()] + ".";

    var n = najblizsza(msze, teraz);
    $("najblizsza-czas").textContent = n ? n.czas : "—";
    $("najblizsza-dzien").textContent = n ? n.dzien : "Zadzwoń do parafii, aby potwierdzić godzinę.";
  }

  function rysujOgloszenia(ogl) {
    function zakonczenie(r) { return norm(r[0]) === "zakonczenie"; }
    var zwykle = ogl.filter(function (r) { return !zakonczenie(r); });
    var koniec = ogl.filter(zakonczenie);
    $("ogloszenia-data").textContent = zwykle.length ? String(zwykle[0][0] || "").trim() : "";
    $("ogloszenia-lista").innerHTML = zwykle.length ? zwykle.map(function (r) {
      return "<li>" + esc(r[1]).replace(/\n/g, "<br>") + "</li>";
    }).join("") : '<li class="brak">Brak ogłoszeń w tym tygodniu.</li>';
    $("ogloszenia-koniec").innerHTML = koniec.map(function (r) { return "<p>" + esc(r[1]) + "</p>"; }).join("");
  }

  function csv(tekst) {
    var rows = [], row = [], pole = "", cudz = false;
    for (var i = 0; i < tekst.length; i++) {
      var c = tekst[i];
      if (cudz) {
        if (c === '"' && tekst[i + 1] === '"') { pole += '"'; i++; }
        else if (c === '"') cudz = false;
        else pole += c;
      } else if (c === '"') cudz = true;
      else if (c === ",") { row.push(pole); pole = ""; }
      else if (c === "\n") { row.push(pole); rows.push(row); row = []; pole = ""; }
      else if (c !== "\r") pole += c;
    }
    if (pole || row.length) { row.push(pole); rows.push(row); }
    return rows;
  }
  function pobierz(zakladka) {
    var url = "https://docs.google.com/spreadsheets/d/" + KONFIG.arkuszId +
      "/gviz/tq?tqx=out:csv&headers=1&sheet=" + encodeURIComponent(zakladka);
    return fetch(url, { cache: "no-store" }).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.text();
    }).then(function (t) { return wiersze(csv(t).slice(1)); });
  }

  function mapa() {
    var cel = encodeURIComponent(KONFIG.celMapy);
    $("link-trasa").href = "https://www.google.com/maps/dir/?api=1&destination=" + cel;
    $("link-mapa").href = "https://www.google.com/maps/search/?api=1&query=" + cel;
    if (KONFIG.osadzMape) {
      $("mapa").innerHTML = '<iframe title="Mapa dojazdu do kościoła" loading="lazy" referrerpolicy="no-referrer-when-downgrade" src="https://www.google.com/maps?q=' + cel + '&output=embed"></iframe>';
    }
  }

  function rysuj(dane) {
    rysujMsze(wiersze(dane.msze));
    rysujOgloszenia(wiersze(dane.ogloszenia));
  }

  $("kopiuj-konto").addEventListener("click", function () {
    var nr = $("nr-konta").textContent.replace(/\s/g, ""), btn = this;
    function zaznacz() { var r = document.createRange(); r.selectNodeContents($("nr-konta")); var sel = getSelection(); sel.removeAllRanges(); sel.addRange(r); }
    var p = navigator.clipboard && navigator.clipboard.writeText(nr);
    if (p) p.then(function () { btn.textContent = "Skopiowano"; }, zaznacz); else zaznacz();
  });

  mapa();
  rysuj(DANE);
  if (KONFIG.arkuszId) {
    var z = KONFIG.zakladki;
    Promise.all([pobierz(z.msze), pobierz(z.ogloszenia)])
      .then(function (w) { if (w[0].length) rysuj({ msze: w[0], ogloszenia: w[1] }); })
      .catch(function () { /* zostaje kopia wpisana w stronę */ });
  }
})();
