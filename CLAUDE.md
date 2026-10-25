# CLAUDE.md – Projektkontext FBH-Monitor

Diese Datei hält den Stand und die Entscheidungen des Projekts fest, damit eine neue Sitzung
ohne den ursprünglichen Chatverlauf weiterarbeiten kann. **Sprache im Projekt: Deutsch**
(Dateien, Kommentare, Commit-Messages, Antworten an den Nutzer).

## Ziel

Überwachung der Vor- und Rücklauftemperaturen jedes Fußbodenheizkreises in einem Einfamilienhaus.
Zwei Heizkreisverteiler (EG, OG) mit je 7 Kreisen. Einzelraumregelung mit thermischen Stellantrieben
ist vorhanden. Zielsystem Home Assistant, Firmware ESPHome. Maker-Projekt: Der Nutzer entwirft
Platinen in KiCad, ätzt/fräst/bohrt selbst, konstruiert in FreeCAD und druckt in 3D. Alles soll
möglichst kompakt sein. Im Verteilerkasten gibt es 230 V und Netzwerk mit PoE.

## Status (25.10.2026)

| Bereich | Stand |
|---|---|
| Konzept, Schaltpläne, Bauanleitung | fertig (`docs/bauanleitung.html`) |
| ESPHome-Konfiguration | fertig, `esphome config` mit ESPHome 2026.10 gültig; **Kompilierung noch nicht getestet** |
| Home-Assistant-Package | fertig, Jinja-Logik mit simulierten Zuständen getestet; Stellantrieb-Entitäten sind Platzhalter |
| CAD (CadQuery) | Rohrclips, Fühlerknoten, Modul-Baugruppe, Distanzhülse; STEP/STL in `cad/export/` |
| Bestellung | auf Digi-Key und reichelt aufgeteilt (`bestellung/`), Warenkörbe gefüllt, noch nicht bestellt |
| KiCad-Projekte | **offen** – nächster Schritt |
| Gehäuse für das Modul | **offen** |
| Aufbau, Kalibrierung, Inbetriebnahme | offen |

## Architektur und Entscheidungen

### Modul je Verteiler
- **Olimex ESP32-POE-ISO, WROOM-Variante** (nicht WROVER: dort Ethernet-Takt auf GPIO0 und GPIO33 belegt).
  ISO-Variante wegen galvanischer Trennung; darf gleichzeitig an USB und PoE. PoE nach IEEE 802.3af.
- Ethernet in ESPHome: LAN8720, MDC GPIO23, MDIO GPIO18, `clk: {pin: GPIO17, mode: CLK_OUT}`,
  `phy_addr: 0`, `power_pin` GPIO12 (Strapping-Warnung bewusst unterdrückt).
- Eigene Komplettplatine mit ESP32+PHY+PoE wurde verworfen (QFN 0,5 mm, RMII 50 MHz, 1500-V-Trennung
  sind nicht sinnvoll selbst ätzbar).

### Pinbelegung Olimex (aus Olimex-KiCad-Layout Rev. O, github.com/OLIMEX/ESP32-POE-ISO)
- Board 28 × 98,15 mm. Koordinaten: x quer (0 = linke Kante, EXT1-Seite), y längs (0 = Antennenende).
- EXT1 bei x = 1,29 mm, EXT2 bei x = 26,69 mm (Abstand 25,40). Pin 1 bei y = 33,22, Pin 10 bei y = 56,08, Raster 2,54.
- EXT1: 1 +5V, **2 +3.3V**, **3 GND**, 4 EN, 5 GPIO0, 6 GPIO1, 7 GPIO2, 8 GPIO3, 9 GPIO4, 10 GPIO5.
- EXT2: 1 GPI39, 2 GPI36, 3 GPI35, 4 GPI34, **5 GPIO33**, **6 GPIO32**, 7 GPIO16, 8 GPIO15, 9 GPIO14, 10 GPIO13.
- Montagelöcher Ø 2,2 mm: (2,56 / 27,48), (25,42 / 27,48), (7,64 / 95,42). RJ45 am Ende y ≈ 77,7–98,6, USB links bei y = 62,65.
- Die EXT-Footprints liegen bei Olimex auf der Unterseite: Stiftleisten von oben einstecken, unten verlöten,
  Board steckt mit Bauteilseite nach oben auf der Basisplatine.

### Basisplatine (38 × 38 mm, einseitig)
- Liegt unter dem Olimex, Bereich x 0–38, y 24–62 (Olimex-Koordinaten). Rechts 10 mm Überstand für J1/J2.
- Buchsenleisten 1×10, 8,5 mm hoch, exakt unter EXT1/EXT2. Stapelabstand Platine–Platine ≈ 11 mm
  (8,5 Buchse + 2,5 Stiftleisten-Kunststoff). Verbindung: M2 × 16 + Mutter + gedruckte Distanzhülse 11 mm
  an MH2/MH3; zwei weitere M2-Löcher (35 / 27) und (35 / 59) für das Gehäuse.
- Bauteile: R1, R2 = 4,7 kΩ Pull-up nach 3,3 V (bei Problemen 2,2 kΩ), C1 = 100 nF, J1/J2 = JST-PH 3-pol gewinkelt
  (S3B-PH-K-S), optional ESD-Diode je Kette.
- **Kette A** = J1 = GPIO32 (EXT2-6): Balken-Referenz + 7 Vorläufe (8 Knoten).
  **Kette B** = J2 = GPIO33 (EXT2-5): 7 Rückläufe.

### Fühlerknoten (10 × 26 mm, einseitig)
- DS18B20 im TO-92, flach auf der Kupferseite, Beinchen 90° gebogen auf SMD-Pads (~1,2 × 2,5 mm);
  Rücken liegt ohne Spalt an der Platine und wird mit 2K-Epoxid fixiert (Kraft über Körper, nicht Lötstellen).
- Zwei JST-PH 3-pol **gewinkelt** (S3B-PH-K-S) an den Enden, Kabel quer zum Rohr. Optional C 100 nF 1206.
- **Pinfolge überall 1 GND · 2 DQ · 3 VDD** (= DS18B20-TO-92-Belegung, Leiterbahnen laufen gerade durch).
- Lineare 1-Wire-Kette, Segmentkabel ca. 80 mm (Abgangsabstand 50 mm, nur ~14 mm Luft zwischen Steckern
  → Schlaufe). Kettenende offen, kein Abschluss. Kabel 1:1 – gedrehte Kabel zerstören den Fühler.

### Wärmeübergang
- Silikon-Wärmeleitpad 1,5 mm, 5 × 5 mm, weich (Shore 00 ≤ 50), am Rohrscheitel auf 1,1 mm gedrückt (~27 %).
  Kupfer-Schuh wurde vom Nutzer ausdrücklich abgelehnt. Paste wird nicht verwendet.
- Dämmung ist entscheidend: Clip + je 3 cm Rohr mit zwei Lagen Armaflex-Band.
- VL-Knoten 3–5 cm unter der Verschraubung (sonst Wärmeleitung vom Balken), RL-Knoten direkt unter der Verschraubung.

### Rohrclips (gemessen vom Nutzer)
- Abgang: Kunststoffrohr **Ø 17,3 mm**, Clip 14 mm lang → 29 × 22 × 14 mm, ~4,3 g.
- Vorlaufbalken: runder Abschnitt **Ø 26,7 mm, 16 mm breit**, Clip **16 mm** lang (Nutzerwunsch) → 31 × 29 × 16 mm.
- C-Form, Öffnung 120° (100° wäre zu viel Aufbiegung), Wand 2,2 mm, radiales Spiel 0,1 mm,
  zwei Rastnasen halten die Knotenplatine. PETG oder ASA, kein PLA.
- Druck: Rastnasen-Seite aufs Bett, ohne Stützmaterial, Brim. STL-Dateien sind so ausgerichtet.

### Firmware-Logik (ESPHome)
- `esphome/common/fbh-basis.yaml`: Board, Ethernet, zwei `one_wire`-Busse, drei Template-Numbers
  (Heizbetrieb ab Vorlauf 25 °C, Schwelle VL-Abfall 2,0 K, Mindestspreizung 1,0 K), Binary Sensor *Heizbetrieb*.
- `esphome/common/fbh-kreis.yaml`: per `packages` mit `vars` eingebunden (kreis, vl_addr, rl_addr, vl_offset, rl_offset).
  Erzeugt *Kreis N VL/RL/Spreizung/Durchfluss*. Durchfluss = Heizbetrieb ∧ (Balken − VL ≤ Schwelle) ∧ (VL − RL ≥ Spreizung),
  `delayed_on_off: 3min`.
- Entitäts-IDs in HA: `sensor.fbh_eg_kreis_1_vl`, `binary_sensor.fbh_eg_kreis_1_durchfluss`,
  `sensor.fbh_eg_vl_balken`, `binary_sensor.fbh_eg_heizbetrieb` (OG analog mit `fbh_og`).
- Fühleradressen sind Platzhalter `0x0000000000000000`; werden beim Inbetriebnehmen aus dem Log übernommen.
- `secrets.yaml` nie committen (steht in `.gitignore`), nur `secrets.example.yaml`.

### Home Assistant
- `homeassistant/packages/fbh_monitor.yaml`: `binary_sensor.fbh_kreisfehler` (Soll/Ist, delay_on 20 min),
  `binary_sensor.fbh_vorlauf_zu_hoch` (input_number `fbh_vl_maximum`), `binary_sensor.fbh_sensorausfall`,
  Sensoren aktive Kreise, Automation mit persistent_notification (Push auskommentiert).
- `homeassistant/custom_templates/fbh.jinja`: Zuordnung Durchfluss-Sensor → Stellantrieb.
  **Platzhalter `switch.STELLANTRIEB_EG_K1` usw. – echte Entitäten des Nutzers noch eintragen.**
- Entitätsnamen bewusst ohne Umlaute (Slug-Probleme).

## Bestellung (Stand 25.10.2026, Warenkörbe gefüllt, nicht bestellt)
- **Digi-Key** (`bestellung/digikey_warenkorb.csv`): 3 × Olimex ESP32-POE-ISO (2 + 1 Reserve/Test, hält Gratisversand),
  4 × Stiftleiste 35-PRPC010SAAN-RC-ND, 70 × 455-1720-ND, 70 × PHR-3 455-1126-ND, 200 × SPH-002T-P0.5L 455-2148-100-ND
  (455-2148-1-ND ist ausgelaufen).
- **reichelt** (`bestellung/reichelt_warenkorb.csv`): Buchsenleisten MPE 094-1-010, 32 × DS 18B20 (Maxim, 1,40 €),
  Widerstände METALL 4,70K, Kondensatoren 12061C104KAT2A, Arctic TP-3 1,5 mm (ARCTIC 04007),
  Litze ECON KL014 schwarz/rot/orange 10 m (gelb nicht als 10 m → **DQ ist orange**).
- Lokal: FR4 einseitig, PETG/ASA, Epoxid, Armaflex-Tape, M2-Schrauben/Muttern, Patchkabel, JST-PH-Crimpzange.

## Repository und Werkzeuge
- `docs/bauanleitung.html`: Bauanleitung (eine Datei, Renderings als Base64 eingebettet). Wird zusätzlich als
  claude.ai-Artifact veröffentlicht; Änderungen hier machen und bei Bedarf neu veröffentlichen.
- `cad/fbh_cad.py`: parametrische Modelle. `python cad/fbh_cad.py` erzeugt alle Exporte in `cad/export/`.
  Wichtige Parameter oben im Skript (ROHR_D, BALKEN_D, BALKEN_LAENGE, CLIP_*, PAD_*).
- `cad/render_ansichten.py`: Renderings nach `cad/renders/` (PyVista offscreen, nicht versioniert).
- ESPHome prüfen: `esphome config esphome/fbh-eg.yaml` (braucht eine `secrets.yaml` mit gültigen Base64-Schlüsseln).
- Commits: Autor Thomas Blankschein, Commit-Message auf Deutsch.

## Nächste Schritte
1. **KiCad-Projekte** `hardware/basisplatine/` und `hardware/fuehlerknoten/`:
   Schaltplan wie oben, Footprints aus der KiCad-Standardbibliothek, einseitig (Kupfer unten),
   Leiterbahnen ≥ 0,6 mm, Abstände ≥ 0,4 mm, Pads ≥ 1,8 mm, Bohrungen 0,8 mm (Bauteile) / 1,0 mm (Leisten).
   Basisplatine mit Buchsenleisten-Positionen aus den Olimex-Koordinaten, Ursprung Antennenende.
   Knoten mit TO-92-SMD-Pads auf der Kupferseite; Nutzen 15 Knoten + Basisplatine auf einer Europakarte.
   DRC und Gerber/Drill-Export (für Fräse), Ergebnis committen.
2. **Gehäuse** für Modul: innen ~40 × 100 × 32 mm, RJ45 Stirnseite, USB links, J1/J2 rechts, Hutschiene
   oder Kabelbinder-Schlitze, Lüftungsschlitze. Olimex-STEP aus deren KiCad-Dateien als Referenz.
3. Stellantrieb-Entitäten in `fbh.jinja` eintragen (Nutzer hat Home Assistant; Namen erfragen oder auslesen).
4. Nach dem Aufbau: Adressen, Offsets, Schwellwerte einmessen; Kompilierung/Flash bestätigen.
