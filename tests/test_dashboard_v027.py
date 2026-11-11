"""Régressions structurelles de la refonte autonome du tableau de bord."""
import unittest
from html.parser import HTMLParser
from moulinette.dashboard import render_dashboard


def row(ex, result, checks):
    return {'exercise':ex,'result':result,'source_label':'démo','created_at':'2026-01-01T12:00:00',
            'isolation':'Bubblewrap','checks':checks}

class DashboardParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.exercise=[]; self.options=[]; self.ids=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='option':self.options.append(a.get('value'))
        if 'exercise' in a.get('class','').split():self.exercise.append(a)

class DashboardV027Tests(unittest.TestCase):
    def setUp(self):
        passed=row('c00/ex00','passed',[{'status':'pass','name':'Test','message':'ok'}])
        failed=row('c01/ex00','failed',[{'status':'fail','name':'Test','message':'no'}])
        incomplete=row('c02/ex00','incomplete',[{'status':'unavailable','name':'Test','message':'attente'}])
        self.html=render_dashboard({'count':3,'recent':[passed,failed,incomplete],'latest':[passed,failed,incomplete]})
        self.p=DashboardParser();self.p.feed(self.html)
    def test_all_exercises_have_four_semantic_states(self):
        self.assertEqual(len(self.p.exercise),109)
        classes=[x['class'] for x in self.p.exercise]
        self.assertEqual(sum('ok-row' in c for c in classes),1)
        self.assertEqual(sum('bad-row' in c for c in classes),1)
        self.assertEqual(sum('pending-row' in c for c in classes),1)
        self.assertEqual(sum('neutral-row' in c for c in classes),106)
        for text in ('Réussi','À revoir','Incomplet','À découvrir'):
            self.assertIn(text,self.html)
    def test_theme_choices_and_filters_are_available_offline(self):
        for x in ('aurora','nightowl','ocean','forest','ember','sakura','cyberpunk','matcha','espresso','nordic','sunset','random','dm','mono','serif','system','humanist','c00','c13'):
            self.assertIn(x,self.p.options)
        for x in ('theme','font','theme-message','exercise-search','exercise-module','filter-count','no-results','roastbox','humor','bg-stage','bg-matrix','bg-terminal','atom-svg','live-form','live-path','live-exercise','live-submit'):
            self.assertIn(x,self.p.ids)
        self.assertIn('class="atom-electron"',self.html)
        self.assertIn('data:image/svg+xml;base64,',self.html)
        self.assertIn('Corriger ce fichier',self.html)
        self.assertNotIn('en un regard',self.html)
        self.assertNotIn('relancez <code>moulinette dashboard</code>',self.html)
        self.assertIn('data:font/woff2;base64,',self.html)
        self.assertIn('data:application/pdf;base64,',self.html)
        self.assertNotIn('https://',self.html)
        self.assertNotIn('__FONT__',self.html)
    def test_humor_is_above_the_statistics_and_removed_intro_is_absent(self):
        self.assertLess(self.html.index('id="roastbox"'),self.html.index('class="stats"'))
        self.assertLess(self.html.index('id="humor"'),self.html.index('class="stats"'))
        self.assertNotIn('Avancer, <em>un exercice</em>',self.html)
        self.assertNotIn('Vos essais, vos progrès, votre rythme.',self.html)
    def test_latest_incomplete_score_remains_hidden(self):
        latest=row('c02/ex00','incomplete',[{'status':'pass','name':'a','message':'ok'},
                                             {'status':'unavailable','name':'b','message':'non disponible'}])
        page=render_dashboard({'count':1,'recent':[latest],'latest':[latest]})
        self.assertIn('<div class="stat-value">—</div>',page)
        self.assertIn('badge pending">Incomplet',page)
    def test_untrusted_display_strings_are_escaped(self):
        x=row('c00/ex00','failed',[{'status':'fail','name':'<img src=x>','message':'<script>alert(1)</script>'}])
        x['source_label']='"><img src=x>'
        page=render_dashboard({'count':1,'recent':[x],'latest':[x]})
        self.assertNotIn('<script>alert(1)</script>',page)
        self.assertNotIn('<img src=x>',page)
        self.assertIn('&lt;img src=x&gt;',page)

if __name__=='__main__':unittest.main()
