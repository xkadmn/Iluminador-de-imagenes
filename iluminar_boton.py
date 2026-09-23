# -*- coding: utf-8 -*-
"""
=====================================================================
 ILUMINAR BOTON  (ovalo / rectangulo / redondeado / pincel)
=====================================================================

Que hace:
  Abris tu captura, marcas la zona a iluminar arrastrando el mouse.
  La zona queda nitida con borde verde fino, la nitidez se degrada
  hacia afuera y hay un halo de color alrededor. El resto queda
  borroso. Mientras arrastras ves el contorno al instante (sin lag).

--------------------------------------------------------------------
COMO USARLO
--------------------------------------------------------------------
1) Instala Pillow una vez:   pip install Pillow
2) Pone este archivo junto a tu imagen y escribi su nombre en ARCHIVO.
3) Ejecutalo (doble clic, o  python iluminar_boton.py ).
4) Teclas de modo:  O ovalo   R rectangulo   C cuadrado redondeado   P pincel
   Arrastra para marcar. Z deshacer  B borrar  G/Enter guardar  Esc salir
   +/- grosor del pincel (modo pincel)
   +/- radio de las esquinas (modo cuadrado redondeado, tambien
       mientras arrastras: ves el cambio en vivo)
       0% = esquinas rectas ... 100% = maximo redondeo (circulo/pastilla)
5) Guarda un archivo terminado en "_iluminado.png".

--------------------------------------------------------------------
 OPCIONES DE ESTILO (elegi cambiando estas dos lineas de abajo)
--------------------------------------------------------------------
 HALO        -> color del brillo alrededor de la zona iluminada:
                  "suave"    = blanco calido (apenas amarillo)
                  "amarillo" = amarillo mas marcado
                  "dorado"   = dorado

 HALO_TAMANO -> que tan ancho es ese brillo (igual de difuminado en ambos):
                  "amplio"  = se extiende bastante hacia afuera
                  "angosto" = pegado al borde, mas contenido

 FONDO  -> como se ve el resto de la imagen:
             "claro"  = borroso y aclarado (el de siempre)
             "oscuro" = borroso y oscurecido (resalta mas el boton)
--------------------------------------------------------------------
"""

import math
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageFilter, ImageDraw, ImageChops, ImageTk

# =====================================================================
#  CONFIGURACION
# =====================================================================
ARCHIVO = "captura.png"

# ---- OPCIONES DE ESTILO ----
HALO         = "amarillo"   # COLOR del halo:  "suave" | "amarillo" | "dorado"
HALO_TAMANO  = "amplio"     # ANCHO del halo:  "amplio" | "angosto"
FONDO        = "claro"      # fondo:           "claro" | "oscuro"

# ---- resto del estilo (podes dejarlo asi) ----
DESENFOQUE     = 6
ACLARADO       = 0.42    # fuerza del velo cuando FONDO="claro"
OSCURECIDO     = 0.45    # fuerza del velo cuando FONDO="oscuro"
COLOR_BORDE    = (150, 200, 45)
GROSOR_BORDE   = 2
HALO_ANCHOS    = {"amplio": 35, "angosto": 11}   # cuanto se extiende el halo
HALO_BLUR      = 30                              # difuminado (igual en ambos)
DEGRADE        = 16
NITIDO_CENTRO  = 6
RADIO_ESQUINA  = 14
PINCEL_INICIAL = 30

# ---- modo cuadrado redondeado ----
RADIO_PCT_INICIAL = 30   # radio de esquina inicial, en % (0 = recto, 100 = maximo)
RADIO_PCT_PASO    = 10   # cuanto cambia con cada +/-

# colores de halo disponibles
COLORES_HALO = {
    "suave":    (252, 250, 205),
    "amarillo": (255, 225, 120),
    "dorado":   (240, 190, 70),
}

MAX_ANCHO_VENTANA = 1500
MAX_ALTO_VENTANA  = 800

# =====================================================================
#  EFECTO
# =====================================================================
def radio_desde_pct(caja, pct):
    """Convierte el % elegido en radio en pixeles para esa caja.
    100% = la mitad del lado mas corto (circulo o forma de pastilla)."""
    x0, y0, x1, y1 = caja
    return (pct / 100.0) * min(x1 - x0, y1 - y0) / 2.0


def construir_mascara(marcas, size):
    W, H = size
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for mk in marcas:
        if mk["tipo"] == "ovalo":
            d.ellipse(mk["caja"], fill=255)
        elif mk["tipo"] == "rectangulo":
            d.rounded_rectangle(mk["caja"], radius=RADIO_ESQUINA, fill=255)
        elif mk["tipo"] == "redondeado":
            r = radio_desde_pct(mk["caja"], mk["radio_pct"])
            d.rounded_rectangle(mk["caja"], radius=r, fill=255)
        elif mk["tipo"] == "pincel":
            r = mk["r"]; pts = mk["puntos"]
            for (x, y) in pts:
                d.ellipse((x-r, y-r, x+r, y+r), fill=255)
            for i in range(1, len(pts)):
                d.line((pts[i-1], pts[i]), fill=255, width=int(2*r))
    return m


def aplicar_efecto(original, marcas, halo=None, halo_tamano=None, fondo_estilo=None):
    # si no se pasan, usar los valores por defecto de arriba
    if halo is None: halo = HALO
    if halo_tamano is None: halo_tamano = HALO_TAMANO
    if fondo_estilo is None: fondo_estilo = FONDO

    W, H = original.size
    mask = construir_mascara(marcas, original.size)

    # FONDO segun opcion
    fb = original.filter(ImageFilter.GaussianBlur(DESENFOQUE))
    if fondo_estilo == "oscuro":
        fondo = Image.blend(fb, Image.new("RGB", (W, H), (0, 0, 0)), OSCURECIDO)
    else:
        fondo = Image.blend(fb, Image.new("RGB", (W, H), (255, 255, 255)), ACLARADO)

    # HALO segun opcion
    color_halo = COLORES_HALO.get(halo, COLORES_HALO["suave"])
    ancho_halo = HALO_ANCHOS.get(halo_tamano, HALO_ANCHOS["amplio"])
    halo_m = mask.filter(ImageFilter.MaxFilter(ancho_halo)).filter(ImageFilter.GaussianBlur(HALO_BLUR))
    res = Image.composite(Image.new("RGB", (W, H), color_halo), fondo, halo_m)

    # degrade de nitidez + centro nitido
    res = Image.composite(original, res, mask.filter(ImageFilter.GaussianBlur(DEGRADE)))
    res = Image.composite(original, res, mask.filter(ImageFilter.GaussianBlur(NITIDO_CENTRO)))

    # borde verde fino
    d = ImageDraw.Draw(res)
    for mk in marcas:
        if mk["tipo"] == "ovalo":
            d.ellipse(mk["caja"], outline=COLOR_BORDE, width=GROSOR_BORDE)
        elif mk["tipo"] == "rectangulo":
            d.rounded_rectangle(mk["caja"], radius=RADIO_ESQUINA, outline=COLOR_BORDE, width=GROSOR_BORDE)
        elif mk["tipo"] == "redondeado":
            r = radio_desde_pct(mk["caja"], mk["radio_pct"])
            d.rounded_rectangle(mk["caja"], radius=r, outline=COLOR_BORDE, width=GROSOR_BORDE)
        elif mk["tipo"] == "pincel":
            solo = construir_mascara([mk], original.size)
            grande = solo.filter(ImageFilter.MaxFilter(GROSOR_BORDE*2+1))
            anillo = ImageChops.subtract(grande, solo)
            res = Image.composite(Image.new("RGB", (W, H), COLOR_BORDE), res, anillo)
            d = ImageDraw.Draw(res)
    return res


def _puntos_redondeado(x0, y0, x1, y1, r, pasos=10):
    """Puntos del contorno de un rectangulo redondeado, para dibujarlo
    en el canvas de tkinter (que no tiene esa forma de fabrica)."""
    r = max(0.0, min(r, (x1 - x0) / 2.0, (y1 - y0) / 2.0))
    esquinas = [
        (x1 - r, y0 + r, -90),   # arriba-derecha
        (x1 - r, y1 - r,   0),   # abajo-derecha
        (x0 + r, y1 - r,  90),   # abajo-izquierda
        (x0 + r, y0 + r, 180),   # arriba-izquierda
    ]
    pts = []
    for cx, cy, a0 in esquinas:
        for i in range(pasos + 1):
            a = math.radians(a0 + 90.0 * i / pasos)
            pts += [cx + r * math.cos(a), cy + r * math.sin(a)]
    return pts


# =====================================================================
#  VENTANA
# =====================================================================
def main():
    try:
        original = Image.open(ARCHIVO).convert("RGB")
    except FileNotFoundError:
        print("ERROR: no encuentro '%s'. Revisa el nombre y la carpeta." % ARCHIVO)
        input("Enter para cerrar...")
        return

    W, H = original.size
    escala = min(MAX_ANCHO_VENTANA / W, MAX_ALTO_VENTANA / H, 1.0)
    disp_w, disp_h = int(W * escala), int(H * escala)
    vista = original.resize((disp_w, disp_h))

    estado = {"modo": "ovalo", "pincel": PINCEL_INICIAL,
              "radio_pct": RADIO_PCT_INICIAL, "ultimo": None,
              "arrastrando": False, "ini": None, "puntos_pincel": [],
              "halo": HALO, "halo_tamano": HALO_TAMANO, "fondo": FONDO}
    marcas = []
    preview_ids = []

    root = tk.Tk()
    root.title("Iluminar boton")

    barra = tk.Label(root, text="", anchor="w", font=("Segoe UI", 10))
    barra.pack(fill="x")

    # ---- fila de botones de estilo ----
    panel = tk.Frame(root)
    panel.pack(fill="x", pady=3)

    canvas = tk.Canvas(root, width=disp_w, height=disp_h, cursor="crosshair",
                       highlightthickness=0)
    canvas.pack()

    fondo_tk = ImageTk.PhotoImage(vista)
    img_id = canvas.create_image(0, 0, anchor="nw", image=fondo_tk)
    root.fondo_tk = fondo_tk

    def actualizar_barra():
        nombres = {"ovalo": "OVALO", "rectangulo": "RECTANGULO",
                   "redondeado": "CUADRADO REDONDEADO", "pincel": "PINCEL"}
        t = "  Modo: %s   |   O R C P modo  Z deshacer  B borrar  G/Enter guardar  Esc salir" % (
            nombres[estado["modo"]])
        if estado["modo"] == "pincel":
            t += "   |   pincel %d (+/-)" % estado["pincel"]
        elif estado["modo"] == "redondeado":
            t += "   |   radio esquina %d%% (+/-)" % estado["radio_pct"]
        barra.config(text=t)

    def escalar(mk, f):
        n = {"tipo": mk["tipo"]}
        if mk["tipo"] in ("ovalo", "rectangulo", "redondeado"):
            x0, y0, x1, y1 = mk["caja"]
            n["caja"] = (x0*f, y0*f, x1*f, y1*f)
            if mk["tipo"] == "redondeado":
                n["radio_pct"] = mk["radio_pct"]
        else:
            n["r"] = mk["r"]*f
            n["puntos"] = [(x*f, y*f) for (x, y) in mk["puntos"]]
        return n

    def render_fondo():
        if not marcas:
            canvas.itemconfig(img_id, image=fondo_tk)
            root.fondo_tk = fondo_tk
            return
        prev = aplicar_efecto(vista, [escalar(mk, escala) for mk in marcas],
                              halo=estado["halo"], halo_tamano=estado["halo_tamano"],
                              fondo_estilo=estado["fondo"])
        nueva = ImageTk.PhotoImage(prev)
        canvas.itemconfig(img_id, image=nueva)
        root.fondo_tk = nueva

    def limpiar_preview():
        for pid in preview_ids:
            canvas.delete(pid)
        preview_ids.clear()

    def a_real(x, y):
        return (x/escala, y/escala)

    def dibujar_preview_caja(ex, ey):
        limpiar_preview()
        ix, iy = estado["ini"]
        x0, x1 = sorted((ix, ex)); y0, y1 = sorted((iy, ey))
        if estado["modo"] == "ovalo":
            preview_ids.append(canvas.create_oval(x0, y0, x1, y1, outline=_hex(COLOR_BORDE), width=2))
        elif estado["modo"] == "redondeado":
            r = radio_desde_pct((x0, y0, x1, y1), estado["radio_pct"])
            preview_ids.append(canvas.create_polygon(_puntos_redondeado(x0, y0, x1, y1, r),
                                                     outline=_hex(COLOR_BORDE), fill="", width=2))
        else:
            preview_ids.append(canvas.create_rectangle(x0, y0, x1, y1, outline=_hex(COLOR_BORDE), width=2))

    def presionar(ev):
        estado["arrastrando"] = True
        estado["ini"] = (ev.x, ev.y)
        estado["ultimo"] = (ev.x, ev.y)
        if estado["modo"] == "pincel":
            r = estado["pincel"]
            preview_ids.append(canvas.create_oval(ev.x-r, ev.y-r, ev.x+r, ev.y+r,
                                                  outline=_hex(COLOR_BORDE), width=2))
            estado["puntos_pincel"] = [(ev.x, ev.y)]

    def mover(ev):
        if not estado["arrastrando"]:
            return
        estado["ultimo"] = (ev.x, ev.y)
        if estado["modo"] == "pincel":
            r = estado["pincel"]
            x0, y0 = estado["puntos_pincel"][-1]
            preview_ids.append(canvas.create_line(x0, y0, ev.x, ev.y,
                                                  fill=_hex(COLOR_BORDE), width=max(2, int(r*0.5))))
            estado["puntos_pincel"].append((ev.x, ev.y))
        else:
            dibujar_preview_caja(ev.x, ev.y)

    def soltar(ev):
        if not estado["arrastrando"]:
            return
        estado["arrastrando"] = False
        if estado["modo"] == "pincel":
            pts = [a_real(x, y) for (x, y) in estado.get("puntos_pincel", [])]
            if pts:
                marcas.append({"tipo": "pincel", "r": estado["pincel"]/escala, "puntos": pts})
        else:
            ix, iy = estado["ini"]
            x0, x1 = sorted((ix, ev.x)); y0, y1 = sorted((iy, ev.y))
            if (x1-x0) >= 6 and (y1-y0) >= 6:
                rx0, ry0 = a_real(x0, y0); rx1, ry1 = a_real(x1, y1)
                mk = {"tipo": estado["modo"], "caja": (rx0, ry0, rx1, ry1)}
                if estado["modo"] == "redondeado":
                    mk["radio_pct"] = estado["radio_pct"]
                marcas.append(mk)
        limpiar_preview()
        render_fondo()

    def set_modo(m): estado["modo"] = m; actualizar_barra()
    def deshacer(ev=None):
        if marcas: marcas.pop(); render_fondo()
    def borrar(ev=None):
        marcas.clear(); limpiar_preview(); render_fondo()

    def cambiar_radio(delta):
        estado["radio_pct"] = max(0, min(100, estado["radio_pct"] + delta))
        actualizar_barra()
        # si estas arrastrando, el contorno se actualiza en vivo
        if estado["arrastrando"] and estado["ultimo"]:
            dibujar_preview_caja(*estado["ultimo"])

    def mas(ev=None):
        if estado["modo"] == "redondeado":
            cambiar_radio(+RADIO_PCT_PASO); return
        estado["pincel"] = min(estado["pincel"]+5, 200); actualizar_barra()
    def menos(ev=None):
        if estado["modo"] == "redondeado":
            cambiar_radio(-RADIO_PCT_PASO); return
        estado["pincel"] = max(estado["pincel"]-5, 4); actualizar_barra()
    def guardar(ev=None):
        if not marcas:
            messagebox.showwarning("Nada marcado", "Marca al menos una zona antes de guardar.")
            return
        out = aplicar_efecto(original, marcas,
                             halo=estado["halo"], halo_tamano=estado["halo_tamano"],
                             fondo_estilo=estado["fondo"])
        salida = ARCHIVO.rsplit(".", 1)[0] + "_iluminado.png"
        out.save(salida)
        messagebox.showinfo("Listo", "Guardado como:\n" + salida)
    def salir(ev=None): root.destroy()

    # ---- botones de estilo (dentro del panel de arriba) ----
    OPC_HALO   = ["suave", "amarillo", "dorado"]
    OPC_TAMANO = ["amplio", "angosto"]
    OPC_FONDO  = ["claro", "oscuro"]

    btn_halo   = tk.Button(panel, width=16)
    btn_tamano = tk.Button(panel, width=16)
    btn_fondo  = tk.Button(panel, width=16)

    def refrescar_botones():
        btn_halo.config(text="Halo: %s" % estado["halo"])
        btn_tamano.config(text="Ancho: %s" % estado["halo_tamano"])
        btn_fondo.config(text="Fondo: %s" % estado["fondo"])

    def ciclar(clave, opciones):
        i = opciones.index(estado[clave])
        estado[clave] = opciones[(i + 1) % len(opciones)]
        refrescar_botones()
        render_fondo()   # aplicar el cambio al instante

    btn_halo.config(command=lambda: ciclar("halo", OPC_HALO))
    btn_tamano.config(command=lambda: ciclar("halo_tamano", OPC_TAMANO))
    btn_fondo.config(command=lambda: ciclar("fondo", OPC_FONDO))

    tk.Label(panel, text="Estilo:").pack(side="left", padx=(8, 4))
    btn_halo.pack(side="left", padx=3)
    btn_tamano.pack(side="left", padx=3)
    btn_fondo.pack(side="left", padx=3)
    refrescar_botones()

    canvas.bind("<Button-1>", presionar)
    canvas.bind("<B1-Motion>", mover)
    canvas.bind("<ButtonRelease-1>", soltar)
    for k in ("o","O"): root.bind(k, lambda e: set_modo("ovalo"))
    for k in ("r","R"): root.bind(k, lambda e: set_modo("rectangulo"))
    for k in ("c","C"): root.bind(k, lambda e: set_modo("redondeado"))
    for k in ("p","P"): root.bind(k, lambda e: set_modo("pincel"))
    root.bind("<plus>", mas); root.bind("<equal>", mas); root.bind("<minus>", menos)
    root.bind("<KP_Add>", mas); root.bind("<KP_Subtract>", menos)
    for k in ("z","Z"): root.bind(k, deshacer)
    for k in ("b","B"): root.bind(k, borrar)
    for k in ("g","G"): root.bind(k, guardar)
    root.bind("<Return>", guardar)
    root.bind("<Escape>", salir)

    actualizar_barra()
    root.mainloop()


def _hex(rgb):
    return "#%02x%02x%02x" % rgb


if __name__ == "__main__":
    main()
