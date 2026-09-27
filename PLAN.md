# Plan: z grafiki 2D do żywicznej figurki 36 mm (research 2026-09-25)

Wszystko poniżej sprawdzone z tego kontenera (4 CPU, 15 GB RAM, brak GPU), chyba że napisano „niesprawdzone”.
Pliki testowe: `scratchpad/research/` (skrypty `cpu_*.py`, porównanie `compare_cpu.png`, normalne `normals_crop.png`, `height_hp_crop.png`).

## 0. Najważniejsze wnioski
1. **Hunyuan3D-2 da się uruchomić lokalnie na CPU i nie zużywa to limitu ZeroGPU.** Zmierzone czasy:
   - `Hunyuan3D-2mini-Turbo` z jednego obrazu, octree 512, 5 kroków: **247 s**, 1,26 mln trójkątów.
   - `Hunyuan3D-2mv-Turbo` z 3 widoków (przód, tył, lewy bok), octree 512: **442 s** (ok. 7,5 min).
   - Jakość jest porównywalna z Hunyuan3D-2.1 ze Space'a albo lepsza (`compare_cpu.png`). MV z arkusza dał wyraźnie więcej detalu z tyłu (futro, peleryna), ale laska wyszła rozmyta, bo jej poza różni się w każdym widoku.
   - Wniosek: tył przestaje być „zgadywany”, gdy podamy **spójne** widoki. Limit GPU jest potrzebny tylko do edycji 2D.
2. **Konar nie powinien być proceduralny.** Konar wygenerowany razem z postacią z obrazu Kontext (`edit/kontext_s7.png`) wychodzi w tym samym stylu i rozdzielczości co ciało, a dłonie go obejmują (widać to w wyniku CPU mini). Proceduralną rurę z v2 należy porzucić.
3. **Bandaże 0,1 mm z luminancji nie mają szans.** Po voxel remeshu 0,035 mm i zagruntowaniu takie wypukłości znikają. Co działa lepiej, od najlepszego:
   - (a) przesadzić bandaże już na obrazie wejściowym, bo miniatury rzeźbi się z przesadą ×1,5–2,
   - (b) wyrzeźbić **rowki 0,15–0,25 mm** na szwach pasów, bo ostre krawędzie czytają się po druku i washu,
   - (c) użyć mapy wysokości z **normalnych AI** (Marigold-e2e, CPU, 58 s przy 1248 px) zamiast z luminancji,
   - (d) głowę owinąć paskami-wstążkami w Blenderze (shrinkwrap + solidify 0,2 mm).
4. **Z kontenera nie ma dostępu do żadnych zewnętrznych API 3D.** Nie łączą się: meshy, tripo3d, fal.run, replicate, stability, api-inference, download.pytorch.org, modelscope, civitai, hitem3d, zmkj (backend Direct3D-S2), gradio.live. Działają: huggingface.co, *.hf.space, router.huggingface.co, pypi, github, generativelanguage.googleapis.com (tylko odpowiada 404, nieużywane).
5. Spaces „bez ZeroGPU” (`ilcve21/Sparc3D`, `wushuang98/Direct3D-S2-v1.0-demo`, `TencentARC/Pixal3D-Server`) to tylko **iframe'y** do zewnętrznych serwerów. Z kontenera są nieosiągalne, ale **użytkownik może ich użyć ręcznie w przeglądarce** (bez limitu HF). Żaden działający Space 3D nie ma własnego, dedykowanego GPU. Wszystkie korzystają z ZeroGPU.

## 1. Rekomendowany pipeline (darmowy, ok. 45–70 s GPU dziennie + ok. 20 min CPU)

| # | Krok | Gdzie | Wywołanie | Koszt |
|---|---|---|---|---|
| 1 | Front: podmiana laski na konar i **przesadzone bandaże** | ZeroGPU | `black-forest-labs/FLUX.1-Kontext-Dev` `/infer` (już działa, `scripts/kontext.py`), prompt dopisać: *"bandage strips thick and clearly layered with deep gaps between strips, like a sculpted tabletop miniature"*. Alternatywa: `linoyts/Qwen-Image-Edit-2511-Fast` `/infer(images=[front, konar_referencja.jpg], prompt, seed, randomize_seed=False, true_guidance_scale=1, num_inference_steps=4, height=1248, width=832, rewrite_prompt=False)`. Qwen przyjmuje **drugi obraz jako referencję konaru** (niesprawdzone, bo nie było limitu) | Kontext ok. 30–38 s. Qwen-Fast: `@spaces.GPU()` 60 s max, realnie ok. 10–20 s |
| 2 | Spójne widoki tył / lewy / prawy z edytowanego frontu | ZeroGPU | `multimodalart/qwen-image-multiple-angles-3d-camera` `/infer_camera_edit(image, azimuth=180 / 90 / 270, elevation=0, distance=1.0, seed=S, randomize_seed=False, guidance_scale=1.0, num_inference_steps=4, height=1248, width=832)`. To Qwen-Image-Edit-2511 z LoRA multiple-angles, a prompt to `<sks> back view eye-level shot medium shot` | 3 × ok. 10–15 s (niesprawdzone). Po każdym widoku kontrola: konar w tej samej pozie? |
| 3 | Wycięcie tła | CPU | `rembg` / BiRefNet lokalnie. `hy3dgen.rembg` jest już w repo Hunyuan | 0 |
| 4 | **Bryła MV** | **CPU** | `scratchpad/research/cpu_hy2mv.py` (Hunyuan3D-2mv-Turbo, `enable_flashvdm`, octree 512, 5 kroków, fp32, **DiT zwalniany przed dekodowaniem**, bez tego jest OOM). Widoki podaje się jako dict `{'front','back','left','right'}` | **7,5 min, 0 limitu**. Wariant jakościowy: `hunyuan3d-dit-v2-mv-fast` z 20–30 krokami, ok. 20–30 min CPU (niesprawdzone). Waga 4,9 GB (fp16), dysk ma tylko ok. 11 GB wolne |
| 4b | (opcja) bryła jednowidokowa do porównania | ZeroGPU | `microsoft/TRELLIS.2`: `/start_session`, `/preprocess_image`, `/image_to_3d(resolution='1024')`, `/extract_glb(decimation_target=500000)`. 1536 ma najwyższą rozdzielczość voxeli (ok. 0,023 mm przy 36 mm), ale obie funkcje mają `duration=120`: 1536 może nie zmieścić się w 120 s, a darmowy limit starcza na ok. 1 próbę dziennie | ok. 60–120 s GPU |
| 5 | Normalne AI z frontu i tyłu (1248 px lub po upscale ×2) | **CPU** | `cpu_normals.py`: `GonzaloMartinGarcia/marigold-e2e-ft-normals`, 1 krok, `processing_resolution=1248`. Całkowanie Frankot-Chellappa i high-pass (sigma ok. 6 px), jak w teście | 58 s / widok, 5,2 GB wag |
| 6 | Detal w Blenderze (nowy `detail.py`) | CPU | 1) remesh 0,02–0,025 mm; 2) rzut mapy wysokości z kamery ortho front/back, **maska**: tylko jasne obszary bandaży, erozja 8 px od sylwetki (inaczej halo na krawędziach), amplituda 0,15–0,25 mm; 3) **rowki** na szwach bandaży: linie z high-passu albo Canny na mapie normalnych, szerokość ok. 0,12 mm, głębokość 0,15–0,2 mm, profil V; 4) głowa: 8–12 wstążek (krzywa na powierzchni, shrinkwrap, solidify 0,2 mm, bevel krawędzi) | kilka minut |
| 7 | Konar | CPU | **Zostawić konar z AI.** Tylko wygładzić lub wyprostować (smooth w masce wzdłuż osi) i dociągnąć dolny koniec do podstawki. Jeśli jest zły: wygenerować **sam konar** z `concept/konar_referencja.jpg` przez CPU mini-turbo (4 min, ten sam styl i rozdzielczość), dopasować w dłonie i zrobić union | 0–4 min |
| 8 | Podstawka, szczelność, grubości, eksport | CPU | istniejące: `assemble.py` (bez rury), `finalize.py`, `check.py`, `thick.py`. Decymacja do 1,5–2 mln trójkątów (3MF < 30 MB) | ok. 5 min |

Razem: ok. 45–70 s GPU (kroki 1 i 2) zamiast 3–4 min. Resztę dnia można poświęcić na 2–3 seedy kroku 2.

## 2. Fallbacki
- Qwen multi-angles daje niespójny tył: użyć Kontext z promptem *"same character, same pose, viewed from directly behind, orthographic, plain grey background"* (ok. 35 s na widok). Można też podać do 2mv tylko front + tył, bez boków.
- 2mv na CPU z wygenerowanymi widokami wygląda gorzej niż jednowidokowy: CPU `cpu_hy2mini.py 512` (4 min) z frontu i porównać.
- Potrzeba ostrzejszego detalu niż Hunyuan: TRELLIS.2 1024/1536 (Space) albo `Stable-X/Hi3DGen` `/generate_3d(image, seed, ss_guidance_strength=3, ss_sampling_steps=50, slat_guidance_strength=3, slat_sampling_steps=6)` (60 s max, zwraca też obraz `normal_bridge`). Hi3DGen jest właśnie od geometrii z normalnych. `Stable-X/ReconViaGen` `/generate_and_extract_glb(multiimages=[...])` to multiview oparty na TRELLIS (120 s).
- Space'y Hunyuan (bryła): 2mv `/shape_generation` ma `duration=40`, 2.1 ma 60, 2mini-Turbo ma 60, TripoSG `/image_to_3d` 120–180. Nie działają lub są wstrzymane: Step1X-3D (PAUSED), UltraShape, TripoSF, Direct3D-S2 ZeroGPU (CONFIG_ERROR). Nie ma Space'ów z Hunyuan 2.5 ani 3.x.
- Zapasowe normalne na GPU: `prs-eth/marigold-normals` (ZeroGPU). Lokalnie są też `jingheya/lotus-normal-g-v1-1` i `Stable-X/yoso-normal-v1-8-1` (niesprawdzone na CPU).

## 3. Ekonomia limitów (z dokumentacji HF, stan na 2026-09)
- ZeroGPU = połowa RTX Pro 6000 Blackwell (48 GB). Dzienny limit wg docs:
  - niezalogowany: 2 min,
  - **darmowe konto: 5 min** (w praktyce obserwowaliśmy ok. 3,5 min),
  - **PRO: 40 min**, a ponad limit płatne kredytami **$1 za 10 min**.
  - Limit odnawia się 24 h po pierwszym użyciu. Rozmiar `xlarge` liczy się ×2.
- Czas „requested” ustawia autor Space'a (`@spaces.GPU(duration=…)`). Zużywany jest czas faktyczny, ale prawdopodobnie **musi zostać tyle limitu, ile wynosi requested**, żeby wywołanie ruszyło. Błąd Qwen-2509 („600 s > maximum”) wynikał z 600 s ustawionych w Space. Hi3DGen ma 600 s tylko w funkcji startowej, a samo `generate_3d` ma 60 s, więc zadziała.
- **Własna kopia Space'a** (Duplicate): darmowe konto może hostować 2 Space'y ZeroGPU (konto starsze niż 30 dni). Zużycie idzie z własnego limitu, ale można skrócić `duration` i np. oddawać surowy mesh TRELLIS.2 bez decymacji. Wymaga tokena z uprawnieniem zapisu (obecny ma tylko `repo.content.read`).
- **Inference Providers** (router.huggingface.co): obecny token dostaje 403, bo brakuje uprawnienia „Make calls to Inference Providers”. Nowy token by wystarczył. Przez fal-ai / wavespeed dostępne są Qwen-Image-Edit-2511 (także LoRA Multiple-Angles) i FLUX-Kontext. Nie ma ani jednego modelu image-to-3D. Kredyty: darmowe konto $0,10/mies. (ok. 2–3 obrazy), PRO $2/mies. plus pay-as-you-go.
- **HF Jobs**: płatne GPU na minuty, każdy z dodatnim saldem kredytów. Ceny: L4 $0,80/h, L40S $1,80/h, A100 $2,50/h. Można w nich uruchomić TRELLIS.2 1536 bez decymacji albo Hunyuan 2.1 za kilka centów za przebieg, ale trzeba zbudować środowisko CUDA (duży jednorazowy wysiłek, niesprawdzone).
- Uwaga: API Hub ma limit **1000 zapytań / 5 min na konto**. Masowe `/runtime` (ten research) raz go przekroczyło, więc zapytania trzeba robić oszczędnie, bo token współdzieli inny agent.

## 4. Co warto kupić lub włączyć (koszt i korzyść)
1. **HF PRO, $9/mies.: najlepszy stosunek ceny do efektu.** Daje 8× limit (40 min dziennie) i najwyższy priorytet w kolejkach. Starcza na TRELLIS.2 1536 + Hi3DGen + kilka seedów MV każdego dnia, a do tego $2 kredytów na Providers lub Jobs. Iteracje przestają być reglamentowane.
2. Token z uprawnieniem **Inference Providers**: darmowy. Edycje 2D bez ZeroGPU, ale darmowe kredyty wystarczą na ok. 3 obrazy.
3. Ręcznie w przeglądarce użytkownika (kontener tych stron nie widzi): Hitem3D/Sparc3D (Space `ilcve21/Sparc3D`), Direct3D-S2, Hunyuan3D 3.x (web Tencenta), Tripo, Meshy. Najwięcej drobnego detalu dają dziś te komercyjne, zwykle z darmowymi kredytami na start, a potem ok. $10–20/mies. (ceny do sprawdzenia). Wystarczy wrzucić tam przygotowane widoki i oddać GLB do `ai/`, a dalej działa ten sam pipeline Blendera.
4. Własne GPU lub HF Jobs mają sens dopiero przy wielu postaciach.

## 5. Checklista dla kolejnej postaci
1. `concept/`: front (i jeśli jest, arkusz). Wyciąć, upscale ×2–4, tło szare.
2. Edycja frontu (1 wywołanie): uprościć rekwizyty, **przesadzić detale** (bandaże, pasy, grube krawędzie). Kontrola wzrokowa.
3. `views.py`: tył, lewy i prawy z Qwen multi-angles, stały seed. Kontrola spójności na contact sheecie.
4. `hy_cpu.py mv 512` (7,5 min). Opcjonalnie `hy_cpu.py mini 512` z samego frontu. Render porównawczy (`render.py`).
5. `normals.py` front i tył (CPU, 1 min na widok), potem `detail.py` (wysokość z normalnych w masce + rowki + wstążki).
6. Rekwizyt: zostawić z AI albo `hy_cpu.py mini` z referencji i dopasować.
7. `assemble.py`, `finalize.py`, `check.py`, `thick.py`, rendery.

Skrypty do napisania, jako uogólnienie tego, co jest w `research/`:
- `views.py` (gradio_client, Qwen multi-angles, fallback Kontext),
- `hy_cpu.py` (połączenie `cpu_hy2mini.py` i `cpu_hy2mv.py`; parametry: tryb, octree, kroki, wariant turbo/fast),
- `normals.py` (Marigold-e2e i całkowanie),
- `detail.py` (bpy: remesh, displacement z maską, rowki, wstążki),
- `pipeline.sh`, który spina wszystko w całość.

Środowisko CPU: `python3 -m venv --system-site-packages hyvenv` + `pip install diffusers transformers einops omegaconf accelerate opencv-python-headless pymeshlab trimesh scikit-image rembg onnxruntime`. Do tego `git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-2`, a wagi pobiera się `snapshot_download` z `allow_patterns` (tylko safetensors turbo + VAE turbo), `HY3DGEN_MODELS=…/models`. torch 2.14 jest już w systemie.
