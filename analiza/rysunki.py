"""Wireframe dashboardu (krok 8) i schemat modelu danych (krok 4) jako PNG.

Uruchomienie: python analiza/rysunki.py  ->  raport/wykresy/15_*.png, 16_*.png, 17_*.png
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WYK = os.path.join(ROOT, "raport", "wykresy")
os.makedirs(WYK, exist_ok=True)

NAVY = "#184f95"
GREEN = "#0ca30c"
RED = "#d03b3b"
TLO = "#f0efec"
KARTA = "#ffffff"
INK = "#0b0b0b"
INK2 = "#52514e"
LINIA = "#b9b8b2"
plt.rcParams["font.family"] = ["Segoe UI", "DejaVu Sans"]


def pudelko(ax, x, y, w, h, tytul, opis="", pytanie="", szkic=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.6", fc=KARTA, ec=LINIA, lw=1))
    ax.text(x + 1, y + h - 1.2, tytul, fontsize=10, fontweight="bold", color=INK, va="top")
    if opis:
        ax.text(x + 1, y + h - 3.6, opis, fontsize=8, color=INK2, va="top", wrap=True)
    if pytanie:
        ax.add_patch(FancyBboxPatch((x + w - 7.5, y + h - 3.2), 6.5, 2.4, boxstyle="round,pad=0,rounding_size=0.8", fc=NAVY, ec="none"))
        ax.text(x + w - 4.25, y + h - 2.0, pytanie, fontsize=8, color="white", ha="center", va="center", fontweight="bold")
    if szkic:
        szkic(ax, x, y, w, h)


def sz_slupki(ax, x, y, w, h, prog=True):
    wart = [0.95, 0.9, 0.85, 0.8, 0.72, 0.6, 0.55, 0.5]
    for i, v in enumerate(wart):
        kol = GREEN if v >= 0.7 else LINIA
        ax.add_patch(Rectangle((x + 2, y + 2 + i * (h - 9) / len(wart)), (w - 6) * v, (h - 9) / len(wart) * 0.65, fc=kol, ec="none"))
    if prog:
        xp = x + 2 + (w - 6) * 0.7
        ax.plot([xp, xp], [y + 1.5, y + h - 6], color=RED, ls="--", lw=1.2)
        ax.text(xp + 0.4, y + 1.2, "próg 6%", fontsize=7, color=RED)


def sz_mapa(ax, x, y, w, h):
    import numpy as np
    rng = np.random.default_rng(3)
    ax.add_patch(Rectangle((x + 2, y + 2), w - 4, h - 9, fc="#e9eef6", ec="none"))
    for _ in range(12):
        px, py = x + 4 + rng.random() * (w - 8), y + 4 + rng.random() * (h - 14)
        r = 0.6 + rng.random() * 1.6
        ax.add_patch(plt.Circle((px, py), r, fc=GREEN if rng.random() > 0.35 else RED, alpha=0.6, ec="white"))


def sz_linie(ax, x, y, w, h):
    import numpy as np
    xs = np.linspace(x + 2, x + w - 2, 11)
    ax.plot(xs, y + 4 + np.linspace(0, h - 14, 11) * 0.9, color=NAVY, lw=1.6)
    ax.plot(xs, y + 4 + np.linspace(0, h - 14, 11) * 0.25 + 2, color="#eb6834", lw=1.6)


def sz_punkty(ax, x, y, w, h):
    import numpy as np
    rng = np.random.default_rng(7)
    ax.add_patch(Rectangle((x + w * 0.62, y + 2), w * 0.36, h - 9, fc="#fbe3e3", ec="none"))
    ax.text(x + w * 0.64, y + 2.5, "strefa ryzyka", fontsize=7, color=RED)
    for _ in range(14):
        ax.add_patch(plt.Circle((x + 3 + rng.random() * (w - 6), y + 3 + rng.random() * (h - 12)), 0.7, fc=NAVY, ec="white"))


def sz_heat(ax, x, y, w, h):
    import numpy as np
    rng = np.random.default_rng(1)
    kol = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf"]
    n, m = 6, 4
    cw, ch = (w - 4) / m, (h - 9) / n
    for i in range(n):
        for j in range(m):
            ax.add_patch(Rectangle((x + 2 + j * cw, y + 2 + i * ch), cw - 0.3, ch - 0.3, fc=kol[rng.integers(0, 5)], ec="none"))


def karta_kpi(ax, x, y, w, h, nazwa, war, kolor_war):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.6", fc=KARTA, ec=LINIA, lw=1))
    ax.text(x + 1, y + h - 1.3, nazwa, fontsize=8, color=INK2, va="top")
    ax.text(x + 1, y + 1.4, war, fontsize=15, color=kolor_war, fontweight="bold")


def ramka(tytul, podtytul):
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.set_xlim(0, 160)
    ax.set_ylim(0, 90)
    ax.axis("off")
    ax.add_patch(Rectangle((0, 0), 160, 90, fc=TLO, ec="none"))
    ax.add_patch(Rectangle((0, 83), 160, 7, fc=NAVY, ec="none"))
    ax.text(2, 86.5, tytul, fontsize=15, color="white", fontweight="bold", va="center")
    ax.text(158, 86.5, podtytul, fontsize=9, color="white", va="center", ha="right")
    return fig, ax


# ------------------------------------------------------------------ strona 1
fig, ax = ramka("Strona 1 – strategiczna: porównanie miast", "ceny ofertowe, nie transakcyjne · 08.2023–06.2024")
for i, f in enumerate(["Miesiąc ▾", "Segment metrażu ▾", "Województwo ▾"]):
    ax.add_patch(FancyBboxPatch((2 + i * 27, 77.5), 25, 4, boxstyle="round,pad=0,rounding_size=0.5", fc=KARTA, ec=LINIA))
    ax.text(3 + i * 27, 79.5, f, fontsize=9, color=INK, va="center")
ax.add_patch(FancyBboxPatch((122, 77.5), 36, 4, boxstyle="round,pad=0,rounding_size=0.5", fc="none", ec=NAVY, ls="--"))
ax.text(123, 79.5, "P1 · P2 · P3 = pytania klienta", fontsize=8, color=NAVY, va="center")
kpi = [("Rentowność brutto", "5,85%", NAVY), ("Cena za m²", "12 989 zł", INK), ("Czynsz za m²", "65,9 zł", INK),
       ("Obciążenie płacy (40–60 m²)", "32,9%", RED), ("Nowa podaż / 1000 mieszk.", "8,8", INK)]
for i, (n, v, k) in enumerate(kpi):
    karta_kpi(ax, 2 + i * 31.4, 66, 29.8, 9.5, n, v, k)
pudelko(ax, 2, 34, 77, 30, "Ranking miast wg rentowności brutto", "słupki; zielone ≥ próg 6%, szare poniżej; linia progu", "P1", sz_slupki)
pudelko(ax, 81, 34, 77, 30, "Mapa miast", "bąbelek = rentowność, kolor = obciążenie płacy (czerwony > 30%)", "P1 P3", sz_mapa)
pudelko(ax, 2, 2, 77, 30, "Trend ceny i czynszu za m²", "linie, mediana miesięczna; czynsz od 11.2023", "P1", sz_linie)
pudelko(ax, 81, 2, 77, 30, "Macierz ryzyka: obciążenie płacy × nowa podaż", "punkty = miasta; prawy obszar = obciążenie > 30%", "P3", sz_punkty)
fig.savefig(os.path.join(WYK, "15_wireframe_strategiczna.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ------------------------------------------------------------------ strona 2
fig, ax = ramka("Strona 2 – analityczna: segmenty (drill-through z miasta)", "← powrót do strony 1 · ceny ofertowe, nie transakcyjne")
for i, f in enumerate(["Miasto: Łódź (z drill-through)", "Miesiąc ▾", "Typ budynku ▾"]):
    ax.add_patch(FancyBboxPatch((2 + i * 34, 77.5), 32, 4, boxstyle="round,pad=0,rounding_size=0.5", fc=KARTA, ec=LINIA))
    ax.text(3 + i * 34, 79.5, f, fontsize=9, color=INK, va="center")
pudelko(ax, 2, 34, 77, 41, "Heatmapa: miasto × metraż", "macierz z formatowaniem warunkowym (kolor = rentowność)", "P2", sz_heat)
pudelko(ax, 81, 34, 77, 41, "Rentowność wg odległości od centrum", "słupki dla < 2 / 2–5 / 5–10 / > 10 km", "P2",
        lambda a, x, y, w, h: sz_slupki(a, x, y, w, h, prog=True))
pudelko(ax, 2, 2, 77, 30, "Wpływ cech na czynsz vs cenę", "premia za balkon, windę, parking, stan premium (pp)", "P2", sz_slupki)
pudelko(ax, 81, 2, 77, 30, "Tabela szczegółów", "liczba ofert, mediany, rentowność; tooltip z liczbą ofert", "P1 P2", sz_heat)
fig.savefig(os.path.join(WYK, "16_wireframe_analityczna.png"), dpi=150, bbox_inches="tight")
plt.close(fig)

# ------------------------------------------------------------------ schemat modelu (gwiazda)
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 140)
ax.set_ylim(0, 80)
ax.axis("off")


def tabela(x, y, nazwa, kolumny, fakt=False):
    w, h = 26, 4 + 3 * len(kolumny)
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.8", fc="white", ec=NAVY if fakt else LINIA, lw=1.6 if fakt else 1))
    ax.add_patch(FancyBboxPatch((x, y + h - 4), w, 4, boxstyle="round,pad=0,rounding_size=0.8", fc=NAVY if fakt else "#e9eef6", ec="none"))
    ax.text(x + 1.2, y + h - 2, nazwa, fontsize=11, fontweight="bold", color="white" if fakt else NAVY, va="center")
    for i, k in enumerate(kolumny):
        ax.text(x + 1.2, y + h - 6 - i * 3, k, fontsize=9, color=INK, va="center")
    return (x, y, w, h)


D = {
    "D_Kalendarz": tabela(2, 56, "D_Kalendarz", ["Date (klucz)", "Rok, Miesiac", "wspolny_okres"]),
    "D_Miasto": tabela(38, 60, "D_Miasto", ["city (klucz)", "miasto, wojewodztwo", "kod_gus"]),
    "D_Segment": tabela(74, 60, "D_Segment", ["segment (klucz)", "kolejnosc, opis"]),
    "D_Odleglosc": tabela(110, 60, "D_Odleglosc", ["segment_odleglosc (klucz)", "kolejnosc, opis"]),
    "F_Sprzedaz": tabela(20, 8, "F_Sprzedaz", ["city, miesiac", "segment_metraz", "segment_odleglosc", "price, cena_m2", "czy_outlier, ostatnia_oferta"], True),
    "F_Najem": tabela(62, 8, "F_Najem", ["city, miesiac", "segment_metraz", "segment_odleglosc", "price (czynsz), cena_m2", "czy_outlier, ostatnia_oferta"], True),
    "F_GUS_Rok": tabela(104, 14, "F_GUS_Rok", ["city, rok", "wynagrodzenie, ludnosc", "bezrobocie, saldo migracji", "mieszkania_oddane"], True),
}


def polacz(a, b):
    xa, ya, wa, ha = D[a]
    xb, yb, wb, hb = D[b]
    p1 = (xa + wa / 2, ya)
    p2 = (xb + wb / 2, yb + hb)
    ax.annotate("", xy=p2, xytext=p1, arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1, shrinkA=0, shrinkB=0))
    ax.text(p1[0] + 0.5, p1[1] - 2, "1", fontsize=9, color=INK2)
    ax.text(p2[0] + 0.5, p2[1] + 0.8, "*", fontsize=11, color=INK2)


for d in ["D_Kalendarz", "D_Miasto", "D_Segment", "D_Odleglosc"]:
    for f in ["F_Sprzedaz", "F_Najem"]:
        polacz(d, f)
polacz("D_Miasto", "F_GUS_Rok")
ax.text(70, 2, "Schemat gwiazdy: 4 wymiary, 3 tabele faktów, 9 relacji 1:* (filtrowanie pojedyncze, od wymiaru do faktu). "
        "Miary w osobnej tabeli _Miary.", ha="center", fontsize=10, color=INK2)
fig.savefig(os.path.join(WYK, "17_schemat_modelu.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("OK")
