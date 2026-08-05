#!/usr/bin/env python3
"""Génère le site multi-pages Enfance Éclairée dans site/ à partir de template.html.
Les articles du blog sont lus dans content/blog/*.md (gérés via Decap CMS sur /admin)."""
import base64, pathlib, re, shutil

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "site"
BASE_URL = "https://enfance-eclairee.fr"
OUT.mkdir(exist_ok=True)

html = (ROOT / "template.html").read_text()

# ---------- découpage ----------
head = re.search(r"<head>(.*?)</head>", html, re.S).group(1)
body = re.search(r"<body>(.*?)</body>", html, re.S).group(1)
script = re.search(r"<script>(.*?)</script>\s*$", body, re.S).group(1)

parts = re.split(r"<!-- =+ ([^=]+?) =+ -->", body)
chunks = {}
for i in range(1, len(parts) - 1, 2):
    name = parts[i].strip()
    content = parts[i + 1]
    # retirer le script final du dernier chunk
    content = re.sub(r"<script>.*?</script>\s*$", "", content, flags=re.S)
    # retirer le bouton fab du footer chunk (on le gère à part)
    chunks[name] = content

# extraire le call-fab du chunk FOOTER
fab = re.search(r'(<a href="tel:[^"]*" class="call-fab".*?</a>)', chunks["FOOTER"], re.S).group(1)
chunks["FOOTER"] = chunks["FOOTER"].replace(fab, "")

# ---------- nav par page ----------
PAGES_NAV = [
    ("methode.html", "La pédagogie"),
    ("ateliers.html", "Ateliers &amp; formations"),
    ("qui-sommes-nous.html", "Qui sommes-nous"),
    ("blog.html", "Blog"),
    ("contact.html", "Contact"),
]

def nav(active):
    cur = ' class="current"'
    lis = "\n".join(
        f'      <li><a href="{href}"{cur if href == active else ""}>{label}</a></li>'
        for href, label in PAGES_NAV
    )
    return f'''<nav id="nav">
  <div class="wrap nav-in">
    <a href="index.html" class="brand">
      <svg class="crest" viewBox="0 0 200 234"><use href="#crest"/></svg>
      <span class="brand-name">Enfance Éclairée<em>Pédagogie Montessori · Metz</em></span>
    </a>
    <ul class="nav-links" id="navLinks">
{lis}
    </ul>
    <a href="contact.html" class="btn small nav-cta">Demander un programme</a>
    <button class="burger" id="burger" aria-label="Menu"><span></span><span></span><span></span></button>
  </div>
</nav>'''

GARLAND = '''<svg viewBox="0 0 260 34" style="width:200px;margin:18px auto 0;display:block" aria-hidden="true">
      <path d="M5 5 Q130 26 255 5" fill="none" stroke="#C2A277" stroke-width="2"/>
      <path d="M30 8 l9 15 9-13Z" fill="#A9BFA0"/><path d="M75 12 l9 15 9-13Z" fill="#EACE8C"/>
      <path d="M122 14 l9 15 9-13Z" fill="#EFB9A2"/><path d="M169 12 l9 15 9-13Z" fill="#A9BFA0"/>
      <path d="M214 8 l9 15 9-13Z" fill="#EACE8C"/>
    </svg>'''

def page_hero(eyebrow, title, sub):
    return f'''<header class="page-hero has-blobs">
  <div class="blob b-amande slow" style="width:340px;height:340px;left:-140px;top:-60px"></div>
  <div class="blob b-rose rev" style="width:300px;height:300px;right:-120px;bottom:-100px"></div>
  <svg class="big-arc" viewBox="0 0 600 600" style="width:420px;right:-120px;top:-160px"><circle cx="300" cy="300" r="260" fill="none" stroke="#F0C3AE" stroke-width="2.5" stroke-dasharray="6 14" stroke-linecap="round"/></svg>
  <span class="doodle" style="width:24px;height:24px;left:12%;top:34%;color:var(--gold)"><svg viewBox="0 0 24 24" stroke="currentColor"><use href="#doodle-sparkle"/></svg></span>
  <span class="doodle" style="width:22px;height:22px;right:14%;top:30%;color:var(--rose);animation-delay:1s"><svg viewBox="0 0 24 24" stroke="currentColor"><use href="#doodle-heart"/></svg></span>
  <div class="wrap">
    <span class="eyebrow">{eyebrow}</span>
    <h1>{title}</h1>
    <p>{sub}</p>
    {GARLAND}
  </div>
</header>'''

# ---------- JS commun avec gardes ----------
JS = """
// nav
const nav=document.getElementById('nav');
addEventListener('scroll',()=>nav.classList.toggle('scrolled',scrollY>10));
const burger=document.getElementById('burger'),links=document.getElementById('navLinks');
burger.addEventListener('click',()=>{burger.classList.toggle('open');links.classList.toggle('open')});
links.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{burger.classList.remove('open');links.classList.remove('open')}));

// reveal
const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}}),{threshold:.12});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));

// tabs (page ateliers)
document.querySelectorAll('.tab').forEach(t=>t.addEventListener('click',()=>{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.age-panel').forEach(x=>x.classList.remove('active'));
  t.classList.add('active');
  document.getElementById('panel-'+t.dataset.age).classList.add('active');
}));

// temoignages (accueil)
const track=document.getElementById('tTrack');
if(track){
  const slides=track.children.length,dotsBox=document.getElementById('tDots');
  let cur=0,timer;
  for(let i=0;i<slides;i++){const d=document.createElement('span');d.className='t-dot'+(i?'':' active');d.onclick=()=>go(i);dotsBox.appendChild(d)}
  function go(i){cur=(i+slides)%slides;track.style.transform=`translateX(-${cur*100}%)`;
    dotsBox.querySelectorAll('.t-dot').forEach((d,k)=>d.classList.toggle('active',k===cur));restart()}
  function restart(){clearInterval(timer);timer=setInterval(()=>go(cur+1),5200)}
  document.getElementById('tPrev').onclick=()=>go(cur-1);
  document.getElementById('tNext').onclick=()=>go(cur+1);
  restart();
}

// faq (page ateliers)
document.querySelectorAll('.faq-q').forEach(q=>q.addEventListener('click',()=>{
  const item=q.parentElement,a=item.querySelector('.faq-a'),open=item.classList.contains('open');
  document.querySelectorAll('.faq-item.open').forEach(o=>{o.classList.remove('open');o.querySelector('.faq-a').style.maxHeight=0});
  if(!open){item.classList.add('open');a.style.maxHeight=a.scrollHeight+'px'}
}));

// blog (page blog)
const artOv=document.getElementById('artOverlay');
if(artOv){
  const artC=document.getElementById('artContent');
  document.querySelectorAll('.blog-link').forEach(b=>b.addEventListener('click',()=>{
    artC.innerHTML=document.getElementById(b.dataset.art).innerHTML;
    artOv.classList.add('open');document.body.style.overflow='hidden';
  }));
  const artHide=()=>{artOv.classList.remove('open');document.body.style.overflow=''};
  document.getElementById('artClose').addEventListener('click',artHide);
  artOv.addEventListener('click',e=>{if(e.target===artOv)artHide()});
  addEventListener('keydown',e=>{if(e.key==='Escape')artHide()});
}

// catalogue : fiches détaillées (page ateliers)
const fOv=document.getElementById('ficheOverlay');
if(fOv){
  const fC=document.getElementById('ficheContent');
  document.querySelectorAll('.cat-link').forEach(b=>b.addEventListener('click',()=>{
    const t=document.getElementById('fiche-'+b.dataset.fiche);
    if(!t)return;
    fC.innerHTML=t.innerHTML;
    fOv.classList.add('open');document.body.style.overflow='hidden';
    fOv.scrollTop=0;
  }));
  const fHide=()=>{fOv.classList.remove('open');document.body.style.overflow=''};
  document.getElementById('ficheClose').addEventListener('click',fHide);
  fOv.addEventListener('click',e=>{if(e.target===fOv)fHide()});
  addEventListener('keydown',e=>{if(e.key==='Escape')fHide()});
}

// formulaire (accueil + contact) — envoi réel via Netlify Forms
const form=document.getElementById('contactForm');
const fEmail=document.getElementById('fEmail');
const emailOk=v=>/^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$/.test(v.trim());
if(fEmail){
  const check=()=>{const ok=emailOk(fEmail.value)||fEmail.value==='';
    fEmail.classList.toggle('bad',!ok&&fEmail.value!=='');
    fEmail.classList.toggle('good',ok&&fEmail.value!=='');
    fEmail.closest('.f-field').classList.toggle('show-err',!ok&&fEmail.value!=='');};
  fEmail.addEventListener('input',check);fEmail.addEventListener('blur',check);
}
if(form)form.addEventListener('submit',e=>{
  e.preventDefault();
  if(fEmail&&!emailOk(fEmail.value)){
    fEmail.classList.add('bad');fEmail.closest('.f-field').classList.add('show-err');fEmail.focus();return;
  }
  const btn=form.querySelector('button[type="submit"]');
  btn.textContent='Envoi en cours…';
  fetch('https://formsubmit.co/ajax/jacqueline.schmitt.1965@gmail.com',{method:'POST',
    headers:{'Content-Type':'application/json','Accept':'application/json'},
    body:JSON.stringify((()=>{const d=Object.fromEntries(new FormData(form));d._replyto=d['Email']||'';return d})())})
  .finally(()=>{
    form.classList.add('sent');
    document.getElementById('formOk').classList.add('on');
    document.getElementById('formOk').scrollIntoView({behavior:'smooth',block:'center'});
  });
});
"""


# ---------- fiches ateliers (page ateliers : chaque atelier est cliquable) ----------
FICHES = (ROOT / "content" / "fiches-ateliers.html").read_text()

# ---------- blog : articles depuis content/blog/*.md (gérés via Decap CMS sur /admin) ----------
BLOG_DIR = ROOT / "content" / "blog"

MOIS_FR = ["", "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"]

def date_fr(iso):
    a, m, j = iso[:10].split("-")
    return f"Le {int(j)} {MOIS_FR[int(m)]} {a}"

def b64img(path):
    """Renvoie le chemin de l'image (copiée dans site/) au lieu du base64 : pages légères, cache navigateur."""
    return path


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def parse_article(path):
    raw = path.read_text()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", raw, re.S)
    meta = {"slug": path.stem, "body": m.group(2).strip()}
    for line in m.group(1).splitlines():
        mm = re.match(r"^(\w+):\s*(.*)$", line.strip())
        if mm:
            k, v = mm.group(1), mm.group(2).strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            meta[k] = v
    return meta

def md_inline(t):
    t = esc(t)
    t = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)",
               lambda m: f'<img src="{b64img(m.group(2))}" alt="{m.group(1)}" style="max-width:100%;border-radius:14px;margin:8px 0">', t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", t)
    return t

def md_to_html(md):
    out, para, lst = [], [], []
    def flush():
        if para:
            out.append("<p>" + md_inline(" ".join(para)) + "</p>")
            para.clear()
        if lst:
            out.append("<ul>\n" + "\n".join(f"      <li>{md_inline(i)}</li>" for i in lst) + "\n    </ul>")
            lst.clear()
    for line in md.splitlines():
        s = line.strip()
        if not s:
            flush()
        elif s.startswith("<"):
            # bloc HTML brut (encadrés art-callout, figures…) : passage tel quel,
            # en inlinant les images locales référencées par src="img/…"
            flush()
            out.append(re.sub(r'src="(img/[^"]+)"', lambda m: f'src="{b64img(m.group(1))}"', s))
        elif re.match(r"^#{1,6}\s", s):
            flush()
            titre = re.sub(r"^#+\s*", "", s)
            out.append("<h4>" + md_inline(titre) + "</h4>")
        elif re.match(r"^[-*]\s+", s):
            if para:
                flush()
            lst.append(re.sub(r"^[-*]\s+", "", s))
        else:
            if lst:
                flush()
            para.append(s)
    flush()
    return "\n    ".join(out)

TAG_ATTR = {
    "sauge": 'class="blog-tag"',
    "ocre": 'class="blog-tag t-ocre"',
    "rose": 'class="blog-tag t-rose"',
    "blush": 'class="blog-tag" style="background:var(--blush);color:var(--marron)"',
    "amande": 'class="blog-tag" style="background:var(--amande-soft);color:var(--olive-deep)"',
}

articles = sorted((parse_article(p) for p in BLOG_DIR.glob("*.md")),
                  key=lambda a: (a.get("date", ""), a["slug"]), reverse=True)
assert articles, "aucun article trouvé dans content/blog/"

DELAYS = ["", " d1", " d2"]
cards = []
for i, a in enumerate(articles):
    tag = TAG_ATTR.get(a.get("couleur", "sauge"), TAG_ATTR["sauge"])
    cards.append(f'''      <article class="blog-card reveal{DELAYS[i % 3]}">
        <div class="bc-img"><img src="{b64img(a["image"])}" alt="{esc(a.get("alt", a["title"]))}"></div>
        <span {tag}>{esc(a["tag"])}</span>
        <h3>{esc(a["title"])}</h3>
        <p>{esc(a["description"])}</p>
        <div class="blog-foot">
          <span class="blog-author"><img src="__IMG_AVATAR__" alt="Jacqueline Schmitt"><span><b>Jacqueline Schmitt</b><small>{date_fr(a["date"])}</small></span></span>
          <a class="blog-more" href="{a["slug"]}.html">Voir l'article</a>
        </div>
      </article>''')

BLOG_SECTION = f'''<section class="sect has-blobs" id="blog" style="padding-top:30px">
  <div class="blob b-amande slow" style="width:320px;height:320px;left:-120px;top:18%"></div>
  <div class="wrap">
    <div class="blog-grid">
{chr(10).join(cards)}
    </div>
  </div>
</section>'''

def suggestions(a):
    """3 articles a lire ensuite : meme categorie d abord."""
    autres = [x for x in articles if x["slug"] != a["slug"]]
    memes = [x for x in autres if x.get("tag") == a.get("tag")]
    choix = (memes + [x for x in autres if x not in memes])[:3]
    if not choix:
        return ""
    cartes = "\n".join(
        '<a class="sugg-card" href="%s.html"><img src="%s" alt="%s"><span><b>%s</b><small>%s</small></span></a>'
        % (x["slug"], b64img(x["image"]), esc(x.get("alt") or x["title"]), esc(x["title"]), esc(x["tag"]))
        for x in choix)
    return ('<div class="sugg"><h3 class="sugg-t">A lire ensuite <em>sur le blog</em></h3>'
            '<div class="sugg-grid">' + cartes + '</div></div>')

def art_page(a):
    return f"""<header class="art-hero">
  <img class="bg" src="{b64img(a["image"])}" alt="">
  <div class="veil"></div>
  <div class="wrap">
    <div class="art-crumb"><a href="index.html" style="color:inherit">Accueil</a> · <a href="blog.html" style="color:inherit">Blog</a> · <b>{esc(a["title"])}</b></div>
    <span class="art-pill">♥ Blog · {esc(a["tag"])}</span>
    <h1>{esc(a["title"])}</h1>
    <div class="art-author"><img src="__IMG_AVATAR__" alt="Jacqueline Schmitt"><span><b>Jacqueline Schmitt</b><small>Éducatrice Montessori · {date_fr(a["date"])}</small></span></div>
  </div>
</header>
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Accueil","item":"{BASE_URL}/"}},{{"@type":"ListItem","position":2,"name":"Blog","item":"{BASE_URL}/blog"}},{{"@type":"ListItem","position":3,"name":"{esc(a["title"])}"}}]}}</script>
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"BlogPosting","headline":"{esc(a["title"])}","description":"{esc(a["description"])}","image":"{BASE_URL}/{a["image"]}","datePublished":"{a["date"]}","dateModified":"{a["date"]}","inLanguage":"fr-FR","author":{{"@type":"Person","name":"Jacqueline Schmitt","jobTitle":"Éducatrice Montessori","url":"{BASE_URL}/qui-sommes-nous"}},"publisher":{{"@type":"Organization","name":"Enfance Éclairée","logo":{{"@type":"ImageObject","url":"{BASE_URL}/favicon.svg"}}}},"mainEntityOfPage":"{BASE_URL}/{a["slug"]}","keywords":"{esc(a["tag"])}, Montessori, Metz, petite enfance"}}</script>
<section class="sect" style="padding:56px 0 30px">
  <div class="wrap art-page">
    {md_to_html(a["body"])}
    {suggestions(a)}
    <a class="art-back" href="blog.html">← Tous les articles</a>
  </div>
</section>"""


QUI_HERO = """<header class="art-hero">
  <img class="bg" src="__IMG_HERO__" alt="">
  <div class="veil"></div>
  <div class="wrap">
    <div class="art-crumb"><a href="index.html" style="color:inherit">Accueil</a> · <b>Qui sommes-nous</b></div>
    <span class="art-pill">&#9829; Qui sommes-nous</span>
    <h1>Jacqueline, l&#8217;&#226;me d&#8217;<em style="font-family:'Dancing Script',cursive;font-style:normal;color:var(--sauge)">Enfance &#201;clair&#233;e</em></h1>
    <p style="color:#5C4F3E;max-width:640px;margin-top:6px">&#201;ducatrice Montessori 0-6 ans, formatrice et animatrice, fondatrice d&#8217;Apprendre Autrement Metz devenu Enfance &#201;clair&#233;e. Elle accompagne les familles et les professionnels de la petite enfance.</p>
  </div>
</header>"""

QUI_PARCOURS = """<section class="sect has-blobs" style="padding-top:30px">
  <div class="blob b-ocre slow" style="width:320px;height:320px;right:-120px;top:6%"></div>
  <div class="blob b-rose rev" style="width:300px;height:300px;left:-110px;bottom:20%"></div>
  <div class="wrap">
    <div class="sect-head reveal">
      <span class="eyebrow">Son univers</span>
      <h2>Section par section, <em>tout savoir</em></h2>
    </div>

    <div class="zz reveal">
      <div class="zz-img"><img src="__IMG_FORMATION__" alt="Manipulation de matériel Montessori"></div>
      <div>
        <h3>Son <em>parcours</em></h3>
        <p>Bac ST2S puis CAP Petite Enfance : le soin de l&#8217;enfant comme vocation, d&#232;s le d&#233;part. Titulaire du titre AMGE (assistante maternelle et garde d&#8217;enfants &#224; domicile), Jacqueline a pass&#233; plus de dix ans au plus pr&#232;s des tout-petits et des familles.</p>
        <p>Puis la r&#233;v&#233;lation : la formation Enfance Positive Luxembourg, celle qui, selon ses mots, lui a permis d&#8217;&#234;tre ce qu&#8217;elle est aujourd&#8217;hui. Elle fonde alors Apprendre Autrement Metz, devenu Enfance &#201;clair&#233;e.</p>
        <p style="font-family:'Dancing Script',cursive;font-size:22px;color:var(--olive);margin:0">Sa boussole : observer pour mieux proposer et adapter &#8212; son OPA.</p>
      </div>
    </div>

    <div class="zz rev reveal">
      <div class="zz-img"><img src="__IMG_CPHOTO__" alt="L&#8217;espace nido am&#233;nag&#233; par Jacqueline"></div>
      <div>
        <h3>Son <em>centre</em> &#224; Metz</h3>
        <p>Un espace enti&#232;rement am&#233;nag&#233; pour la p&#233;dagogie Montessori, o&#249; elle accueille enfants, parents et professionnels.</p>
        <ul>
          <li><svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>Metz, Moselle &#183; adresse exacte communiqu&#233;e &#224; la r&#233;servation</li>
          <li><svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>Les mercredis &amp; samedis, de 9h30 &#224; 17h00</li>
          <li><svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>06 10 08 96 71 &#183; jacqueline.schmitt.1965@gmail.com</li>
          <li><svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>Plus de 10 ans d&#8217;exp&#233;rience aupr&#232;s des 0&#8211;6 ans</li>
        </ul>
      </div>
    </div>

    <div class="zz reveal">
      <div class="zz-img"><img src="__IMG_CTA__" alt="Maman et son b&#233;b&#233; dans une chambre douce"></div>
      <div>
        <h3>L&#8217;accompagnement des <em>parents</em></h3>
        <p>Parents, futurs parents, ou parents qui traversent une p&#233;riode difficile : Jacqueline accompagne avec bienveillance et sans jugement.</p>
        <ul>
          <li><svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>Ateliers parents : comprendre, observer, accompagner son enfant</li>
          <li><svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>Soutien &#224; la parentalit&#233;, m&#234;me dans les temp&#234;tes</li>
          <li><svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>Montessori &#224; la maison, avec ce que vous avez d&#233;j&#224;</li>
          <li><svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>Vous repartez capable de mettre en place les activit&#233;s vous-m&#234;me</li>
        </ul>
      </div>
    </div>

    <div class="zz rev reveal">
      <div class="zz-img"><img src="__IMG_CAT4__" alt="Jouets en bois choisis avec soin"></div>
      <div>
        <h3>Le bon <em>mat&#233;riel</em>, les bons choix</h3>
        <p>Quels meubles choisir, quels jouets acheter, lesquels &#233;viter : Jacqueline vous conseille pour un mat&#233;riel adapt&#233; &#224; votre enfant et &#224; votre budget &#8212; sans achats inutiles.</p>
        <ul>
          <li><svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>Conseil &#224; l&#8217;achat du bon mat&#233;riel et des bons jouets</li>
          <li><svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>Homestaging Montessori : l&#8217;am&#233;nagement pi&#232;ce par pi&#232;ce</li>
          <li><svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>Espaces d&#8217;autonomie et de motricit&#233; libre</li>
        </ul>
      </div>
    </div>

    <div class="reveal" style="text-align:center;margin-top:10px">
      <a href="contact.html" class="btn">R&#233;server mon &#233;change gratuit</a>
    </div>
  </div>
</section>"""


# ---------- pages thématiques du catalogue ----------
THEMES = [
 ("vie-pratique-sensorielle","Vie pratique & sensorielle","__IMG_CAT1__","Les gestes du quotidien et l'éveil des sens : le cœur battant de la pédagogie Montessori.",[
  ("La vie pratique, dès 18 mois","Verser, transvaser, s'habiller, nettoyer : les gestes du quotidien deviennent de vrais apprentissages. L'enfant y gagne coordination, concentration et la fierté de faire seul. En atelier, chaque geste est décomposé, présenté lentement, puis laissé à l'enfant autant de fois qu'il le souhaite."),
  ("La vie sensorielle, petits et grands","Explorer textures, sons, odeurs et couleurs pour affiner chaque sens. C'est la base de tous les apprentissages : un enfant qui discrimine finement par les sens prépare les mathématiques, le langage et l'écriture."),
  ("Le bac à manipulation","Riz, graines, objets à saisir : un bac, mille explorations. On y travaille la motricité fine, la concentration et le retour au calme. Jacqueline montre comment le composer, le renouveler et le présenter."),
  ("La motricité fine et le développement de la main","Pincer, visser, enfiler, boutonner : la main qui se précise prépare l'écriture et l'autonomie. Des progressions concrètes, du plus simple au plus fin, adaptées à chaque âge."),
  ("La mud kitchen","Une cuisine de plein air pour toucher la terre, transvaser, mélanger, inventer. La nature comme terrain d'apprentissage, et une mine d'activités sensorielles à moindre coût."),
 ]),
 ("eveil-apprentissages","Éveil & apprentissages","__IMG_CAT2__","Du premier son à la première lettre : accompagner les grandes découvertes sans forcer.",[
  ("Les étagères créative, musicale et thématique","Composer des étagères qui donnent envie : peu d'objets, bien choisis, en libre accès, renouvelés au fil des intérêts. Trois univers (créer, écouter, découvrir) et une méthode pour les faire vivre."),
  ("L'apprentissage du son, bien avant le solfège","Écouter, reconnaître, produire : l'oreille se forme bien avant la lecture des notes. Clochettes, boîtes à sons et jeux d'écoute pour éveiller l'oreille musicale."),
  ("L'apprentissage d'une trace, bien avant l'outil scripteur","Tracer dans la semoule, peindre au doigt, gribouiller en grand : la trace se construit avant le crayon. Un chemin naturel et sans pression vers l'écriture."),
  ("Écriture et lecture","Lettres rugueuses, jeux de sons, premiers mots : entrer dans l'écrit par les sens, au rythme de chaque enfant, selon ses périodes sensibles."),
  ("Les grands verbes Montessori","Verser, ouvrir, presser, plier… ces verbes du quotidien racontent le développement de l'enfant et guident le choix des activités adaptées à chaque étape."),
 ]),
 ("emotions-developpement","Émotions & développement","__IMG_CAT3__","Comprendre ce qui se passe dans la tête du tout-petit pour mieux l'accompagner.",[
  ("La gestion des émotions","Mettre des mots sur les tempêtes, offrir des outils concrets pour s'apaiser, accompagner sans punir l'émotion. Pour les professionnels comme pour les parents."),
  ("Les fidgets","Des objets à manipuler pour retrouver calme et concentration : lesquels choisir, quand les proposer, comment les présenter aux enfants stressés ou à grand besoin de mouvement."),
  ("Le jeu","Le jeu libre comme moteur du développement : quoi proposer, quand intervenir, comment enrichir sans diriger."),
  ("La formation du cerveau de l'enfant et les neurosciences","Ce que les neurosciences nous apprennent du cerveau de 0 à 6 ans : maturation, émotions, apprentissages — et comment adapter nos réponses d'adultes."),
 ]),
 ("montessori-au-quotidien","Montessori au quotidien","__IMG_CAT4__","La pédagogie chez vous : aménager, choisir, simplifier — sans tout racheter.",[
  ("Montessori à la maison (Montessori friendly)","Adapter la maison sans tout racheter : hauteur d'enfant, libre accès, routines simples. Des changements concrets qui transforment le quotidien."),
  ("Installer des loose parts chez soi","Bois, tissus, contenants, trésors de la nature : des pièces libres pour un jeu créatif sans fin, à installer chez vous en toute sécurité."),
  ("Le homestaging Montessori","Jacqueline vous conseille dans l'aménagement d'un espace pour le bébé et l'enfant : quels meubles choisir, quels jouets, quelle organisation — chez vous, pièce par pièce, selon votre budget."),
  ("Aménager un espace d'autonomie et de motricité libre","Tapis ferme, miroir, étagère basse : un coin où l'enfant joue seul, en sécurité, et développe librement sa motricité."),
 ]),
 ("univers-par-age","Les univers par âge","__IMG_CAT5__","Nido, communauté enfantine, maison enfantine : un environnement pour chaque étape de 0 à 6 ans.",[
  ("Nido 0–6 mois","Mobiles adaptés au développement visuel, contrastes, motricité libre sur tapis : l'éveil tout en douceur des premiers mois."),
  ("Nido 6–18 mois","Premiers déplacements, paniers aux trésors, objets à saisir et à transvaser : l'exploration prend de l'ampleur."),
  ("Nido avec mobiles et géométrie, 18 mois à 3 ans","Observer, trier, emboîter : les formes, les couleurs et la géométrie entrent en scène."),
  ("Communauté enfantine, à partir de 18 mois","L'âge du « moi tout seul » : vie pratique, langage et premières collaborations en petit groupe."),
  ("Maison enfantine, de 3 à 6 ans","L'esprit absorbant à son apogée : matériel sensoriel, premiers pas vers l'écriture et les mathématiques, autonomie et confiance."),
 ]),
]

def theme_page(slug, title, cover, intro, items):
    body = "\n".join(f"<h4>{t}</h4>\n<p>{d}</p>" for t, d in items)
    return f"""<header class="art-hero">
  <img class="bg" src="{cover}" alt="">
  <div class="veil"></div>
  <div class="wrap">
    <div class="art-crumb"><a href="index.html" style="color:inherit">Accueil</a> · <a href="ateliers.html" style="color:inherit">Ateliers &amp; formations</a> · <b>{title}</b></div>
    <span class="art-pill">&#9829; Catalogue</span>
    <h1>{title}</h1>
    <p style="color:#5C4F3E;max-width:620px;margin-top:6px">{intro}</p>
  </div>
</header>
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{{"@type":"ListItem","position":1,"name":"Accueil","item":"{BASE_URL}/"}},{{"@type":"ListItem","position":2,"name":"Ateliers et formations","item":"{BASE_URL}/ateliers"}},{{"@type":"ListItem","position":3,"name":"{title}"}}]}}</script>
<section class="sect" style="padding:56px 0 30px">
  <div class="wrap art-page">
    <div class="art-body">
    {body}
    </div>
    <div class="art-callout co-rose" style="margin-top:26px">
      <h5>En pratique</h5>
      <ul>
        <li>Dans les locaux Enfance &#201;clair&#233;e &#224; Metz, les mercredis et samedis, 9h30 &#8211; 17h00</li>
        <li>En version professionnels de la petite enfance ou parents</li>
        <li>Programme construit sur mesure selon les &#226;ges et vos besoins</li>
      </ul>
    </div>
    <a class="art-back" href="ateliers.html">&#8592; Retour aux ateliers &amp; formations</a>
  </div>
</section>"""


QUI_CENTRE = """<section class="sect has-blobs" style="padding-top:0">
  <div class="blob b-rose slow" style="width:300px;height:300px;left:-110px;top:20%"></div>
  <div class="wrap">
    <div class="sect-head reveal">
      <span class="eyebrow">Son centre &#224; Metz</span>
      <h2>Ce que Jacqueline vous <em>propose</em></h2>
      <p>Plus de 10 ans d&#8217;exp&#233;rience aupr&#232;s des 0&#8211;6 ans, au service des familles et des professionnels.</p>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;max-width:960px;margin:0 auto" class="qui-centre-grid">
      <div class="art-callout" style="margin:0">
        <h5>Dans ses locaux Enfance &#201;clair&#233;e</h5>
        <ul>
          <li>Metz, Moselle &#183; adresse exacte communiqu&#233;e &#224; la r&#233;servation</li>
          <li>Les mercredis &amp; samedis, de 9h30 &#224; 17h00</li>
          <li>06 10 08 96 71 &#183; jacqueline.schmitt.1965@gmail.com</li>
          <li>Un espace enti&#232;rement am&#233;nag&#233; pour la p&#233;dagogie Montessori</li>
        </ul>
      </div>
      <div class="art-callout co-rose" style="margin:0">
        <h5>Son accompagnement</h5>
        <ul>
          <li>Formations Montessori pour les professionnels de la petite enfance</li>
          <li>Ateliers pour les enfants de 0 &#224; 6 ans, par tranche d&#8217;&#226;ge</li>
          <li>Ateliers parents &amp; accompagnement &#224; la parentalit&#233;, m&#234;me dans les p&#233;riodes difficiles</li>
          <li>Conseil pour l&#8217;achat du bon mat&#233;riel et des bons jouets, adapt&#233;s &#224; votre enfant et &#224; votre budget</li>
          <li>Homestaging Montessori : quels meubles, quel am&#233;nagement, pi&#232;ce par pi&#232;ce</li>
        </ul>
      </div>
    </div>
    <div class="reveal" style="text-align:center;margin-top:38px">
      <a href="contact.html" class="btn">R&#233;server mon &#233;change gratuit</a>
    </div>
  </div>
</section>"""

# ---------- pages ----------
META = {
    "index.html": (
        "Enfance Éclairée Metz · Formations & Ateliers Montessori 0-6 ans",
        "Formations Montessori, ateliers 0-6 ans et accompagnement des parents à Metz, par Jacqueline, éducatrice Montessori depuis plus de 10 ans.",
    ),
    "methode.html": (
        "La pédagogie Montessori expliquée · Enfance Éclairée Metz",
        "Qu'est-ce que la pédagogie Montessori ? Ses principes, ses effets sur les enfants et ce que dit la recherche scientifique.",
    ),
    "ateliers.html": (
        "Ateliers & formations Montessori 0–6 ans · Enfance Éclairée Metz",
        "Plus de 25 ateliers et formations Montessori : vie pratique, éveil, émotions, univers par âge. À Metz, pour les pros et les familles.",
    ),
    "blog.html": (
        "Le blog · Conseils Montessori & petite enfance · Enfance Éclairée",
        "Conseils concrets et éclairages scientifiques sur la pédagogie Montessori, les émotions et le développement de l'enfant de 0 à 6 ans.",
    ),
    "contact.html": (
        "Contact · Enfance Éclairée Metz",
        "Contactez Jacqueline pour une formation Montessori, un atelier en structure d'accueil ou un accompagnement parental, à Metz et alentours.",
    ),
    "mentions-legales.html": (
        "Mentions légales · Enfance Éclairée",
        "Mentions légales et politique de confidentialité du site Enfance Éclairée.",
    ),
    "404.html": (
        "Page introuvable · Enfance Éclairée",
        "Cette page n'existe pas ou plus.",
    ),
}

LEGAL = '''<section class="sect" style="padding-top:30px">
  <div class="wrap" style="max-width:760px">
    <div style="display:grid;gap:26px;color:#5C4F3E;font-size:15.5px">
      <div>
        <h2 style="font-size:22px;margin-bottom:10px">Éditeur du site</h2>
        <p>Enfance Éclairée · Jacqueline Schmitt, entrepreneur individuel<br>Metz, Moselle, France<br>Téléphone : 06 10 08 96 71 · Email : jacqueline.schmitt.1965@gmail.com<br>SIRET : [à compléter]<br>Directrice de la publication : Jacqueline Schmitt</p>
      </div>
      <div>
        <h2 style="font-size:22px;margin-bottom:10px">Hébergement</h2>
        <p>Site hébergé par GitHub, Inc. (GitHub Pages) · 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, États-Unis · www.github.com<br>Nom de domaine enregistré auprès de GoDaddy Operating Company, LLC · www.godaddy.com</p>
      </div>
      <div>
        <h2 style="font-size:22px;margin-bottom:10px">Propriété intellectuelle</h2>
        <p>L'ensemble des contenus de ce site (textes, images, logo, blason) est la propriété d'Enfance Éclairée, sauf mention contraire. Toute reproduction sans autorisation préalable est interdite.</p>
      </div>
      <div>
        <h2 style="font-size:22px;margin-bottom:10px">Données personnelles</h2>
        <p>Les informations transmises via le formulaire de contact sont utilisées uniquement pour répondre à votre demande. Elles ne sont ni cédées ni vendues à des tiers. Conformément au RGPD, vous disposez d'un droit d'accès, de rectification et de suppression de vos données : il vous suffit d'écrire à jacqueline.schmitt.1965@gmail.com.</p>
        <p>Ce site n'utilise pas de cookies de suivi publicitaire.</p>
      </div>
    </div>
  </div>
</section>'''

NOTFOUND = '''<section class="sect" style="text-align:center;padding:90px 0 110px">
  <div class="wrap">
    <svg viewBox="0 0 200 234" style="width:110px;margin:0 auto 26px;display:block"><use href="#crest"/></svg>
    <h2 style="font-size:clamp(28px,3.4vw,40px);margin-bottom:14px">Oups, cette page s'est <em style="font-family:'Caveat',cursive;font-style:normal;color:var(--sauge);font-size:1.18em">égarée</em></h2>
    <p style="color:#6B5C48;max-width:440px;margin:0 auto 30px">Comme un tout-petit en pleine exploration, elle est partie voir ailleurs. Retournons en terrain connu.</p>
    <a href="index.html" class="btn">Revenir à l'accueil</a>
  </div>
</section>'''

def compose(page, *sections):
    title, desc = META[page]
    h = head
    h = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", h, flags=re.S)
    h = re.sub(r'(<meta name="description" content=")[^"]*(">)', rf"\g<1>{desc}\g<2>", h)
    h = re.sub(r'(<meta property="og:title" content=")[^"]*(">)', rf"\g<1>{title}\g<2>", h)
    h = re.sub(r'(<meta property="og:description" content=")[^"]*(">)', rf"\g<1>{desc}\g<2>", h)
    canon = BASE_URL + "/" + ("" if page == "index.html" else page[:-5])
    h += f'<link rel="canonical" href="{canon}">'
    h += ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"LocalBusiness",'
          '"name":"Enfance Éclairée","description":"Formations et ateliers Montessori 0-6 ans pour les professionnels de la petite enfance et les familles, à Metz.",'
          '"telephone":"+33610089671","email":"jacqueline.schmitt.1965@gmail.com",'
          '"address":{"@type":"PostalAddress","addressLocality":"Metz","addressRegion":"Grand Est","addressCountry":"FR"},'
          '"founder":{"@type":"Person","name":"Jacqueline Schmitt","jobTitle":"Éducatrice Montessori"},'
          '"openingHours":["We 09:30-17:00","Sa 09:30-17:00"],'
          f'"url":"{BASE_URL}","areaServed":"Metz et alentours, Moselle"}}</script>')
    if page == "ateliers.html":
        h += ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"Service",'
              '"serviceType":"Formations et ateliers Montessori 0-6 ans",'
              '"provider":{"@type":"LocalBusiness","name":"Enfance Éclairée","telephone":"+33610089671"},'
              '"areaServed":{"@type":"City","name":"Metz"},'
              '"audience":{"@type":"Audience","audienceType":"Professionnels de la petite enfance, parents et futurs parents"},'
              '"hasOfferCatalog":{"@type":"OfferCatalog","name":"Ateliers et formations Montessori","itemListElement":['
              '{"@type":"Offer","itemOffered":{"@type":"Service","name":"Formations Montessori pour professionnels de la petite enfance"}},'
              '{"@type":"Offer","itemOffered":{"@type":"Service","name":"Ateliers Montessori pour les enfants de 0 à 6 ans"}},'
              '{"@type":"Offer","itemOffered":{"@type":"Service","name":"Ateliers parents et accompagnement à la parentalité"}},'
              '{"@type":"Offer","itemOffered":{"@type":"Service","name":"Homestaging Montessori et aménagement d espaces"}}]}}</script>')
    if page == "index.html":
        h += '<script type="application/ld+json">' + (ROOT / "faq_schema.json").read_text(encoding="utf-8") + "</script>"
    content = "\n".join(sections)
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>{h}</head>
<body>
{chunks['BLASON (defs)']}
{chunks['TOPBAR']}
{nav(page)}
{content}
{chunks['FOOTER']}
{fab}
<script>{JS}</script>
</body>
</html>"""

cta_ext = chunks["CTA BAND"].replace('href="#contact"', 'href="contact.html"')

pages = {
    "index.html": compose(
        "index.html",
        chunks["HERO"],
        chunks["MARQUEE"],
        chunks["SIGNATURES"],
        chunks["OFFRES"],
        chunks["AGES / TABS"],
        chunks["IMMERSION"],
        chunks["ABOUT"],
        chunks["TEMOIGNAGES"],
        chunks["PROCESS"],
        chunks["CTA BAND"],
        chunks["CONTACT"],
        chunks["FAQ"],
    ),
    "methode.html": compose(
        "methode.html",
        page_hero("Comprendre", "La pédagogie <em>Montessori</em>",
                  "Une posture bienveillante et facilitatrice d'apprentissages : ses principes, sa vision de l'enfant, et ce que la recherche scientifique en dit."),
        chunks["METHODE MONTESSORI"],
        cta_ext,
    ),
    "ateliers.html": compose(
        "ateliers.html",
        page_hero("Le catalogue", "Ateliers &amp; <em>formations</em>",
                  "Plus de 25 thèmes à transmettre, des univers pensés pour chaque âge, et un déroulement simple et clair. Cliquez sur un atelier pour en découvrir le détail."),
        chunks["CATALOGUE"],
        chunks["AGES / TABS"],
        chunks["IMMERSION"],
        chunks["PROCESS"],
        chunks["LISTE"],
        FICHES,
        cta_ext,
    ),
    "blog.html": compose(
        "blog.html",
        page_hero("Le blog", "Conseils &amp; <em>inspirations</em>",
                  "Des articles courts et concrets pour comprendre votre enfant et faire vivre Montessori au quotidien."),
        BLOG_SECTION,
    ),
    "contact.html": compose(
        "contact.html",
        page_hero("Contact", "Écrivons la suite <em>ensemble</em>",
                  "Une question, un projet de formation ou d'atelier ? Jacqueline vous répond sous 24 à 48h."),
        chunks["CONTACT"],
    ),
    "mentions-legales.html": compose(
        "mentions-legales.html",
        page_hero("Informations", "Mentions <em>légales</em>",
                  "Mentions légales et politique de confidentialité du site Enfance Éclairée."),
        LEGAL,
    ),
    "404.html": compose(
        "404.html",
        NOTFOUND,
    ),
}
META["qui-sommes-nous.html"] = ("Qui sommes-nous · Enfance Éclairée Metz",
    "Jacqueline, éducatrice Montessori 0-6 ans à Metz : son parcours, sa posture bienveillante, son OPA et sa vision.")
for _slug,_t,_c,_i,_items in THEMES:
    META[_slug+".html"] = (_t + " · Enfance Éclairée Metz", _i)
    pages[_slug+".html"] = compose(_slug+".html", theme_page(_slug,_t,_c,_i,_items), cta_ext)
pages["qui-sommes-nous.html"] = compose("qui-sommes-nous.html", QUI_HERO, chunks["ABOUT"], QUI_PARCOURS, cta_ext)
for a in articles:
    _t_clean = re.sub("<[^>]+>", "", a["title"])
    _suffix = "" if len(_t_clean) > 45 else " · Enfance Éclairée"
    META[a["slug"] + ".html"] = (_t_clean + _suffix, a["description"])
    pages[a["slug"] + ".html"] = compose(a["slug"] + ".html", art_page(a), cta_ext)

# ajustements par page
# methode : retirer le sect-head redondant (le page-hero fait le titre) + resserrer
pages["methode.html"] = pages["methode.html"].replace(
    '''<div class="sect-head reveal">
      <span class="eyebrow">La pédagogie</span>
      <h2>Qu'est-ce que la pédagogie <em>Montessori</em> ?</h2>
      <p>Une approche éducative fondée il y a plus d'un siècle par Maria Montessori, médecin et pédagogue, aujourd'hui reconnue dans le monde entier.</p>
    </div>''', "").replace(
    '<section class="sect has-blobs" id="methode">',
    '<section class="sect has-blobs" id="methode" style="padding-top:30px">')
# ateliers : retirer le sect-head du catalogue + resserrer
pages["ateliers.html"] = pages["ateliers.html"].replace(
    '''<div class="sect-head reveal">
      <span class="eyebrow">Le catalogue</span>
      <h2>Plus de 25 thèmes <em>à transmettre</em></h2>
      <p>Des années de pratique condensées en ateliers et formations prêts à être partagés, avec les familles comme avec les professionnels.</p>
    </div>''', "").replace(
    '<section class="sect has-blobs" id="catalogue">',
    '<section class="sect has-blobs" id="catalogue" style="padding-top:30px">')
# blog : la section est générée depuis content/blog/*.md (voir plus haut), rien à ajuster
# contact page : retirer le sect-head redondant
pages["contact.html"] = pages["contact.html"].replace(
    '''<div class="sect-head reveal">
      <span class="eyebrow">Contact</span>
      <h2>Écrivons la suite <em>ensemble</em></h2>
    </div>''', "")
# footer : liens vers les pages
for p in pages:
    pages[p] = (pages[p]
        .replace('href="#offres"', 'href="ateliers.html"')
        .replace('href="#methode"', 'href="methode.html"')
        .replace('href="#ages"', 'href="ateliers.html"')
        .replace('href="#blog"', 'href="blog.html"')
        .replace('href="#apropos"', 'href="qui-sommes-nous.html"')
        .replace('href="#temoignages"', 'href="index.html#temoignages"'))
    # le lien #contact reste en ancre sur l'accueil et la page contact, sinon vers contact.html
    if p not in ("index.html", "contact.html"):
        pages[p] = pages[p].replace('href="#contact"', 'href="contact.html"')

# ---------- images ----------
IMG = {
 '__IMG_HERO__':'hero.jpg','__IMG_FORMATION__':'formation.jpg','__IMG_ATELIER__':'atelier_structures.jpg',
 '__IMG_PARENTS__':'reel_sensoriel.jpg',
 '__IMG_NIDO__':'nido.jpg','__IMG_COMMUNAUTE__':'communaute.jpg','__IMG_MAISON__':'maison.jpg',
 '__IMG_REEL_NIDO__':'reel_nido.jpg','__IMG_REEL_NATURE__':'reel_nature.jpg','__IMG_REEL_ETAGERE__':'reel_etagere.jpg',
 '__IMG_REEL_SENSORIEL__':'reel_sensoriel.jpg','__IMG_JACQUELINE__':'jacqueline.jpg',
 '__IMG_BLOG1__':'reel_etagere.jpg','__IMG_BLOG2__':'rocks_craft.jpg','__IMG_BLOG3__':'communaute.jpg',
 '__IMG_BLOG4__':'paint_girl.jpg','__IMG_BLOG5__':'blocks_hand.jpg','__IMG_BLOG6__':'hero.jpg',
 '__IMG_CAT1__':'reel_sensoriel.jpg','__IMG_CAT2__':'reel_nature.jpg','__IMG_CAT3__':'paint_girl.jpg',
 '__IMG_CAT4__':'boats.jpg','__IMG_CAT5__':'nido.jpg',
 '__IMG_METH1__':'boats.jpg','__IMG_METH2__':'blocks_hand.jpg','__IMG_METH3__':'ball_forest.jpg',
 '__IMG_CPHOTO__':'reel_nido.jpg',
 '__IMG_BLOG7__':'boats.jpg',
 '__IMG_AVATAR__':'avatar.jpg','__IMG_CTA__':'cta.jpg',
 '__IMG_LI1__':'nido.jpg','__IMG_LI2__':'reel_nido.jpg','__IMG_LI3__':'bear_baby.jpg',
 '__IMG_LI4__':'formation.jpg','__IMG_LI5__':'atelier_structures.jpg','__IMG_ART11__':'maison.jpg','__IMG_SALLE__':'salle.jpg',
}
for name, doc in pages.items():
    for ph, img in IMG.items():
        if ph in doc:
            doc = doc.replace(ph, "img/opt/" + img)
    # images hors du premier écran : chargement différé (Core Web Vitals)
    doc = re.sub(r'<img (?!class="bg")(?![^>]*loading=)([^>]*?)>', r'<img loading="lazy" decoding="async" \1>', doc)
    # URLs propres : index.html -> ./ , page.html -> page
    doc = re.sub(r'href="index\.html(#[^"]*)?"', lambda m: 'href="./' + (m.group(1) or '') + '"', doc)
    doc = re.sub(r'href="([a-z0-9-]+)\.html(#[^"]*)?"', lambda m: 'href="' + m.group(1) + (m.group(2) or '') + '"', doc)
    assert "__IMG_" not in doc, f"placeholder restant dans {name}"
    (OUT / name).write_text(doc)
    print(f"{name}: {len(doc)//1024} KB")

# ---------- admin (Decap CMS) ----------
if (ROOT / "admin").exists():
    shutil.copytree(ROOT / "admin", OUT / "admin", dirs_exist_ok=True)
    print("admin/ copié dans site/admin/")
print("Site généré dans", OUT)


# ---------- images : copie des fichiers ----------
if (ROOT / "favicon.svg").exists():
    shutil.copy(ROOT / "favicon.svg", OUT / "favicon.svg")
for d in ("img/opt", "img/uploads"):
    src = ROOT / d
    if src.exists():
        dst = OUT / d
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst)
print("images copiées dans site/img/")

# ---------- SEO : sitemap + robots ----------
urls = [n for n in pages if n not in ("404.html",)]
sm = ['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for n in sorted(urls):
    loc = BASE_URL + "/" + ("" if n=="index.html" else n[:-5])
    sm.append(f"  <url><loc>{loc}</loc></url>")
sm.append("</urlset>")
(OUT/"sitemap.xml").write_text("\n".join(sm))
(OUT/"robots.txt").write_text(f"User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: {BASE_URL}/sitemap.xml\n")
print("sitemap.xml + robots.txt générés")
