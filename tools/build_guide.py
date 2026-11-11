"""Reconstruit le guide PDF ; nécessite reportlab (dépendance de développement)."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit

root=Path(__file__).resolve().parents[1]; assets=root/'moulinette'/'assets'
pdfmetrics.registerFont(TTFont('DM',str(assets/'DMSans-Regular.ttf')))
pdfmetrics.registerFont(TTFont('DMBold',str(assets/'DMSans-Bold.ttf')))
W,H=A4; bg='#011627'; panel='#0b253a'; line='#29465a'; ink='#d6deeb'; muted='#9eb4c6'; blue='#82aaff'; purple='#c792ea'; green='#addb67'
c=canvas.Canvas(str(assets/'guide-provisoire.pdf'),pagesize=A4)
c.setTitle('Moulinette Lab — guide local v0.25-dev');c.setAuthor('Moulinette Lab')
def color(v): c.setFillColor(HexColor(v))
def text(x,y,s,size=10,font='DM',col=ink): color(col);c.setFont(font,size);c.drawString(x,y,s)
def para(x,y,s,width=460,size=10,leading=15,col=muted,font='DM'):
 color(col);c.setFont(font,size)
 for row in simpleSplit(s,font,size,width): c.drawString(x,y,row);y-=leading
 return y
def section(y,num,title,body,command=None):
 text(48,y,num,10,'DMBold',purple); text(78,y,title,13,'DMBold',ink)
 y=para(78,y-22,body,465,9.5,14)
 if command:
  c.setFillColor(HexColor(panel)); c.roundRect(78,y-17,465,27,7,fill=1,stroke=0)
  text(88,y-7,command,8,'DM',blue);y-=32
 return y-15
def frame(page):
 color(bg); c.rect(0,0,W,H,stroke=0,fill=1)
 color(blue); c.roundRect(42,H-60,28,28,7,stroke=0,fill=1)
 text(46,H-50,'</>',8,'DMBold',bg);text(80,H-45,'MOULINETTE LAB',11,'DMBold');text(80,H-59,'GUIDE LOCAL  ·  VERSION 0.25-DEV',8,'DM',muted)
 c.setStrokeColor(HexColor(line));c.line(42,H-75,W-42,H-75);c.line(42,48,W-42,48)
 text(42,30,'PROTOTYPE LOCAL  ·  DOCUMENT PROVISOIRE',7,'DMBold',muted)
 text(W-70,30,f'{page} / 3',7,'DM',muted)
frame(1)
text(44,H-116,'VOTRE ESPACE D’APPRENTISSAGE',9,'DMBold',purple)
text(44,H-160,'Guide d’utilisation',31,'DMBold')
text(44,H-183,'Prendre en main le tableau de bord local.',11,'DM',muted)
c.setFillColor(HexColor(panel));c.setStrokeColor(HexColor(line));c.roundRect(44,H-257,W-88,48,10,fill=1,stroke=1)
text(57,H-229,'SÉCURITÉ',9,'DMBold',green)
para(57,H-245,'Les trois modes sont expérimentaux ou non isolés : code de confiance uniquement.',450,9,12,ink)
y=H-295
y=section(y,'01','Corriger un rendu local','Depuis le dossier du projet ou après installation, utilisez un dossier que vous avez écrit ou vérifié. Le mode cgroup reste expérimental.', 'python3 -m moulinette check ./mon-rendu --exercise c00/ex00 --experimental-cgroup-sandbox')
y=section(y,'02','Ouvrir le tableau de bord','Générez la page locale et ouvrez-la dans votre navigateur. Si le navigateur ne démarre pas, ouvrez le chemin affiché dans le terminal.', 'python3 -m moulinette dashboard')
y=section(y,'03','Consulter votre historique','Chaque correction est enregistrée sur cet ordinateur. Le tableau récapitule les 50 dernières et le dernier état des exercices C 00, C 01 et C 02. Relancez dashboard pour actualiser la page.')
c.showPage();frame(2)
text(44,H-115,'COMPRENDRE VOS RÉSULTATS',9,'DMBold',purple)
text(44,H-158,'Résultats & données',28,'DMBold')
y=H-205
y=section(y,'04','Score local, pas note officielle','Si tous les contrôles sont disponibles, le score est le nombre de contrôles réussis divisé par les contrôles réussis et échoués exécutés, de poids égal. Un échec peut arrêter la correction avant les autres contrôles. Les informations sont exclues. Un résultat incomplet n’a pas de score.')
y=section(y,'05','Données et confidentialité','L’historique est conservé dans ~/.local/share/moulinette-lab ou sous XDG_DATA_HOME si défini. Les diagnostics peuvent contenir des extraits de code et des chemins. Aucune donnée n’est envoyée par le tableau de bord.')
y=section(y,'06','Ne pas enregistrer une correction','Ajoutez --no-history à check. La correction ne modifie alors pas la base historique. Les corrections antérieures à la v0.17 ne sont pas importées automatiquement.', 'python3 -m moulinette check ./mon-rendu --exercise c00/ex00 --experimental-cgroup-sandbox --no-history')
y=section(y,'07','Ce qui reste à construire','Autres sujets, import PDF, autres langages et sécurité complète ne sont pas disponibles. Les PDF C 00 v8, C 01 v6 et C 02 v6 sont utilisés ici ; les tests et scores ne sont pas officiels.')
para(48,y-2,'Conseil : si la page affiche « aucune correction », effectuez une nouvelle correction. Pour générer la page sans ouvrir le navigateur : python3 -m moulinette dashboard --no-open.',485,9,13,muted)
c.showPage();frame(3)
text(44,H-115,'DÉPÔT PUBLIC DE CONFIANCE',9,'DMBold',purple)
text(44,H-158,'Correction GitHub',28,'DMBold')
y=H-205
y=section(y,'08','Avant de commencer','Uniquement vos dépôts GitHub publics dont vous avez vérifié le contenu. Git utilise Bubblewrap et un stockage temporaire limité, mais partage le réseau de l’hôte : l’isolation est incomplète. La commande refuse de commencer sans --trust-github. Git doit être installé.')
y=section(y,'09','Choisir le bon dossier','Dans check, remplacez le chemin local par https://github.com/PROPRIETAIRE/DEPOT et ajoutez --trust-github. Si le rendu est dans un sous-dossier, ajoutez --subdir suivi de son chemin relatif. Gardez l’option de mode explicite.')
y=section(y,'10','Choisir la version','Sans --ref, la branche par défaut est utilisée. Pour une branche ou un tag, indiquez --ref puis son nom ; pour un commit, indiquez son SHA complet. Le rapport indique le SHA réellement évalué. Les redirections et sous-modules sont refusés.')
y=section(y,'11','Historique et limites','La référence du dépôt et le SHA sont conservés dans l’historique local, sauf avec --no-history. Les dépôts privés, SSH et Git LFS ne sont pas pris en charge. Le tmpfs Git est limité à 128 Mio, mais ne constitue ni un quota global ni une sandbox fiable.')
para(48,y-2,'La correction continue d’utiliser les tests non officiels C 00, C 01 et C 02. Un téléchargement réussi ne valide ni le code ni la sécurité de son exécution.',485,9,13,muted)
c.save()
