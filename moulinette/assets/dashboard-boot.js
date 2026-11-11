/* Theme and font choices are stored locally; nothing is sent over the network. */
(function () {
  const names = ['aurora', 'nightowl', 'ocean', 'forest', 'ember', 'sakura', 'cyberpunk', 'matcha', 'espresso', 'nordic', 'sunset'];
  const fonts = ['dm', 'mono', 'serif', 'system', 'humanist'];
  let choice = 'aurora', last = null, font = 'dm', available = true;
  try {
    const stored = localStorage.getItem('ml-theme-choice');
    choice = stored || 'aurora';
    last = localStorage.getItem('ml-theme-last');
    font = localStorage.getItem('ml-font-choice') || 'dm';
    if (!stored) localStorage.setItem('ml-theme-choice', choice);
  } catch (e) { available = false; }
  if (choice !== 'random' && !names.includes(choice)) choice = 'aurora';
  if (!fonts.includes(font)) font = 'dm';
  let active = choice;
  if (choice === 'random') {
    const options = names.filter(name => name !== last);
    active = options[Math.floor(Math.random() * options.length)];
  }
  document.documentElement.setAttribute('data-theme', active);
  document.documentElement.setAttribute('data-font', font);
  if (choice === 'random' && available) {
    try { localStorage.setItem('ml-theme-last', active); }
    catch (e) { available = false; }
  }
  window.__mlThemeState = {choice, active, font, fonts, available, names};
})();
