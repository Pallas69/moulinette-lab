"""Génère les quatre variantes blanc et Océan à partir des guides éditables."""
import html
import importlib.util
import random
import re
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

PROJECT=Path(__file__).resolve().parents[1]
DEST=PROJECT/'docs'
PALETTES={
    'blanc':dict(background='#ffffff', panel='#f0f7f6',ink='#203237', muted='#50676b',
                 accent='#17636e',inline='#075968',circle='#f1f8f7',rings='#c9e4e0',
                 glyph='#d9ecea',details='#badbd5',rule='#a9d2cc'),
    # Couleurs reprises du thème Océan du tableau de bord.
    'ocean':dict(background='#071b20', panel='#102d32',ink='#e9faf8',muted='#a0beb9',
                 accent='#7ce0d4',inline='#b0f4e8',circle='#0c2c31',rings='#21565b',
                 glyph='#21474b',details='#38777a',rule='#28565a'),
}

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod

def configure(mod,palette,output,kind):
    color=lambda k:colors.HexColor(palette[k])
    mod.OUTPUT=output
    mod.ASSET=PROJECT/'moulinette'/'assets'/(('guide-utilisation-' if kind=='manuel' else 'guide-style-c-')+output.stem.rsplit('-',1)[-1]+'.pdf')
    mod.BACKGROUND=color('background');mod.PANEL=color('panel')
    mod.INK=color('ink');mod.MUTED=color('muted');mod.PURPLE=color('accent');mod.WHITE=color('ink')
    for name in ('cover_title','cover_sub','cover_body','h1','body','bullet','code'):
        mod.styles[name].textColor=color('ink')
    for name in ('cover_label','h2'):
        mod.styles[name].textColor=color('accent')
    def markup(text):
        text=html.escape(text,quote=False)
        text=re.sub(r'`([^`]+)`',lambda m:'<font name="JetBrainsMono" color="'+palette['inline']+'">'+m.group(1)+'</font>',text)
        return re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)
    mod.markup=markup
    def footer(canvas,doc):
        w,h=A4;rng=random.Random((53210 if kind=='manuel' else 2902)+doc.page)
        canvas.saveState()
        canvas.setFillColor(color('background'));canvas.rect(0,0,w,h,fill=1,stroke=0)
        corner=rng.choice(('top_right','bottom_left','bottom_right')) if doc.page>1 else 'top_right'
        if corner=='top_right':cx,cy=w+rng.randint(-10,35),h+rng.randint(-120,-45)
        elif corner=='bottom_left':cx,cy=rng.randint(-80,-25),rng.randint(55,165)
        else:cx,cy=w+rng.randint(15,70),rng.randint(70,180)
        radius=rng.randint(75,115)
        canvas.setFillColor(color('circle'));canvas.circle(cx,cy,radius,fill=1,stroke=0)
        canvas.setStrokeColor(color('rings'));canvas.setLineWidth(.9)
        for step in (28,57,87):canvas.circle(cx,cy,radius+step,fill=0,stroke=1)
        glyphs=['</>','$','&','#','*'];rng.shuffle(glyphs)
        spots=[(w*.74,h*.72),(w*.84,h*.45),(w*.66,h*.20),(w*.13,h*.31)];rng.shuffle(spots)
        canvas.setFillColor(color('glyph'))
        for symbol,(x,y) in zip(glyphs[:4],spots):
            canvas.saveState();canvas.translate(x+rng.randint(-15,15),y+rng.randint(-20,20))
            canvas.rotate(rng.choice((-15,-8,0,8,15)));canvas.setFont('JetBrainsMono',rng.choice((32,40,48)))
            canvas.drawString(0,0,symbol);canvas.restoreState()
        canvas.setStrokeColor(color('details'));canvas.setFillColor(color('details'))
        x=w-rng.randint(38,65);y=h*rng.uniform(.25,.65)
        for i in range(3):canvas.circle(x,y+i*8,1.15,fill=1,stroke=0)
        canvas.saveState();canvas.translate(rng.randint(24,42),h*rng.uniform(.37,.75));canvas.rotate(45)
        canvas.rect(-4,-4,8,8,stroke=1,fill=0);canvas.restoreState()
        if doc.page==1:
            canvas.setFont('LiberationSerif',9);canvas.setFillColor(color('accent'))
            canvas.drawString(2*cm,1.35*cm,'PROTOTYPE LOCAL  ·  CODE DE CONFIANCE UNIQUEMENT')
        else:
            canvas.setStrokeColor(color('rule'));canvas.line(2*cm,h-1.38*cm,w-2*cm,h-1.38*cm)
            canvas.setFont('LiberationSerif-Bold',9);canvas.setFillColor(color('accent'));canvas.drawString(2*cm,h-1.1*cm,'MOULINETTE LAB')
            canvas.setFont('LiberationSerif',9);canvas.setFillColor(color('muted'))
            title='GUIDE STYLE C' if kind=='style' else 'GUIDE UTILISATEUR'
            canvas.drawRightString(w-2*cm,h-1.1*cm,title+'  ·  v0.32.8-dev')
            canvas.setStrokeColor(color('rule'));canvas.line(2*cm,1.55*cm,w-2*cm,1.55*cm)
            canvas.drawString(2*cm,1.1*cm,'Projet non officiel  ·  Code de confiance uniquement')
            canvas.drawRightString(w-2*cm,1.1*cm,str(doc.page))
        canvas.restoreState()
    mod.footer=footer

for kind,script in [('manuel','creer_manuel.py'),('style','creer_guide_style.py')]:
    for theme,palette in PALETTES.items():
        mod=load(PROJECT/'tools'/script,'preview_'+kind+'_'+theme)
        prefix='manuel-utilisateur' if kind=='manuel' else 'guide-style-c'
        output=DEST/(prefix+'-v0.32.8-'+theme+'.pdf')
        configure(mod,palette,output,kind);mod.make()
        if theme=='ocean':
            import shutil
            shutil.copyfile(output,DEST/(prefix+'-v0.32.8.pdf'))
            shutil.copyfile(output,PROJECT/'moulinette'/'assets'/('guide-utilisation.pdf' if kind=='manuel' else 'guide-style-c.pdf'))
