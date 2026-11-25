"""EDA i kontrola KPI dla projektu SAB (etap 2).

Liczy te same wielkości co miary DAX w modelu Power BI (te same definicje,
odsiew outlierów 1.-99. percentyl ceny/czynszu za m2 w mieście), testuje
wstępnie hipotezy H1-H5 z etapu 1 i rysuje wykresy do raportu.

Uruchomienie (z katalogu repozytorium):
    python analiza/eda.py
Wyniki: raport/eda/*.csv, raport/eda/wyniki.json, raport/wykresy/*.png
"""
import csv
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DANE = os.path.join(ROOT, "dane")
OUT = os.path.join(ROOT, "raport", "eda")
WYK = os.path.join(ROOT, "raport", "wykresy")
os.makedirs(OUT, exist_ok=True)
os.makedirs(WYK, exist_ok=True)

WSPOLNY_START = pd.Timestamp("2023-11-01")
SEG_METRAZ = ["<40", "40-60", "60-80", ">80"]
SEG_ODL = ["<2 km", "2-5 km", "5-10 km", ">10 km"]

# ------------------------------------------------------------------ styl wykresów
NAVY = "#184f95"      # kolor główny (granat)
BLUE = "#2a78d6"      # seria 1
ORANGE = "#eb6834"    # seria 2
AQUA = "#1baf7a"      # seria 3
GREY = "#b9b8b2"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
ORD4 = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]  # porządkowa skala 4 segmentów
CRIT = "#d03b3b"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"],
    "font.size": 10,
    "axes.edgecolor": GRID,
    "axes.labelcolor": INK2,
    "axes.titlecolor": INK,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "legend.frameon": False,
    "figure.dpi": 100,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "figure.facecolor": "white",
})


def zapisz(fig, nazwa):
    fig.savefig(os.path.join(WYK, nazwa))
    plt.close(fig)


def pl(x, n=0):
    """Liczba w polskim zapisie (spacja tysięcy, przecinek dziesiętny)."""
    s = f"{x:,.{n}f}".replace(",", " ").replace(".", ",")
    return s


# ------------------------------------------------------------------ wczytanie
def wczytaj(najem):
    czesci = []
    katalog = os.path.join(DANE, "kaggle")
    for f in sorted(os.listdir(katalog)):
        if not f.endswith(".csv") or ("rent" in f) != najem:
            continue
        d = pd.read_csv(os.path.join(katalog, f), dtype={"id": str})
        s = f[-11:-4]
        d["miesiac"] = pd.Timestamp(int(s[:4]), int(s[5:7]), 1)
        czesci.append(d)
    df = pd.concat(czesci, ignore_index=True)
    df["cena_m2"] = df.price / df.squareMeters
    df["segment_metraz"] = pd.cut(df.squareMeters, [0, 40, 60, 80, np.inf], right=False, labels=SEG_METRAZ)
    df["segment_odleglosc"] = pd.cut(df.centreDistance, [0, 2, 5, 10, np.inf], right=False, labels=SEG_ODL)
    df["nowy_budynek"] = np.where(df.buildYear.isna(), np.nan, df.buildYear >= 2020)
    q = df.groupby("city").cena_m2.quantile([0.01, 0.99]).unstack()
    q.columns = ["p01", "p99"]
    df = df.join(q, on="city")
    df["czy_outlier"] = (df.cena_m2 < df.p01) | (df.cena_m2 > df.p99)
    ost = df.groupby("id").miesiac.transform("max")
    df["ostatnia_oferta"] = df.miesiac == ost
    return df.drop(columns=["p01", "p99"])


S = wczytaj(False)
N = wczytaj(True)
Sc = S[~S.czy_outlier]
Nc = N[~N.czy_outlier]

miasta = list(csv.DictReader(open(os.path.join(DANE, "mapowanie", "miasta.csv"), encoding="utf-8-sig"), delimiter=";"))
NAZWA = {m["city"]: m["miasto"] for m in miasta}
KOD = {m["kod_gus"]: m["city"] for m in miasta}


def gus(plik, filtr, idx_rok, idx_wart):
    wynik = {}
    with open(os.path.join(DANE, "gus", plik), encoding="utf-8") as f:
        for r in list(csv.reader(f, delimiter=";"))[1:]:
            if r[0] in KOD and filtr(r):
                wynik[(KOD[r[0]], int(r[idx_rok]))] = float(r[idx_wart].replace(",", "."))
    return wynik


G = {
    "wynagrodzenie": gus("gus_wynagrodzenie.csv", lambda r: r[2] == "ogółem", 3, 4),
    "ludnosc": {k: v * 1000 for k, v in gus("gus_ludnosc.csv", lambda r: r[2] == "ludność w tysiącach", 3, 4).items()},
    "bezrobocie": gus("gus_stopa.csv", lambda r: r[2] == "ogółem", 3, 4),
    "saldo_migracji_na_1000": gus("gus_saldo_migracji.csv", lambda r: r[2] == "saldo migracji ogółem na 1000 ludności" and r[3] == "ogółem", 4, 5),
    "mieszkania_oddane": gus("gus_mieszkanie_oddane.csv", lambda r: r[2] == "ogółem" and r[3] == "mieszkania", 4, 5),
}


def g(w, c, rok=2024):
    return G[w][(c, rok)]


# ------------------------------------------------------------------ KPI


MIN_N = 30  # minimalna liczba wierszy w komórce macierzy (najem i sprzedaż)


def rentownosc(n, s, min_n=1):
    """Jak miara DAX: mediana czynszu m2 * 12 / mediana ceny m2 (sprzedaż od 11.2023)."""
    s = s[s.miesiac >= WSPOLNY_START]
    if len(n) < min_n or len(s) < min_n:
        return np.nan
    return n.cena_m2.median() * 12 / s.cena_m2.median()


wiersze = []
for c in NAZWA:
    s, n = Sc[Sc.city == c], Nc[Nc.city == c]
    p0 = s[s.miesiac == pd.Timestamp("2023-08-01")].cena_m2.median()
    p1 = s[s.miesiac == pd.Timestamp("2024-06-01")].cena_m2.median()
    r0 = n[n.miesiac == pd.Timestamp("2023-11-01")].cena_m2.median()
    r1 = n[n.miesiac == pd.Timestamp("2024-06-01")].cena_m2.median()
    lud = g("ludnosc", c)
    wiersze.append({
        "city": c,
        "miasto": NAZWA[c],
        "ludnosc_2024": lud,
        "oferty_sprzedazy": S[S.city == c].id.nunique(),
        "oferty_najmu": N[N.city == c].id.nunique(),
        "mediana_ceny_m2": s.cena_m2.median(),
        "mediana_czynszu_m2": n.cena_m2.median(),
        "rentownosc_brutto": rentownosc(n, s),
        "czynsz_40_60": n[n.segment_metraz == "40-60"].price.median(),
        "wynagrodzenie_2024": g("wynagrodzenie", c),
        "obciazenie_placy": n[n.segment_metraz == "40-60"].price.median() / g("wynagrodzenie", c),
        "oferty_najmu_na_10_tys": N[N.city == c].id.nunique() / lud * 10000,
        "saldo_migracji_na_1000": g("saldo_migracji_na_1000", c),
        "nowa_podaz_na_1000": g("mieszkania_oddane", c) / lud * 1000,
        "bezrobocie_2024": g("bezrobocie", c),
        "zmiana_ceny_m2": p1 / p0 - 1,
        "zmiana_czynszu_m2": r1 / r0 - 1,
    })
K = pd.DataFrame(wiersze).sort_values("rentownosc_brutto", ascending=False).reset_index(drop=True)
K.to_csv(os.path.join(OUT, "kpi_miasta.csv"), index=False, sep=";", decimal=",", encoding="utf-8-sig")

# całość (wszystkie miasta) - jak karta KPI bez filtrów
calosc = {
    "rentownosc_brutto": rentownosc(Nc, Sc),
    "mediana_ceny_m2": Sc.cena_m2.median(),
    "mediana_czynszu_m2": Nc.cena_m2.median(),
}


def macierz(kolumna, poziomy):
    t = {}
    for c in NAZWA:
        for p in poziomy:
            t[(NAZWA[c], p)] = rentownosc(Nc[(Nc.city == c) & (Nc[kolumna] == p)], Sc[(Sc.city == c) & (Sc[kolumna] == p)], MIN_N)
    m = pd.Series(t).unstack()[poziomy]
    m = m.loc[K.miasto]
    return m


R_SEG = macierz("segment_metraz", SEG_METRAZ)
R_ODL = macierz("segment_odleglosc", SEG_ODL)
R_SEG.to_csv(os.path.join(OUT, "rentownosc_miasto_metraz.csv"), sep=";", decimal=",", encoding="utf-8-sig")
R_ODL.to_csv(os.path.join(OUT, "rentownosc_miasto_odleglosc.csv"), sep=";", decimal=",", encoding="utf-8-sig")

R_NOWE = {}
for c in NAZWA:
    R_NOWE[NAZWA[c]] = {
        "nowe (od 2020)": rentownosc(Nc[(Nc.city == c) & (Nc.buildYear >= 2020)], Sc[(Sc.city == c) & (Sc.buildYear >= 2020)], MIN_N),
        "starsze": rentownosc(Nc[(Nc.city == c) & (Nc.buildYear < 2020)], Sc[(Sc.city == c) & (Sc.buildYear < 2020)], MIN_N),
    }
R_NOWE = pd.DataFrame(R_NOWE).T.loc[K.miasto]
R_NOWE.to_csv(os.path.join(OUT, "rentownosc_nowe_budynki.csv"), sep=";", decimal=",", encoding="utf-8-sig")


def spearman(a, b):
    a, b = pd.Series(a).rank(), pd.Series(b).rank()
    return float(np.corrcoef(a, b)[0, 1])


# premie za cechy: mediana z cechą / bez cechy - 1, w każdym mieście, potem mediana z miast
def premia(df, maska_tak, maska_nie):
    w = []
    for c in NAZWA:
        d = df[df.city == c]
        a, b = d[maska_tak(d)].cena_m2.median(), d[maska_nie(d)].cena_m2.median()
        if pd.notna(a) and pd.notna(b):
            w.append(a / b - 1)
    return float(np.median(w))


CECHY = {
    "balkon": (lambda d: d.hasBalcony == "yes", lambda d: d.hasBalcony == "no"),
    "miejsce parkingowe": (lambda d: d.hasParkingSpace == "yes", lambda d: d.hasParkingSpace == "no"),
    "winda": (lambda d: d.hasElevator == "yes", lambda d: d.hasElevator == "no"),
    "ochrona": (lambda d: d.hasSecurity == "yes", lambda d: d.hasSecurity == "no"),
    "komórka lokatorska": (lambda d: d.hasStorageRoom == "yes", lambda d: d.hasStorageRoom == "no"),
    "stan premium (vs low)": (lambda d: d.condition == "premium", lambda d: d.condition == "low"),
    "uczelnia < 1 km": (lambda d: d.collegeDistance < 1, lambda d: d.collegeDistance >= 1),
}
P = pd.DataFrame({k: {"premia_czynsz": premia(Nc, *v), "premia_cena": premia(Sc, *v)} for k, v in CECHY.items()}).T
P["roznica_pp"] = (P.premia_czynsz - P.premia_cena) * 100
P.to_csv(os.path.join(OUT, "premie_cech.csv"), sep=";", decimal=",", encoding="utf-8-sig")

# ------------------------------------------------------------------ hipotezy
H = {}
duze = ["Warszawa", "Kraków", "Gdańsk"]
male = ["Łódź", "Częstochowa", "Bydgoszcz"]
rk = K.set_index("miasto").rentownosc_brutto
H["H1"] = {
    "rentownosc_male": {m: rk[m] for m in male},
    "rentownosc_duze": {m: rk[m] for m in duze},
    "srednia_male": float(np.mean([rk[m] for m in male])),
    "srednia_duze": float(np.mean([rk[m] for m in duze])),
    "spearman_ludnosc_rentownosc": spearman(K.ludnosc_2024, K.rentownosc_brutto),
    "spearman_cena_rentownosc": spearman(K.mediana_ceny_m2, K.rentownosc_brutto),
}
H["H2"] = {
    "miasta_gdzie_<40_wyzsza_niz_>80": int((R_SEG["<40"] > R_SEG[">80"]).sum()),
    "mediana_<40": float(R_SEG["<40"].median()),
    "mediana_>80": float(R_SEG[">80"].median()),
    "calosc_<40": rentownosc(Nc[Nc.segment_metraz == "<40"], Sc[Sc.segment_metraz == "<40"]),
    "calosc_>80": rentownosc(Nc[Nc.segment_metraz == ">80"], Sc[Sc.segment_metraz == ">80"]),
}
H["H3"] = {
    "spearman_saldo_zmiana_ceny": spearman(K.saldo_migracji_na_1000, K.zmiana_ceny_m2),
    "srednia_zmiana_saldo_dodatnie": float(K[K.saldo_migracji_na_1000 > 0].zmiana_ceny_m2.mean()),
    "srednia_zmiana_saldo_ujemne": float(K[K.saldo_migracji_na_1000 < 0].zmiana_ceny_m2.mean()),
    "miasta_saldo_dodatnie": K[K.saldo_migracji_na_1000 > 0].miasto.tolist(),
    "spearman_nowa_podaz_zmiana_ceny": spearman(K.nowa_podaz_na_1000, K.zmiana_ceny_m2),
}
odl_pelne = R_ODL[["<2 km", "2-5 km", "5-10 km"]].dropna()
H["H4"] = {
    "miasta_gdzie_5-10_wyzsza_niz_<2": int((R_ODL["5-10 km"] > R_ODL["<2 km"]).sum()),
    "miasta_z_danymi": int(R_ODL[["<2 km", "5-10 km"]].dropna().shape[0]),
    "miasta_monotonicznie_rosnaca_<2_2-5_5-10": int(((odl_pelne["2-5 km"] > odl_pelne["<2 km"]) & (odl_pelne["5-10 km"] > odl_pelne["2-5 km"])).sum()),
    "mediana_miast": {k: float(R_ODL[k].median()) for k in SEG_ODL},
}
H["H5"] = {
    "miasta_gdzie_nowe_nizsza": int((R_NOWE["nowe (od 2020)"] < R_NOWE["starsze"]).sum()),
    "miasta_z_danymi": int(R_NOWE.dropna().shape[0]),
    "mediana_nowe": float(R_NOWE["nowe (od 2020)"].median()),
    "mediana_starsze": float(R_NOWE["starsze"].median()),
}
H["P7"] = {"spearman_nasycenie_czynsz": spearman(K.oferty_najmu_na_10_tys, K.mediana_czynszu_m2)}

wyniki = {
    "calosc": calosc,
    "prog_6pct_miasta_powyzej": K[K.rentownosc_brutto >= 0.06].miasto.tolist(),
    "obciazenie_powyzej_30pct": K[K.obciazenie_placy > 0.30].miasto.tolist(),
    "mediana_rentownosci_miast": float(K.rentownosc_brutto.median()),
    "outliery": {"sprzedaz": int(S.czy_outlier.sum()), "najem": int(N.czy_outlier.sum()),
                 "sprzedaz_pct": float(S.czy_outlier.mean()), "najem_pct": float(N.czy_outlier.mean())},
    "wplyw_outlierow": {
        "mediana_ceny_m2_z": float(S.cena_m2.median()), "mediana_ceny_m2_bez": float(Sc.cena_m2.median()),
        "mediana_czynszu_m2_z": float(N.cena_m2.median()), "mediana_czynszu_m2_bez": float(Nc.cena_m2.median()),
        "rentownosc_z": rentownosc(N, S), "rentownosc_bez": rentownosc(Nc, Sc),
    },
    "duplikaty": {"sprzedaz_unikalne_id": int(S.id.nunique()), "najem_unikalne_id": int(N.id.nunique()),
                  "sprzedaz_wiersze": len(S), "najem_wiersze": len(N)},
    "hipotezy": H,
}
with open(os.path.join(OUT, "wyniki.json"), "w", encoding="utf-8") as f:
    json.dump(wyniki, f, ensure_ascii=False, indent=1, default=float)

# ------------------------------------------------------------------ wykresy
# 1. histogram ceny za m2
fig, ax = plt.subplots(figsize=(10, 4.8))
bins = np.arange(3000, 33000, 1000)
ax.hist(Sc.cena_m2, bins=bins, color=BLUE, edgecolor="white", linewidth=1.5)
ax.axvline(Sc.cena_m2.median(), color=INK, lw=1.2, ls="--")
ax.text(Sc.cena_m2.median() + 300, ax.get_ylim()[1] * 0.92, f"mediana {pl(Sc.cena_m2.median())} zł/m²", color=INK, fontsize=9)
ax.set_title("Rozkład ofertowej ceny za m² (sprzedaż, przedziały co 1 000 zł)")
ax.set_xlabel("cena za m², zł")
ax.set_ylabel("liczba wierszy (ofert w miesiącach)")
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: pl(x)))
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: pl(x)))
ax.grid(axis="x", visible=False)
zapisz(fig, "01_histogram_cena_m2.png")

# 2. histogram czynszu za m2
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.hist(Nc.cena_m2, bins=np.arange(10, 195, 5), color=BLUE, edgecolor="white", linewidth=1.5)
ax.axvline(Nc.cena_m2.median(), color=INK, lw=1.2, ls="--")
ax.text(Nc.cena_m2.median() + 2, ax.get_ylim()[1] * 0.92, f"mediana {pl(Nc.cena_m2.median(), 1)} zł/m²", color=INK, fontsize=9)
ax.set_title("Rozkład ofertowego czynszu za m² (najem, przedziały co 5 zł)")
ax.set_xlabel("czynsz miesięczny za m², zł")
ax.set_ylabel("liczba wierszy")
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: pl(x)))
ax.grid(axis="x", visible=False)
zapisz(fig, "02_histogram_czynsz_m2.png")

# 3. boxplot czynszu za m2 wg miast (z outlierami - widać, co odcina reguła 1-99 pct)
kol = N.groupby("city").cena_m2.median().sort_values().index
fig, ax = plt.subplots(figsize=(10, 6))
bp = ax.boxplot([N[N.city == c].cena_m2 for c in kol], vert=False, widths=0.6, patch_artist=True,
                whis=(1, 99), flierprops=dict(marker="o", markersize=2, markerfacecolor=GREY, markeredgecolor="none", alpha=0.6),
                medianprops=dict(color=INK, lw=1.5), boxprops=dict(facecolor="#cde2fb", edgecolor=NAVY),
                whiskerprops=dict(color=NAVY), capprops=dict(color=NAVY))
ax.set_yticks(range(1, len(kol) + 1), [NAZWA[c] for c in kol])
ax.set_title("Czynsz za m² według miast (wąsy = 1. i 99. percentyl, kropki = outliery)")
ax.set_xlabel("czynsz miesięczny za m², zł")
ax.grid(axis="y", visible=False)
zapisz(fig, "03_boxplot_czynsz_m2_miasta.png")

# 4. liczba ofert wg miast (unikalne id)
o = K.sort_values("oferty_sprzedazy")
fig, ax = plt.subplots(figsize=(10, 6))
y = np.arange(len(o))
ax.barh(y + 0.2, o.oferty_sprzedazy, height=0.38, color=BLUE, label="sprzedaż")
ax.barh(y - 0.2, o.oferty_najmu, height=0.38, color=ORANGE, label="najem")
ax.set_yticks(y, o.miasto)
for yy, v in zip(y, o.oferty_sprzedazy):
    ax.text(v + 300, yy + 0.2, pl(v), va="center", fontsize=8, color=INK2)
for yy, v in zip(y, o.oferty_najmu):
    ax.text(v + 300, yy - 0.2, pl(v), va="center", fontsize=8, color=INK2)
ax.set_title("Liczba unikalnych ofert (DISTINCTCOUNT id) według miast")
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: pl(x)))
ax.legend(loc="lower right")
ax.grid(axis="y", visible=False)
zapisz(fig, "04_oferty_miasta.png")

# 5. udział segmentów metrażu (100%) - sprzedaż i najem
fig, axs = plt.subplots(1, 2, figsize=(11, 6), sharey=True)
kol = K.miasto.tolist()[::-1]
for ax, df, tyt in [(axs[0], S, "Sprzedaż"), (axs[1], N, "Najem")]:
    t = pd.crosstab(df.city.map(NAZWA), df.segment_metraz, normalize="index").loc[kol, SEG_METRAZ]
    lewo = np.zeros(len(t))
    for i, sgm in enumerate(SEG_METRAZ):
        ax.barh(range(len(t)), t[sgm], left=lewo, color=ORD4[i], edgecolor="white", linewidth=1, label=sgm + " m²")
        lewo += t[sgm].values
    ax.set_title(tyt)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    ax.grid(False)
axs[0].set_yticks(range(len(kol)), kol)
axs[1].legend(loc="lower center", bbox_to_anchor=(-0.05, -0.14), ncol=4)
fig.suptitle("Udział segmentów metrażu w ofertach (miasta wg rentowności)", x=0.02, ha="left", fontweight="bold", fontsize=12)
zapisz(fig, "05_segmenty_metrazu.png")

# 6. cechy mieszkań: udział "tak"
cechy = [("hasBalcony", "balkon"), ("hasParkingSpace", "parking"), ("hasElevator", "winda"),
         ("hasStorageRoom", "komórka"), ("hasSecurity", "ochrona")]
fig, axs = plt.subplots(1, 2, figsize=(11, 4.5), gridspec_kw={"width_ratios": [3, 2]})
ax = axs[0]
x = np.arange(len(cechy))
vs = [(S[k] == "yes").mean() for k, _ in cechy]
vn = [(N[k] == "yes").mean() for k, _ in cechy]
ax.bar(x - 0.2, vs, 0.38, color=BLUE, label="sprzedaż")
ax.bar(x + 0.2, vn, 0.38, color=ORANGE, label="najem")
for xx, a, b in zip(x, vs, vn):
    ax.text(xx - 0.2, a + 0.01, f"{a:.0%}", ha="center", fontsize=8, color=INK2)
    ax.text(xx + 0.2, b + 0.01, f"{b:.0%}", ha="center", fontsize=8, color=INK2)
ax.set_xticks(x, [n for _, n in cechy])
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
ax.set_title("Udział ofert z daną cechą")
ax.legend()
ax.grid(axis="x", visible=False)
ax = axs[1]
kat = ["premium", "low", "brak danych"]
def stan(df):
    v = df.condition.fillna("brak danych").value_counts(normalize=True)
    return [v.get(k, 0) for k in kat]
x = np.arange(3)
a, b = stan(S), stan(N)
ax.bar(x - 0.2, a, 0.38, color=BLUE, label="sprzedaż")
ax.bar(x + 0.2, b, 0.38, color=ORANGE, label="najem")
for xx, p, q in zip(x, a, b):
    ax.text(xx - 0.2, p + 0.01, f"{p:.0%}", ha="center", fontsize=8, color=INK2)
    ax.text(xx + 0.2, q + 0.01, f"{q:.0%}", ha="center", fontsize=8, color=INK2)
ax.set_xticks(x, kat)
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
ax.set_title("Stan (condition)")
ax.grid(axis="x", visible=False)
zapisz(fig, "06_cechy.png")

# 7. trend cen i czynszów: indeks, małe wielokrotności
mies = sorted(S.miesiac.unique())
fig, axs = plt.subplots(3, 5, figsize=(13, 7.5), sharex=True, sharey=True)
for ax, c in zip(axs.flat, K.city):
    ps = Sc[Sc.city == c].groupby("miesiac").cena_m2.median()
    pn = Nc[Nc.city == c].groupby("miesiac").cena_m2.median()
    ax.plot(ps.index, ps / ps.iloc[0] * 100, color=BLUE, lw=2)
    ax.plot(pn.index, pn / pn.iloc[0] * 100, color=ORANGE, lw=2)
    ax.axhline(100, color=INK2, lw=0.8)
    ax.set_title(NAZWA[c], fontsize=10)
    ax.tick_params(labelsize=8)
    ax.grid(axis="x", visible=False)
axs[0, 0].set_ylim(85, 125)
for ax in axs[-1]:
    ax.set_xticks([pd.Timestamp("2023-08-01"), pd.Timestamp("2024-01-01"), pd.Timestamp("2024-06-01")], ["08.23", "01.24", "06.24"])
fig.legend(handles=[plt.Line2D([], [], color=BLUE, lw=2, label="cena m² (08.2023 = 100)"),
                    plt.Line2D([], [], color=ORANGE, lw=2, label="czynsz m² (11.2023 = 100)")],
           loc="upper right", ncol=2, frameon=False)
fig.suptitle("Trend mediany ceny i czynszu za m², indeks", x=0.02, ha="left", fontweight="bold", fontsize=12)
fig.tight_layout()
zapisz(fig, "07_trend_indeks.png")

# 8. czynsz a odległość od centrum - 3 największe rynki najmu, próbka
fig, ax = plt.subplots(figsize=(10, 5.5))
rng = np.random.default_rng(42)
for c, kolor in [("warszawa", BLUE), ("krakow", ORANGE), ("wroclaw", AQUA)]:
    d = Nc[Nc.city == c]
    prob = d.sample(min(1200, len(d)), random_state=42)
    ax.scatter(prob.centreDistance, prob.cena_m2, s=8, color=kolor, alpha=0.25, edgecolors="none")
    b = d.groupby(pd.cut(d.centreDistance, np.arange(0, 17, 1)), observed=False).cena_m2.median()
    xs = np.arange(0.5, 16.5, 1)[: len(b)]
    ok = b.notna().values & (d.groupby(pd.cut(d.centreDistance, np.arange(0, 17, 1)), observed=False).size().values >= 30)
    ax.plot(xs[ok], b.values[ok], color=kolor, lw=2.5, label=f"{NAZWA[c]} (mediana w pasmach 1 km)")
ax.set_title("Czynsz za m² a odległość od centrum (próbka 1 200 ofert na miasto)")
ax.set_xlabel("odległość od centrum, km")
ax.set_ylabel("czynsz za m², zł")
ax.set_ylim(20, 160)
ax.legend()
zapisz(fig, "08_czynsz_odleglosc.png")


def heatmapa(m, tytul, nazwa, kolumny_opis):
    fig, ax = plt.subplots(figsize=(8, 7))
    v = m.values.astype(float)
    norm = matplotlib.colors.Normalize(vmin=np.nanmin(v), vmax=np.nanmax(v))
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("seq", SEQ)
    ax.imshow(np.ma.masked_invalid(v), cmap=cmap, norm=norm, aspect="auto")
    for i in range(v.shape[0]):
        for j in range(v.shape[1]):
            if np.isnan(v[i, j]):
                ax.text(j, i, "–", ha="center", va="center", color=INK2)
            else:
                ciemne = norm(v[i, j]) > 0.55
                ax.text(j, i, f"{v[i, j] * 100:.1f}%".replace(".", ","), ha="center", va="center", fontsize=9,
                        color="white" if ciemne else INK, fontweight="bold" if v[i, j] >= 0.06 else "normal")
    ax.set_xticks(range(len(m.columns)), kolumny_opis)
    ax.set_yticks(range(len(m.index)), m.index)
    ax.tick_params(length=0)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.xaxis.tick_top()
    ax.set_title(tytul, pad=28)
    zapisz(fig, nazwa)


heatmapa(R_SEG, "Rentowność brutto: miasto × metraż (pogrubione ≥ 6%)", "09_heatmapa_rentownosc_metraz.png",
         ["< 40 m²", "40–60 m²", "60–80 m²", "> 80 m²"])
heatmapa(R_ODL, "Rentowność brutto: miasto × odległość od centrum", "13_heatmapa_rentownosc_odleglosc.png",
         ["< 2 km", "2–5 km", "5–10 km", "> 10 km"])


def punkty(x, y, etykiety, tytul, xl, yl, nazwa, xfmt=None, yfmt=None, linie=(), przesun=None):
    przesun = przesun or {}
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(x, y, s=70, color=BLUE, edgecolors="white", linewidths=1.5, zorder=3)
    for xx, yy, e in zip(x, y, etykiety):
        ax.annotate(e, (xx, yy), xytext=przesun.get(e, (6, 4)), textcoords="offset points", fontsize=9, color=INK)
    for typ, wart, opis in linie:
        if typ == "x":
            ax.axvline(wart, color=CRIT, lw=1.2, ls="--")
            ax.text(wart, ax.get_ylim()[0], " " + opis, color=CRIT, fontsize=9, va="bottom")
        else:
            ax.axhline(wart, color=INK2, lw=1, ls="--")
    ax.set_title(tytul)
    ax.set_xlabel(xl)
    ax.set_ylabel(yl)
    if xfmt:
        ax.xaxis.set_major_formatter(xfmt)
    if yfmt:
        ax.yaxis.set_major_formatter(yfmt)
    zapisz(fig, nazwa)


pct = matplotlib.ticker.PercentFormatter(1, decimals=0)
punkty(K.saldo_migracji_na_1000, K.zmiana_ceny_m2, K.miasto,
       "H3: saldo migracji 2024 a zmiana mediany ceny m² 08.2023→06.2024 (Spearman ρ = " + pl(H['H3']['spearman_saldo_zmiana_ceny'], 2) + ")",
       "saldo migracji na 1000 mieszkańców (2024)", "zmiana ceny za m²", "10_migracje_zmiana_ceny.png", yfmt=pct,
       linie=[("y", 0, "")])

# 11. ranking rentowności z progiem 6%
r = K.sort_values("rentownosc_brutto")
fig, ax = plt.subplots(figsize=(10, 6))
kolory = [NAVY if v >= 0.06 else GREY for v in r.rentownosc_brutto]
ax.barh(r.miasto, r.rentownosc_brutto, color=kolory, height=0.65)
for i, v in enumerate(r.rentownosc_brutto):
    ax.text(v + 0.0007, i, f"{v * 100:.2f}%".replace(".", ","), va="center", fontsize=9, color=INK,
            bbox=dict(facecolor="white", edgecolor="none", pad=1), zorder=4)
ax.axvline(0.06, color=CRIT, lw=1.5, ls="--")
ax.text(0.0603, len(r) - 0.4, "próg 6%", color=CRIT, fontsize=9)
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
ax.set_xlim(0, max(r.rentownosc_brutto) * 1.12)
ax.set_title("Rentowność brutto najmu według miast (11.2023–06.2024)")
ax.legend(handles=[matplotlib.patches.Patch(color=NAVY, label="≥ 6% (powyżej progu)"),
                   matplotlib.patches.Patch(color=GREY, label="< 6%")], loc="lower right")
ax.grid(axis="y", visible=False)
zapisz(fig, "11_ranking_rentownosc.png")

punkty(K.obciazenie_placy, K.nowa_podaz_na_1000, K.miasto,
       "Macierz ryzyka: obciążenie płacy czynszem × nowa podaż", "czynsz mieszkania 40–60 m² / przeciętne wynagrodzenie brutto 2024",
       "mieszkania oddane na 1000 mieszkańców (2024)", "12_ryzyko_obciazenie_podaz.png", xfmt=pct,
       linie=[("x", 0.30, "próg 30%")], przesun={"Łódź": (6, -13), "Gdańsk": (-48, 4)})

# 14. nowe vs starsze budynki (dumbbell)
d = R_NOWE.dropna()
fig, ax = plt.subplots(figsize=(9, 6))
for i, (m, w) in enumerate(d.iterrows()):
    ax.plot([w["starsze"], w["nowe (od 2020)"]], [i, i], color=GREY, lw=2, zorder=1)
ax.scatter(d["starsze"], range(len(d)), s=60, color=BLUE, label="starsze (< 2020)", zorder=2, edgecolors="white")
ax.scatter(d["nowe (od 2020)"], range(len(d)), s=60, color=ORANGE, label="nowe (od 2020)", zorder=2, edgecolors="white")
ax.set_yticks(range(len(d)), d.index)
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
ax.set_title("H5: rentowność brutto – nowe budynki a starsze")
ax.legend(loc="lower right")
ax.grid(axis="y", visible=False)
ax.invert_yaxis()
zapisz(fig, "14_nowe_vs_starsze.png")

print(json.dumps(wyniki, ensure_ascii=False, indent=1, default=float))
print(K.round(4).to_string())
print(R_SEG.round(4).to_string())
print(R_ODL.round(4).to_string())
print(R_NOWE.round(4).to_string())
print(P.round(4).to_string())
