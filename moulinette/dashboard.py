"""Tableau de bord statique, autonome et alimenté par l'historique local."""
import base64
import html
import hashlib
import json
import math
import os
import tempfile
from importlib.resources import files
from pathlib import Path
from string import Template
from .exercise_catalog import (
    ALL_EXERCISES,
    canonical_exercise,
    CPP_EXERCISES,
    EXERCISES,
    PISCINE_LABELS,
    PISCINE_ORDER,
    PISCINES,
    PY_EXERCISES,
)
from .history import data_directory, read_history, read_unlocked_piscines, score
from .dashboard_insights import (
    explanations,
    compare_checks,
    stage_of,
    summarize_stages,
    summarize_history,
    parse_diff,
    parse_norm,
)


def esc(value):
    return html.escape(str(value), quote=True)


def _asset(name):
    return base64.b64encode(files('moulinette').joinpath('assets', name).read_bytes()).decode('ascii')


def _text_asset(name):
    return files('moulinette').joinpath('assets', name).read_text(encoding='utf-8')


def _lcs_masks(a, b):
    n, m = len(a), len(b)
    if n > 256 or m > 256:
        limit = min(n, m)
        same = [i < limit and a[i] == b[i] for i in range(max(n, m))]
        return same[:n], same[:m]
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        row = dp[i]
        nxt = dp[i + 1]
        ai = a[i]
        for j in range(m - 1, -1, -1):
            row[j] = nxt[j + 1] + 1 if ai == b[j] else (nxt[j] if nxt[j] >= row[j + 1] else row[j + 1])
    ma, mb = [False] * n, [False] * m
    i = j = 0
    while i < n and j < m:
        if a[i] == b[j]:
            ma[i] = mb[j] = True
            i += 1
            j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            i += 1
        else:
            j += 1
    return ma, mb


def _glyph(b):
    if b == 10:
        return r'\n', 'g-inv'
    if b == 0:
        return r'\0', 'g-inv'
    if b == 9:
        return r'\t', 'g-inv'
    if b == 13:
        return r'\r', 'g-inv'
    if b < 32 or b == 127 or b > 126:
        return f'\\x{b:02x}', 'g-inv'
    return chr(b), ''


def _render_bytes(data, mask, diff_cls):
    if not data:
        return '<span class="g-empty">∅ (aucun octet)</span>'
    parts = []
    n = len(data)
    for i, b in enumerate(data):
        trailing = False
        if b == 32:
            trailing = True
            for k in range(i + 1, n):
                if data[k] == 10:
                    break
                if data[k] not in (32, 9):
                    trailing = False
                    break
        if b == 32 and trailing:
            text, cls = '·', 'g-trail'
        elif b == 32:
            text, cls = ' ', ''
        else:
            text, cls = _glyph(b)
        if not mask[i]:
            cls = (cls + ' ' + diff_cls).strip()
        if cls:
            parts.append(f'<span class="{cls}">{esc(text)}</span>')
        else:
            parts.append(esc(text))
        if b == 10:
            parts.append('\n')
    return ''.join(parts)


def _render_diff(diff):
    me, ma = _lcs_masks(diff['expected'], diff['actual'])
    exp_html = _render_bytes(diff['expected'], me, 'g-diff')
    act_html = _render_bytes(diff['actual'], ma, 'g-diff')
    note = '<small class="diff-note">Aperçu borné par le moteur ; les tailles totales sont indiquées.</small>' if diff.get('truncated') else ''
    return (
        '<div class="diff-box">'
        '<div class="diff-head"><strong>Comparateur de sortie (Expected vs Your Output)</strong>'
        '<span class="diff-legend"><code>\\n</code> saut de ligne · <code>\\0</code> octet nul · <code>·</code> espace de fin de ligne</span></div>'
        '<div class="diff-cols">'
        f'<div class="diff-col"><div class="diff-col-head"><span>Expected Output</span><span>{diff["expected_total"]} octet(s)</span></div><pre>{exp_html}</pre></div>'
        f'<div class="diff-col"><div class="diff-col-head"><span>Your Output</span><span>{diff["actual_total"]} octet(s)</span></div><pre>{act_html}</pre></div>'
        f'</div>{note}</div>'
    )


def _render_norm_items(items):
    if not items:
        return ''
    rows = []
    for it in items[:12]:
        file_prefix = (esc(it['file']) + ' · ') if it.get('file') else ''
        col_part = f" · col {it['col']}" if it.get('col') is not None else ''
        rows.append(
            f'<li><span class="norm-loc">{file_prefix}ligne {it["line"]}{col_part}</span> '
            f'<code class="norm-code">{esc(it["code"])}</code> <span>{esc(it["text"])}</span></li>'
        )
    return '<div class="norm-box"><strong>Lignes signalées par Norminette</strong><ul>' + ''.join(rows) + '</ul></div>'


def _render_history_viz(history, active_piscine='c'):
    viz = summarize_history(history, piscine=active_piscine)
    mods_html = ''.join(
        f'<div class="mod-item {"ok-mod" if m["cls"] == "ok" else ""}"><div class="mod-top"><strong>{esc(m["label"])}</strong><span>{m["done"]} / {m["total"]}</span></div><div class="mod-bar" aria-hidden="true"><span style="width:{m["percent"]}%"></span></div></div>'
        for m in viz['modules']
    )
    c = viz['counts']
    cells = ''.join(
        f'<span class="act-cell {esc(t["cls"])}" title="{esc(t["exercise"] + " · " + t["label"] + " · " + t["when"])}"></span>'
        for t in viz['timeline']
    ) or '<small class="g-empty">Aucune tentative enregistrée.</small>'
    mod_count = len(viz['modules'])
    return (
        '<section class="history-viz" aria-label="Synthèse par module et activité enregistrée">'
        f'<article class="panel"><div class="panelhead"><div><h3 id="viz-modules-title">Progression par module · {esc(PISCINE_LABELS[active_piscine])}</h3><p>Exercices validés au dernier essai par module</p></div><span class="paneltag" id="viz-modules-tag">{mod_count} MODULES</span></div><div class="mod-grid" id="viz-modules-grid">{mods_html}</div></article>'
        '<article class="panel"><div class="panelhead"><div><h3>Activité enregistrée</h3><p>Répartition et chronologie des corrections conservées (jusqu’à 50)</p></div>'
        f'<span class="paneltag">{viz["recent_total"]} AFFICHÉES</span></div>'
        f'<div class="activity-counts"><span class="badge ok">Réussis : {c["passed"]}</span><span class="badge bad">À revoir : {c["failed"]}</span><span class="badge pending">Incomplets : {c["incomplete"]}</span></div>'
        f'<div class="activity-strip" aria-label="Chronologie des corrections">{cells}</div>'
        '<small class="viz-note">Ces indicateurs reflètent uniquement les contrôles réellement exécutés et enregistrés localement ; ils n’établissent aucune garantie d’absence de fuite mémoire, d’absence de crash hors cas testés ou de conformité complète.</small>'
        '</article></section>'
    )


def _render_live_panel(unlocked):
    opts_list = ['<option value="auto">Exercice : Détection auto</option>']
    for p_key in PISCINE_ORDER:
        if p_key not in unlocked:
            continue
        for ex in sorted(PISCINES[p_key]):
            opts_list.append(f'<option value="{esc(ex)}">{esc(ex)}</option>')
    opts = ''.join(opts_list)
    return (
        '<section class="panel live-panel" id="direct" aria-label="Barre de recherche et correction de fichier">'
        '<div class="panelhead"><div><h3>Corriger un fichier ou un dossier</h3><p>Renseignez le chemin du fichier (.c, .cpp, .py) ou du dossier à évaluer ; les étapes s’actualisent après confirmation par le moteur</p></div><span class="paneltag" id="live-status">PRÊT</span></div>'
        f'<form class="live-form" id="live-form"><select id="live-exercise" aria-label="Exercice">{opts}</select>'
        '<input id="live-path" type="search" placeholder="Rechercher ou coller le chemin du fichier (.c, .cpp, .py) ou dossier à corriger…" autocomplete="off" required>'
        '<select id="live-mode" aria-label="Mode d’exécution"><option value="bubblewrap">Bubblewrap expérimental</option><option value="local">Local non isolé (confirmer)</option></select>'
        '<button class="primary" type="submit" id="live-submit">Corriger ce fichier</button></form>'
        '<div class="attempt-stages" id="live-stages">'
        '<div class="stage-pill neutral-stage" data-stage="files"><div class="stage-top"><strong>01 · Fichiers</strong><span class="badge neutral">En attente</span></div><small>—</small></div>'
        '<div class="stage-pill neutral-stage" data-stage="build"><div class="stage-top"><strong>02 · Compilation</strong><span class="badge neutral">En attente</span></div><small>—</small></div>'
        '<div class="stage-pill neutral-stage" data-stage="tests"><div class="stage-top"><strong>03 · Tests</strong><span class="badge neutral">En attente</span></div><small>—</small></div>'
        '<div class="stage-pill neutral-stage" data-stage="norm"><div class="stage-top"><strong>04 · Norminette</strong><span class="badge neutral">En attente</span></div><small>—</small></div>'
        '</div><div class="live-checks" id="live-checks"></div></section>'
        '<script>(function(){var f=document.getElementById("live-form");if(!f)return;'
        'var root=document.documentElement;'
        'var livePort=root.getAttribute("data-live-port")||"";'
        'var tok=new URLSearchParams(location.search).get("t")||root.getAttribute("data-live-token")||"";'
        'var base=(location.protocol==="http:"||location.protocol==="https:")?"":(livePort?("http:"+"//127.0.0.1:"+livePort):"");'
        'function esc(s){var d=document.createElement("div");d.textContent=String(s||"");return d.innerHTML;}'
        'function showStaticFallback(p,ex,m,st,box){'
        'var exFlag=(ex&&ex!=="auto")?(" --exercise "+ex):"";'
        'var modeFlag=(m==="local")?" --unsafe-local":" --experimental-sandbox";'
        'st.textContent="MODE STATIQUE";'
        'box.innerHTML="<div class=\\"check\\"><span class=\\"check-dot info\\"></span><div><b>Commande prête</b><p>Dans votre terminal : <code>moulinette check \\""+esc(p)+"\\""+esc(exFlag+modeFlag)+"</code><br>Lancez <code>moulinette dashboard</code> pour activer le démon local de correction en un clic.</p></div></div>";}'
        'f.addEventListener("submit",function(ev){ev.preventDefault();'
        'var ex=document.getElementById("live-exercise").value,p=document.getElementById("live-path").value.trim(),m=document.getElementById("live-mode").value;'
        'var st=document.getElementById("live-status"),box=document.getElementById("live-checks");box.innerHTML="";'
        'if(location.protocol==="file:"&&!base){showStaticFallback(p,ex,m,st,box);return;}'
        'st.textContent="EN COURS";'
        'var counts={files:{p:0,f:0,u:0},build:{p:0,f:0,u:0},tests:{p:0,f:0,u:0},norm:{p:0,f:0,u:0}};'
        'document.querySelectorAll("#live-stages .stage-pill").forEach(function(el){el.className="stage-pill neutral-stage";el.querySelector(".badge").className="badge neutral";el.querySelector(".badge").textContent="En attente";el.querySelector("small").textContent="—";});'
        'fetch(base+"/api/run",{method:"POST",headers:{"Content-Type":"application/json","X-Moulinette-Token":tok},body:JSON.stringify({exercise:ex,path:p,mode:m,confirm_unsafe:m==="local"})})'
        '.then(function(r){return r.json().then(function(d){return{ok:r.ok,d:d};});}).then(function(res){'
        'if(!res.ok){st.textContent="ERREUR";box.innerHTML="<div class=\\"check\\"><span class=\\"check-dot fail\\"></span><div><b>Refus</b><p>"+esc(res.d.error)+"</p></div></div>";return;}'
        'var es=new EventSource(base+"/api/events?run="+encodeURIComponent(res.d.run)+"&t="+encodeURIComponent(tok));'
        'es.onmessage=function(msg){var e=JSON.parse(msg.data);'
        'if(e.type==="check"){var row=document.createElement("div");row.className="check";row.innerHTML="<span class=\\"check-dot "+esc(e.status)+"\\"></span><div><b>"+esc(e.name)+"</b><p>"+esc(e.message)+"</p></div>";box.appendChild(row);'
        'var c=counts[e.stage];if(c){if(e.status==="pass")c.p++;else if(e.status==="fail")c.f++;else if(e.status==="unavailable")c.u++;'
        'var pill=document.querySelector("#live-stages [data-stage=\\""+e.stage+"\\"]");if(pill){var cls=c.f?"bad":(c.u?"pending":(c.p?"ok":"neutral"));var lbl=c.f?"À revoir":(c.u?"Incomplet":(c.p?"Validé":"Info"));'
        'pill.className="stage-pill "+cls+"-stage";var b=pill.querySelector(".badge");b.className="badge "+cls;b.textContent=lbl;pill.querySelector("small").textContent=c.p+" ✓ · "+c.f+" ✗";}}}'
        'else if(e.type==="done"){st.textContent=e.result==="passed"?"RÉUSSI":(e.result==="failed"?"À REVOIR":"INCOMPLET");es.close();'
        'setTimeout(function(){location.reload();},1400);}};})'
        '.catch(function(){showStaticFallback(p,ex,m,st,box);});});})();</script>'
    )


def _compute_piscines_state(history, db_path=None):
    """Calcule l'état des 3 piscines (C -> C++ -> Python), leurs compteurs et leur déblocage."""
    by_exercise = {}
    for x in history.get('latest', []):
        if isinstance(x, dict) and 'exercise' in x:
            norm = canonical_exercise(x['exercise']) or x['exercise']
            by_exercise[norm] = x

    unlocked = read_unlocked_piscines(history, db_path=db_path)
    active = 'py' if 'py' in unlocked else ('cpp' if 'cpp' in unlocked else 'c')

    piscines_info = {}
    for p_key in PISCINE_ORDER:
        cat = PISCINES[p_key]
        total = len(cat)
        protons = sum(1 for e in cat if by_exercise.get(e, {}).get('result') == 'passed')
        neutrons = sum(1 for e in cat if by_exercise.get(e, {}).get('result') == 'failed')
        incomplete = sum(1 for e in cat if by_exercise.get(e, {}).get('result') == 'incomplete')
        percent = round(protons / total * 100) if total else 0
        is_unlocked = p_key in unlocked
        is_completed = (protons == total and total > 0)
        piscines_info[p_key] = {
            'key': p_key,
            'label': PISCINE_LABELS[p_key],
            'icon': {'c': 'C', 'cpp': 'C++', 'py': 'PY'}[p_key],
            'unlocked': is_unlocked,
            'completed': is_completed,
            'active': p_key == active,
            'protons': protons,
            'neutrons': neutrons,
            'electrons': total,
            'incomplete': incomplete,
            'done': protons,
            'total': total,
            'percent': percent,
            'animated_electrons': protons + neutrons,
        }
    return by_exercise, unlocked, active, piscines_info


def _render_piscine_progression_panel(active, piscines_info):
    """Affiche le parcours ordonné 1. Piscine C -> 2. Piscine C++ -> 3. Piscine Python."""
    cards = []
    order_nums = {'c': '01', 'cpp': '02', 'py': '03'}
    lock_reasons = {
        'c': 'Débloquée par défaut',
        'cpp': 'Verrouillée sur le tableau de bord tant que les 109 exercices de la Piscine C ne sont pas tous « Réussi » au dernier essai.',
        'py': 'Verrouillée sur le tableau de bord tant que les 45 exercices de la Piscine C++ ne sont pas tous « Réussi » au dernier essai.',
    }
    for p_key in PISCINE_ORDER:
        info = piscines_info[p_key]
        num = order_nums[p_key]
        if info['active']:
            state_badge = '<span class="badge ok">Piscine en cours</span>'
        elif info['unlocked']:
            state_badge = '<span class="badge neutral">Débloquée · Lecture</span>'
        else:
            state_badge = '<span class="badge pending">Verrouillée (UI)</span>'
        sub = f"{info['protons']} / {info['total']} réussis ({info['percent']} %)"
        reason = (
            'Sélectionnez cette piscine pour consulter ses exercices et son historique.'
            if info['unlocked'] else lock_reasons[p_key]
        )
        btn_attrs = (
            f'type="button" class="piscine-step {"is-active" if info["active"] else ""} {"is-unlocked" if info["unlocked"] else "is-locked"}" '
            f'data-piscine-select="{esc(p_key)}" '
            + ('' if info['unlocked'] else 'disabled aria-disabled="true"')
        )
        cards.append(
            f'<button {btn_attrs}>'
            f'<div class="piscine-step-top"><strong>{num} · {esc(info["label"])}</strong>{state_badge}</div>'
            f'<div class="piscine-step-count">{esc(sub)}</div>'
            f'<small class="piscine-step-note">{esc(reason)}</small>'
            '</button>'
        )

    if active == 'c':
        explain = (
            "Piscine en cours : Piscine C. La Piscine C++ se débloquera automatiquement sur ce tableau de bord dès que "
            "les 109 exercices de la Piscine C auront pour dernière tentative le statut « Réussi ». "
            "La ligne de commande (moulinette check) peut évaluer des exercices C++ ou Python dès maintenant : leurs résultats sont conservés."
        )
    elif active == 'cpp':
        explain = (
            "Piscine en cours : Piscine C++ (débloquée définitivement après validation complète de la Piscine C). "
            "Vous pouvez consulter la Piscine C à tout moment en lecture. La Piscine Python se débloquera dès que les 45 exercices C++ seront « Réussi »."
        )
    else:
        explain = (
            "Piscine en cours : Piscine Python (toutes les piscines C, C++ et Python sont débloquées définitivement). "
            "Cliquez sur une piscine ci-dessus pour consulter ses résultats et son historique."
        )

    return (
        '<section class="panel piscine-panel" id="parcours-piscines" aria-label="Ordre et progression des piscines">'
        '<div class="panelhead"><div><h3>Parcours séquentiel : 1. Piscine C → 2. Piscine C++ → 3. Piscine Python</h3>'
        f'<p id="piscine-explain">{esc(explain)}</p></div>'
        f'<span class="paneltag" id="active-piscine-tag">EN COURS : {esc(PISCINE_LABELS[active].upper())}</span></div>'
        f'<div class="piscine-steps" id="piscine-steps">{"".join(cards)}</div>'
        '</section>'
    )


def render_dashboard(history, live_mode=True, db_path=None):
    recent = history['recent']
    by_exercise, unlocked, active_piscine, piscines_info = _compute_piscines_state(history, db_path=db_path)
    active_info = piscines_info[active_piscine]
    active_catalog = PISCINES[active_piscine]

    completed = active_info['done']
    all_ex = active_info['total']
    protons = active_info['protons']
    neutrons = active_info['neutrons']
    electrons_total = active_info['electrons']
    anim_electrons = active_info['animated_electrons']
    # Repli SVG 2D hors Canvas : même nombre de corrections, pas de particules fictives.
    atom_fallback = []
    statuses = [by_exercise.get(ex, {}).get('result') for ex in sorted(active_catalog)]
    for i, status in enumerate(x for x in statuses if x in ('passed', 'failed')):
        phase = i * 1.7
        x, y = 176 * math.cos(phase), 68 * math.sin(phase)
        speed = 1.5 * (-1 if i % 3 == 1 else 1) * (0.22 + (i % 3) * 0.05)
        color = '#ff5f70' if status == 'failed' else '#3cbbff'
        atom_fallback.append(
            f'<g class="atom-shell" transform="rotate({i * 53 % 180})">'
            '<ellipse class="atom-orbit" cx="0" cy="0" rx="176" ry="68"/>'
            f'<g class="atom-electron" data-rx="176" data-ry="68" data-speed="{speed}" data-phase="{phase}" transform="translate({x:.2f},{y:.2f})">'
            f'<circle r="5" fill="{color}"/></g></g>'
        )

    latest = recent[0] if recent else None
    names = {'passed': 'Réussi', 'failed': 'À revoir', 'incomplete': 'Incomplet'}
    cats = {'passed': 'ok', 'failed': 'bad', 'incomplete': 'pending'}
    score_text = lambda row: ('—' if score(row) is None else str(score(row)) + ' %')

    def build_tiles_and_modules(p_key):
        cat = PISCINES[p_key]
        icon_txt = {'c': 'C', 'cpp': 'C++', 'py': 'PY'}[p_key]
        p_tiles = []
        for ex, spec in sorted(cat.items()):
            row = by_exercise.get(ex)
            status = row['result'] if row else None
            label = names.get(status, 'À découvrir')
            cls = cats.get(status, 'neutral')
            source = spec['source']
            module = ex.split('/')[0]
            p_tiles.append(
                f'<div class="exercise {cls}-row" data-piscine="{esc(p_key)}" data-module="{esc(module)}" '
                f'data-result="{esc(status or "unattempted")}" data-search="{esc(ex + " " + source)}"><span class="file-icon">{esc(icon_txt)}</span>'
                f'<div class="exbody"><strong>{esc(ex)}</strong><small>{esc(source)}</small></div>'
                f'<span class="badge {cls}">{label}</span></div>'
            )
        p_mods = sorted({ex.split('/')[0] for ex in cat})
        return p_tiles, p_mods

    tiles, modules = build_tiles_and_modules(active_piscine)
    # Garantit que c00 et c13 sont toujours présents dans les options de module initiales ou du sélecteur
    module_options = ''.join(f'<option value="{esc(m)}">{esc(m.upper())}</option>' for m in modules)
    if active_piscine != 'c':
        module_options += ''.join(
            f'<option value="{esc(m)}" hidden>{esc(m.upper())}</option>'
            for m in sorted({ex.split('/')[0] for ex in EXERCISES})
        )

    # Données JSON pour basculer en lecture entre les piscines débloquées
    client_piscines = {}
    for p_key in PISCINE_ORDER:
        if p_key not in unlocked:
            continue
        p_tiles, p_mods = build_tiles_and_modules(p_key)
        p_viz = summarize_history(history, piscine=p_key)
        client_piscines[p_key] = {
            **piscines_info[p_key],
            'tiles_html': ''.join(p_tiles),
            'modules': p_mods,
            'viz_modules': p_viz['modules'],
        }
    piscines_json = json.dumps(client_piscines, ensure_ascii=False).replace('</', '<\\/')

    entries = []
    for index, row in enumerate(recent):
        badge = names.get(row['result'], 'Inconnu')
        cls = cats.get(row['result'], 'neutral')
        ex_name = canonical_exercise(row.get('exercise', '')) or row.get('exercise', '')
        default_source = ALL_EXERCISES.get(ex_name, {}).get('source')
        stages_html = ''.join(
            f'<div class="stage-pill {s["cls"]}-stage"><div class="stage-top"><strong>{esc(s["title"])}</strong><span class="badge {s["cls"]}">{esc(s["label"])}</span></div><small>{esc(s["detail"])}</small></div>'
            for s in summarize_stages(row.get('checks', []))
        )
        stages_bar = f'<div class="attempt-stages" aria-label="Étapes de la correction">{stages_html}</div>'
        details = []
        for check in row['checks']:
            if not isinstance(check, dict):
                continue
            checkstatus = check.get('status', 'info')
            cname = check.get('name', '')
            cmsg = check.get('message', '')
            tips = explanations(ex_name, check)
            hints = ('<div class="explanation"><strong>Pour comprendre</strong><ul>' + ''.join('<li>' + esc(tip) + '</li>' for tip in tips) + '</ul><small>Explications indicatives à partir du diagnostic enregistré, sans lecture du fichier actuel.</small></div>') if tips else ''
            extra = ''
            if checkstatus == 'fail':
                st = stage_of(cname)
                if st == 'norm':
                    extra = _render_norm_items(parse_norm(cmsg, default_source))
                elif st == 'tests':
                    d = parse_diff(cmsg)
                    if d:
                        extra = _render_diff(d)
            details.append(f'<div class="check"><span class="check-dot {esc(checkstatus)}"></span><div><b>{esc(cname)}</b><p>{esc(cmsg)}</p>{hints}{extra}</div></div>')
        previous = next((r for r in recent[index + 1:] if (canonical_exercise(r.get('exercise', '')) or r.get('exercise', '')) == ex_name), None)
        comparison = ''
        if previous:
            improved, regressed, unknown = compare_checks(row, previous)
            changes = []
            if improved:
                changes.append('De échec à réussi : ' + ', '.join(improved))
            if regressed:
                changes.append('De réussi à échec : ' + ', '.join(regressed))
            if unknown:
                changes.append('État non concluant : ' + ', '.join(unknown))
            if not changes:
                changes.append('Aucun changement comparable parmi les contrôles exécutés et identifiés de façon unique.')
            stamp = previous['created_at'].replace('T', ' ')[:19] + ' UTC'
            comparison = '<div class="comparison"><strong>Comparaison avec la tentative précédente</strong><p>' + esc(' · '.join(changes)) + '</p><small>Précédente : ' + esc(stamp) + ' · ' + esc(previous.get('source_label', '')) + ' · Seuls les contrôles correspondants sont comparés ; une étape non exécutée n’est ni réussie ni échouée.</small></div>'
        when = esc(row['created_at'].replace('T', ' ')[:19]) + ' UTC'
        entries.append(f'''<details class="attempt"><summary><span class="file-icon">↗</span><span class="attempt-title"><strong>{esc(ex_name)}</strong><small>{esc(row['source_label'])} · {when}</small></span><span class="attempt-score">{score_text(row)}</span><span class="badge {cls}">{badge}</span><span class="chevron" aria-hidden="true">⌄</span></summary><div class="attempt-details"><p class="detail-mode">Mode : {esc(row['isolation'])}</p>{stages_bar}{comparison}{''.join(details)}</div></details>''')
    empty = '''<div class="empty"><span class="empty-icon" aria-hidden="true">✧</span><strong>Aucune correction enregistrée</strong><p>Les prochaines corrections apparaîtront ici. Les résultats antérieurs à la v0.17 ne sont pas importés automatiquement.</p><code>moulinette check ./mon-rendu --exercise c00/ex00 --experimental-sandbox</code></div>'''
    last_info = (esc(latest['exercise']) + ' · ' + esc(latest['created_at'].replace('T', ' ')[:16]) + ' UTC') if latest else 'Aucune correction pour le moment'
    score_label = score_text(latest) if latest else '—'
    percent = active_info['percent']
    done_word = 'exercice' if completed == 1 else 'exercices'
    active_label = PISCINE_LABELS[active_piscine]
    favicon_b64 = base64.b64encode(
        b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        b'<defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">'
        b'<stop offset="0%" stop-color="#d3bfff"/><stop offset="100%" stop-color="#7c4dff"/>'
        b'</linearGradient></defs>'
        b'<rect width="64" height="64" rx="18" fill="url(#g)"/>'
        b'<text x="32" y="41" text-anchor="middle" fill="#160e28" '
        b'font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
        b'font-size="24" font-weight="900">&lt;/&gt;</text></svg>'
    ).decode('ascii')
    live_database_note = ('<p>Base personnalisée : pour y enregistrer depuis la page, utilisez le mode live avec --db. La commande check seule utilise la base par défaut.</p>' if db_path is not None else '')
    live_port, live_token = '', ''
    try:
        from .live import read_live_daemon
        lp, lt = read_live_daemon() if db_path is None else (None, None)
        if lp and lt:
            live_port, live_token = str(lp), str(lt)
    except Exception:
        pass
    css = _text_asset('dashboard.css').replace('__FONT__', _asset('dm-sans.woff2'))
    template = Template('''<!doctype html>
<html lang="fr" data-count="$count" data-active-piscine="$active_piscine" data-live-port="$live_port" data-live-token="$live_token"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,$favicon">
<title>Moulinette Lab · Tableau de bord</title><script>$boot</script><style>$css</style></head>
<body><div class="bg-stage" id="bg-stage" aria-hidden="true"><canvas class="bg-matrix" id="bg-matrix"></canvas><div class="bg-terminal" id="bg-terminal"></div></div><div class="shell">
<header class="topbar">
 <a class="brand" href="#apercu" aria-label="Moulinette Lab, accueil"><span class="brandmark">&lt;/&gt;</span><span><b>MOULINETTE</b><small>LAB · MODE AUTODIDACTE</small></span></a>
 <nav class="navlinks" aria-label="Navigation principale"><a href="#apercu">Vue d’ensemble</a><a href="#parcours-piscines">Piscines</a><a href="#direct">Corriger un fichier</a><a href="#exercices">Exercices</a><a href="#corrections">Corrections</a><a href="#methodologie">À savoir</a></nav>
 <div class="nav-right"><div class="font-control"><label for="font">Choisir la police</label><select id="font"><option value="dm">Police : DM Sans</option><option value="mono">Police : Terminal Mono</option><option value="serif">Police : Éditorial Serif</option><option value="system">Police : Néo-Grotesque</option><option value="humanist">Police : Humaniste</option></select></div><div class="theme-control"><label for="theme">Choisir le thème</label><select id="theme"><option value="aurora">Aurore</option><option value="nightowl">Night Owl</option><option value="ocean">Océan</option><option value="forest">Forêt</option><option value="ember">Braise</option><option value="sakura">Sakura Nocturne</option><option value="cyberpunk">Cyberpunk Néon</option><option value="matcha">Matcha Kyoto</option><option value="espresso">Espresso Caramel</option><option value="nordic">Fjord Polaire</option><option value="sunset">Mirage Doré</option><option value="random">Aléatoire à l’ouverture</option></select></div></div>
</header>
<section class="guide-downloads" aria-label="Téléchargement des guides"><div class="guide-intro"><strong>Documents PDF</strong><span>Téléchargement direct · disponible hors ligne</span></div>$guide_links</section>
<div class="theme-message" id="theme-message" role="status" aria-live="polite"></div>
<main id="apercu">
<section class="hero" aria-labelledby="hero-title"><div><h1 class="sr" id="hero-title">Tableau de bord</h1><div class="kicker">Votre espace d’apprentissage</div><div class="roastbox" id="roastbox"><span class="spark" aria-hidden="true">✳</span><p id="roast">Le compilateur a trouvé ton code. Il aurait préféré trouver la paix.</p><button type="button" id="next" aria-label="Changer de phrase">↻</button></div><label class="humor-toggle" for="humor"><input type="checkbox" id="humor" role="switch" checked><span class="humor-track" aria-hidden="true"><span></span></span><span>Humour</span></label><div class="hero-actions"><a class="primary" href="#direct">Corriger un fichier <span aria-hidden="true">↗</span></a><a class="secondary" href="#exercices">Voir mes exercices</a><a class="secondary" href="#corrections">Mes corrections</a></div></div>
<div class="hero-art" id="hero-art" data-protons="$protons" data-neutrons="$neutrons" data-electrons="$electrons" data-animated-electrons="$anim_electrons" aria-label="$active_label : $done exercices réussis sur $total"><canvas class="atom-canvas" id="atom-canvas" width="420" height="420" aria-hidden="true"></canvas><svg class="atom-svg" id="atom-svg" viewBox="-195 -195 390 390" aria-hidden="true"><circle class="atom-core" cx="0" cy="0" r="15"/>$atom_fallback</svg><span class="orbit-dot" aria-hidden="true"></span><div class="progress-card" id="progress-card"><div class="ring" id="progress-ring" style="--progress:$percent"><div class="ring-inner" id="progress-percent">$percent %</div></div><strong id="progress-title">Votre progression</strong><small id="progress-subtitle">$done $done_word sur $total réussis</small><span class="progress-piscine-badge" id="progress-piscine-badge">$active_label</span></div></div></section>
<section class="stats" aria-label="Votre activité"><article class="stat"><div class="stat-top">Exercices réussis <span class="stat-icon" aria-hidden="true">✓</span></div><div class="stat-value" id="stat-done-value">$done <span>/ $total</span></div><div class="stat-note" id="stat-done-note">Au dernier essai · Parcours disponible ($active_label)</div></article><article class="stat"><div class="stat-top">Dernier score <span class="stat-icon" aria-hidden="true">✳</span></div><div class="stat-value">$score</div><div class="stat-note">Contrôles locaux · non officiel</div></article><article class="stat"><div class="stat-top">Corrections <span class="stat-icon" aria-hidden="true">↗</span></div><div class="stat-value">$count</div><div class="stat-note">$last</div></article></section>
<div class="section-title"><div><div class="section-kicker">Votre parcours</div><h2>Votre progression</h2></div><p>Des données réelles, enregistrées sur cet ordinateur.</p></div>
$piscine_panel$live_panel$history_viz<div class="grid"><section class="panel" id="exercices"><div class="panelhead"><div><h3 id="exercises-panel-title">42 · $active_label</h3><p>Statut de la dernière tentative par exercice</p></div><span class="paneltag" id="exercises-panel-tag">$done / $total</span></div><div class="progressline" aria-hidden="true"><span id="exercises-progress-bar" style="width:$percent%"></span></div>
<div class="filters"><label class="sr" for="exercise-search">Rechercher un exercice ou un fichier</label><input id="exercise-search" type="search" placeholder="Rechercher un exercice…" autocomplete="off"><label class="sr" for="exercise-module">Filtrer par module</label><select id="exercise-module"><option value="">Tous les modules</option>$module_options</select></div>
<div class="exercise-list" id="exercise-list">$tiles<p class="no-results" id="no-results" hidden>Aucun exercice ne correspond à cette recherche.</p></div><p class="filter-count" id="filter-count" aria-live="polite">$total exercices affichés</p></section>
<section class="panel" id="corrections"><div class="panelhead"><div><h3>Dernières corrections</h3><p>Ouvrez une correction pour voir ses détails et, si disponible parmi les 50 affichées, sa tentative précédente</p></div><span class="paneltag">50 DERNIÈRES</span></div><div class="attempts">$entries</div></section></div>
<section class="note" id="methodologie"><strong>À savoir.</strong> Le score correspond aux contrôles réussis divisés par les contrôles réussis et échoués qui ont été exécutés, tous de poids égal. Un échec peut arrêter la correction avant les autres contrôles. Les informations sont exclues ; si un contrôle est indisponible ou le résultat incomplet, aucun score n’est affiché. Ce n’est ni une note officielle ni une garantie de conformité. Les diagnostics restent locaux et peuvent contenir du code ou des chemins. Cette page s’actualise automatiquement à chaque correction. Code de confiance uniquement.</section>
</main><footer class="footer"><span>Moulinette Lab · prototype local · tests non officiels</span><span>Construit pour apprendre, à votre rythme.</span></footer></div>
<script id="piscine-payload" type="application/json">$piscines_json</script>
<script>$js</script></body></html>''')
    groups = []
    for label, stem, filebase in (
        ('Manuel utilisateur', 'guide-utilisation', 'manuel-moulinette-lab'),
        ('Guide du style C', 'guide-style-c', 'guide-style-c-moulinette-lab'),
    ):
        links = []
        for theme, title in (('blanc', 'Blanc'), ('ocean', 'Océan')):
            data = _asset(stem + '-' + theme + '.pdf')
            filename = filebase + '-v0.32.8-' + theme + '.pdf'
            links.append(f'<a class="guide" data-document="{stem}" data-theme="{theme}" href="data:application/pdf;base64,{data}" download="{filename}" aria-label="Télécharger {label}, thème {title}">{title} ↓</a>')
        groups.append('<div class="guide-group"><strong>' + esc(label) + '</strong><div class="guide-buttons">' + ''.join(links) + '</div></div>')
    return template.substitute(
        boot=_text_asset('dashboard-boot.js'),
        css=css,
        favicon=favicon_b64,
        active_piscine=esc(active_piscine),
        active_label=esc(active_label),
        live_port=esc(live_port),
        live_token=esc(live_token),
        guide_links=''.join(groups),
        done=completed,
        done_word=done_word,
        total=all_ex,
        protons=protons,
        neutrons=neutrons,
        electrons=electrons_total,
        anim_electrons=anim_electrons,
        atom_fallback=''.join(atom_fallback),
        percent=percent,
        score=score_label,
        count=history['count'],
        last=last_info,
        tiles=''.join(tiles),
        piscine_panel=_render_piscine_progression_panel(active_piscine, piscines_info),
        live_panel=(live_database_note + _render_live_panel(unlocked)) if live_mode else '',
        history_viz=_render_history_viz(history, active_piscine=active_piscine),
        module_options=module_options,
        entries=''.join(entries) if entries else empty,
        piscines_json=piscines_json,
        js=_text_asset('dashboard.js'),
    )


def write_dashboard(output_path=None, db_path=None):
    content = render_dashboard(read_history(db_path=db_path), db_path=db_path)
    if output_path is not None:
        dest = Path(output_path).expanduser()
        directory = dest.parent
        directory.mkdir(parents=True, exist_ok=True)
    else:
        directory = data_directory()
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        if directory.is_symlink() or not directory.is_dir():
            raise OSError('Le dossier du tableau de bord doit être un dossier réel.')
        if db_path is None:
            dest = directory / 'dashboard.html'
        else:
            key = hashlib.sha256(str(Path(db_path).expanduser().resolve()).encode('utf-8')).hexdigest()[:16]
            dest = directory / ('dashboard-' + key + '.html')
    if dest.is_symlink():
        raise OSError('La destination du tableau de bord ne doit pas être un lien symbolique.')
    fd, temp = tempfile.mkstemp(prefix='.dashboard-', suffix='.html', dir=directory, text=True)
    try:
        try:
            stream = os.fdopen(fd, 'w', encoding='utf-8')
        except BaseException:
            try:
                os.close(fd)
            except OSError:
                pass
            raise
        with stream:
            stream.write(content)
        os.replace(temp, dest)
    finally:
        try:
            os.unlink(temp)
        except FileNotFoundError:
            pass
    return dest
