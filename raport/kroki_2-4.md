# Kroki 2–4: wczytanie danych, profilowanie i model

Projekt Power BI jest zapisany w formacie tekstowym **PBIP**:

```
SAB_projekt.pbip                  ← to otwierasz w Power BI Desktop
SAB_projekt.SemanticModel/        ← model: zapytania M, tabele, relacje, miary (TMDL)
SAB_projekt.Report/               ← strony raportu (na razie jedna pusta)
```

## Jak otworzyć

1. Power BI Desktop → **Plik → Otwórz** → `SAB_projekt.pbip`.
2. Na żółtym pasku kliknij **Zastosuj zmiany** albo wybierz **Odśwież** na wstążce. Wczytanie 19 plików CSV trwa 1–3 min.
3. Jeśli repozytorium leży w innym folderze: **Przekształć dane → Zarządzaj parametrami → `SciezkaDanych`**. Wpisz pełną ścieżkę do folderu `dane\` (z `\` na końcu).
4. Opcjonalnie **Plik → Zapisz jako → .pbix**, jeśli prowadzący chce jeden plik.

Kontrola po odświeżeniu. Te liczby wierszy policzyłem niezależnie w Pythonie i powinny się zgadzać z paskiem stanu Power Query:

| Zapytanie | Wiersze | Kolumny | Ładowane do modelu |
|---|---:|---:|---|
| `F_Sprzedaz` | 195 568 | 36 | tak |
| `F_Najem` | 70 847 | 36 | tak |
| `F_GUS_Rok` | 30 | 8 | tak |
| `D_Miasto` | 15 | 6 | tak |
| `D_Kalendarz` | 11 | 5 | tak |
| `D_Segment` | 4 | 3 | tak |
| `_Miary` | 0 | 1 (ukryta) | tak, tylko miary |
| `GUS_Surowe` | 3 902 (wszystkie jednostki BDL) | 5 | nie (etap pośredni) |
| `SciezkaDanych` | parametr | – | nie |

## Krok 2. Zapytania Power Query

Wszystkie zapytania czytają pliki przez jedno źródło `Folder.Files(SciezkaDanych)`. Dzięki temu Power BI nie pyta o poziomy prywatności przy łączeniu plików.

- **F_Sprzedaz / F_Najem**: pliki z `dane\kaggle\` rozdzielone filtrem nazwy (zawiera / nie zawiera `rent`). `miesiac` pochodzi z nazwy pliku (`…_2023_08.csv` → 2023-08-01). Typy są ustawione z kulturą **en-US** (kropka dziesiętna), więc wynik nie zależy od ustawień regionalnych pliku. Kolumny `has*` zamienione z `yes/no` na `true/false`. Dodane kolumny: `cena_m2`, `segment_metraz`, `segment_odleglosc`, `nowy_budynek` i `ostatnia_oferta`.
- **GUS_Surowe**: 5 eksportów BDL, każdy z własnym filtrem wymiaru. Typy z kulturą **pl-PL** (przecinek dziesiętny).

  | Plik | Wskaźnik | Filtr |
  |---|---|---|
  | `gus_wynagrodzenie.csv` | `wynagrodzenie` | Wyszczególnienie = ogółem |
  | `gus_ludnosc.csv` | `ludnosc` | Wskaźniki = ludność w tysiącach |
  | `gus_stopa.csv` | `bezrobocie` | Ogółem = ogółem (bez „Polska = 100”) |
  | `gus_saldo_migracji.csv` | `saldo_migracji_na_1000` | saldo migracji ogółem na 1000 ludności, płeć ogółem |
  | `gus_mieszkanie_oddane.csv` | `mieszkania_oddane` | formy budownictwa ogółem, mieszkania |

- **F_GUS_Rok**: odfiltrowanie 15 miast (po `kod_gus` z `D_Miasto`), przestawienie (pivot) po `wskaznik`, ludność × 1000 i scalenie z `D_Miasto` (dochodzi `city`).
- **D_Miasto**: `dane\mapowanie\miasta.csv` (separator `;`). Kody zostają tekstem, żeby nie zgubić wiodącego zera (`0264000`).
- **D_Kalendarz**: kalendarz **miesięczny** 2023-08…2024-06 w Power Query, kolumny `Date`, `Rok`, `Miesiac`, `MiesiacNr` i `wspolny_okres`.
- **D_Segment**: 4 segmenty metrażu z kolumną `kolejnosc` (sortowanie).

> Do raportu: zrób screen listy zapytań w Power Query (lewy panel) i paska z liczbą wierszy.

## Krok 3. Profilowanie jakości danych

Liczby policzone na **całym** zbiorze. W Power Query przełącz profilowanie na „cały zestaw danych”, wtedy wynik będzie ten sam.

### Braki danych (% pustych pól)

| Kolumna | F_Sprzedaz | F_Najem |
|---|---:|---:|
| condition | **74,81%** (146 307) | **72,92%** (51 665) |
| buildingMaterial | 39,57% (77 382) | 40,93% (28 997) |
| type | 21,61% (42 261) | 23,66% (16 762) |
| floor | 17,69% (34 594) | 12,16% (8 613) |
| buildYear | 16,47% (32 216) | 27,78% (19 682) |
| hasElevator | 4,96% (9 702) | 5,54% (3 924) |
| collegeDistance | 2,78% (5 436) | 1,23% (874) |
| floorCount | 1,22% | 1,95% |
| pozostałe `*Distance` | < 0,4% | < 0,3% |
| id, city, price, squareMeters, rooms, centreDistance, pozostałe has* | 0% | 0% |

### Zakresy wartości

| Miara | F_Sprzedaz | F_Najem |
|---|---|---|
| `city`: unikalne wartości | **15** | **15** |
| `price`: min / max / średnia / mediana | 150 000 / 3 250 000 / 784 183 / 699 000 zł | 346 / 23 000 / 3 853 / 3 100 zł |
| `squareMeters`: min / max / średnia / mediana | 25 / 150 / 58,7 / 54,6 m² | 25 / 150 / 55,3 / 50,0 m² |
| `cena_m2`: min / max / mediana | 3 000 / 32 097 / 12 979 zł/m² | 11,3 / 189,5 / 66,0 zł/m² |
| `centreDistance` max | 16,94 km | 16,62 km |
| `buildYear` | 1850–2024 | 1850–2024 |
| `rooms` | 1–6 | 1–6 |

- Metraż jest już przefiltrowany przez autora zbioru do **25–150 m²**: nie ma ani jednej wartości poza tym zakresem.
- Kolumny `has*` w źródle to **tekst `yes`/`no`**, nie wartości logiczne. W Power Query zamienione na true/false. W `hasElevator` puste pole zamienia się w `null`.
- `condition` ma tylko wartości `premium`/`low`. W najmie `low` występuje tylko 262 razy, więc pytanie o standard da się analizować jedynie z zastrzeżeniem.
- `ownership`: w sprzedaży 12 ofert ma wartość `udział`, w najmie wszystkie oferty mają `condominium`.

### Duplikaty

| | F_Sprzedaz | F_Najem |
|---|---:|---:|
| Wiersze | 195 568 | 70 847 |
| Unikalne `id` | **92 967** | **37 941** |
| `id` występujące w > 1 miesiącu | **45 347** | **16 994** |
| Wiersze nadmiarowe (powtórzenia) | 102 601 (52%) | 32 906 (46%) |
| Maksymalna liczba wystąpień `id` | 11 (wszystkie miesiące) | 8 (wszystkie miesiące) |
| Pary (`id`, `miesiac`) zdublowane | 0 | 0 |
| `id` w więcej niż jednym mieście | 0 | 0 |

**Decyzja:** mediany miesięczne liczymy na wszystkich wierszach, bo w danym miesiącu oferta występuje raz. Do analizy całego okresu bierzemy każde `id` raz, z ostatniego miesiąca. Zamiast osobnej tabeli (sortowanie + `Table.Buffer` + usunięcie duplikatów) dodałem w obu faktach kolumnę **`ostatnia_oferta`** (true dla ostatniego miesiąca danego `id`). Wystarczy filtr `ostatnia_oferta = true` na wizualizacji lub w `CALCULATE`. Dla 15 miast da to 92 967 ofert sprzedaży i 37 941 ofert najmu. Liczbę ofert liczymy zawsze przez `DISTINCTCOUNT(id)`.

### Outliery (podgląd przed krokiem 6)

Poza przedziałem od 1. do 99. percentyla ceny / czynszu za m² w danym mieście leży **3 872** wierszy sprzedaży (2,0%) i **1 286** wierszy najmu (1,8%).

### Słownik danych

| Tabela | Kolumna | Typ | Znaczenie | Źródło | Uwagi |
|---|---|---|---|---|---|
| F_Sprzedaz, F_Najem | id | tekst | identyfikator oferty | Kaggle | powtarza się między miesiącami; liczyć przez DISTINCTCOUNT |
| F_Sprzedaz, F_Najem | city | tekst | miasto (małe litery, bez polskich znaków) | Kaggle | klucz do D_Miasto |
| F_Sprzedaz | price | liczba dziesiętna | cena ofertowa, zł | Kaggle | wartość ofertowa, nie transakcyjna |
| F_Najem | price | liczba dziesiętna | miesięczny czynsz ofertowy, zł | Kaggle | bez opłat do spółdzielni; wartość ofertowa |
| F_Sprzedaz, F_Najem | squareMeters | liczba dziesiętna | metraż, m² | Kaggle | przefiltrowany przez autora do 25–150 |
| F_Sprzedaz, F_Najem | rooms | liczba całkowita | liczba pokoi | Kaggle | 1–6 |
| F_Sprzedaz, F_Najem | buildYear | liczba całkowita | rok budowy | Kaggle | braki 16% / 28% |
| F_Sprzedaz, F_Najem | centreDistance | liczba dziesiętna | odległość od centrum, km | Kaggle | podstawa segment_odleglosc |
| F_Sprzedaz, F_Najem | collegeDistance | liczba dziesiętna | odległość do najbliższej uczelni, km | Kaggle | braki 2,8% / 1,2% |
| F_Sprzedaz, F_Najem | condition | tekst | standard: premium / low | Kaggle | braki ~73–75%; tylko z zastrzeżeniem |
| F_Sprzedaz, F_Najem | hasBalcony, hasParkingSpace, hasElevator | logiczny | czy jest balkon / miejsce parkingowe / winda | Kaggle | w źródle tekst yes/no; hasElevator ma ~5% braków |
| F_Sprzedaz, F_Najem | miesiac | data | miesiąc publikacji (1. dzień miesiąca) | nazwa pliku | klucz do D_Kalendarz |
| F_Sprzedaz, F_Najem | cena_m2 | liczba dziesiętna | price / squareMeters | wyliczona | w F_Najem: czynsz za m² |
| F_Sprzedaz, F_Najem | segment_metraz | tekst | <40, 40-60, 60-80, >80 m² | wyliczona | klucz do D_Segment; przedziały lewostronnie domknięte |
| F_Sprzedaz, F_Najem | segment_odleglosc | tekst | <2 km, 2-5 km, 5-10 km, >10 km | wyliczona | z centreDistance |
| F_Sprzedaz, F_Najem | nowy_budynek | logiczny | buildYear ≥ 2020 | wyliczona | null, gdy brak buildYear |
| F_Sprzedaz, F_Najem | ostatnia_oferta | logiczny | wiersz z ostatniego miesiąca danego id | wyliczona | deduplikacja do analiz całego okresu |
| F_GUS_Rok | kod | tekst | kod jednostki BDL (7 cyfr) | GUS BDL | = D_Miasto[kod_gus] |
| F_GUS_Rok | city | tekst | miasto | D_Miasto | dołączone przez scalenie po kodzie |
| F_GUS_Rok | rok | liczba całkowita | rok danych | GUS BDL | 2023, 2024 |
| F_GUS_Rok | wynagrodzenie | liczba dziesiętna | przeciętne miesięczne wynagrodzenie brutto, zł | GUS BDL | dane roczne |
| F_GUS_Rok | ludnosc | liczba całkowita | ludność ogółem, osoby | GUS BDL | w BDL w tys., przeliczone × 1000 |
| F_GUS_Rok | bezrobocie | liczba dziesiętna | stopa bezrobocia rejestrowanego, % | GUS BDL | stan na koniec roku |
| F_GUS_Rok | saldo_migracji_na_1000 | liczba dziesiętna | saldo migracji ogółem na 1000 ludności | GUS BDL | już znormalizowane przez GUS |
| F_GUS_Rok | mieszkania_oddane | liczba całkowita | mieszkania oddane do użytkowania, ogółem | GUS BDL | tylko rocznie, bez podziału „na wynajem” |
| D_Miasto | city / miasto | tekst | klucz Kaggle / nazwa wyświetlana | ręcznie | city: klucz relacji |
| D_Miasto | nazwa_gus, kod_gus | tekst | nazwa i kod jednostki w BDL | BDL | zgodne znak w znak z eksportami |
| D_Miasto | teryt_powiat, wojewodztwo | tekst | kod TERYT powiatu, województwo | ręcznie | do filtra województwa i mapy |
| D_Kalendarz | Date, Rok, Miesiac | data / liczba / tekst | miesiąc kalendarzowy | wyliczona | 11 miesięcy 2023-08…2024-06 |
| D_Kalendarz | wspolny_okres | logiczny | miesiąc, w którym są dane sprzedaży i najmu | wyliczona | od 2023-11 |
| D_Segment | segment, kolejnosc, opis | tekst / liczba / tekst | segment metrażu | ręcznie | 4 wiersze |

### Reguły jakości danych (Data Quality Rules)

| # | Reguła | Wynik |
|---|---|---|
| 1 | `city` należy do 15 miast z D_Miasto (każda oferta ma dopasowanie) | spełniona (15/15 w obu faktach) |
| 2 | `price > 0` i `squareMeters` w przedziale 25–150 | spełniona (0 naruszeń) |
| 3 | `cena_m2` mieści się między 1. a 99. percentylem w danym mieście; poza zakresem = outlier | 3 872 (sprzedaż) i 1 286 (najem) do oznaczenia w kroku 6 |
| 4 | Para (`id`, `miesiac`) jest unikalna | spełniona (0 duplikatów) |
| 5 | Liczba wierszy ofert przed i po scaleniu z D_Miasto jest taka sama | spełniona (relacja *:1, brak zgubionych wierszy) |
| 6 | Każda para miasto–rok w GUS ma komplet wartości: 15 × 2 = 30 wierszy, brak `null` w `city` | spełniona (30 wierszy, 5 wskaźników) |
| 7 | `buildYear` między 1850 a 2024 | spełniona (0 naruszeń) |
| 8 | Każde `id` należy do jednego miasta | spełniona |

## Krok 4. Model danych

Relacje (wszystkie typu wiele-do-jednego, filtrowanie pojedyncze od wymiaru do faktu):

| Z (wiele) | Do (jeden) |
|---|---|
| F_Sprzedaz[city], F_Najem[city], F_GUS_Rok[city] | D_Miasto[city] |
| F_Sprzedaz[miesiac], F_Najem[miesiac] | D_Kalendarz[Date] |
| F_Sprzedaz[segment_metraz], F_Najem[segment_metraz] | D_Segment[segment] |

Miary w tabeli `_Miary`, w folderach:

- **Ceny**: Mediana ceny m2, Mediana czynszu m2.
- **KPI**: Rentownosc brutto, Obciazenie placy, Oferty najmu na 10 tys, Saldo migracji na 1000, Nowa podaz na 1000, Zmiana ceny m2 %.
- **Liczebności**: liczba ofert (DISTINCTCOUNT id) i liczba wierszy, osobno dla sprzedaży i najmu.
- **GUS**: Wynagrodzenie 2024, Bezrobocie 2024.

Automatyczne tabele dat są wyłączone, bo model ma własny kalendarz.

> Do raportu: screen widoku **Model**, który jest diagramem relacji.

## Zmiany względem instrukcji i etapu 1 (do sekcji „Zmiany” w raporcie)

1. **Saldo migracji**: BDL podaje je już „na 1000 ludności”. Miara `Saldo migracji na 1000` nie dzieli więc przez ludność. Dla kilku miast liczy średnią ważoną ludnością.
2. **Ludność**: eksport BDL jest w tysiącach osób, w Power Query przeliczona na osoby (× 1000).
3. **Mieszkania oddane**: tylko „ogółem” i tylko rocznie, bez podziału „na wynajem” i bez wersji miesięcznej.
4. **Format GUS**: eksporty BDL są już w formacie długim (kolumna `Rok`), więc krok „anuluj przestawienie” nie był potrzebny. Każdy plik wymagał natomiast własnego filtra wymiaru, bo pliki zawierały kilka wskaźników naraz (np. gęstość zaludnienia, „Polska = 100”).
5. **D_Kalendarz**: miesięczny (11 wierszy) i zbudowany w Power Query zamiast dziennego `CALENDAR` w DAX. Oferty mają datę = 1. dzień miesiąca, więc dzienny kalendarz miałby ~300 pustych dni.
6. **Deduplikacja**: kolumna `ostatnia_oferta` zamiast osobnej, zdeduplikowanej kopii tabeli. Efekt ten sam, model mniejszy.
7. **Rentowność**: liczona na wspólnym okresie 11.2023–06.2024 (filtr w mierze), bo najem zaczyna się od 11.2023.
8. **Przygotowanie danych w Power Query** zamiast w Pythonie. Python posłużył tylko do niezależnej kontroli liczb z profilowania.
