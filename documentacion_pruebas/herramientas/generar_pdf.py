"""Convierte el informe de auditoría (Markdown sencillo) en PDF con reportlab.

Uso: python generar_pdf.py entrada.md salida.pdf "Informe N.º 001" "27/09/2026"
     [--titulo "..."] [--subtitulo "..."] [--alcance "..."] [--autoria "..."]
Sin opciones usa la portada del informe de auditoría.
Soporta: # títulos, párrafos, **negrita**, `código`, listas, tablas con |,
bloques ``` , imágenes ![alt](ruta), líneas --- y saltos de página <<<PAGINA>>>.
"""
import os
import re
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, LongTable, PageBreak,
    PageTemplate, Paragraph, Preformatted, Spacer, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

FUENTES = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", FUENTES + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DV-B", FUENTES + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DVM", FUENTES + "DejaVuSansMono.ttf"))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV", boldItalic="DV-B")

AZUL = colors.HexColor("#1d3557")
AZUL_CLARO = colors.HexColor("#e8eef6")
GRIS = colors.HexColor("#555555")

EMOJIS = {
    "🟢": '<font color="#1a8f3c">●</font>',
    "🟡": '<font color="#c9a400">●</font>',
    "🟠": '<font color="#e06c00">●</font>',
    "🔴": '<font color="#c62828">●</font>',
    "⚫": '<font color="#333333">●</font>',
    "✅": '<font color="#1a8f3c">✔</font>',
    "❌": '<font color="#c62828">✘</font>',
    "⚠️": "⚠", "⚠": "⚠",
}

base = getSampleStyleSheet()
E = {
    "normal": ParagraphStyle("n", parent=base["Normal"], fontName="DV", fontSize=9.5, leading=13.5, spaceAfter=5),
    "celda": ParagraphStyle("c", parent=base["Normal"], fontName="DV", fontSize=7.3, leading=9.2),
    "celda_cab": ParagraphStyle("cc", parent=base["Normal"], fontName="DV-B", fontSize=7.3, leading=9.2, textColor=colors.white),
    "lista": ParagraphStyle("l", parent=base["Normal"], fontName="DV", fontSize=9.5, leading=13, leftIndent=14, bulletIndent=4, spaceAfter=2),
    "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="DV-B", fontSize=16, leading=20, textColor=AZUL, spaceBefore=6, spaceAfter=10),
    "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="DV-B", fontSize=12.5, leading=16, textColor=AZUL, spaceBefore=10, spaceAfter=6),
    "h3": ParagraphStyle("h3", parent=base["Heading3"], fontName="DV-B", fontSize=10.5, leading=14, textColor=colors.black, spaceBefore=8, spaceAfter=4),
    "codigo": ParagraphStyle("code", parent=base["Code"], fontName="DVM", fontSize=7.2, leading=9, backColor=colors.HexColor("#f4f4f4"), borderPadding=4, spaceAfter=6),
    "portada_t": ParagraphStyle("pt", fontName="DV-B", fontSize=22, leading=28, alignment=TA_CENTER, textColor=AZUL),
    "portada_s": ParagraphStyle("ps", fontName="DV", fontSize=12, leading=17, alignment=TA_CENTER, textColor=GRIS),
    "toc1": ParagraphStyle("t1", fontName="DV-B", fontSize=10, leading=14, leftIndent=0),
    "toc2": ParagraphStyle("t2", fontName="DV", fontSize=9, leading=12, leftIndent=14),
}


def en_linea(texto):
    """Convierte el formato en línea de Markdown a marcas de reportlab."""
    texto = texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    texto = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", texto)
    texto = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", texto)
    # El código se aparta primero para que ** y * no se crucen con sus etiquetas.
    codigos = []

    def apartar(m):
        codigos.append(m.group(1).replace("*", "&#42;"))
        return f"\x01{len(codigos) - 1}\x01"

    texto = re.sub(r"`([^`]+)`", apartar, texto)
    texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
    texto = re.sub(r"(?<![\w*])\*(?!\s)([^*]+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", texto)
    texto = texto.replace("*", "&#42;")
    texto = re.sub(
        "\x01(\\d+)\x01",
        lambda m: f'<font name="DVM" size="8">{codigos[int(m.group(1))]}</font>',
        texto
    )
    for emoji, reemplazo in EMOJIS.items():
        texto = texto.replace(emoji, reemplazo)
    # Quitar emojis restantes que DejaVu no dibuja.
    texto = re.sub("[\U0001F000-\U0001FAFF✀-➿️⏸-⏺]", "", texto)
    return texto


def tabla(filas, ancho):
    celdas = [[c.strip() for c in f.strip().strip("|").split("|")] for f in filas]
    celdas = [f for f in celdas if not all(re.fullmatch(r":?-{2,}:?", c or "--") for c in f)]
    n = max(len(f) for f in celdas)
    celdas = [f + [""] * (n - len(f)) for f in celdas]
    largos = [max(8, min(60, max(len(f[i]) for f in celdas))) for i in range(n)]
    total = sum(largos)
    anchos = [ancho * l / total for l in largos]
    datos = [
        [Paragraph(en_linea(c), E["celda_cab"] if i == 0 else E["celda"]) for c in f]
        for i, f in enumerate(celdas)
    ]
    t = LongTable(datos, colWidths=anchos, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, AZUL_CLARO]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#b0b8c4")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


class Documento(BaseDocTemplate):
    def __init__(self, salida, titulo_pie, **kw):
        super().__init__(salida, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm,
                         topMargin=2 * cm, bottomMargin=1.8 * cm, **kw)
        self.titulo_pie = titulo_pie
        marco = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate(id="p", frames=[marco], onPage=self.pie)])

    def pie(self, canvas, doc):
        if doc.page == 1:
            return
        canvas.saveState()
        canvas.setFont("DV", 7.5)
        canvas.setFillColor(GRIS)
        canvas.drawString(self.leftMargin, 1.1 * cm, self.titulo_pie)
        canvas.drawRightString(A4[0] - self.rightMargin, 1.1 * cm, f"Página {doc.page}")
        canvas.setStrokeColor(AZUL)
        canvas.line(self.leftMargin, A4[1] - 1.4 * cm, A4[0] - self.rightMargin, A4[1] - 1.4 * cm)
        canvas.restoreState()

    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style.name in ("h1", "h2"):
            nivel = 0 if f.style.name == "h1" else 1
            texto = f.getPlainText()
            clave = f"h{id(f)}"
            self.canv.bookmarkPage(clave)
            self.canv.addOutlineEntry(texto, clave, level=nivel)
            self.notify("TOCEntry", (nivel, texto, self.page, clave))


PORTADA_AUDITORIA = {
    "titulo": "INFORME FINAL DE AUDITORÍA Y PRUEBAS",
    "subtitulo": "YURA — Robot interactivo para la práctica del idioma quechua",
    "alcance": "Alcance: cerebro del robot (Python), base de datos SQLite, pantalla web local,<br/>"
               "plataforma web Laravel (revisión estática) y documento de tesis (agosto 2026)",
    "autoria": "Auditoría realizada con Claude Code (7 subagentes especializados)<br/>"
               "para el equipo del proyecto YURA — Cochabamba, Bolivia",
    "pie": "Auditoría técnica y de pruebas",
}


def convertir(md, salida, numero, fecha, base_dir, portada=None):
    portada = {**PORTADA_AUDITORIA, **(portada or {})}
    lineas = open(md, encoding="utf-8").read().splitlines()
    doc = Documento(salida, f"YURA · {numero} · {portada['pie']} · {fecha}",
                    title=f"{numero} — {portada['titulo'].capitalize()}", author="Preparado con Claude Code para el equipo YURA")
    ancho = doc.width
    h = []

    # Portada
    h += [Spacer(1, 5 * cm),
          Paragraph(portada["titulo"], E["portada_t"]), Spacer(1, 0.5 * cm),
          Paragraph(portada["subtitulo"], E["portada_s"]),
          Spacer(1, 1.2 * cm),
          Paragraph(f"<b>{numero}</b> · {fecha}", E["portada_s"]), Spacer(1, 0.4 * cm),
          Paragraph(portada["alcance"], E["portada_s"]),
          Spacer(1, 3 * cm),
          Paragraph(portada["autoria"], E["portada_s"]),
          PageBreak()]
    toc = TableOfContents()
    toc.levelStyles = [E["toc1"], E["toc2"]]
    h += [Paragraph("Índice", ParagraphStyle("indice", parent=E["h1"])), toc, PageBreak()]

    i = 0
    while i < len(lineas):
        l = lineas[i]
        s = l.strip()
        if s == "<<<PAGINA>>>":
            h.append(PageBreak()); i += 1; continue
        if s.startswith("```"):
            bloque = []
            i += 1
            while i < len(lineas) and not lineas[i].strip().startswith("```"):
                bloque.append(lineas[i]); i += 1
            h.append(Preformatted("\n".join(bloque), E["codigo"], maxLineLength=110))
            i += 1; continue
        if s.startswith("|"):
            filas = []
            while i < len(lineas) and lineas[i].strip().startswith("|"):
                filas.append(lineas[i]); i += 1
            h += [tabla(filas, ancho), Spacer(1, 6)]
            continue
        m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", s)
        if m:
            ruta = m.group(2) if os.path.isabs(m.group(2)) else os.path.join(base_dir, m.group(2))
            if os.path.exists(ruta):
                img = Image(ruta)
                escala = min(ancho / img.imageWidth, 9 * cm / img.imageHeight, 1)
                img.drawWidth, img.drawHeight = img.imageWidth * escala, img.imageHeight * escala
                h.append(KeepTogether([img, Paragraph(f"<i>{en_linea(m.group(1))}</i>", E["celda"]), Spacer(1, 6)]))
            else:
                h.append(Paragraph(f"[Imagen no encontrada: {en_linea(m.group(2))}]", E["celda"]))
            i += 1; continue
        if s.startswith("#### "):
            h.append(Paragraph(en_linea(s[5:]), E["h3"]))
        elif s.startswith("### "):
            h.append(Paragraph(en_linea(s[4:]), E["h3"]))
        elif s.startswith("## "):
            h.append(Paragraph(en_linea(s[3:]), E["h2"]))
        elif s.startswith("# "):
            h.append(Paragraph(en_linea(s[2:]), E["h1"]))
        elif re.match(r"^[-*] ", s):
            sangria = (len(l) - len(l.lstrip())) // 2
            estilo = ParagraphStyle("li", parent=E["lista"], leftIndent=14 + 12 * sangria, bulletIndent=4 + 12 * sangria)
            h.append(Paragraph(en_linea(s[2:]), estilo, bulletText="•"))
        elif re.match(r"^\d+[.)] ", s):
            num, resto = s.split(" ", 1)
            h.append(Paragraph(en_linea(resto), E["lista"], bulletText=num))
        elif s.startswith(">"):
            h.append(Paragraph(en_linea(s.lstrip("> ")), ParagraphStyle("q", parent=E["normal"], leftIndent=12, textColor=GRIS)))
        elif s in ("---", "***"):
            h.append(Spacer(1, 8))
        elif s:
            parrafo = [s]
            while i + 1 < len(lineas) and lineas[i + 1].strip() and not re.match(r"^(#|\||[-*] |\d+[.)] |```|>|!\[|<<<)", lineas[i + 1].strip()):
                i += 1; parrafo.append(lineas[i].strip())
            h.append(Paragraph(en_linea(" ".join(parrafo)), E["normal"]))
        i += 1

    doc.multiBuild(h)


if __name__ == "__main__":
    import argparse
    lector = argparse.ArgumentParser()
    lector.add_argument("entrada")
    lector.add_argument("salida")
    lector.add_argument("numero")
    lector.add_argument("fecha")
    for opcion in ("titulo", "subtitulo", "alcance", "autoria", "pie"):
        lector.add_argument(f"--{opcion}")
    args = lector.parse_args()
    portada = {
        clave: valor for clave in ("titulo", "subtitulo", "alcance", "autoria", "pie")
        if (valor := getattr(args, clave))
    }
    convertir(args.entrada, args.salida, args.numero, args.fecha,
              os.path.dirname(os.path.abspath(args.entrada)), portada)
    print("PDF generado:", args.salida)
