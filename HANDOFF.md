# Figurka D&D: zabandażowany druid, stan projektu

Ten plik przekazuje kontekst do następnej sesji Claude Code.

## Cel
Model 3D do druku: postać z grafik w `concept/` (zabandażowany druid lub łowca w futrzanym płaszczu).

## Ustalenia z użytkownikiem
| Parametr | Wartość |
|---|---|
| Skala | 32 mm heroic. Postać 1,90 m to **36 mm** od stopy do czubka głowy |
| Podstawka | okrągła 25 mm × 3 mm, zintegrowana (rozmiar Medium w D&D) |
| Drukarka | jeszcze nie wiadomo. Główny cel to żywica, FDM tylko pomocniczo |
| Konar | **zwykły gruby konar, jak najmniej szczegółowy**, jak na `concept/konar_referencja.jpg`: prosty, lekko wygięty, 1–2 krótkie odłamane kikuty, bez oczu, grzybów i korony gałązek |
| Poza | konar **po skosie w obu dłoniach**, jak na key arcie. Dolny koniec oparty o podstawkę |
| Repo | docelowo osobne prywatne repo `czaplevsky/dnd-bandaged-druid-mini`, jeszcze nieutworzone (Claude nie ma uprawnień, użytkownik tworzy je sam). Na razie pliki leżą na tej gałęzi w folderze `dnd-mini/` |

## Środowisko
- Sieć: Custom z domenami `huggingface.co`, `*.huggingface.co`, `*.hf.co`, `*.hf.space`. Działa.
- Hugging Face: `HF_TOKEN` jest w zmiennych środowiska (użytkownik dodał go przed nową sesją).
- Brak karty graficznej, 4 rdzenie, 15 GB RAM.
- Blender: `python3 -m venv bvenv && bvenv/bin/pip install bpy==5.0.1 trimesh networkx lxml`. Globalnie zainstalowany numpy 2.x psuje bpy, dlatego potrzebny jest osobny venv.
- `pip install gradio_client`

## Co już jest
- `prepped/`: widoki przód, bok i tył wycięte z arkusza, powiększone 4x Real-ESRGAN, na przezroczystym tle i wyrównane.
- `ai/hunyuan2mv_v1.glb`: pierwszy wynik Hunyuan3D-2mv z trzech widoków.
  - Dobre: sylwetka, pancerz, futro, peleryna.
  - Złe: zdublowana, pokręcona laska (poza laski różni się między widokami), brak bandaży, mesh nieszczelny.
- `scripts/procedural/`: pierwsza wersja w całości proceduralna (bpy). Użytkownik ocenił ją jako „ludzik Lego”, więc ta droga jest porzucona. Pomocniczo nadają się:
  - `render.py`: render clay z 5 kamer (`render.py model.stl outdir res ortho_scale center_z`),
  - `check.py`: szczelność, wymiary, objętość,
  - `finalize.py`: usuwa drobne odpryski, eksportuje STL i 3MF.
- `scripts/gen.py`: wywołanie dem Hunyuan3D przez `gradio_client` (obsługuje `HF_TOKEN`).
- `scripts/conv.py`: GLB (oś Y w górę) na STL (oś Z w górę), przeskalowany.

## Plan dalszej pracy
1. Wygenerować kilka wariantów tylko z widoku z przodu (`view_front_rgba.png`), w którym jest chwyt po skosie:
   - Hunyuan3D-2.1 z `octree_resolution` 512,
   - `microsoft/TRELLIS.2`,
   - ewentualnie `VAST-AI/TripoSG`.
   Porównać rendery i wybrać najlepszy.
2. Opcjonalnie: przed generowaniem podmienić na obrazie wejściowym skomplikowaną laskę na prosty konar (edycja 2D), żeby AI nie tworzyło gałązek.
3. W Blenderze:
   - naprawić mesh (voxel remesh ok. 0,03–0,04 mm),
   - wyciąć laskę z modelu AI i wstawić prosty konar: rura o średnicy ok. 2,5 mm z lekką korą, 1–2 kikuty, przez obie dłonie, dolny koniec na podstawce,
   - dodać bandaże na twarzy i ciele jako płytką rzeźbę paskami (0,15–0,25 mm),
   - skala 36 mm, podstawka 25 × 3 mm,
   - sprawdzić, czy model jest szczelny i nie ma ścian cieńszych niż ok. 0,5 mm.
4. Wynik:
   - STL i 3MF w mm, 3MF poniżej 30 MB, żeby dało się go wysłać w czacie,
   - rendery podglądowe dla użytkownika.

## Stan v2: gotowe do druku (`print/`)
- `print/druid_mini_36mm.3mf` oraz `print/druid_mini_36mm_stl.zip`
  - jednostki mm, szczelna, jednolita bryła, 1,2 mln trójkątów,
  - postać 36 mm, podstawka 25 × 3 mm, wysokość całkowita ok. 39 mm, ok. 3,4 ml żywicy.
- Proces (skrypty w `scripts/final/`, uruchamiane ze scratchpada z venv `bvenv`):
  1. `scripts/kontext.py`: FLUX.1-Kontext podmienia na widoku z przodu laskę na prosty konar. Wynik: `edit/front_plain_bough.png`.
  2. `gen.py h21 edit/front_plain_bough.png`: Hunyuan3D-2.1. Wynik: `ai/hunyuan21_plain_bough.glb`.
  3. `prep.py`: usuwa płytę podłoża, obraca do osi Z w górę, skaluje do 36 mm.
  4. `branch_swap.py`: łata dziury, remesh, wycina konar AI wzdłuż osi zmierzonej promieniami (`depthmap.py`).
  5. `relief.py`: płaskorzeźba bandaży, futra i pasów rzutowana z grafiki (przód z obrazu Kontext, tył z arkusza). Detal głównie wypukły, do tego +0,08 mm naskórka.
  6. `assemble.py`: własny prosty konar przez obie dłonie, podstawka, voxel remesh 0,035 mm, decymacja.
  7. `finalize.py`, `check.py`, `thick.py`: walidacja.
- Limit ZeroGPU na darmowym koncie HF: ok. 3–4 minuty dziennie.
