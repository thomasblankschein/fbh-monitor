"""Renderings der CAD-Modelle (Offscreen mit PyVista/VTK).
Aufruf: pip install cadquery pyvista && python cad/render_ansichten.py
Ausgabe: cad/renders/*.png
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pyvista as pv
import cadquery as cq
import fbh_cad as F

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders")
os.makedirs(OUT, exist_ok=True)

FARBEN = {
    "fr4": "#cdbf7a", "olimex": "#2f5e45", "schwarz": "#26282b", "zinn": "#b9bec4",
    "jst": "#efe7d2", "widerstand": "#8fb3dc", "kondensator": "#d98b2b", "nylon": "#f4f4ef",
    "blech": "#c3c8cd", "gold": "#d8b44a", "clip": "#3e454c", "rohr": "#c8452c",
    "pad": "#7fb7d6", "ader_gnd": "#1d1d1d", "ader_dq": "#e8c22c", "ader_vdd": "#c8312b",
}


def mesh(shape, tol=0.03):
    s = shape.val() if hasattr(shape, "val") else shape
    if isinstance(s, cq.Workplane):
        s = s.val()
    verts, tris = s.tessellate(tol, 0.2)
    pts = np.array([(v.x, v.y, v.z) for v in verts])
    faces = np.hstack([[3, *t] for t in tris])
    return pv.PolyData(pts, faces)


def plotter(size=(1600, 1200)):
    p = pv.Plotter(off_screen=True, window_size=size)
    p.set_background("#f3f5f6")
    p.enable_anti_aliasing("ssaa")
    return p


def add(p, shape, farbe, **kw):
    m = mesh(shape)
    p.add_mesh(m, color=FARBEN.get(farbe, farbe), smooth_shading=False,
               specular=0.25, specular_power=20, ambient=0.18, diffuse=0.85, **kw)
    # Kanten leicht betonen
    e = m.extract_feature_edges(feature_angle=35, boundary_edges=False, non_manifold_edges=False, manifold_edges=False)
    if e.n_points:
        p.add_mesh(e, color="#1b1f22", line_width=1.2, opacity=0.35)


def adern(p, x0, x1, y, z_mitte, sgn_z=1):
    for dz, farbe in ((-2.0, "ader_gnd"), (0.0, "ader_dq"), (2.0, "ader_vdd")):
        z = z_mitte + dz * sgn_z
        a, b = (x0, y, z), (x1, y, z)
        line = pv.Line(a, b)
        p.add_mesh(line.tube(radius=0.55, n_sides=16), color=FARBEN[farbe], smooth_shading=True, specular=0.3)


def save(p, name):
    p.screenshot(os.path.join(OUT, name))
    p.close()
    print("ok", name)


# ---------------------------------------------------------------- 1 Basisplatine
basis = F.basisplatine()
st = F.stecker_basis()
p = plotter()
for k, (w, c) in basis.items():
    if not k.startswith("bolzen"):
        add(p, w, c)
for k, (w, c) in st.items():
    add(p, w, c)
yc = {"j1": F.J_POS["j1"] + F.PH_B / 2, "j2": F.J_POS["j2"] + F.PH_B / 2}
for j, y in yc.items():
    for dy, farbe in ((-2.0, "ader_gnd"), (0.0, "ader_dq"), (2.0, "ader_vdd")):
        line = pv.Line((F.BASIS[2] + 5.0, y + dy, F.PCB_T + 2.4), (F.BASIS[2] + 22, y + dy * 1.4, F.PCB_T + 2.4))
        p.add_mesh(line.tube(radius=0.55, n_sides=16), color=FARBEN[farbe], smooth_shading=True)
p.camera_position = [(-40, -45, 75), (22, 43, 3), (0, 0, 1)]
p.camera.zoom(1.15)
save(p, "1_basisplatine.png")

# ---------------------------------------------------------------- 2 Gesamtaufbau
oli = F.olimex()
p = plotter()
for k, (w, c) in {**basis, **oli, **st}.items():
    add(p, w, c)
for j, y in yc.items():
    for dy, farbe in ((-2.0, "ader_gnd"), (0.0, "ader_dq"), (2.0, "ader_vdd")):
        line = pv.Line((F.BASIS[2] + 5.0, y + dy, F.PCB_T + 2.4), (F.BASIS[2] + 26, y + dy * 1.4, F.PCB_T + 2.4))
        p.add_mesh(line.tube(radius=0.55, n_sides=16), color=FARBEN[farbe], smooth_shading=True)
p.camera_position = [(95, -60, 85), (18, 50, 8), (0, 0, 1)]
p.camera.zoom(1.05)
save(p, "2_gesamtaufbau.png")

p = plotter((1600, 900))
for k, (w, c) in {**basis, **oli, **st}.items():
    add(p, w, c)
p.camera_position = [(170, 43, 10), (14, 49, 10), (0, 0, 1)]
p.camera.zoom(1.5)
save(p, "3_gesamtaufbau_seite.png")

# ---------------------------------------------------------------- 3 Rohrclip
d = F.ROHR_D
clip = F.rohrclip(d)
knoten = F.fuehlerknoten(d)
rohr = F.zyl_z(0, 0, -30, d / 2, 60).cut(F.zyl_z(0, 0, -31, d / 2 - 2.0, 62))


def szene_clip(p, dx=0.0, mit_rohr=True, mit_knoten=True):
    t = (dx, 0, 0)
    if mit_rohr:
        add(p, rohr.translate(t), "rohr")
    add(p, clip.translate(t), "clip")
    if mit_knoten:
        for k, (w, c) in knoten.items():
            add(p, w.translate(t), c)


p = plotter()
szene_clip(p)
yb = F.knoten_yb(d / 2)
ys = yb + F.PCB_T + 0.3 + F.PHR_H / 2
adern(p, -F.KNOTEN_L / 2 - F.PHR_L + 1.0, -40, ys, 0)
adern(p, F.KNOTEN_L / 2 + F.PHR_L - 1.0, 40, ys, 0)
p.camera_position = [(55, 70, 45), (0, 6, 0), (0, 0, 1)]
p.camera.zoom(1.25)
save(p, "4_rohrclip_mit_knoten.png")

p = plotter()
szene_clip(p, mit_rohr=False, mit_knoten=False)
p.camera_position = [(45, 30, 55), (0, 4, 0), (0, 0, 1)]
p.camera.zoom(1.1)
save(p, "5_rohrclip_leer.png")

# Ansicht entlang Rohrachse
p = plotter((1400, 1200))
szene_clip(p)
p.camera_position = [(0, 4, 120), (0, 4, 0), (0, 1, 0)]
p.enable_parallel_projection()
p.camera.zoom(1.6)
save(p, "6_rohrclip_stirnseite.png")

# ---------------------------------------------------------------- 4 Kette an drei Rohren
p = plotter((1800, 1100))
pitch = 50.0
for i in range(3):
    szene_clip(p, dx=i * pitch)
for i in range(2):
    x0 = i * pitch + F.KNOTEN_L / 2 + F.PHR_L - 1.0
    x1 = (i + 1) * pitch - F.KNOTEN_L / 2 - F.PHR_L + 1.0
    adern(p, x0, x1, ys, 0)
adern(p, -F.KNOTEN_L / 2 - F.PHR_L + 1.0, -30, ys, 0)
p.camera_position = [(110, 260, 120), (50, 6, 0), (0, 0, 1)]
p.enable_parallel_projection()
p.camera.zoom(1.9)
save(p, "7_kette.png")

# ---------------------------------------------------------------- 5 Fühlerknoten von unten
p = plotter((1600, 1000))
for k, (w, c) in F.fuehlerknoten(d, mit_steckern=False).items():
    add(p, w, c)
p.camera_position = [(-30, -25, -45), (0, yb, 0), (0, 1, 0)]
p.camera.zoom(1.3)
save(p, "8_fuehlerknoten_unten.png")

# ---------------------------------------------------------------- 6 Balkenclip
db = F.BALKEN_D
clip_b = F.rohrclip(db, laenge=F.BALKEN_LAENGE)
knoten_b = F.fuehlerknoten(db)
band = F.zyl_z(0, 0, -8, db / 2, 16)
p = plotter()
add(p, band, "#c9a24a")
add(p, clip_b, "clip")
for k, (w, c) in knoten_b.items():
    add(p, w, c)
ybb = F.knoten_yb(db / 2) + F.PCB_T + 0.3 + F.PHR_H / 2
adern(p, -F.KNOTEN_L / 2 - F.PHR_L + 1.0, -38, ybb, 0)
adern(p, F.KNOTEN_L / 2 + F.PHR_L - 1.0, 38, ybb, 0)
p.camera_position = [(95, 55, 38), (0, 9, 0), (0, 1, 0)]
p.camera.zoom(1.2)
save(p, "9_balkenclip.png")

# ---------------------------------------------------------------- 7 Druckausrichtung
p = plotter((1600, 1000))
bett = F.box(-45, -25, -1.0, 90, 50, 1.0)
add(p, bett, "#5b6066")
add(p, F.druckausrichtung(F.rohrclip(F.ROHR_D)).translate((-18, 0, 0)), "clip")
add(p, F.druckausrichtung(F.rohrclip(F.BALKEN_D, laenge=F.BALKEN_LAENGE)).translate((20, 0, 0)), "#4f7a9a")
p.camera_position = [(10, -110, 75), (0, 0, 10), (0, 0, 1)]
p.camera.zoom(1.35)
save(p, "10_druckbett.png")

# ---------------------------------------------------------------- 8 Schnitt durch Clip
def add_schnitt(p, shape, farbe):
    m = mesh(shape, tol=0.02)
    try:
        h = m.clip_closed_surface(normal=(0, 0, 1), origin=(0, 0, 0.0))
    except Exception:
        h = m.clip(normal=(0, 0, 1), origin=(0, 0, 0.0))
    if h.n_points == 0:
        return
    p.add_mesh(h, color=FARBEN.get(farbe, farbe), smooth_shading=False, specular=0.2, ambient=0.25, diffuse=0.8)
    e = h.extract_feature_edges(feature_angle=30, boundary_edges=False, non_manifold_edges=False, manifold_edges=False)
    if e.n_points:
        p.add_mesh(e, color="#1b1f22", line_width=1.2, opacity=0.4)

p = plotter((1600, 1300))
add_schnitt(p, rohr, "rohr")
add_schnitt(p, clip, "clip")
for k, (w, c) in F.fuehlerknoten(d, mit_steckern=True).items():
    if k == "beine":
        continue
    add_schnitt(p, w, c)
p.camera_position = [(0, 9, 110), (0, 9, 0), (0, 1, 0)]
p.enable_parallel_projection()
p.camera.zoom(1.45)
save(p, "11_schnitt.png")
