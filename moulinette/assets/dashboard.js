(function () {
  const theme = window.__mlThemeState;
  const labels = {
    aurora:'Aurore',
    nightowl:'Night Owl',
    ocean:'Océan',
    forest:'Forêt',
    ember:'Braise',
    sakura:'Sakura Nocturne',
    cyberpunk:'Cyberpunk Néon',
    matcha:'Matcha Kyoto',
    espresso:'Espresso Caramel',
    nordic:'Fjord Polaire',
    sunset:'Mirage Doré'
  };
  const select = document.getElementById('theme');
  const message = document.getElementById('theme-message');
  function describe() {
    if (!theme.available) message.textContent = 'Enregistrement du thème indisponible dans ce navigateur.';
    else if (theme.choice === 'random') message.textContent = 'Aléatoire à l’ouverture · ' + labels[theme.active];
    else message.textContent = 'Thème mémorisé sur ce navigateur';
  }
  select.value = theme.choice;
  describe();
  select.addEventListener('change', function () {
    let selected = select.value;
    if (selected !== 'random' && !theme.names.includes(selected)) selected = 'aurora';
    theme.choice = selected;
    if (selected === 'random') {
      const options = theme.names.filter(name => name !== theme.active);
      theme.active = options[Math.floor(Math.random() * options.length)];
    } else theme.active = selected;
    document.documentElement.setAttribute('data-theme', theme.active);
    try {
      localStorage.setItem('ml-theme-choice', selected);
      localStorage.setItem('ml-theme-last', theme.active);
      theme.available = true;
    } catch (e) { theme.available = false; }
    describe();
  });

  const search = document.getElementById('exercise-search');
  const moduleSelect = document.getElementById('exercise-module');
  let rows = Array.from(document.querySelectorAll('.exercise'));
  const count = document.getElementById('filter-count');
  const noResults = document.getElementById('no-results');
  function filter() {
    rows = Array.from(document.querySelectorAll('.exercise'));
    const query = search.value.trim().toLocaleLowerCase();
    const module = moduleSelect.value;
    let shown = 0;
    rows.forEach(row => {
      const match = (!query || row.dataset.search.toLocaleLowerCase().includes(query)) &&
        (!module || row.dataset.module === module);
      row.hidden = !match;
      if (match) shown++;
    });
    count.textContent = shown + ' exercice' + (shown === 1 ? '' : 's') + ' affiché' + (shown === 1 ? '' : 's');
    if (noResults) noResults.hidden = shown !== 0;
    if (typeof window.__mlUpdateAtomScope === 'function') {
      window.__mlUpdateAtomScope(module, rows);
    }
  }
  search.addEventListener('input', filter);
  moduleSelect.addEventListener('change', filter);

  const phrases = [
    "Le compilateur a trouvé ton code. Il aurait préféré trouver la paix.",
    "Tes bugs ont fondé une colocation. Le loyer est payé en heures de sommeil.",
    "Ton programme est vivant. Les avertissements, eux, demandent une minute de silence.",
    "Une erreur de moins. Le chaos tient encore debout, mais il boite.",
    "Ton code a survécu aux tests. On ne peut pas en dire autant de ta tranquillité.",
    "Le point-virgule était là depuis le début. Il méditait simplement en dehors de la ligne.",
    "Ce matin, ton compilateur a pris un café. Il savait que la journée serait longue.",
    "Un pointeur entre dans un bar. Personne ne sait vraiment où il voulait aller.",
    "Ton code et la Norminette ont une relation compliquée. Au moins, ils communiquent.",
    "La boucle infinie a demandé une pause. On attend encore sa réponse.",
    "Un bug résolu, c’est un mystère de moins et trois onglets de documentation de plus.",
    "Ton terminal ne juge pas. La Norminette, en revanche, a préparé une liste.",
    "Les accolades jouent à cache-cache. L’une d’elles prend son rôle très au sérieux.",
    "Ta variable inutilisée avait pourtant beaucoup de potentiel.",
    "Le `return` est parti sans dire au revoir. La fonction l’a très mal pris.",
    "Ton programme compile : les étoiles, les types et les planètes sont alignés.",
    "Il y a deux sortes de développeurs : ceux qui sauvegardent et ceux qui vont bientôt apprendre.",
    "Le fichier `main.c` voulait rester discret. Le compilateur l’a quand même trouvé.",
    "Ton indentation et tes intentions ne racontent pas encore exactement la même histoire.",
    "Un `NULL` bien placé vaut mieux qu’une longue promenade en mémoire inconnue.",
    "Le débogueur est un détective : il pose beaucoup de questions et ne paie jamais le café.",
    "La fonction est courte, claire et efficace. Elle est aussi dans un autre fichier.",
    "Ton code a une excellente personnalité. Sa syntaxe travaille encore sur la sienne.",
    "La Piscine : l’endroit où même les caractères ont besoin d’un échappement.",
    "Un commentaire dit « facile ». Le code, lui, a demandé un avocat.",
    "Tu as trouvé le bug ! Lui pensait pourtant avoir bien choisi sa cachette.",
    "La compilation a réussi du premier coup. Vérifie quand même que tu as sauvegardé.",
    "Les warnings sont comme les petites miettes : on les remarque surtout quand il y en a partout.",
    "Ton tableau commence à zéro. Ton café, lui, commence à manquer.",
    "Le `while` a dit « encore une fois ». Le processeur a levé les yeux au ciel.",
    "Tu voulais une fonction simple. Elle a invité ses amis les cas limites.",
    "Ce `if` n’est pas compliqué : il a seulement plusieurs opinions.",
    "Une variable locale a essayé de voyager. Elle a vite atteint la fin de sa portée.",
    "Ton code est presque parfait. Il lui manque juste ce détail que le test vient de trouver.",
    "Le `malloc` a réservé une table. Le `free` espère que quelqu’un se souviendra de payer.",
    "Le `segfault` est un message bref pour une conversation généralement très longue.",
    "Les pointeurs : parce qu’une adresse peut parfois remplacer une explication.",
    "Ta fonction récursive se comprend elle-même. C’est déjà une belle preuve de confiance.",
    "La Norminette n’a rien contre toi. Elle a juste beaucoup d’avis sur les espaces.",
    "Ton programme ne tourne pas en rond : il explore méthodiquement le même problème.",
    "Ce bug était évident. Maintenant que tu l’as trouvé.",
    "L’ordinateur fait exactement ce qu’on lui demande. C’est parfois le problème.",
    "Le code est propre, le café est chaud : profitons de ces deux minutes historiques.",
    "Un fichier d’en-tête, c’est une promesse. Le compilateur vérifie qu’on la tient.",
    "Le `Makefile` a dit « rien à faire ». Pour une fois, personne ne l’a contredit.",
    "Les tests passent. Les bugs restants organisent probablement une réunion discrète.",
    "Un tableau vide a rejoint la conversation. Il n’a pas grand-chose à ajouter.",
    "Ton code a besoin d’espace. La Norminette préfère quand il est bien placé.",
    "Le `char` voulait devenir `int`. Une promotion à suivre de près.",
    "La mémoire a bonne mine. On espère surtout qu’elle retrouve son chemin vers `free`.",
    "Un bon nom de variable fait gagner du temps. `truc2`, lui, cultive le mystère.",
    "Tu as corrigé la ligne 42. La ligne 43 commence à transpirer.",
    "Ce `else` attendait son tour depuis le début de la fonction.",
    "L’algorithme est élégant. Les cas particuliers ont demandé des chaises supplémentaires.",
    "Ton programme a passé le premier test. Il avance à son rythme, comme nous tous.",
    "La valeur est négative, mais le moral des troupes reste positif.",
    "Les prototypes sont comme les présentations : mieux vaut les faire avant d’appeler.",
    "La documentation est là pour toi. Elle ne mord que si tu fermes l’onglet trop tôt.",
    "Une boucle `for` est entrée dans le code. Elle avait déjà prévu sa sortie.",
    "La dernière virgule s’est invitée à la fête. Le compilateur vérifie sa carte.",
    "Ton code n’a pas peur des défis. Il serait quand même ravi d’avoir un exemple.",
    "Un octet a demandé plus de place. On lui a répondu de voir avec les sept autres bits.",
    "Le terminal est noir, mais ton avenir avec les pointeurs reste lumineux.",
    "La fonction a trouvé sa valeur de retour. Elle était juste derrière une accolade.",
    "Une erreur de compilation ne définit pas ton niveau. Elle définit surtout une ligne à regarder.",
    "Le débogage, c’est chercher ses clés alors qu’on les a soi-même cachées.",
    "Cette fonction fait une seule chose. Elle la fait juste dans douze fichiers.",
    "Le test du tableau vide est arrivé sans bagage, mais il avait beaucoup à dire.",
    "Ton `strcmp` compare des chaînes. Il évite soigneusement de comparer les personnes.",
    "Tu as écrit du C aujourd’hui. Les accolades apprécient ta compagnie.",
    "Le compilateur a levé un drapeau rouge. C’était son seul moyen de demander de l’attention.",
    "Les espaces et les tabulations se disputent la place. La Norminette arbitre.",
    "Ton code est comme un puzzle : la pièce manquante est souvent un point-virgule.",
    "Le `printf` de débogage aimerait rester dans le rendu. Il va falloir lui expliquer.",
    "Un `int` entre dans une boucle. Il en sort grandi, ou au moins incrémenté.",
    "Le bug a disparu après une pause. La pause réclame maintenant une place dans l’équipe.",
    "Ton programme parle au terminal. Pour l’instant, le terminal répond surtout par des erreurs.",
    "Le dernier test était jaloux des autres. Il a donc décidé de ne pas passer.",
    "La récursivité, c’est quand une fonction rappelle une fonction qui rappelle une fonction.",
    "Une chaîne sans caractère nul cherche encore où se termine son histoire.",
    "Le `switch` a cherché sa branche. On espère qu’il a trouvé une sortie.",
    "Ce pointeur est très sociable : il adore faire référence aux autres.",
    "Ton code compile et tes tests passent. La tasse de café n’en revient pas.",
    "La meilleure optimisation du jour : retrouver le bon dossier avant de compiler.",
    "Le bug s’était caché dans la condition. Une cachette classique, mais confortable.",
    "Une fonction de tri a mis de l’ordre dans sa vie. Le reste du projet suit doucement.",
    "Ton fichier a été sauvegardé. Le test suivant mérite donc une seconde chance.",
    "Le compilateur connaît tes erreurs de syntaxe. Tes progrès, lui, il les voit moins bien.",
    "Un `sizeof` ne dit pas tout, mais il mesure déjà une partie du problème.",
    "La fonction ne reçoit pas de paramètre. Elle apprécie cette journée sans rendez-vous.",
    "Il manque une accolade. Les autres ont organisé une recherche de groupe.",
    "La Norminette compte les lignes. Toi, tu peux aussi compter les progrès.",
    "Le dernier caractère est un saut de ligne. Il tient à partir avec panache.",
    "Ce `NULL` ne désigne personne. Pour une fois, c’est exactement ce qu’on voulait.",
    "Ton programme est déterminé : il échoue toujours de la même façon. C’est un début d’enquête.",
    "Un `free` en trop, c’est comme rendre deux fois la même clé : le propriétaire s’inquiète.",
    "Un tableau et son indice se sont rencontrés. Ils espèrent rester dans les limites.",
    "L’ordinateur n’a pas d’intuition. Heureusement, il a beaucoup de patience pour les essais.",
    "Ton meilleur outil de débogage est parfois une bonne nuit de sommeil.",
    "Les tests sont des amis exigeants : ils applaudissent seulement quand tu tiens ta promesse.",
    "Cette ligne avait l’air innocente. Le compilateur avait un autre témoignage.",
    "Un opérateur inattendu a frappé à la porte. `do-op` lui a répondu zéro.",
    "Ton code n’est pas encore fini, mais il sait déjà où trouver la documentation.",
    "Un bug de moins aujourd’hui, c’est une histoire de plus à raconter demain.",
    "Les reines sont bien placées. Elles demandent maintenant un échiquier plus grand."
  ];
  const box = document.getElementById('roastbox'), text = document.getElementById('roast');
  const toggle = document.getElementById('humor'), next = document.getElementById('next');
  let active = true;
  try { active = localStorage.getItem('ml-humor') !== 'off'; } catch (e) {}
  function showHumor() {
    box.hidden = !active;
    toggle.checked = active;
  }
  function nextJoke() {
    const i = phrases.indexOf(text.textContent);
    text.textContent = phrases[(i + 1 + Math.floor(Math.random() * (phrases.length - 1))) % phrases.length];
  }
  toggle.addEventListener('change', function () {
    active = toggle.checked;
    try { localStorage.setItem('ml-humor', active ? 'on' : 'off'); } catch (e) {}
    showHumor();
  });
  next.addEventListener('click', nextJoke);
  setInterval(function () { if (active && !document.hidden) nextJoke(); }, 30000);
  showHumor();

  const fontSelect = document.getElementById('font');
  if (fontSelect) {
    fontSelect.value = theme.font || 'dm';
    fontSelect.addEventListener('change', function () {
      let chosen = fontSelect.value;
      if (!theme.fonts || !theme.fonts.includes(chosen)) chosen = 'dm';
      theme.font = chosen;
      document.documentElement.setAttribute('data-font', chosen);
      try { localStorage.setItem('ml-font-choice', chosen); } catch (e) {}
    });
  }

  const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const canvas = document.getElementById('bg-matrix');
  if (canvas && canvas.getContext && !reduceMotion) {
    const ctx = canvas.getContext('2d');
    const glyphs = '01{}[]();*->&|!~^%+=<>0x7F0x42ELFSYSMEMASTCCLD';
    let cols = [], w = 0, h = 0;
    function resize() {
      w = canvas.width = window.innerWidth || 1280;
      h = canvas.height = window.innerHeight || 720;
      const count = Math.max(12, Math.floor(w / 28));
      cols = Array.from({length: count}, (_, i) => ({
        x: i * 28 + 10,
        y: Math.random() * -h,
        speed: 1.1 + Math.random() * 1.9
      }));
    }
    resize();
    window.addEventListener('resize', resize);
    setInterval(function () {
      const style = getComputedStyle(document.documentElement);
      const bg = style.getPropertyValue('--bg').trim() || '#100e16';
      const accent = style.getPropertyValue('--accent').trim() || '#b5a1ff';
      ctx.fillStyle = bg;
      ctx.globalAlpha = 0.14;
      ctx.fillRect(0, 0, w, h);
      ctx.globalAlpha = 0.55;
      ctx.fillStyle = accent;
      ctx.font = '12px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace';
      for (let i = 0; i < cols.length; i++) {
        const c = cols[i];
        const ch = glyphs[Math.floor(Math.random() * glyphs.length)];
        ctx.fillText(ch, c.x, c.y);
        c.y += c.speed * 13;
        if (c.y > h + 40 && Math.random() > 0.94) c.y = -20;
      }
    }, 65);
  }

  const bgTerm = document.getElementById('bg-terminal');
  if (bgTerm) {
    const termLines = [
      '$ cc -Wall -Wextra -Werror -std=c99 -O2 -c unit.c -o unit.o',
      '[elf64] .text 0x00401040 · .rodata 0x00402000 · align 16B',
      '[bwrap] unshare --user --net --ipc --pid --ro-bind /usr /usr',
      '[seccomp] bpf filter active · 24 syscalls blocked (x86_64)',
      '[ld] symbol table verified via nm -u · 0 forbidden symbol',
      '[mem] address space RLIMIT_AS=256M · pipe capture 64 KiB',
      '[lexer] syntax & style analysis · 0 formatting violation',
      '[runner] process group isolated · session cleanup verified',
      '$ ar rcs libunit.a unit.o && ranlib libunit.a',
      '[status] pipeline ready · local sqlite WAL journal synced'
    ];
    let lineIdx = 0, charPos = 0, visible = [];
    if (reduceMotion) {
      bgTerm.textContent = termLines.slice(0, 6).join('\n');
    } else {
      setInterval(function () {
        const current = termLines[lineIdx];
        charPos += 3;
        const partial = current.slice(0, charPos);
        const lines = visible.concat([partial + '▌']);
        bgTerm.textContent = lines.join('\n');
        if (charPos >= current.length) {
          visible.push(current);
          if (visible.length > 7) visible.shift();
          lineIdx = (lineIdx + 1) % termLines.length;
          charPos = 0;
        }
      }, 75);
    }
  }

  // Atome en perspective : un électron par dernier résultat réussi ou à revoir.
  // Le noyau est unique ; les incomplets et non corrigés ne créent pas d’électron.
  const heroArt = document.getElementById('hero-art');
  const atomCanvas = document.getElementById('atom-canvas');
  const atomSvg = document.getElementById('atom-svg');
  const atomContext = atomCanvas && atomCanvas.getContext ? atomCanvas.getContext('2d') : null;
  let redrawAtom = function () {};
  const atomState = {protons: 0, neutrons: 0, electrons: 0, results: [], orbits: [], nucleons: [], stars: []};

  function rebuildAtomBodies() {
    atomState.progress = atomState.electrons ? atomState.protons / atomState.electrons : 0;
    // Un électron, donc une orbite, pour chaque résultat exploitable.
    atomState.orbits = atomState.results.map(function (result, i) {
      const slot = i % 3;
      return {
        particleCount: 1, particles: [result],
        rx: 150 + (i >= 3 ? (i % 5 - 2) * 3 : 0),
        ry: 150 + (i >= 3 ? (i % 5 - 2) * 3 : 0),
        tiltX: i < 3 ? (slot === 1 ? 1.25 : 1.0) : 0.65 + (i % 7) * .11,
        tiltY: i < 3 ? (slot - 1) * 0.95 : i * 1.28,
        tiltZ: slot * Math.PI / 3,
        speed: 1.5 * (slot % 2 ? -1 : 1) * (0.22 + slot * 0.05),
        phase: i * 1.7, precess: 0
      };
    });

  }

  window.__mlUpdateAtomScope = function (mod, rows) {
    // La recherche ne modifie pas les comptes ; seul le filtre de module les modifie.
    const scoped = rows.filter(function (row) { return !mod || row.dataset.module === mod; });
    atomState.electrons = scoped.length;
    atomState.protons = scoped.filter(function (row) { return row.dataset.result === 'passed'; }).length;
    atomState.neutrons = scoped.filter(function (row) { return row.dataset.result === 'failed'; }).length;
    atomState.results = scoped.map(function (row) { return row.dataset.result; }).filter(function (r) { return r === 'passed' || r === 'failed'; });
    rebuildAtomBodies();
    if (!atomContext && atomSvg) {
      atomSvg.innerHTML = '<circle class="atom-core" cx="0" cy="0" r="15"/>' + atomState.orbits.map(function (orb, i) {
        const x = (176 * Math.cos(orb.phase)).toFixed(2), y = (68 * Math.sin(orb.phase)).toFixed(2);
        const color = orb.particles[0] === 'failed' ? '#ff5f70' : '#3cbbff';
        return '<g class="atom-shell" transform="rotate(' + (i * 53 % 180) + ')"><ellipse class="atom-orbit" cx="0" cy="0" rx="176" ry="68"/><g class="atom-electron" data-rx="176" data-ry="68" data-speed="' + orb.speed + '" data-phase="' + orb.phase + '" transform="translate(' + x + ',' + y + ')"><circle r="5" fill="' + color + '"/></g></g>';
      }).join('');
    }
    if (heroArt) {
      heroArt.dataset.protons = String(atomState.protons);
      heroArt.dataset.neutrons = String(atomState.neutrons);
      heroArt.dataset.electrons = String(atomState.electrons);
      heroArt.dataset.animatedElectrons = String(atomState.results.length);
      heroArt.dataset.animatedOrbits = String(atomState.orbits.length);
      heroArt.dataset.atomScope = mod || 'piscine';
      const badge = document.getElementById('progress-piscine-badge');
      const scope = mod ? mod.toUpperCase() : (badge ? badge.textContent : 'Piscine');
      heroArt.setAttribute('aria-label', scope + ' : ' + atomState.protons + ' réussis, ' + atomState.neutrons + ' à revoir sur ' + atomState.electrons + ' exercices');
    }
    redrawAtom();
  };

  function project3D(x, y, z, cx, cy) {
    const fov = 460;
    const scale = fov / (fov + z);
    return {x: cx + x * scale, y: cy + y * scale, scale: scale, z: z};
  }

  function rotate3D(x, y, z, ax, ay, az) {
    // Rotation Z
    let x1 = x * Math.cos(az) - y * Math.sin(az);
    let y1 = x * Math.sin(az) + y * Math.cos(az);
    let z1 = z;
    // Rotation X
    let y2 = y1 * Math.cos(ax) - z1 * Math.sin(ax);
    let z2 = y1 * Math.sin(ax) + z1 * Math.cos(ax);
    let x2 = x1;
    // Rotation Y
    let x3 = x2 * Math.cos(ay) + z2 * Math.sin(ay);
    let z3 = -x2 * Math.sin(ay) + z2 * Math.cos(ay);
    return {x: x3, y: y2, z: z3};
  }

  if (atomContext) {
    const actx = atomContext;
    if (actx && atomSvg) {
      atomSvg.style.opacity = '0';
    }
    const cw = atomCanvas.width = 420;
    const ch = atomCanvas.height = 420;
    const cx = cw / 2;
    const cy = ch / 2;

    function drawAtomFrame(dt) {
      if (!actx) return;
      actx.clearRect(0, 0, cw, ch);
      const style = getComputedStyle(document.documentElement);
      const accent = style.getPropertyValue('--accent').trim() || '#70cfff';
      const back = [], front = [];

      // Chaque électron possède son anneau incliné dans l’espace.
      atomState.orbits.forEach(function (orb) {
        const add = function (item, z) { (z < 0 ? back : front).push(item); };
        const steps = atomState.orbits.length > 24 ? 28 : 56;
        for (let i = 0; i < steps; i++) {
          const a = 2 * Math.PI * i / steps, b = 2 * Math.PI * (i + 1) / steps;
          const x = rotate3D(Math.cos(a)*orb.rx, Math.sin(a)*orb.ry, 0, orb.tiltX, orb.tiltY, orb.tiltZ);
          const y = rotate3D(Math.cos(b)*orb.rx, Math.sin(b)*orb.ry, 0, orb.tiltX, orb.tiltY, orb.tiltZ);
          add({kind:'line', a:project3D(x.x,x.y,x.z,cx,cy), b:project3D(y.x,y.y,y.z,cx,cy)}, (x.z+y.z)/2);
        }
        for (let i = 0; i < orb.particleCount; i++) {
          const a = orb.phase + dt * orb.speed + 2 * Math.PI * i / orb.particleCount;
          const v = rotate3D(Math.cos(a)*orb.rx, Math.sin(a)*orb.ry, 0, orb.tiltX, orb.tiltY, orb.tiltZ);
          add({kind:'electron', p:project3D(v.x,v.y,v.z,cx,cy), result:orb.particles[i]}, v.z);
        }
      });
      function renderPass(items, foreground) {
        items.forEach(function (item) {
          if (item.kind === 'line') {
            actx.strokeStyle = accent;
            actx.globalAlpha = (foreground ? 0.78 : 0.38) * Math.min(1, 4 / Math.sqrt(Math.max(1, atomState.orbits.length)));
            actx.lineWidth = foreground ? 1.4 : 1;
            actx.beginPath(); actx.moveTo(item.a.x,item.a.y); actx.lineTo(item.b.x,item.b.y); actx.stroke();
          } else {
            const size = (atomState.results.length > 45 ? 3.5 : 6) * item.p.scale;
            actx.globalAlpha = foreground ? 1 : 0.7;
            const electronColor = item.result === 'failed' ? '#ff5f70' : '#3cbbff';
            actx.fillStyle = electronColor;
            actx.shadowColor = electronColor; actx.shadowBlur = 9;
            actx.beginPath(); actx.arc(item.p.x,item.p.y,Math.max(1.7,size),0,Math.PI*2); actx.fill();
            actx.shadowBlur = 0;
            actx.fillStyle = 'rgba(255,255,255,0.8)';
            actx.beginPath(); actx.arc(item.p.x-size*.25,item.p.y-size*.28,Math.max(.6,size*.27),0,Math.PI*2); actx.fill();
          }
        });
        actx.globalAlpha = 1;
      }
      renderPass(back, false);

      // Un seul noyau : sa lueur augmente avec les réussites du périmètre.
      const glow = actx.createRadialGradient(cx-5,cy-6,1,cx,cy,40);
      glow.addColorStop(0, 'rgba(255,255,255,0.95)');
      glow.addColorStop(0.20, accent);
      glow.addColorStop(1, 'rgba(80,160,220,0)');
      actx.globalAlpha = 0.45 + 0.5 * atomState.progress;
      actx.fillStyle = glow;
      actx.beginPath(); actx.arc(cx,cy,40,0,Math.PI*2); actx.fill();
      actx.globalAlpha = 1;
      actx.fillStyle = accent;
      actx.beginPath(); actx.arc(cx,cy,10,0,Math.PI*2); actx.fill();
      actx.fillStyle = 'rgba(255,255,255,.72)';
      actx.beginPath(); actx.arc(cx-3,cy-3,3,0,Math.PI*2); actx.fill();
      renderPass(front, true);
    }

    redrawAtom = function () { if (reduceMotion) drawAtomFrame(0); };
    drawAtomFrame(0);
    if (!reduceMotion) {
      const t0Atom = performance.now();
      let lastAtomFrame = 0;
      const loopAtom3D = function (now) {
        if (!document.hidden && now - lastAtomFrame >= 33) {
          drawAtomFrame((now - t0Atom) / 1000);
          lastAtomFrame = now;
        }
        requestAnimationFrame(loopAtom3D);
      };
      requestAnimationFrame(loopAtom3D);
    }
  } else if (atomSvg && !reduceMotion) {
    // Repli SVG 2D si le canvas HTML5 n'est pas disponible
    {
      const t0 = performance.now();
      const stepAtom = function (now) {
        const dt = (now - t0) / 1000;
        const electrons = Array.from(document.querySelectorAll('#atom-svg .atom-electron'));
        for (let i = 0; i < electrons.length; i += 1) {
          const el = electrons[i];
          const rx = parseFloat(el.getAttribute('data-rx') || '176');
          const ry = parseFloat(el.getAttribute('data-ry') || '68');
          const speed = parseFloat(el.getAttribute('data-speed') || '1');
          const phase = parseFloat(el.getAttribute('data-phase') || '0');
          const angle = phase + dt * speed;
          const x = (Math.cos(angle) * rx).toFixed(2);
          const y = (Math.sin(angle) * ry).toFixed(2);
          el.setAttribute('transform', 'translate(' + x + ',' + y + ')');
        }
        requestAnimationFrame(stepAtom);
      };
      requestAnimationFrame(stepAtom);
    }
  }

  // Sélecteur de consultation des piscines débloquées (C -> C++ -> Python)
  const payloadEl = document.getElementById('piscine-payload');
  let piscinesData = {};
  if (payloadEl) {
    try { piscinesData = JSON.parse(payloadEl.textContent || '{}'); } catch (e) { piscinesData = {}; }
  }
  const stepBtns = Array.from(document.querySelectorAll('[data-piscine-select]'));
  stepBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const pKey = btn.getAttribute('data-piscine-select');
      const info = piscinesData[pKey];
      if (!info || !info.unlocked) return;

      stepBtns.forEach(function (b) {
        b.classList.toggle('is-active', b.getAttribute('data-piscine-select') === pKey);
      });

      const ring = document.getElementById('progress-ring');
      const pctEl = document.getElementById('progress-percent');
      const subEl = document.getElementById('progress-subtitle');
      const badgeEl = document.getElementById('progress-piscine-badge');
      if (ring) ring.style.setProperty('--progress', String(info.percent));
      if (pctEl) pctEl.textContent = info.percent + ' %';
      if (subEl) subEl.textContent = info.done + ' ' + (info.done === 1 ? 'exercice' : 'exercices') + ' sur ' + info.total + ' réussis';
      if (badgeEl) badgeEl.textContent = info.label;

      const statVal = document.getElementById('stat-done-value');
      const statNote = document.getElementById('stat-done-note');
      if (statVal) statVal.innerHTML = info.done + ' <span>/ ' + info.total + '</span>';
      if (statNote) statNote.textContent = 'Au dernier essai · Parcours disponible (' + info.label + ')';

      const exTitle = document.getElementById('exercises-panel-title');
      const exTag = document.getElementById('exercises-panel-tag');
      const exBar = document.getElementById('exercises-progress-bar');
      const exList = document.getElementById('exercise-list');
      if (exTitle) exTitle.textContent = '42 · ' + info.label;
      if (exTag) exTag.textContent = info.done + ' / ' + info.total;
      if (exBar) exBar.style.width = info.percent + '%';
      if (exList) {
        exList.innerHTML = info.tiles_html + '<p class="no-results" id="no-results" hidden>Aucun exercice ne correspond à cette recherche.</p>';
      }
      if (moduleSelect && Array.isArray(info.modules)) {
        moduleSelect.innerHTML = '<option value="">Tous les modules</option>' + info.modules.map(function (m) {
          return '<option value="' + m + '">' + m.toUpperCase() + '</option>';
        }).join('');
      }
      const vizTitle = document.getElementById('viz-modules-title');
      const vizTag = document.getElementById('viz-modules-tag');
      const vizGrid = document.getElementById('viz-modules-grid');
      if (vizTitle) vizTitle.textContent = 'Progression par module · ' + info.label;
      if (vizTag && Array.isArray(info.viz_modules)) vizTag.textContent = info.viz_modules.length + ' MODULES';
      if (vizGrid && Array.isArray(info.viz_modules)) {
        vizGrid.innerHTML = info.viz_modules.map(function (m) {
          return '<div class="mod-item ' + (m.cls === 'ok' ? 'ok-mod' : '') + '"><div class="mod-top"><strong>' + m.label + '</strong><span>' + m.done + ' / ' + m.total + '</span></div><div class="mod-bar" aria-hidden="true"><span style="width:' + m.percent + '%"></span></div></div>';
        }).join('');
      }
      filter();
    });
  });

  filter();

  document.addEventListener('visibilitychange', function () {
    if (document.hidden) return;
    const activeEl = document.activeElement;
    if (activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'SELECT')) return;
    if (document.querySelector('details.attempt[open]')) return;
    if (location.protocol === 'http:' || location.protocol === 'https:') {
      fetch('/api/history').then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
        if (d && String(d.count) !== String(document.documentElement.getAttribute('data-count') || '')) {
          location.reload();
        }
      }).catch(function () {});
    }
  });
})();
