#!/usr/bin/env python3
"""Transforme une issue GitHub « Nouvel article » en article du blog.
Lit le corps de l'issue (format issue-form), télécharge la photo,
écrit content/blog/<slug>.md — le commit déclenche la reconstruction du site."""
import json, os, pathlib, re, sys, unicodedata, urllib.request, datetime

event = json.load(open(os.environ["GITHUB_EVENT_PATH"]))
issue = event["issue"]
title = issue["title"].strip()
body = issue["body"] or ""

def section(name):
    m = re.search(r"### " + re.escape(name) + r"\s*\n+(.*?)(?=\n### |\Z)", body, re.S)
    return (m.group(1).strip() if m else "").replace("_No response_", "").strip()

resume = section("Résumé")
categorie = section("Catégorie") or "Blog"
couleur_label = section("Couleur du badge")
photo_bloc = section("Photo de l'article")
alt = section("Description de la photo") or title
texte = section("Texte de l'article")

COULEURS = {"Vert sauge": "sauge", "Ocre doré": "ocre", "Rose": "rose"}
couleur = COULEURS.get(couleur_label, "sauge")

# slug propre à partir du titre
slug = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
slug = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")[:60] or "article"

# photo : première URL d'image du bloc (drag & drop GitHub) — hôtes GitHub uniquement
img_url = None
m = re.search(r'\((https://[^)]+)\)', photo_bloc) or re.search(r'src="(https://[^"]+)"', photo_bloc) or re.search(r'(https://\S+)', photo_bloc)
if m:
    url = m.group(1)
    if re.match(r"https://(user-images\.githubusercontent\.com|github\.com/user-attachments|private-user-images\.githubusercontent\.com)/", url):
        img_url = url
image_path = "img/opt/hero.jpg"  # photo par défaut si aucune fournie
if img_url:
    dest = pathlib.Path("img/uploads"); dest.mkdir(parents=True, exist_ok=True)
    ext = ".png" if ".png" in img_url.lower() else ".jpg"
    target = dest / (slug + ext)
    req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0", "Authorization": "Bearer " + os.environ.get("GITHUB_TOKEN", "")})
    try:
        data = urllib.request.urlopen(req, timeout=30).read()
        if len(data) > 1000:
            target.write_bytes(data)
            image_path = str(target)
    except Exception as e:
        print("photo non téléchargée:", e)

# corps : #### -> h4, paragraphes -> <p>
paras = []
for bloc in re.split(r"\n\s*\n", texte.strip()):
    b = bloc.strip()
    if not b:
        continue
    if b.startswith("####"):
        paras.append("<h4>" + b.lstrip("# ").strip() + "</h4>")
    else:
        paras.append("<p>" + b.replace("\n", "<br>") + "</p>")
corps = "\n".join(paras)

date = datetime.date.today().isoformat()
md = f'''---
title: "{title.replace('"', "'")}"
description: "{resume.replace('"', "'")}"
date: {date}
tag: "{categorie.replace('"', "'")}"
couleur: "{couleur}"
image: "{image_path}"
alt: "{alt.replace('"', "'")}"
---
{corps}
'''
out = pathlib.Path("content/blog") / (slug + ".md")
out.write_text(md, encoding="utf-8")
print("article écrit:", out)
with open(os.environ["GITHUB_OUTPUT"], "a") as f:
    f.write(f"slug={slug}\n")
