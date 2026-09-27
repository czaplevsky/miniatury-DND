# Figurka D&D z concept artu: retrospektywa i playbook

Dla przyszłych sesji Claude Code (kontener w chmurze: 4 CPU, 15 GB RAM, bez GPU) i dla użytkownika.
Źródła: `models/bandaged-druid/HANDOFF.md`, `pipeline/RESEARCH_PLAN.md`, `models/bandaged-druid/LOG.md` (numery prób poniżej to `#N` z tego logu), `pipeline/PIPELINE.md`, `pipeline/RESEARCH_PLAN.md`, rendery w `models/bandaged-druid/renders/`.

---

## 1. Podsumowanie projektu i oś czasu

**Cel:** zabandażowany druid z dwóch grafik AI (key art + arkusz turnaround). Żywica, 32 mm heroic: postać 1,90 m ma **36 mm od podeszwy do czubka głowy**, podstawka **25 × 3 mm** (Medium). Konar trzymany po skosie w obu dłoniach.

| Wersja | Co zrobiono | Dlaczego / werdykt |
|---|---|---|
| **v1** | Figurka w całości proceduralna z brył w Blenderze (bpy). HF był zablokowany przez politykę sieci | Użytkownik: „ludzik Lego, tragedia”. Dużo pracy wyrzuconej do kosza. Należało od razu poprosić o dostęp do sieci/HF |
| **v2** | FLUX Kontext podmienia ozdobną laskę na zwykły konar (świetne). Hunyuan3D-2.1 ze Space'a → mesh z płytą podłoża (wycięta). Konar AI wycięty (oś wyznaczona promieniami, bo szacunek „na oko” był błędny), wstawiona proceduralna rura. Bandaże jako relief 0,1 mm z luminancji | „Bardzo słabe”: bandaży prawie nie widać, konar nie pasuje rozdzielczością do reszty |
| **research** | Agent badawczy sprawdził opcje z kontenera | **Największy przełom: Hunyuan3D-2 mini/mv turbo działa na CPU (4–7,5 min, 0 limitu GPU).** Limit HF jest potrzebny tylko do edycji 2D |
| **v3** (#1–#24) | Kontext: przód jako „rzeźba miniatury” (#3). Bryła CPU mini-turbo (#10). Normalne Marigold na CPU (#13). `detail.py`: rowki bandaży, wstążki na głowie, futro, pogrubienie konaru (d1–d11) | Czytelne bandaże na brzuchu; futro jak sztruks, tył płaski, głowa jak „ul” |
| **v4** (#25–#43) | Głowa z 11 krzyżujących się pasów (#26). Futro z opadających kosmyków (#27–#28). Fałdy peleryny i poszarpany dół. Kontext: prawdziwy profil (#35) i tył (seed 3). **Hybryda: ostry przód z mini ∪ tył z MV (front+back)**. d18 (#42) | Użytkownik lubi d18 → v4 |
| **v5** (#46–#50) | Depeg (kolce na barkach, płetwa na karku, gałązka przy kolanie), usunięcie szwu hybrydy przez przycięcie peleryny frontowej (#48), ochrona cienkich ścian (#50). Poprawka zapisu 3MF | „Wygląda całkiem nieźle”. Plik: `print/druid_mini_v5.3mf` (23,9 MB, 1,9 mln trójkątów, 4,2 ml żywicy) |

---

## 2. Co zadziałało / co nie zadziałało

### Kontynuować (keep doing)
| Praktyka | Dowód |
|---|---|
| **Edycja 2D przed 3D** (Kontext: uprość rekwizyt, przesadź detal) | v2: podmiana laski na konar za 1 wywołanie. #3: „sculpt like tabletop miniature” daje warstwowe bandaże i zachowuje pozę 1:1 |
| **Bryła na CPU** (Hunyuan3D-2 mini-turbo, octree 512) | #10: najczystsza bryła, szczelna, konar w obu pięściach; 0 s GPU. Porównanie: `renders/research_compare_cpu.png` |
| **Rekwizyt generowany razem z postacią** (nie proceduralnie) | research §0.2; v3+ konar z AI z samym pogrubieniem (#23–#24) |
| **Hybryda: mini (przód) ∪ MV front+back (tył)** | #42 najlepszy wynik; boki z Kontext pogorszyły MV (PIPELINE: „adding the Kontext profile made it worse”) |
| **Detal geometryczny ≥0,15 mm: rowki V 0,18 mm, pasy 0,5–0,6 mm, kosmyki 1,2–2,8 mm** | #26 głowa czyta się jak na portrecie; #27–#28 futro czyta się jako futro |
| **Mierzenie na meshu, nie na obrazie** (linia oczu, oś konaru, grubość) | #20: linia oczu z obrazu była 0,65 mm obok; v2: oś konaru „na oko” była błędna |
| **Log każdej próby do pliku** (#, co, koszt, werdykt) | Agent przerwany 2× limitem sesji (429) i wznowił pracę tylko dzięki `LOG.md` |
| **Rendery w stałych kamerach + zbliżenia + porównanie z poprzednią wersją** | `renders/v4_vs_v5.png` pokazał różnice niewidoczne na pełnym ujęciu |
| **Walidacja po eksporcie przez ponowne wczytanie pliku** | Wykryty błąd 3MF (4 miejsca po przecinku → zdegenerowane fragmenty w v4) |

### Nigdy więcej (never again)
| Błąd | Koszt | Zasada |
|---|---|---|
| Postać z prymitywów bpy (v1) | Wersja wyrzucona w całości | Brak sieci = **najpierw poproś o dostęp**, nie buduj obejścia |
| Mieszanie proceduralnych brył z meshem AI (rura-konar w v2) | „Nie pasuje rozdzielczością” | Wszystkie elementy z tego samego generatora albo rzeźbione na meshu AI |
| Relief <0,15 mm (luminancja 0,1 mm, v2) | Bandaży nie widać | Minimum 0,15 mm, lepiej rowki 0,18–0,25 mm i przesada ×1,5–2 |
| Wywołania GPU bez sprawdzenia API | Błędne parsowanie wyniku (powtórka), TRELLIS.2 `decimation_target` >500000 odrzucony **po** generacji, Qwen-Edit 600 s > max, multiple-angles przerwany (#4) i zjadł resztę limitu (#5) | `view_api()` + walidacja parametrów + zapis surowego wyniku od razu |
| Builder uruchomiony równolegle z researchem | Użytkownik: „najpierw research, bo znowu będziesz eksperymentować” | Research → plan → builder, sekwencyjnie |
| Niespójne widoki do MV (tył z arkusza, #7; front-only s7, #8) | Dziury, gałki zamiast konaru | Do MV tylko widoki z tego samego źródła i pozy |
| Kontext „from his right side” (#36), tył seed 11 (#40) | ~68 s GPU na nic | Kierunek profilu jest ignorowany, więc lustrzane odbicie robi się na CPU; tył wymaga 2–3 seedów |
| `regfit.py` (#14), maski z przecieka­mi (#15–#17, #21–#22) | ~7 prób po 6–7 min | Rejestracja bbox + wizualna kontrola `regview.py`; strefy wybierać w 3D (elipsoida głowy #18, rura wokół polilinii #23) |
| FVOX 0,028 / 0,03 na hybrydzie (#20, #43) | OOM-kill po 12 min | Hybryda: FVOX 0,032; szczyt ~13 GB z 15 GB |
| LOG.md zapisany 2× do korzenia repo | Śmieci w repo | Ścieżki bezwzględne w briefie; `git status` przed commitem |
| Luki w numeracji logu (brak #30–34, #37–39, #44–45) | Nie wiadomo, co kosztowały | Loguj też porażki i przerwania |
| Pełne STL po 95 MB + wagi modeli | Dysk: zostało ~3,5 GB | Kasuj pośrednie STL, trzymaj ZIP/3MF |
| Próba utworzenia repo przez integrację GitHub | 403 | Sprawdź uprawnienia na starcie, powiedz raz |

---

## 3. Złote zasady i checklista startowa (pierwsze 5 minut)

**Złote zasady**
1. Najpierw środowisko, potem plan, potem budowa. Nic proceduralnego „na przeczekanie”.
2. Research (agent) przed builderem. Builder dostaje gotowy przepis.
3. GPU (ZeroGPU) tylko do edycji 2D. Bryła, normalne, detal i walidacja na CPU.
4. Każde wywołanie płatne limitem: `view_api` → tani test → prawdziwe wywołanie → zapis surowego wyniku.
5. Oceniaj w skali druku (zbliżenia ortho 7–17 mm), nie na ładnym ujęciu całości.
6. Jedna zmiana na próbę, jeden wiersz logu na próbę.

**Checklista (wkleić wyniki do `HANDOFF.md`)**
```sh
curl -sS -o /dev/null -w '%{http_code}\n' https://huggingface.co/api/spaces/black-forest-labs/FLUX.1-Kontext-Dev   # 200 = sieć OK
python3 -c "import os;print('HF_TOKEN' in os.environ)"
curl -sS -H "Authorization: Bearer $HF_TOKEN" https://huggingface.co/api/whoami-v2 | head -c 300   # konto, uprawnienia tokena
df -h / ; free -g ; nproc ; nvidia-smi 2>/dev/null || echo "brak GPU"
curl -sS "$HTTPS_PROXY/__agentproxy/status" | head
```
- **GitHub:** sprawdź, czy możesz utworzyć repo lub pushować. Jeśli nie, poproś użytkownika raz, żeby utworzył repo; do tego czasu pracuj na gałęzi w podfolderze.
- **Brak sieci do HF:** zatrzymaj się i daj instrukcję (aplikacja mobilna nie ma tych ustawień): *claude.ai/code w przeglądarce → ikona chmury → koło zębate środowiska → Network access: Custom → domeny `huggingface.co`, `*.huggingface.co`, `*.hf.co`, `*.hf.space`*. Zmiana sieci działa w tej samej sesji. **Zmiana zmiennych (HF_TOKEN) wymaga nowej sesji.**
- **Token HF:** darmowe konto (nie anonim: anonim miał limit na 1 wywołanie). Opcjonalnie uprawnienia „Inference Providers” i zapis (dla duplikatu Space'a).
- **Dysk:** potrzeba ≥15 GB (mini-turbo 4,2 GB, mv 4,9 GB, Marigold 5,2 GB, STL po 50–95 MB).

**Pytania do użytkownika (tylko te, które zmieniają plan)**
1. Drukarka: żywica czy FDM? (grubości minimalne, podpory)
2. Skala i podstawka (domyślnie: 32 mm heroic → ~36 mm dla 1,9 m, 25 mm × 3 mm)
3. Poza i rekwizyt: co uprościć względem grafiki (zdjęcie referencyjne?)
4. Gdzie oddać wynik: osobne repo (kto je tworzy?) czy pliki w czacie (3MF <30 MB)

---

## 4. Rekomendowany pipeline v2.0

Skrypty: `pipeline/`. Środowiska: `hyvenv` (torch, diffusers, Hunyuan3D-2, rembg), `bvenv` (bpy 5.0.1 w osobnym venv, bo globalny numpy 2.x psuje bpy; trimesh, scipy, manifold3d).

| # | Krok | Polecenie | Czas | Limit GPU |
|---|---|---|---|---|
| 0 | Przygotowanie: wycięcie widoków z arkusza, upscale ×2–4 | `cutout.py`, Real-ESRGAN | 2 min | 0 |
| 1 | **Edycja frontu**: uprość rekwizyt (zdjęcie referencyjne), przesadź detal („sculpt … like a tabletop miniature”, gs 3,5) | `edit_front.py kontext SEED SRC OUT` | 30–40 s | ~35 s/wywołanie |
| ▲ | *Decyzja:* poza i rekwizyt 1:1, detal warstwowy? Jeśli nie → kolejny seed (max 3) | | | |
| 2 | **Tył** z edytowanego frontu (Kontext, „viewed from directly behind”) | `kviews.sh SEED 180` | 35–40 s | 2–3 seedy × ~35 s |
| ▲ | *Decyzja:* rekwizyt z przodu, nie za plecami (#40)? Boków **nie** generuj (#36, pogarszały MV) | | | |
| 3 | Wycięcie tła; do „rzeźby” użyj alfy z obrazu kolorowego (#6) | `cutout.py` | 20 s | 0 |
| 4a | Bryła przód: mini-turbo | `hy_cpu.py mini hy/mini.glb 512 5 1 front=…` | 4–9 min | 0 |
| 4b | Bryła tył: mv-turbo front+back | `hy_cpu.py mv hy/mv.glb 512 5 1 front=… back=…` | 5–7,5 min | 0 |
| 4c | Oś Z, skala 36 mm, usunięcie płyty podłoża | `prep.py IN.glb OUT.stl` | 1 min | 0 |
| ▲ | *Decyzja:* szczelna? bez latających kawałków (#11)? Jeśli nie → inny seed | | | |
| 5 | Hybryda (przód mini, tył MV, przycięcie boków peleryny #48) | `hybrid.py mini.stl mv.stl hyb.stl -0.5 37.5 10.6` | 1 min | 0 |
| 6 | Usunięcie kolców i gałązek | `depeg.py hyb.stl hyb_dp.stl` | 2 min | 0 |
| 7 | Normalne AI + mapy + rejestracja | `normals.py IMG PREFIX 1248`, `maps.py`, `reg.py`, `regview.py` | 3 min | 0 |
| 8 | Detal + podstawka | `CUTS=… HYB_Y0=-0.5 FVOX=0.032 FUR_Z0=… detail.py hyb_dp.stl out/dN` | 12–14 min | 0 |
| 9 | Poszarpany dół peleryny | `notch.py IN OUT` | 1 min | 0 |
| 10 | Eksport + walidacja | `finalize.py IN out/NAME` (3MF z 6 miejscami), `thick3.py` | 3 min | 0 |
| 11 | Rendery + porównanie | `rend.sh MESH NAME`, `compare.py` | 3 min | 0 |

**Budżet dzienny (darmowe konto, ~3,5–4,5 min GPU):** krok 1 (1–2×) + krok 2 (2–3×) ≈ 2,5–3 min. Resztę dnia pracuje CPU.
**Uwaga:** `maps.py` ma ręcznie wpisane prostokąty (piksele) stref bandaży i polilinię konaru dla tej postaci. Przy nowej postaci trzeba je ustawić od nowa (albo wybierać strefy w 3D).
**Fallbacki:** TRELLIS.2 (`decimation_target ≤ 500000`, 1 próba dziennie), Hi3DGen `/generate_3d` (60 s), ręcznie w przeglądarce użytkownika: Hitem3D/Sparc3D, Tripo, Meshy, Hunyuan 3.x (kontener ich nie widzi; GLB wrzucić do `ai/`).

---

## 5. Weryfikacja: jak udowodnić, że krok działa

| Co | Jak | Próg zaliczenia |
|---|---|---|
| Edycja 2D | Contact sheet: oryginał \| edycja \| referencja rekwizytu | poza, dłonie i rekwizyt 1:1, detal grubszy |
| Widoki | Front i tył obok siebie | ten sam rekwizyt, ta sama strona, brak nowych elementów |
| Bryła | `rend.sh` 4 widoki | szczelna, 1 bryła, brak dziur w pelerynie |
| Detal | **Zbliżenia w skali druku**: tułów ortho 17 mm, głowa ortho 7 mm, 4 kąty | każdy detal czytelny w zbliżeniu tułowia; nic nie wygląda jak szum |
| Regresja | `compare.py` poprzednia vs nowa, te same kamery | brak nowych artefaktów (szwy, kolce, płetwy) |
| Geometria | `finalize.py` | 1 bryła, `is_watertight`, `winding consistent` |
| Wymiary | bounds | podeszwa→głowa 36,0 ± 0,1 mm; podstawka Ø25 × 3; max promień nad podstawką ≤12,5 mm |
| Grubości | `thick3.py` (nie `thick2.py`, który liczy grzbiety reliefu jako ściany) | <1 % próbek <0,4 mm, tylko końcówki (v5: 0,82 %) |
| Rekwizyt | pomiar średnicy wzdłuż osi | ≥1,5 mm (cel ~2 mm) |
| Eksport | **ponowne wczytanie 3MF/STL** i ponowny `split()` | 1 szczelna bryła, 3MF <30 MB |
| Limit | wiersz w `LOG.md` na każde wywołanie GPU (sekundy, wynik) | suma zgadza się z komunikatem HF |

**Definition of done:** wszystkie wiersze tabeli zaliczone; `print/NAZWA_vN.3mf` + `_stl.zip`; `renders/vN_widoki.png`, `vN_zblizenie.png`, `vN_glowa.png`, `v(N-1)_vs_vN.png`; `LOG.md` z listą znanych niedoskonałości; `HANDOFF.md` zaktualizowany; pliki pośrednie usunięte.

---

## 6. Oszczędzanie tokenów i limitów

**Tokeny Claude i czas**
- **Research przed budową.** Jeden agent badawczy (1–2 h) zaoszczędził dziesiątki prób: CPU Hunyuan zamiast reglamentowanego GPU.
- **Brief z przepisem** (szablon niżej): ścieżki bezwzględne, polecenia, progi, kryteria stopu. Builder nie odkrywa środowiska od zera.
- **Pliki zamiast pamięci:** `LOG.md` (dopisywany po każdej próbie), `HANDOFF.md` (stan + następny krok). Po 429 lub restarcie agent czyta tylko te dwa pliki.
- **Obrazy:** jeden contact sheet (≤1400 px) na próbę zamiast 4–12 osobnych PNG. Nie wczytywać ponownie tych samych renderów. Nie czytać meshy ani 25 KB `detail.py` w całości: `grep` po nazwie parametru.
- **Długie kroki w tle** (`run_in_background`, `nice`), bez odpytywania co minutę.
- **Nie narrować:** raport końcowy = werdykt + ścieżki + liczby.
- **Budżet na iterację:** 1 zmiana, ≤15 min CPU, 1 contact sheet, 1 wiersz logu.
- **Kryteria stopu:** (a) 3 próby bez poprawy w zbliżeniu → zmień podejście albo zapytaj; (b) poprawki widoczne tylko w zbliżeniu ×3 → oddaj wersję; (c) użytkownik powiedział „dobrze”.

**Limit HF (ZeroGPU)**
- Anonim: ~1 wywołanie. Darmowe konto: nominalnie 5 min, realnie **3,5–4,5 min/dzień** (~9 wywołań Kontext). Reset 24 h od pierwszego użycia.
- Wywołanie startuje tylko, jeśli zostało ≥ `duration` Space'a (np. „60s requested vs 31s left”, #5). Najpierw sprawdź `duration` w `app.py`. Space z 600 s nie ruszy nigdy.
- Najpierw `Client(...).view_api()`, sprawdź zakresy parametrów (np. `decimation_target`), zapisz surowy wynik do pliku **przed** parsowaniem.
- Space'y wieloetapowe (TRELLIS.2): każda funkcja płaci osobno; błąd w ostatnim etapie marnuje wszystko.
- Space „bez ZeroGPU” to często iframe do zewnętrznego serwera, nieosiągalny z kontenera.
- API Hub: 1000 zapytań / 5 min na konto. Nie skanuj masowo `/runtime`.

**Co kupić**
| Opcja | Koszt | Korzyść | Kiedy |
|---|---|---|---|
| **HF PRO** | $9/mies. | 40 min GPU/dzień (8×), priorytet, $2 kredytów | **Zawsze przy >1 figurce.** Pozwala na seedy widoków, TRELLIS.2 1536, Hi3DGen |
| Token z „Inference Providers” | 0 | edycje 2D poza ZeroGPU, ale darmowo tylko ~3 obrazy/mies. | dodatek |
| HF Jobs (L4 $0,80/h) | centy/przebieg | TRELLIS.2 bez decymacji | tylko przy wielu postaciach (trzeba zbudować środowisko CUDA) |
| Tripo / Meshy / Hitem3D w przeglądarce | $10–20/mies. | najostrzejszy detal | gdy CPU Hunyuan to za mało; użytkownik wgrywa widoki ręcznie |

---

## 7. Komunikacja z tym użytkownikiem

- Pisze **po polsku**, często z telefonu. Odpowiadaj po polsku, krótko, z obrazkiem (contact sheet) i jednym zdaniem werdyktu.
- Chce **wyników, nie wymówek**. Porażkę zgłoś w jednym zdaniu razem z planem B.
- Ocenia bezpośrednio („ludzik Lego”, „bardzo słabe”). Traktuj to jako dane: zapisz w logu, co konkretnie się nie podoba.
- Chce, żeby agenci **pracowali do wyczerpania limitów**, a nie pytali co chwilę. Pytaj tylko o rzeczy zmieniające plan.
- Chce **osobnego repo**. Jeśli Claude nie może go utworzyć, powiedz raz i pracuj w podfolderze.
- Nie wie, gdzie są ustawienia środowiska: podawaj dokładną ścieżkę kliknięć (web, nie aplikacja mobilna) i uprzedzaj, że zmiana tokena wymaga nowej sesji.
- Ma rację co do kolejności: research → plan → budowa. Nie uruchamiaj równolegle agentów zależnych od siebie.
- Pokazuj wersję obok poprzedniej (`vN-1_vs_vN.png`), żeby w telefonie było widać różnicę.

---

## 8. Szablony

### Brief dla agenta badawczego
```
Cel: znaleźć najlepszą drogę z [OBRAZ/Y] do [CO] w TYM kontenerze (4 CPU, 15 GB RAM, bez GPU, [X] GB dysku).
Ograniczenia: sieć tylko [DOMENY]; HF: [anonim/darmowe/PRO], zostało ~[N] s ZeroGPU — możesz zużyć max [M] s.
Sprawdź (i ZMIERZ z kontenera, nie z pamięci):
 1. Które modele [image-to-3D / normalne / edycja 2D] uruchomią się lokalnie na CPU: czas, RAM, rozmiar wag.
 2. Które Space'y działają: api_name, parametry, duration, limity (view_api, bez wywołań płatnych chyba że test ≤[M] s).
 3. Co jest nieosiągalne z kontenera (lista domen).
 4. Ceny/limity opcji płatnych.
Nie buduj finalnego modelu. Nie pisz do [REPO]. Pliki testowe tylko w [SCRATCHPAD]/research/.
Wynik: [SCRATCHPAD]/research/PLAN.md: tabela kroków (polecenie, czas, koszt limitu, sprawdzone/niesprawdzone),
fallbacki, co kupić. Raport końcowy ≤15 linii.
```

### Brief dla agenta-buildera
```
Cel: [POSTAĆ] jako figurka [SKALA] mm (podeszwa→głowa [H] mm), podstawka [Ø]×[h] mm, druk [żywica/FDM].
Przepis: [ŚCIEŻKA]/PLAN.md kroki [..] — trzymaj się go; odchylenie tylko z wpisem w logu.
Wejścia: [ścieżki obrazów]. Środowiska: [hyvenv], [bvenv]. Skrypty: [ŚCIEŻKA]/scripts/.
Katalog roboczy: [SCRATCHPAD]/vN/ (ścieżki bezwzględne; NIE pisz do korzenia repo, bez git).
Limit GPU: max [N] s dziś; przed każdym wywołaniem view_api + test parametrów; surowy wynik zapisz od razu.
Po każdej próbie dopisz wiersz do [SCRATCHPAD]/vN/LOG.md: | # | co | czas / s GPU | werdykt |
(także porażki i OOM). Na start przeczytaj LOG.md i HANDOFF.md — jeśli istnieją, kontynuuj od ostatniej próby.
Weryfikacja każdej wersji: rend.sh (pełny + zbliżenie ortho 17 + głowa ortho 7), compare.py z poprzednią,
finalize.py (1 bryła, szczelna, wymiary), thick3.py (<1 % <0,4 mm), reload 3MF.
Priorytety poprawek: [1. …, 2. …, 3. …]. Znane pułapki: [FVOX ≥0,032 na hybrydzie; relief ≥0,15 mm; …].
Stop: DoD spełnione ALBO 3 próby bez poprawy ALBO koniec budżetu [T] h. Pracuj do wyczerpania budżetu, nie pytaj o drobiazgi.
Wynik: [REPO]/print/NAZWA_vN.3mf + _stl.zip, renders/vN_*.png, zaktualizowany HANDOFF.md, raport ≤10 linii.
```
