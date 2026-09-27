# D&D minis: pamięć projektu (czytaj na starcie każdej sesji)

Repo na figurki D&D do druku żywicznego, robione z concept artu. Każda postać ma folder `models/<nazwa>/`. Wspólne skrypty są w `pipeline/`. Pełne wnioski: `LESSONS.md`. Użytkownik pisze po polsku, często z telefonu; chce wyników, nie wymówek.

## Standard figurki
- Skala 32 mm heroic: postać 1,90 m ma **36 mm od podeszwy do czubka głowy**.
- Podstawka okrągła **25 × 3 mm** (Medium), zintegrowana, top na z = 3. Wszystko mieści się w promieniu 12,5 mm.
- Druk żywiczny, więc:
  - ścianki ≥ 0,4 mm (cel 0,6),
  - rekwizyty ≥ 2 mm,
  - detal (rowki, paski) **≥ 0,15 mm**, bo płytszy znika.
- Eksport: jedna szczelna bryła; 3MF < 30 MB (limit wysyłki w czacie) + STL w zip.

## Pierwsze 5 minut sesji (zanim cokolwiek zbudujesz)
1. Sieć: `curl -s -o /dev/null -w '%{http_code}' https://huggingface.co/api/spaces/microsoft/TRELLIS.2`. Blokadę zgłoś raz, z dokładnymi krokami:
   - otwórz claude.ai/code w przeglądarce (w apce mobilnej tego nie ma),
   - kliknij ikonę chmurki, potem zębatkę,
   - Network access → Custom,
   - wpisz `huggingface.co`, `*.huggingface.co`, `*.hf.co`, `*.hf.space`,
   - zaznacz „include default list”.
2. `HF_TOKEN` w env (zmiana wymaga NOWEJ sesji). Darmowy ZeroGPU to ok. 3,5–5 min dziennie; HF PRO (9 $) daje 40 min.
3. Dysk (`df -h`, potrzeba ≥ 15 GB), RAM 15 GB, brak GPU.
4. Uprawnienia GitHub: integracja NIE tworzy repozytoriów (403), więc repo zakłada użytkownik.
5. Zadaj tylko pytania zmieniające plan: poza, rekwizyt, co uprościć lub przesadzić, drukarka.

## Twarde zasady
- **Nigdy** zastępczej figurki z prymitywów, gdy narzędzie jest zablokowane (v1 = „ludzik Lego”). **Nigdy** nie mieszaj prymitywów z meshem AI (v2: konar-rura).
- **Najpierw research, potem builder**, nigdy równolegle. Builder dostaje gotową instrukcję (szablon w `LESSONS.md`).
- Limit GPU tylko na edycje 2D (FLUX Kontext). Bryły liczy **CPU** (Hunyuan3D-2 mini/mv turbo, 4–9 min).
- Przed wywołaniem Space'a:
  - sprawdź `view_api`, limity parametrów i `duration`,
  - najpierw zapisz surowy wynik, potem go parsuj,
  - każde wywołanie zapisz w logu.
- Pozycje (oczy, oś rekwizytu, grubości) mierz na meshu (promienie, mapy głębokości), nie na obrazie.
- Każda próba to wiersz w `models/<nazwa>/LOG.md` (#, co, koszt, werdykt). Dzięki temu po przerwaniu (limit sesji 429) da się wznowić pracę.
- Pliki robocze trzymaj w scratchpadzie. Do repo trafiają tylko finalne pliki, rendery, logi i skrypty. Nie twórz plików w katalogu głównym repo.

## Pipeline (szczegóły: `pipeline/PIPELINE.md`, `LESSONS.md` §4)
1. `concept/`: wytnij widoki, upscale, szare tło.
2. Kontext: edycja frontu, która upraszcza rekwizyt i przesadza detal („sculpted tabletop miniature”); potem widok z TYŁU (boki pogarszały wynik). ~30–40 s GPU na wywołanie.
3. `hy_cpu.py`:
   - mini 512 z frontu (ostry przód),
   - mv front+back (tył),
   - `hybrid.py` scala oba.
4. Detal i porządki:
   - `normals.py`: normalne Marigold na CPU,
   - `detail.py`: rowki bandaży, pasy na głowie, kosmyki futra, fałdy; strefy w `maps.py` są **ręcznie wpisane dla druida, przepisz je dla nowej postaci**,
   - `depeg.py`: usuwa cienkie wypustki,
   - `notch.py`: poszarpany brzeg.
5. `finalize.py`: podstawka, remesh 0,032 mm, decymacja, zapis 3MF z 6 miejscami po przecinku.
6. Walidacja (definition of done):
   - jedna szczelna bryła,
   - 36,0 ± 0,1 mm od podeszwy do głowy,
   - mieści się w obrysie podstawki,
   - `thick3.py` < 1 % pod 0,4 mm,
   - **ponowne wczytanie 3MF**,
   - rendery `render.py` (pełne, zbliżenie, głowa) zestawione obok poprzedniej wersji.

Środowisko: venv `bvenv` (bpy 5.0.1 + trimesh, osobny venv, bo globalny numpy 2 psuje bpy), `hyvenv` z repo Hunyuan3D-2 i wagami turbo. Opis instalacji: `pipeline/RESEARCH_PLAN.md`. Skrypty zakładają ścieżki scratchpada, więc przed użyciem sprawdź zmienne na górze pliku.

## Oszczędzanie tokenów
- Jedna zmiana na iterację.
- Jeden contact sheet ≤ 1400 px zamiast wielu obrazów.
- Bez narracji.
- Stop po 3 próbach bez poprawy, wtedy zmień podejście.
- Duże pliki czytaj fragmentami.

## Postacie
| Folder | Status | Finalny plik |
|---|---|---|
| `models/bandaged-druid/` | v5 gotowa („wygląda całkiem nieźle”) | `print/druid_mini_v5.3mf` |
