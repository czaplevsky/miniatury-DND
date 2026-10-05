# G-code FDM (testowy) dla Banach School / Rapid

Pliki pocięte w PrusaSlicer 2.7.2 na **generycznym profilu Marlin**: stół 210×210, dysza 0,4, PLA 210 °C, stół 60 °C, warstwa 0,1 mm, podpory organiczne, brim 5 mm. Profil: `banach_school_pla.ini`.

| Plik | Skala | Wysokość | Czas | Filament |
|---|---|---|---|---|
| `druid_banach_school_100pct.gcode` | 100% | 39 mm | ok. 2 h | ok. 2,0 m (ok. 6 g) |
| `druid_banach_school_150pct.gcode` | 150% (zalecane na FDM) | 58,5 mm | ok. 4 h 50 min | ok. 5,4 m (ok. 16 g) |

Start G-code (sprawdzony): `M140 S60`, `M104 S210`, `G28`, `M190 S60`, `M109 S210`, linia czyszcząca przy X5.

**Uwaga:** to nie jest oficjalny profil Banach. Preferowana droga to **Ultimaker Cura z profilem Banach** (banach3d.pl/do-pobrania), a ten plik służy jako test i wzór.

## Sprawdzenie przed drukiem
1. Rozszerzenie `.gcode`. Plików `.3mf` ani `.stl` drukarka nie wydrukuje.
2. Na początku pliku muszą być `M104/M109` z temperaturą 200–215 i `M140/M190` z 60.
3. Po starcie na ekranie drukarki zadana temperatura dyszy ma wynosić ok. 210.
4. Jeśli zadana temperatura jest ustawiona, a odczyt stoi na 20–30 °C, problem jest sprzętowy (grzałka, czujnik), nie w pliku. Sprawdź ręczne nagrzewanie z menu.
