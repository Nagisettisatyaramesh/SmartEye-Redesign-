/* SmartEye eQMS — site behaviour */
(() => {
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const narrow = () => matchMedia('(max-width: 860px)').matches;
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

/* ---------- scroll loop: one rAF for everything scroll-linked ---------- */
const onScroll = [];
let ticking = false;
function frame(){ ticking = false; onScroll.forEach(fn => fn()); }
function request(){ if(!ticking){ ticking = true; requestAnimationFrame(frame); } }
addEventListener('scroll', request, {passive:true});
addEventListener('resize', request);

/* ---------- header: border, tuck on scroll down ---------- */
const header = $('.top');
let lastY = scrollY;
onScroll.push(() => {
  const y = scrollY;
  header.classList.toggle('scrolled', y > 8);
  const menuOpen = $('.nav.open');
  if(!reduce && !menuOpen) header.classList.toggle('tucked', y > 300 && y > lastY + 4);
  if(y < lastY - 4) header.classList.remove('tucked');
  lastY = y;
});
header.addEventListener('focusin', () => header.classList.remove('tucked'));

/* ---------- mobile menu ---------- */
const mb = $('.menu-btn'), nav = $('#nav');
if(mb){
  const set = o => { nav.classList.toggle('open', o); mb.setAttribute('aria-expanded', o); mb.textContent = o ? 'Close' : 'Menu'; };
  mb.addEventListener('click', () => set(!nav.classList.contains('open')));
  nav.addEventListener('click', e => { if(e.target.closest('a')) set(false); });
  addEventListener('keydown', e => { if(e.key === 'Escape' && nav.classList.contains('open')){ set(false); mb.focus(); } });
}

/* ---------- page progress hairline ---------- */
const bar = $('.progress i');
if(bar) onScroll.push(() => {
  const max = document.documentElement.scrollHeight - innerHeight;
  bar.style.transform = `scaleX(${max > 0 ? clamp(scrollY / max) : 0})`;
});

/* ---------- headline word rise ---------- */
$$('.rise').forEach(h => {
  if(reduce){ h.classList.add('go'); return; }
  let i = 0;
  const wrap = node => {
    [...node.childNodes].forEach(n => {
      if(n.nodeType === 3){
        const frag = document.createDocumentFragment();
        const prev = n.previousSibling;
        n.textContent.split(/(\s+)/).forEach((part, pi) => {
          if(!part) return;
          // punctuation straight after an inline element (e.g. "</em>,") stays glued to it
          if(pi === 0 && prev && prev.nodeType === 1 && !/^\s/.test(part)){
            const last = [...prev.querySelectorAll('.w>span')].pop();
            if(last){ last.textContent += part; return; }
          }
          if(/^\s+$/.test(part)){ frag.appendChild(document.createTextNode(part)); return; }
          const w = document.createElement('span'); w.className = 'w';
          const s = document.createElement('span'); s.textContent = part;
          s.style.transitionDelay = (0.12 + i++ * 0.055) + 's';
          w.appendChild(s); frag.appendChild(w);
        });
        n.replaceWith(frag);
      } else if(n.nodeType === 1) wrap(n);
    });
  };
  wrap(h);
  requestAnimationFrame(() => requestAnimationFrame(() => h.classList.add('go')));
});

/* ---------- reveal on enter (with stagger for grouped children) ---------- */
$$('[data-stagger]').forEach(g => [...g.children].forEach((c, k) => { c.setAttribute('data-reveal',''); c.style.setProperty('--d', (k * 0.08) + 's'); }));
const io = new IntersectionObserver(es => es.forEach(e => {
  if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); }
}), {rootMargin:'0px 0px -8% 0px'});
$$('[data-reveal]').forEach(el => reduce ? el.classList.add('in') : io.observe(el));

/* ---------- parallax (subtle) ---------- */
const para = $$('[data-parallax]');
if(para.length && !reduce) onScroll.push(() => para.forEach(el => {
  const r = el.parentElement.getBoundingClientRect();
  if(r.bottom < 0 || r.top > innerHeight) return;
  const f = parseFloat(el.dataset.parallax) || .12;
  const c = (r.top + r.height / 2 - innerHeight / 2);
  el.style.transform = `translateY(${(-c * f).toFixed(1)}px)`;
}));
$$('.cta-band').forEach(b => { if(!reduce) onScroll.push(() => {
  const r = b.getBoundingClientRect(); b.style.setProperty('--py', ((r.top - innerHeight/2) * -0.15).toFixed(1));
}); });

/* ---------- lifecycle line draws as it enters ---------- */
$$('.stages').forEach(s => { if(!reduce) onScroll.push(() => {
  const r = s.getBoundingClientRect();
  s.style.setProperty('--p', clamp((innerHeight * .9 - r.top) / (innerHeight * .5)).toFixed(3));
}); });

/* ---------- pinned scroll stories (home): design-control waterfall and the SmartEye hub ---------- */
$$('[data-story]').forEach(story => {
  const steps = $$('.step', story), rails = $$('.rail b', story);
  const marks = $$('.box[data-at], .node[data-at]', story), spokes = $$('.spoke', story);
  const loops = $$('.loop, .loop-label', story), flow = $('.flow', story);
  const flowLen = flow ? flow.getTotalLength() : 0;
  if(flow){ flow.style.strokeDasharray = flowLen; flow.style.strokeDashoffset = flowLen; }
  spokes.forEach(l => { const len = Math.hypot(l.x2.baseVal.value - l.x1.baseVal.value, l.y2.baseVal.value - l.y1.baseVal.value);
    l.style.strokeDasharray = len; l.style.strokeDashoffset = len; l.dataset.len = len; });
  const n = steps.length;
  let cur = -1;
  onScroll.push(() => {
    if(narrow() || reduce) return;
    const r = story.getBoundingClientRect();
    const p = clamp(-r.top / (r.height - innerHeight));
    const pos = p * n;
    const idx = Math.min(n - 1, Math.floor(pos));
    rails.forEach((b, k) => b.style.transform = `scaleX(${clamp(pos - k)})`);
    if(flow) flow.style.strokeDashoffset = flowLen * (1 - clamp(p * 1.1));
    if(idx !== cur){
      cur = idx;
      steps.forEach((s, k) => { s.classList.toggle('on', k === idx); s.setAttribute('aria-hidden', k !== idx); });
      marks.forEach(m => { const at = +m.dataset.at; m.classList.toggle('lit', idx >= at); m.classList.toggle('now', idx === at); });
      spokes.forEach(l => { l.style.strokeDashoffset = idx >= +l.dataset.at ? 0 : l.dataset.len; });
      loops.forEach(l => l.classList.toggle('lit', idx >= +l.dataset.from));
    }
  });
});

/* ---------- horizontal pinned scroll (product) ---------- */
const hs = $('[data-hscroll]');
if(hs){
  const track = $('.hscroll-track', hs), fill = $('.hscroll-bar i', hs), count = $('.hscroll-count b', hs);
  const panels = $$('.panel', hs);
  const size = () => {
    if(narrow() || reduce){ hs.style.height = ''; return; }
    const over = track.scrollWidth - innerWidth;
    hs.style.height = (innerHeight + Math.max(0, over)) + 'px';
  };
  size(); addEventListener('resize', size); addEventListener('load', size);
  onScroll.push(() => {
    if(narrow() || reduce) return;
    const r = hs.getBoundingClientRect();
    const over = track.scrollWidth - innerWidth;
    const p = clamp(-r.top / Math.max(1, r.height - innerHeight));
    track.style.transform = `translate3d(${(-over * p).toFixed(1)}px,0,0)`;
    fill.style.transform = `scaleX(${p})`;
    if(count) count.textContent = Math.min(panels.length, 1 + Math.floor(p * panels.length * .999));
  });
}

/* ---------- focus list: item nearest the viewport centre is lit ---------- */
$$('[data-focus-list]').forEach(list => {
  const items = [...list.children];
  if(reduce){ items.forEach(i => i.classList.add('in-focus')); return; }
  onScroll.push(() => {
    const mid = innerHeight * .55;
    items.forEach(i => { const r = i.getBoundingClientRect(); if(r.top < mid) i.classList.add('in-focus'); else i.classList.remove('in-focus'); });
  });
});

/* ---------- statement: words light up as you read ---------- */
$$('[data-read]').forEach(el => {
  const words = $$('.dim', el);
  if(reduce) return;
  onScroll.push(() => {
    const r = el.getBoundingClientRect();
    const p = clamp((innerHeight * .8 - r.top) / (r.height + innerHeight * .35));
    const k = Math.round(p * words.length);
    words.forEach((w, j) => w.classList.toggle('lit', j < k));
  });
});

/* ---------- article table of contents ---------- */
const prose = $('.prose[data-toc]'), toc = $('#toc-list');
if(prose && toc){
  const hs2 = $$('h2', prose);
  if(hs2.length < 2){ toc.closest('.toc').remove(); }
  else {
    hs2.forEach((h, k) => {
      h.id = h.id || 's-' + (k + 1) + '-' + h.textContent.toLowerCase().replace(/[^a-z0-9]+/g,'-').slice(0,40);
      const li = document.createElement('li'); const a = document.createElement('a');
      a.href = '#' + h.id; a.textContent = h.textContent; li.appendChild(a); toc.appendChild(li);
    });
    const links = $$('a', toc);
    onScroll.push(() => {
      let a = 0; hs2.forEach((h, k) => { if(h.getBoundingClientRect().top < 140) a = k; });
      links.forEach((l, k) => l.classList.toggle('active', k === a));
    });
  }
}

/* ---------- video facade ---------- */
$$('[data-video]').forEach(b => b.addEventListener('click', () => {
  const f = document.createElement('iframe');
  f.src = `https://www.youtube-nocookie.com/embed/${b.dataset.video}?autoplay=1&rel=0`;
  f.title = b.getAttribute('aria-label') || 'Video';
  f.allow = 'autoplay; encrypted-media; picture-in-picture'; f.allowFullscreen = true;
  b.replaceChildren(f); b.style.cursor = 'default';
}, {once:true}));

/* ---------- demo form ---------- */
const countries = "Afghanistan|Albania|Algeria|Andorra|Angola|Antigua and Barbuda|Argentina|Armenia|Australia|Austria|Azerbaijan|The Bahamas|Bahrain|Bangladesh|Barbados|Belarus|Belgium|Belize|Benin|Bhutan|Bolivia|Bosnia and Herzegovina|Botswana|Brazil|Brunei|Bulgaria|Burkina Faso|Burundi|Cabo Verde|Cambodia|Cameroon|Canada|Central African Republic|Chad|Chile|China|Colombia|Comoros|Congo, Democratic Republic of the|Congo, Republic of the|Costa Rica|Côte d’Ivoire|Croatia|Cuba|Cyprus|Czech Republic|Denmark|Djibouti|Dominica|Dominican Republic|East Timor (Timor-Leste)|Ecuador|Egypt|El Salvador|Equatorial Guinea|Eritrea|Estonia|Eswatini|Ethiopia|Fiji|Finland|France|Gabon|The Gambia|Georgia|Germany|Ghana|Greece|Grenada|Guatemala|Guinea|Guinea-Bissau|Guyana|Haiti|Honduras|Hungary|Iceland|India|Indonesia|Iran|Iraq|Ireland|Israel|Italy|Jamaica|Japan|Jordan|Kazakhstan|Kenya|Kiribati|Korea, North|Korea, South|Kosovo|Kuwait|Kyrgyzstan|Laos|Latvia|Lebanon|Lesotho|Liberia|Libya|Liechtenstein|Lithuania|Luxembourg|Madagascar|Malawi|Malaysia|Maldives|Mali|Malta|Marshall Islands|Mauritania|Mauritius|Mexico|Micronesia, Federated States of|Moldova|Monaco|Mongolia|Montenegro|Morocco|Mozambique|Myanmar (Burma)|Namibia|Nauru|Nepal|Netherlands|New Zealand|Nicaragua|Niger|Nigeria|North Macedonia|Norway|Oman|Pakistan|Palau|Panama|Papua New Guinea|Paraguay|Peru|Philippines|Poland|Portugal|Qatar|Romania|Russia|Rwanda|Saint Kitts and Nevis|Saint Lucia|Saint Vincent and the Grenadines|Samoa|San Marino|Sao Tome and Principe|Saudi Arabia|Senegal|Serbia|Seychelles|Sierra Leone|Singapore|Slovakia|Slovenia|Solomon Islands|Somalia|South Africa|Spain|Sri Lanka|Sudan|Sudan, South|Suriname|Sweden|Switzerland|Syria|Taiwan|Tajikistan|Tanzania|Thailand|Togo|Tonga|Trinidad and Tobago|Tunisia|Turkey|Turkmenistan|Tuvalu|Uganda|Ukraine|United Arab Emirates|United Kingdom|United States|Uruguay|Uzbekistan|Vanuatu|Vatican City|Venezuela|Vietnam|Yemen|Zambia|Zimbabwe".split('|');
$$('select[data-countries]').forEach(sel => countries.forEach(c => sel.add(new Option(c, c))));
/* The form posts to the endpoint in data-endpoint (e.g. the site's existing Contact Form 7 handler).
   Until one is set, it says so plainly and points people to email instead of pretending to send. */
$$('form[data-demo-form]').forEach(form => form.addEventListener('submit', async e => {
  e.preventDefault();
  const f = form.elements, s = $('.form-status', form);
  const name = f.namedItem('name'), email = f.namedItem('email');
  if(!name.value.trim() || !email.value || !email.checkValidity()){
    s.classList.add('error');
    s.textContent = 'Enter your name and a valid email address.';
    (name.value.trim() ? email : name).focus(); return;
  }
  const endpoint = form.dataset.endpoint;
  if(!endpoint){
    s.classList.add('error');
    s.innerHTML = 'Online requests aren’t available yet. Please email <a href="mailto:info@scube-technologies.com">info@scube-technologies.com</a>.';
    return;
  }
  try{
    const res = await fetch(endpoint, {method:'POST', body:new FormData(form)});
    if(!res.ok) throw new Error(res.status);
    s.classList.remove('error'); s.textContent = 'Thank you. Your request has been sent.'; form.reset();
  }catch{
    s.classList.add('error');
    s.innerHTML = 'Your request couldn’t be sent. Please email <a href="mailto:info@scube-technologies.com">info@scube-technologies.com</a>.';
  }
}));

request();
})();
