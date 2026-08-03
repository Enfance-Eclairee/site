# Guide de déploiement — Enfance Éclairée (avec blog auto-géré)

Objectif : la cliente écrit ses articles sur `sonsite.com/admin` (Decap CMS, gratuit),
ils apparaissent automatiquement sur la page blog avec le même design.
**Tout est gratuit** : GitHub (code), Netlify (hébergement + build), Decap CMS (admin).

## Comment ça marche

```
Cliente écrit sur /admin  →  l'article est enregistré dans content/blog/*.md sur GitHub
                          →  Netlify détecte le commit, lance python3 build_site.py
                          →  le site est régénéré et publié (~2 min)
```

Le script `build_site.py` lit `content/blog/*.md` et génère : les cartes de la page
blog (triées par date, plus récent en premier) + une page HTML complète par article.

## Étapes (avec la cliente, la semaine prochaine)

### 1. Compte GitHub de la cliente (elle est propriétaire)
- Elle crée un compte sur github.com avec SON adresse email (gratuit).
- Créer un repo **privé** (ex. `enfance-eclairee`), y pousser tout ce dossier
  (SAUF `site/` — il est dans le .gitignore, Netlify le régénère) :
  `template.html`, `build_site.py`, `content/`, `admin/`, `img/`, `netlify.toml`, `.gitignore`.
- Elle t'ajoute en collaboratrice (Settings → Collaborators) pour que tu puisses maintenir.

### 2. Netlify
- Compte Netlify (gratuit) — idéalement créé par la cliente aussi, connexion "Sign up with GitHub".
- "Add new site → Import an existing project" → choisir le repo.
- Build command et publish directory sont lus depuis `netlify.toml` (rien à saisir).
- Vérifier que le premier deploy passe.

### 3. Activer la connexion à l'admin (OAuth GitHub)
- Sur GitHub (compte de la cliente) : Settings → Developer settings → OAuth Apps → New OAuth App
  - Homepage URL : `https://LE-SITE.netlify.app`
  - Authorization callback URL : `https://api.netlify.com/auth/done`
  - Récupérer Client ID + Client Secret.
- Sur Netlify : Site configuration → Access & security → OAuth → Install provider → GitHub
  → coller Client ID + Secret.
- Dans `admin/config.yml` : remplacer `COMPTE-GITHUB/NOM-DU-REPO` par le vrai repo. Commit.
- Test : ouvrir `https://LE-SITE.netlify.app/admin/`, se connecter avec le compte GitHub
  de la cliente, publier un article test, vérifier qu'il apparaît sur le blog ~2 min après.

### 4. Domaine (GoDaddy)
- Acheter le domaine sur GoDaddy.
- Netlify : Domain management → Add custom domain → suivre les instructions DNS
  (chez GoDaddy : enregistrement A vers l'IP Netlify + CNAME `www` vers le site Netlify,
  ou changer les serveurs DNS pour ceux de Netlify — plus simple).
- HTTPS automatique via Netlify (Let's Encrypt), rien à payer.
- ⚠️ Mettre à jour les mentions légales dans `build_site.py` (variable `LEGAL`) :
  remplacer "GitHub Pages" par "Netlify, Inc. · 512 2nd Street, San Francisco, CA 94107".

### 5. Formulaire de contact
- Le formulaire envoie via formsubmit.co vers `apprendre.autrement.metz@gmail.com`.
- Au premier envoi réel, formsubmit envoie un email de confirmation à cette adresse :
  il faut cliquer le lien pour activer (d'où le besoin d'accès à sa boîte mail).

## Tester l'admin en local (sans GitHub, pour toi)

```
cd EnfanceEclairee-maquette
# décommenter "local_backend: true" dans admin/config.yml
npx decap-server          # terminal 1
python3 build_site.py && python3 -m http.server 8123 -d site   # terminal 2
# ouvrir http://localhost:8123/admin/  (bouton "Login" direct, sans compte)
# ⚠️ recommenter local_backend avant de pousser sur GitHub
```

NB : en local, publier un article via l'admin modifie `content/blog/` mais ne relance
pas le build — relancer `python3 build_site.py` pour voir le résultat.

## Points d'attention
- **Une seule source de vérité** : les articles vivent dans `content/blog/*.md`.
  Les anciens blocs BLOG / ARTICLES de `template.html` ne sont PLUS utilisés
  (ne pas y ajouter d'articles).
- Les 12 articles migrés contiennent du HTML brut (encadrés colorés `art-callout`) :
  si la cliente les ouvre dans l'admin, elle verra ce code — lui dire de ne pas y toucher,
  ou de te demander. Ses NOUVEAUX articles seront en markdown propre.
- Encadrés colorés dans un nouvel article : copier un bloc `<div class="art-callout">…</div>`
  depuis un article existant (toi, pas elle).
- Réutilisation : ce setup (build_site.py + admin/ + netlify.toml) est le template
  pour tous les futurs sites clients avec blog.
