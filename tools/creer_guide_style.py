"""Génère le guide de style C, distinct du manuel utilisateur.

ReportLab est une dépendance optionnelle de maintenance, pas du Lab :
    python -m pip install reportlab
    python tools/generer_guides_themes.py
"""
import html
import re
import random
import shutil
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Preformatted,
                                Spacer, PageBreak, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs' / 'guide-style-c.md'
OUTPUT = ROOT / 'docs' / 'guide-style-c-v0.32.8.pdf'
ASSET = ROOT / 'moulinette' / 'assets' / 'guide-style-c.pdf'
pdfmetrics.registerFont(TTFont('LiberationSerif', str(ROOT/'moulinette/assets/LiberationSerif-Regular.ttf')))
pdfmetrics.registerFont(TTFont('LiberationSerif-Bold', str(ROOT/'moulinette/assets/LiberationSerif-Bold.ttf')))
pdfmetrics.registerFont(TTFont('JetBrainsMono', str(ROOT/'moulinette/assets/JetBrainsMono-Regular.ttf')))
pdfmetrics.registerFontFamily('LiberationSerif', normal='LiberationSerif', bold='LiberationSerif-Bold',
                              italic='LiberationSerif', boldItalic='LiberationSerif-Bold')

# Palette corail douce : fort contraste pour le texte, filigranes discrets.
BACKGROUND=colors.HexColor('#f5d8d1'); PANEL=colors.HexColor('#edc1b5')
INK=colors.HexColor('#37242a'); MUTED=colors.HexColor('#67474b')
PURPLE=colors.HexColor('#80303c'); WHITE=colors.HexColor('#37242a')
styles={
 'cover_title': ParagraphStyle('cover_title',fontName='LiberationSerif-Bold',fontSize=40,leading=44,textColor=WHITE,spaceAfter=12),
 'cover_label': ParagraphStyle('cover_label',fontName='LiberationSerif-Bold',fontSize=11,leading=14,textColor=PURPLE,spaceAfter=38),
 'cover_sub': ParagraphStyle('cover_sub',fontName='LiberationSerif-Bold',fontSize=22,leading=28,textColor=WHITE,spaceAfter=15),
 'cover_body': ParagraphStyle('cover_body',fontName='LiberationSerif',fontSize=12,leading=17,textColor=INK,spaceAfter=15),
 'h1': ParagraphStyle('h1',fontName='LiberationSerif-Bold',fontSize=24,leading=29,textColor=INK,spaceAfter=14,keepWithNext=True),
 'h2': ParagraphStyle('h2',fontName='LiberationSerif-Bold',fontSize=14,leading=18,textColor=PURPLE,spaceBefore=10,spaceAfter=6,keepWithNext=True),
 'body': ParagraphStyle('body',fontName='LiberationSerif',fontSize=11,leading=15.5,textColor=INK,spaceAfter=7),
 'bullet': ParagraphStyle('bullet',fontName='LiberationSerif',fontSize=11,leading=15.5,textColor=INK,leftIndent=15,firstLineIndent=-10,spaceAfter=4),
 'code': ParagraphStyle('code',fontName='JetBrainsMono',fontSize=8.2,leading=12.2,textColor=WHITE),
}

def markup(text):
    text=html.escape(text,quote=False)
    text=re.sub(r'`([^`]+)`',lambda m:'<font name="JetBrainsMono" color="#702b3b">'+m.group(1)+'</font>',text)
    text=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)
    return text

def footer(canvas, doc):
    """Décoration déterministe, différente sur chaque page, derrière le texte."""
    w,h=A4
    rng=random.Random(2902+doc.page)
    canvas.saveState()
    canvas.setFillColor(BACKGROUND);canvas.rect(0,0,w,h,fill=1,stroke=0)
    # Arcs et disques proches des coins : variation stable d'une page à l'autre.
    corner = rng.choice(('top_right','bottom_left','bottom_right')) if doc.page>1 else 'top_right'
    if corner=='top_right':
        cx,cy=w+rng.randint(-10,35),h+rng.randint(-120,-45)
    elif corner=='bottom_left':
        cx,cy=rng.randint(-80,-25),rng.randint(55,165)
    else:
        cx,cy=w+rng.randint(15,70),rng.randint(70,180)
    radius=rng.randint(75,115)
    canvas.setFillColor(colors.HexColor('#f0c5bb'))
    canvas.circle(cx,cy,radius,fill=1,stroke=0)
    canvas.setStrokeColor(colors.HexColor('#e2a99e'));canvas.setLineWidth(0.9)
    for step in (28,57,87):canvas.circle(cx,cy,radius+step,fill=0,stroke=1)
    # Glyphes de code en fond : symboles purs sans contenu personnel, disposés
    # différemment et coloriés très légèrement pour ne pas gêner la lecture.
    glyphs=['</>','$','&','#','*'];rng.shuffle(glyphs)
    spots=[(w*.74,h*.72),(w*.84,h*.45),(w*.66,h*.20),(w*.13,h*.31)]
    rng.shuffle(spots)
    canvas.setFillColor(colors.HexColor('#edbeb5'))
    for symbol,(x,y) in zip(glyphs[:4],spots):
        canvas.saveState();canvas.translate(x+rng.randint(-15,15),y+rng.randint(-20,20))
        canvas.rotate(rng.choice((-15,-8,0,8,15)))
        canvas.setFont('JetBrainsMono',rng.choice((32,40,48)))
        canvas.drawString(0,0,symbol);canvas.restoreState()
    # Détails graphiques légers : petits points et un losange ouvert.
    canvas.setStrokeColor(colors.HexColor('#dfa599'));canvas.setFillColor(colors.HexColor('#dfa599'))
    x=w-rng.randint(38,65);y=h*rng.uniform(.25,.65)
    for i in range(3):canvas.circle(x,y+i*8,1.15,fill=1,stroke=0)
    canvas.saveState();canvas.translate(rng.randint(24,42),h*rng.uniform(.37,.75));canvas.rotate(45)
    canvas.rect(-4,-4,8,8,stroke=1,fill=0);canvas.restoreState()
    if doc.page==1:
        canvas.setFont('LiberationSerif',9);canvas.setFillColor(PURPLE)
        canvas.drawString(2*cm,1.35*cm,'PROTOTYPE LOCAL  ·  CODE DE CONFIANCE UNIQUEMENT')
    else:
        canvas.setStrokeColor(colors.HexColor('#cc9087'));canvas.line(2*cm,h-1.38*cm,w-2*cm,h-1.38*cm)
        canvas.setFont('LiberationSerif-Bold',9);canvas.setFillColor(PURPLE);canvas.drawString(2*cm,h-1.1*cm,'MOULINETTE LAB')
        canvas.setFont('LiberationSerif',9);canvas.setFillColor(MUTED);canvas.drawRightString(w-2*cm,h-1.1*cm,'GUIDE STYLE C  ·  v0.32.8-dev')
        canvas.setStrokeColor(colors.HexColor('#cc9087'));canvas.line(2*cm,1.55*cm,w-2*cm,1.55*cm)
        canvas.drawString(2*cm,1.1*cm,'Projet non officiel  ·  Code de confiance uniquement')
        canvas.drawRightString(w-2*cm,1.1*cm,str(doc.page))
    canvas.restoreState()


def code_block(lines, width):
    pre=Preformatted('\n'.join(lines).expandtabs(4),styles['code'],maxLineLength=120)
    t=Table([[pre]],colWidths=[width],hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PANEL),
                           ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
                           ('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)]))
    return t


def make():
    doc=SimpleDocTemplate(str(OUTPUT),pagesize=A4,leftMargin=2*cm,rightMargin=2*cm,
                          topMargin=1.9*cm,bottomMargin=1.9*cm,
                          title='Moulinette Lab — Guide style C v0.32.8-dev',author='Moulinette Lab',
                          subject='Coding style C et Norminette adaptée')
    flow=[Spacer(1,2.4*cm)];cover=True;code=False;block=[];paragraph=[];lines=SOURCE.read_text(encoding='utf-8').splitlines()
    def flush_paragraph():
        if paragraph:
            flow.append(Paragraph(markup(' '.join(paragraph)),styles['cover_body' if cover else 'body']))
            paragraph.clear()
    for raw in lines:
        line=raw.rstrip()
        if line.startswith('```'):
            flush_paragraph()
            if code:
                flow.append(code_block(block,doc.width));flow.append(Spacer(1,8));block=[];code=False
            else:code=True
            continue
        if code:
            block.append(line);continue
        if line=='<!-- pagebreak -->':
            flush_paragraph();flow.append(PageBreak());cover=False;continue
        if not line:
            flush_paragraph();continue
        if line.startswith('# '):
            flush_paragraph();flow.append(Paragraph(markup(line[2:]),styles['cover_title' if cover else 'h1']));continue
        if cover and line.startswith('GUIDE UTILISATEUR'):
            flush_paragraph();flow.append(Paragraph(markup(line),styles['cover_label']));continue
        if line.startswith('## '):
            flush_paragraph();flow.append(Paragraph(markup(line[3:]),styles['cover_sub' if cover else 'h2']));continue
        if line.startswith('- '):
            flush_paragraph();flow.append(Paragraph('•  '+markup(line[2:]),styles['bullet']));continue
        paragraph.append(line)
    flush_paragraph()
    if code:raise ValueError('Bloc de commande non fermé')
    doc.build(flow,onFirstPage=footer,onLaterPages=footer)
    shutil.copyfile(OUTPUT,ASSET)
    print('Créé :',OUTPUT,'et',ASSET)

if __name__=='__main__':
    raise SystemExit('Moteur interne : utiliser python3 tools/generer_guides_themes.py pour régénérer les quatre PDF.')
