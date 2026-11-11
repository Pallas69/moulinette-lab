"""Génère le manuel PDF depuis docs/manuel-utilisateur.md.

ReportLab est une dépendance optionnelle de maintenance, pas du Lab :
    python -m pip install reportlab
    python tools/generer_guides_themes.py
"""
import html
import re
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
SOURCE = ROOT / 'docs' / 'manuel-utilisateur.md'
OUTPUT = ROOT / 'docs' / 'manuel-utilisateur-v0.32.8.pdf'
ASSET = ROOT / 'moulinette' / 'assets' / 'guide-utilisation.pdf'
pdfmetrics.registerFont(TTFont('LiberationSerif', str(ROOT/'moulinette/assets/LiberationSerif-Regular.ttf')))
pdfmetrics.registerFont(TTFont('LiberationSerif-Bold', str(ROOT/'moulinette/assets/LiberationSerif-Bold.ttf')))
pdfmetrics.registerFont(TTFont('JetBrainsMono', str(ROOT/'moulinette/assets/JetBrainsMono-Regular.ttf')))
pdfmetrics.registerFontFamily('LiberationSerif', normal='LiberationSerif', bold='LiberationSerif-Bold',
                              italic='LiberationSerif', boldItalic='LiberationSerif-Bold')

# Palette Aurore du tableau de bord, utilisée sur toutes les pages du manuel.
BACKGROUND=colors.HexColor('#100e16'); PANEL=colors.HexColor('#211c2e')
INK=colors.HexColor('#f4f1fb'); MUTED=colors.HexColor('#bdb5cb')
PURPLE=colors.HexColor('#c9b8ff'); WHITE=colors.HexColor('#f8f6ff')
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
    text=re.sub(r'`([^`]+)`',lambda m:'<font name="JetBrainsMono" color="#d4c5ff">'+m.group(1)+'</font>',text)
    text=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)
    return text

def footer(canvas, doc):
    w,h=A4
    canvas.saveState()
    canvas.setFillColor(BACKGROUND);canvas.rect(0,0,w,h,fill=1,stroke=0)
    if doc.page==1:
        canvas.setFillColor(colors.HexColor('#201732'));canvas.circle(w+5,h-65,170,fill=1,stroke=0)
        canvas.setStrokeColor(colors.HexColor('#56448d'));canvas.setLineWidth(1)
        canvas.circle(w+5,h-65,210,fill=0,stroke=1);canvas.circle(w+5,h-65,250,fill=0,stroke=1)
        canvas.setFont('LiberationSerif',9);canvas.setFillColor(PURPLE)
        canvas.drawString(2*cm,1.35*cm,'PROTOTYPE LOCAL  ·  CODE DE CONFIANCE UNIQUEMENT')
    else:
        canvas.setStrokeColor(colors.HexColor('#393047'));canvas.line(2*cm,h-1.38*cm,w-2*cm,h-1.38*cm)
        canvas.setFont('LiberationSerif-Bold',9);canvas.setFillColor(PURPLE);canvas.drawString(2*cm,h-1.1*cm,'MOULINETTE LAB')
        canvas.setFont('LiberationSerif',9);canvas.setFillColor(MUTED);canvas.drawRightString(w-2*cm,h-1.1*cm,'GUIDE UTILISATEUR  ·  v0.32.8-dev')
        canvas.setStrokeColor(colors.HexColor('#393047'));canvas.line(2*cm,1.55*cm,w-2*cm,1.55*cm)
        canvas.drawString(2*cm,1.1*cm,'Projet non officiel  ·  Code de confiance uniquement')
        canvas.drawRightString(w-2*cm,1.1*cm,str(doc.page))
    canvas.restoreState()


def code_block(lines, width):
    pre=Preformatted('\n'.join(lines),styles['code'],maxLineLength=120)
    t=Table([[pre]],colWidths=[width],hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PANEL),
                           ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
                           ('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)]))
    return t


def make():
    doc=SimpleDocTemplate(str(OUTPUT),pagesize=A4,leftMargin=2*cm,rightMargin=2*cm,
                          topMargin=1.9*cm,bottomMargin=1.9*cm,
                          title='Moulinette Lab — Guide utilisateur v0.32.8-dev',author='Moulinette Lab',
                          subject='Installation, commandes et limites du prototype local')
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
