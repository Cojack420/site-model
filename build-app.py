"""Build the private Impulse Lane app (GitHub Pages + StatiCrypt + PWA).

  python build-app.py            -> encrypt the latest model into index.html, refresh manifest/sw/icons
  python build-app.py --push     -> same, then commit and push (GitHub Pages serves it)

The password lives in the vault note (API Keys.md) and in app-password.txt here (gitignored, never pushed).
Only the encrypted page is published; without the password nobody can read the model."""
import os, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop", "Impulse Lane", "Impulse Lane 3D.html")
PW = open(os.path.join(HERE, "app-password.txt"), encoding="utf-8").read().strip()
VER = time.strftime("%Y%m%d-%H%M%S")

# 1. encrypt (StatiCrypt 3.5.4, MIT; pinned)
tmp = tempfile.mkdtemp()
shutil.copy(SRC, os.path.join(tmp, "index.html"))
out = os.path.join(tmp, "enc")
subprocess.run(["npx", "-y", "staticrypt@3.5.4", os.path.join(tmp, "index.html"), "-p", PW,
                "--short", "--remember", "365", "-d", out,
                "--template-title", "Impulse Lane", "--template-instructions", "Enter the password to open the model.",
                "--template-color-primary", "#b5531c", "--template-color-secondary", "#1d2a1f"],
               check=True, shell=(os.name == "nt"), capture_output=True)
html = open(os.path.join(out, "index.html"), encoding="utf-8").read()

# 2. make it an installable, offline app
head = ('<link rel="manifest" href="manifest.webmanifest"><meta name="theme-color" content="#1d2a1f">'
        '<link rel="icon" href="icon-192.png"><link rel="apple-touch-icon" href="icon-192.png">'
        '<script>if("serviceWorker" in navigator)navigator.serviceWorker.register("sw.js");</script>')
html = html.replace("</head>", head + "</head>", 1)
open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(html)

open(os.path.join(HERE, "manifest.webmanifest"), "w", encoding="utf-8").write("""{
  "name": "Impulse Lane",
  "short_name": "Impulse Ln",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "orientation": "any",
  "background_color": "#1d2a1f",
  "theme_color": "#1d2a1f",
  "icons": [
    {"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
    {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"}
  ]
}
""")

# network-first for the page (updates show up), cache fallback (works offline);
# CDN libraries (three.js etc.) cached on first online use.
open(os.path.join(HERE, "sw.js"), "w", encoding="utf-8").write(f"""const C = "impulse-{VER}";
const CORE = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png"];
self.addEventListener("install", e => {{ e.waitUntil(caches.open(C).then(c => c.addAll(CORE))); self.skipWaiting(); }});
self.addEventListener("activate", e => {{ e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== C).map(k => caches.delete(k))))); self.clients.claim(); }});
self.addEventListener("fetch", e => {{
  const r = e.request;
  if (r.method !== "GET") return;
  const u = new URL(r.url);
  if (u.origin === location.origin) {{
    e.respondWith(fetch(r).then(res => {{ const cp = res.clone(); caches.open(C).then(c => c.put(r, cp)); return res; }})
      .catch(() => caches.match(r).then(m => m || caches.match("index.html"))));
  }} else if (/cdn\\.jsdelivr\\.net|unpkg\\.com|cdnjs\\.cloudflare\\.com/.test(u.host)) {{
    e.respondWith(caches.match(r).then(m => m || fetch(r).then(res => {{ const cp = res.clone(); caches.open(C).then(c => c.put(r, cp)); return res; }})));
  }}
}});
""")

# 3. icons: a plat outline + house footprint (own look; not a rounded tile)
if not os.path.exists(os.path.join(HERE, "icon-512.png")):
    from PIL import Image, ImageDraw
    for n in (512, 192):
        im = Image.new("RGB", (n, n), "#1d2a1f"); d = ImageDraw.Draw(im); k = n / 512
        lot = [(70, 420), (430, 395), (455, 120), (95, 95)]
        d.line([(x * k, y * k) for x, y in lot + [lot[0]]], fill="#e8b04a", width=max(3, int(14 * k)))
        d.polygon([(x * k, y * k) for x, y in [(190, 300), (320, 292), (316, 228), (186, 236)]], fill="#f4efe4")
        d.line([(60 * k, 470 * k), (470 * k, 445 * k)], fill="#b5531c", width=max(2, int(10 * k)))
        im.save(os.path.join(HERE, f"icon-{n}.png"))

print("built", VER, "| index.html", round(len(html) / 1e6, 2), "MB")
if "--push" in sys.argv:
    g = ["git", "-C", HERE]
    subprocess.run(g + ["add", "index.html", "sw.js", "manifest.webmanifest", "icon-192.png", "icon-512.png", "build-app.py", ".gitignore"], check=True)
    subprocess.run(g + ["commit", "-q", "-m", f"App build {VER}"], check=False)
    subprocess.run(g + ["-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential", "push", "-q", "origin", "HEAD:main"], check=True)
    print("pushed")
