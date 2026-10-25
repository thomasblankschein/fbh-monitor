"""
FBH-Monitor – parametrische 3D-Modelle (CadQuery 2.x)

Erzeugt STEP- und STL-Dateien für:
  - Rohrclips (Druckteil)                    -> rohrclip_*_D<d>.step / *_druck.stl
  - Fühlerknoten (Platine + Bauteile)        -> fuehlerknoten.step
  - Basisplatine mit Olimex ESP32-POE-ISO    -> modul_baugruppe.step
    (Olimex nur vereinfacht: Umriss, Löcher, Steckleisten, Modul, RJ45, USB –
     Lage aus dem KiCad-Layout Rev. O von Olimex)

Aufruf:  python fbh_cad.py            -> Clips für Abgang (17,3 mm) und Balken (26,7 mm)
         python fbh_cad.py 20.0       -> Clip für beliebigen Durchmesser
In FreeCAD: STEP importieren oder dieses Skript im CadQuery-Workbench ausführen.

Koordinaten Modul: x quer (0 = linke Kante Olimex, EXT1-Seite),
                   y längs (0 = Antennenende), z hoch (0 = Unterseite Basisplatine)
Koordinaten Clip:  Rohrachse = z, Knoten liegt auf +y, Kette verläuft entlang x
"""
import sys
import math
import cadquery as cq

# --------------------------------------------------------------------------
# Parameter
# --------------------------------------------------------------------------
# Gemessen am Verteiler (25.10.2026):
ROHR_D = 17.3            # Außendurchmesser Kunststoffrohr an den Abgängen
BALKEN_D = 26.7          # runder Abschnitt am Vorlaufbalken (16 mm breit)
CLIP_SPIEL = 0.1         # radiales Spiel Clip/Rohr (Druck fällt meist etwas enger aus)
CLIP_WAND = 2.2          # Wandstärke Ring
CLIP_LAENGE = 14.0       # Länge entlang Rohr (Abgang)
BALKEN_LAENGE = 16.0     # Länge Balkenclip = Breite des runden Abschnitts
CLIP_OEFFNUNG = 120.0    # Öffnungswinkel unten in Grad

PCB_T = 1.6              # Platinendicke
KNOTEN_L = 26.0          # Knotenplatine quer zum Rohr (x)
KNOTEN_B = 10.0          # Knotenplatine entlang Rohr (z)
TO92_H = 3.7             # Dicke TO-92 flach liegend; Rücken liegt direkt an der
                         # Platine an (mit Epoxid fixiert), Kraft geht über den Körper
PAD_D = 1.5              # Wärmeleitpad Nenndicke (Silikon, weich, 3–6 W/mK)
PAD_A = 5.0              # Pad-Zuschnitt 5 × 5 mm
PAD_EINGEBAUT = 1.1      # Pad-Dicke eingebaut am Rohrscheitel (~27 % Kompression)

PH_B, PH_T, PH_H = 8.0, 6.0, 4.8          # JST-PH gewinkelt S3B-PH-K-S (vereinfacht)
PHR_L, PHR_H = 6.0, 4.2                   # Stecker PHR-3 (vereinfacht)

# Modul
OLI_B, OLI_L = 28.0, 98.15
EXT1_X, EXT2_X = 1.29, 26.69
EXT_Y0 = 33.22                           # Pin 1
PITCH = 2.54
BUCHSE_H = 8.5                           # Buchsenleiste
STIFT_KUNSTSTOFF = 2.5                   # Kunststoff der Stiftleiste
Z_OLI = PCB_T + BUCHSE_H + STIFT_KUNSTSTOFF   # Unterseite Olimex = 12.6
BASIS = (0.0, 24.0, 38.0, 62.0)          # x0, y0, x1, y1 der Basisplatine


def box(x0, y0, z0, dx, dy, dz):
    return cq.Workplane("XY").box(dx, dy, dz, centered=False).translate((x0, y0, z0))


def zyl_z(x, y, z0, r, h):
    return cq.Workplane("XY").circle(r).extrude(h).translate((x, y, z0))


def zyl_x(x0, y, z, r, l):
    return cq.Workplane("YZ").circle(r).extrude(l).translate((x0, y, z))


# --------------------------------------------------------------------------
# Rohrclip
# --------------------------------------------------------------------------
def knoten_yb(r):
    """Höhe der Knotenplatinen-Unterseite über der Rohrachse:
    Rohr + eingebautes Pad + TO-92 (Rücken an der Platine)."""
    return r + PAD_EINGEBAUT + TO92_H


def rohrclip(d=ROHR_D, oeffnung=CLIP_OEFFNUNG, spiel=CLIP_SPIEL, laenge=CLIP_LAENGE):
    r = d / 2
    ri = r + spiel
    ro = ri + CLIP_WAND
    yb = knoten_yb(r)                     # Unterseite Knotenplatine
    hz = laenge / 2

    ring = zyl_z(0, 0, -hz, ro, laenge)
    # Sattel unter der Platine; mindestens so breit wie der Ring (keine Überhänge)
    hx = max(KNOTEN_L / 2 + 1.5, ro)
    sattel = box(-hx, r - 2.0, -hz, 2 * hx, yb - (r - 2.0), laenge)
    # Seitenwände mit Rastnasen
    w_y0, w_y1 = yb - 1.0, yb + PCB_T + 1.2
    wand1 = box(-hx, w_y0, -hz, 2 * hx, w_y1 - w_y0, hz - KNOTEN_B / 2 - 0.1)
    wand2 = box(-hx, w_y0, KNOTEN_B / 2 + 0.1, 2 * hx, w_y1 - w_y0, hz - KNOTEN_B / 2 - 0.1)
    nase1 = box(-6.0, yb + PCB_T + 0.05, -KNOTEN_B / 2 - 0.1, 12.0, w_y1 - yb - PCB_T - 0.05, 0.9)
    nase2 = box(-6.0, yb + PCB_T + 0.05, KNOTEN_B / 2 - 0.8, 12.0, w_y1 - yb - PCB_T - 0.05, 0.9)
    clip = ring.union(sattel).union(wand1).union(wand2).union(nase1).union(nase2)

    # Rohr, Öffnung unten, Fenster für TO-92 und Beinchen
    clip = clip.cut(zyl_z(0, 0, -hz - 1, ri, laenge + 2))
    a = math.radians(oeffnung / 2)
    keil = (cq.Workplane("XY")
            .polyline([(0, 0), (40 * math.sin(a), -40 * math.cos(a)), (0, -40), (-40 * math.sin(a), -40 * math.cos(a))])
            .close().extrude(laenge + 2).translate((0, 0, -hz - 1)))
    clip = clip.cut(keil)
    clip = clip.cut(box(-3.0, 0, -3.2, 6.0, yb + 0.01, 8.0))
    try:  # Kanten parallel zur Rohrachse leicht verrunden (druckfreundlicher)
        clip = clip.edges("|Z").fillet(0.6)
    except Exception:
        pass
    return clip


# --------------------------------------------------------------------------
# Fühlerknoten (Lage wie im Clip)
# --------------------------------------------------------------------------
def fuehlerknoten(d=ROHR_D, mit_steckern=True):
    r = d / 2
    ys = r + PAD_EINGEBAUT                # flache Seite des TO-92
    yb = knoten_yb(r)
    teile = {}
    # Wärmeleitpad, unten der Rohrrundung angepasst
    pad = box(-PAD_A / 2, r - 0.6, -PAD_A / 2, PAD_A, 0.6 + PAD_EINGEBAUT, PAD_A)
    teile["pad"] = (pad.cut(zyl_z(0, 0, -5, r, 10)), "pad")
    teile["platine"] = (box(-KNOTEN_L / 2, yb, -KNOTEN_B / 2, KNOTEN_L, PCB_T, KNOTEN_B), "fr4")
    # TO-92, flache Seite auf dem Rohr
    rund = zyl_z(0, ys + 1.25, -2.5, 2.45, 5.0)
    teile["to92"] = (rund.intersect(box(-2.4, ys, -2.5, 4.8, TO92_H, 5.0)), "schwarz")
    beine = None
    for x in (-1.27, 0.0, 1.27):
        b = box(x - 0.22, ys + 0.9, 2.5, 0.44, 0.44, 1.8).union(box(x - 0.22, ys + 0.9, 4.0, 0.44, yb - ys - 0.9, 0.44))
        beine = b if beine is None else beine.union(b)
    teile["beine"] = (beine, "zinn")
    # Buchsen gewinkelt, Öffnung nach außen
    yt = yb + PCB_T
    teile["j1"] = (box(-KNOTEN_L / 2, yt, -PH_B / 2, PH_T, PH_H, PH_B), "jst")
    teile["j2"] = (box(KNOTEN_L / 2 - PH_T, yt, -PH_B / 2, PH_T, PH_H, PH_B), "jst")
    if mit_steckern:
        for name, x0, sgn in (("s1", -KNOTEN_L / 2 - PHR_L + 1.0, -1), ("s2", KNOTEN_L / 2 - 1.0, 1)):
            teile[name] = (box(x0, yt + 0.3, -PH_B / 2 + 0.2, PHR_L, PHR_H, PH_B - 0.4), "jst")
    return teile


# --------------------------------------------------------------------------
# Basisplatine + Olimex
# --------------------------------------------------------------------------
LOECHER_OLI = [(2.56, 27.48), (25.42, 27.48), (7.64, 95.42)]
LOECHER_BASIS = [(2.56, 27.48), (25.42, 27.48), (35.0, 27.0), (35.0, 59.0)]
J_POS = {"j1": 32.0, "j2": 46.0}   # y-Anfang der Buchsen (Kette A, Kette B)


def basisplatine():
    x0, y0, x1, y1 = BASIS
    teile = {}
    p = box(x0, y0, 0, x1 - x0, y1 - y0, PCB_T)
    for (x, y) in LOECHER_BASIS:
        p = p.cut(zyl_z(x, y, -1, 1.1, PCB_T + 2))
    teile["basis"] = (p, "fr4")
    ylen = 9 * PITCH + PITCH
    for name, x in (("buchse1", EXT1_X), ("buchse2", EXT2_X)):
        b = box(x - PITCH / 2, EXT_Y0 - PITCH / 2, PCB_T, PITCH, ylen, BUCHSE_H)
        for i in range(10):
            b = b.cut(box(x - 0.45, EXT_Y0 + i * PITCH - 0.45, PCB_T + BUCHSE_H - 3, 0.9, 0.9, 3.1))
        teile[name] = (b, "schwarz")
    # Widerstände 0207 liegend, Keramikkondensator
    teile["r1"] = (zyl_x(9.0, 41.0, PCB_T + 1.3, 1.25, 6.3), "widerstand")
    teile["r2"] = (zyl_x(9.0, 47.0, PCB_T + 1.3, 1.25, 6.3), "widerstand")
    teile["c1"] = (box(10.0, 35.5, PCB_T, 4.5, 2.5, 4.5).edges("|Y").fillet(1.0), "kondensator")
    # Buchsen gewinkelt am rechten Rand
    for name, y in J_POS.items():
        teile[name] = (box(x1 - PH_T, y, PCB_T, PH_T, PH_B, PH_H), "jst")
    # Abstandsbolzen M2 zwischen den Platinen
    for i, (x, y) in enumerate(LOECHER_OLI[:2]):
        teile[f"bolzen{i}"] = (cq.Workplane("XY").polygon(6, 4.0).extrude(Z_OLI - PCB_T).translate((x, y, PCB_T)), "nylon")
    return teile


def stecker_basis():
    x1 = BASIS[2]
    teile = {}
    for name, y in J_POS.items():
        teile["st_" + name] = (box(x1 - 1.0, y + 0.2, PCB_T + 0.3, PHR_L, PH_B - 0.4, PHR_H), "jst")
    return teile


def olimex():
    teile = {}
    p = box(0, 0, Z_OLI, OLI_B, OLI_L, PCB_T)
    for (x, y) in LOECHER_OLI:
        p = p.cut(zyl_z(x, y, Z_OLI - 1, 1.1, PCB_T + 2))
    teile["oli_pcb"] = (p, "olimex")
    zt = Z_OLI + PCB_T
    teile["oli_modul"] = (box(5.0, 0.6, zt, 18.0, 25.5, 3.1), "blech")
    teile["oli_rj45"] = (box(11.05, 77.7, zt, 16.0, 21.2, 13.4), "blech")
    teile["oli_usb"] = (box(-0.6, 62.65 - 3.75, zt, 5.0, 7.5, 2.6), "blech")
    # Stiftleisten auf der Unterseite (Kunststoff + Pins)
    ylen = 10 * PITCH
    for name, x in (("stift1", EXT1_X), ("stift2", EXT2_X)):
        teile[name] = (box(x - PITCH / 2, EXT_Y0 - PITCH / 2, Z_OLI - STIFT_KUNSTSTOFF, PITCH, ylen, STIFT_KUNSTSTOFF), "schwarz")
        pins = None
        for i in range(10):
            q = box(x - 0.32, EXT_Y0 + i * PITCH - 0.32, PCB_T + BUCHSE_H - 6.0, 0.64, 0.64, 6.0)
            pins = q if pins is None else pins.union(q)
        teile[name + "_pins"] = (pins, "gold")
    return teile


def als_compound(teile):
    return cq.Compound.makeCompound([w.val() for (w, _) in teile.values()])


def distanzhuelse(h=Z_OLI - PCB_T, d_aussen=5.0, d_innen=2.4):
    """Distanzhülse zwischen Basisplatine und Olimex (M2-Schraube durch)."""
    return zyl_z(0, 0, 0, d_aussen / 2, h).cut(zyl_z(0, 0, -1, d_innen / 2, h + 2))


def druckausrichtung(clip):
    """Clip mit der Rastnasen-Seite aufs Druckbett legen (+y zeigt nach unten).
    So druckt er ohne Stützmaterial: Nasen liegen auf dem Bett, der Sattel
    überbrückt 10 mm, der Ring wächst als Bogen mit Überhängen unter 45°."""
    c = clip.rotate((0, 0, 0), (1, 0, 0), -90)
    bb = c.val().BoundingBox()
    return c.translate((-bb.center.x, -bb.center.y, -bb.zmin))


def name_d(d):
    return f"{d:.1f}".replace(".", "_").replace("_0", "")


if __name__ == "__main__":
    import os
    os.makedirs("export", exist_ok=True)
    varianten = {"rohrclip_abgang": (ROHR_D, CLIP_LAENGE), "rohrclip_balken": (BALKEN_D, BALKEN_LAENGE)}
    if len(sys.argv) > 1:                       # eigener Durchmesser: python fbh_cad.py 20.0
        varianten = {"rohrclip": (float(sys.argv[1]), CLIP_LAENGE)}
    for basis, (d, laenge) in varianten.items():
        clip = rohrclip(d, laenge=laenge)
        n = f"{basis}_D{name_d(d)}"
        cq.exporters.export(clip, f"export/{n}.step")
        cq.exporters.export(druckausrichtung(clip), f"export/{n}_druck.stl", tolerance=0.02, angularTolerance=0.1)
    cq.exporters.export(distanzhuelse(), "export/distanzhuelse_11mm.stl", tolerance=0.01, angularTolerance=0.1)
    cq.exporters.export(cq.Workplane().add(als_compound(fuehlerknoten(mit_steckern=False))), "export/fuehlerknoten.step")
    modul = {**basisplatine(), **olimex()}
    cq.exporters.export(cq.Workplane().add(als_compound(modul)), "export/modul_baugruppe.step")
    print("Export fertig:", sorted(os.listdir("export")))
