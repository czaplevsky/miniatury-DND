# <Nazwa postaci>

Skopiuj ten folder do `models/<nazwa>/` i uzupełnij.

## Założenia
- Wzrost postaci: … m, czyli 36 mm dla 1,90 m (skala liniowa)
- Rozmiar D&D / podstawka: Medium, 25 × 3 mm
- Poza i rekwizyt: …
- Co uprościć (cienkie, ozdobne elementy): …
- Co przesadzić (bandaże, futro, pasy…): …
- Drukarka: żywica / FDM

## Struktura
- `concept/`: oryginalne grafiki i referencje
- `edit/`: edycje Kontext (front, tył)
- `ai/`: surowe meshe
- `print/`: finalne `.3mf` i `_stl.zip`
- `renders/`: rendery i porównania wersji
- `LOG.md`: tabela prób: `| # | próba | koszt (GPU s / CPU min) | werdykt |`

## Checklista
1. [ ] Środowisko sprawdzone (CLAUDE.md, „Pierwsze 5 minut”)
2. [ ] Widoki wycięte, upscale
3. [ ] Kontext: front (uproszczenie i przesada), potem tył
4. [ ] `hy_cpu` mini + mv, `hybrid`
5. [ ] `maps.py`: strefy dla TEJ postaci, potem `detail`, `depeg`, `notch`
6. [ ] `finalize` i walidacja: bryła, 36 mm, obrys, `thick3`, reload 3MF
7. [ ] Rendery i porównanie z poprzednią wersją, wysłane użytkownikowi
