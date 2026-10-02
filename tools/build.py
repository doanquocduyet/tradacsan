#!/usr/bin/env python3
"""
Sinh trang bài viết tĩnh từ journal/posts.json.

Chạy:  python3 tools/build.py
Tạo ra:
  journal/<slug>.html   — mỗi bài một trang riêng (có title, description, JSON-LD Article + FAQ)
  journal/index.html    — danh sách bài
  sitemap.xml, robots.txt — chỉ khi site.url trong posts.json đã điền
  index.html            — cập nhật mảng ARTICLES giữa hai mốc /* ==ARTICLES== */ và /* ==/ARTICLES== */

Muốn thêm bài: thêm một mục vào "posts" trong journal/posts.json rồi chạy lại. Không sửa tay file .html sinh ra.
"""
import json, os, re, html, sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, "journal", "posts.json")
INDEX = os.path.join(ROOT, "index.html")

with open(POSTS, encoding="utf-8") as f:
    data = json.load(f)
SITE = data["site"]
posts = sorted(data["posts"], key=lambda p: p["date"], reverse=True)
BASE = SITE.get("url", "").rstrip("/")

def esc(s):
    return html.escape(str(s or ""), quote=True)

def vn_date(iso):
    y, m, d = iso.split("-")
    return f"{d}/{m}/{y}"

def abs_url(path):
    return f"{BASE}/{path}" if BASE else path

def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s or "")

# ---------- CSS dùng chung cho trang tĩnh (cùng hệ màu, chữ với index.html) ----------
CSS = """
:root{--green:#14433a;--green-d:#0d2f28;--green-t:#1c5647;--bg:#eef2f2;--ink:#243330;--muted:#6f817c;--line:#dbe3e1;--line-d:#c3cfcb;
--serif:'Playfair Display',Georgia,serif;--sans:'Nunito Sans',system-ui,sans-serif;--pad:clamp(16px,3.4vw,40px)}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.7}
img{display:block;max-width:100%}a{color:inherit}
h1,h2,h3{font-family:var(--serif);font-weight:600;line-height:1.22;color:var(--green-t)}
.ann{background:var(--green);color:#fff;text-align:center;font-size:12.5px;padding:10px var(--pad)}
.ann a{color:#fff}
header{background:#fff;border-bottom:1px solid var(--line)}
.hwrap{max-width:1320px;margin:0 auto;padding:14px var(--pad);display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:10px;text-decoration:none;color:var(--green-t)}
.brand svg{width:30px;height:30px;stroke:currentColor;fill:none;stroke-width:1.3;stroke-linecap:round;stroke-linejoin:round}
.brand b{font-family:var(--serif);font-size:15px;letter-spacing:.08em;font-weight:600}
.brand small{display:block;font-family:var(--serif);font-size:8px;letter-spacing:.2em;text-transform:uppercase;opacity:.8}
nav{display:flex;gap:16px;font-size:13.5px;overflow-x:auto;max-width:100%;scrollbar-width:none;-webkit-overflow-scrolling:touch}nav::-webkit-scrollbar{display:none}nav a{white-space:nowrap;text-decoration:none;color:var(--ink);padding:4px 0;border-bottom:1px solid transparent}nav a:hover{border-bottom-color:var(--ink)}
@media(max-width:600px){.hwrap{padding:10px var(--pad)}.brand b{font-size:13px}}
.wrap{max-width:1320px;margin:0 auto;padding:0 var(--pad)}
.crumb{font-size:12px;color:var(--muted);padding:18px 0 0}.crumb a{text-decoration:none}.crumb a:hover{text-decoration:underline}
.ahero{display:grid;grid-template-columns:1fr;background:#f4f6f5;margin-top:16px}
@media(min-width:860px){.ahero{grid-template-columns:1fr 1fr}}
.ahero .tx{padding:clamp(28px,4vw,56px) var(--pad);display:flex;flex-direction:column;justify-content:center}
.eyebrow{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--green-t);font-weight:700}
.ahero h1{font-size:clamp(26px,3.4vw,42px);margin-top:10px;text-wrap:balance}
.meta{margin-top:14px;font-size:12.5px;color:var(--muted)}
.ahero .im{min-height:220px;background:#fff}.ahero .im img{width:100%;height:100%;object-fit:cover}
.abody{display:grid;grid-template-columns:1fr;gap:30px;padding:40px 0 20px}
@media(min-width:860px){.abody{grid-template-columns:220px minmax(0,68ch);gap:60px}}
.aside{font-size:12.5px;color:var(--green-t);border-top:1px solid var(--line-d);padding-top:16px;align-self:start}
.aside h4{font-family:var(--sans);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;margin:18px 0 8px}
.aside a{display:block;margin-bottom:6px;text-decoration:none}.aside a:hover{text-decoration:underline}
.answer{background:#fff;border-left:3px solid var(--green);padding:16px 18px;margin-bottom:26px;font-size:15px;color:var(--green-t)}
.answer b{display:block;font-size:11px;letter-spacing:.14em;text-transform:uppercase;margin-bottom:6px}
.atext{font-size:15.5px;line-height:1.75;color:var(--green-t)}
.atext p{margin-bottom:16px}.atext ul{margin:0 0 16px 20px}.atext li{margin-bottom:6px}
.atext h2{font-size:23px;margin:30px 0 12px}
.faq{margin-top:34px;border-top:1px solid var(--line-d)}
.faq h2{font-size:22px;margin:22px 0 6px}
.faq details{border-bottom:1px solid var(--line-d)}
.faq summary{cursor:pointer;padding:14px 2px;font-family:var(--serif);font-size:16px;color:var(--green-t);list-style:none;display:flex;justify-content:space-between;gap:12px}
.faq summary::after{content:"+";font-family:var(--sans);color:var(--muted)}
.faq details[open] summary::after{content:"−"}
.faq details p{padding:0 2px 16px;font-size:14.5px;color:var(--green-t)}
.src{margin-top:30px;font-size:13px;color:var(--muted)}.src h3{font-size:14px;margin-bottom:8px;color:var(--green-t)}
.src li{margin-bottom:6px;margin-left:18px}.src a{word-break:break-word}
.rel{margin-top:34px;background:#fff;border:1px solid var(--line);padding:18px 20px}
.rel h3{font-size:17px;margin-bottom:10px}
.rel a{display:inline-block;margin:4px 8px 4px 0;padding:9px 14px;border:1px solid var(--green);color:var(--green);text-decoration:none;font-size:12.5px;letter-spacing:.1em;text-transform:uppercase;font-weight:600}
.rel a:hover{background:var(--green);color:#fff}
.list{display:grid;grid-template-columns:1fr;gap:34px 24px;padding:30px 0 50px}
@media(min-width:700px){.list{grid-template-columns:repeat(2,1fr)}}
@media(min-width:1000px){.list{grid-template-columns:repeat(3,1fr)}}
.card{text-decoration:none}.card .im{aspect-ratio:16/10;overflow:hidden;background:#fff}.card img{width:100%;height:100%;object-fit:cover}
.card .cat{margin-top:12px;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600}
.card h2{font-size:19px;margin-top:6px}.card p{margin-top:8px;font-size:13.5px;color:var(--green-t)}
.card time{display:block;margin-top:8px;font-size:12px;color:var(--muted)}
.jhead{text-align:center;padding:34px 0 10px}.jhead h1{font-size:clamp(28px,3.6vw,42px)}.jhead p{color:var(--green-t);margin-top:10px}
footer{background:var(--green);color:#fff;margin-top:50px;padding:34px var(--pad);font-size:13px}
footer .in{max-width:1320px;margin:0 auto;display:flex;flex-wrap:wrap;gap:14px 30px;justify-content:space-between;align-items:center}
footer a{color:#fff}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
"""

LOGO_SVG = """<svg viewBox="0 0 44 44" aria-hidden="true"><path d="M10 17h20a2 2 0 0 1 2 2v3c0 6.1-4.9 11-11 11h-2c-6.1 0-11-4.9-11-11v-3a2 2 0 0 1 2-2Z"/><path d="M32 20h3.5a4.5 4.5 0 0 1 0 9H33"/><path d="M8 36h26"/><path d="M14 17c0-2.6 3.6-4 8-4s8 1.4 8 4"/><path d="M22 13V9"/><path d="M19 9h6"/><path d="M17 4.5c0 1.4 1.2 1.6 1.2 3M22 3c0 1.6 1.2 1.8 1.2 3.4M27 4.5c0 1.4-1.2 1.6-1.2 3"/></svg>"""

def shell(title, description, body, canonical=None, extra_head="", og_image=None, og_type="website"):
    head = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        f'<title>{esc(title)}</title>',
        f'<meta name="description" content="{esc(description)}">',
        '<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">',
        f'<meta property="og:site_name" content="{esc(SITE["name"])}">',
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(description)}">',
        '<meta property="og:locale" content="vi_VN">',
        '<meta name="twitter:card" content="summary_large_image">',
    ]
    if canonical: head.append(f'<link rel="canonical" href="{esc(canonical)}">'); head.append(f'<meta property="og:url" content="{esc(canonical)}">')
    if og_image: head.append(f'<meta property="og:image" content="{esc(og_image)}">')
    head.append('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    head.append('<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Nunito+Sans:wght@400;600;700&display=swap" rel="stylesheet">')
    head.append(f"<style>{CSS}</style>")
    head.append(extra_head)
    return f"""<!doctype html>
<html lang="vi">
<head>
{chr(10).join(head)}
</head>
<body>
<div class="ann"><a href="../index.html">Miễn phí giao hàng cho đơn từ 500.000₫ — xem cửa hàng</a></div>
<header><div class="hwrap">
  <a class="brand" href="../index.html">{LOGO_SVG}<span><b>TRÀ ĐẶC SẢN</b><small>Việt Nam</small></span></a>
  <nav><a href="../index.html#/c/tra-la-roi">Trà</a><a href="../index.html#/c/dung-cu">Dụng cụ</a><a href="../index.html#/c/qua-tang">Quà tặng</a><a href="index.html">Nhật ký trà</a><a href="../index.html#/brew">Cẩm nang pha</a></nav>
</div></header>
{body}
<footer><div class="in">
  <span>© {date.today().year} {esc(SITE["name"])}</span>
  <span><a href="../index.html#/contact">Liên hệ</a> · <a href="../index.html#/policy/giao-hang">Giao hàng</a> · <a href="../index.html#/policy/doi-tra">Đổi trả</a></span>
</div></footer>
</body>
</html>
"""

def jsonld_article(p):
    url = abs_url(f"journal/{p['slug']}.html")
    img = abs_url(f"img/{p['img']}.jpg")
    author = p.get("author") or SITE.get("author") or SITE["name"]
    art = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": p["title"],
        "description": p["description"],
        "image": [img],
        "datePublished": p["date"],
        "dateModified": p.get("updated") or p["date"],
        "author": {"@type": "Organization", "name": author},
        "publisher": {"@type": "Organization", "name": SITE["name"], "logo": {"@type": "ImageObject", "url": abs_url(SITE.get("logo", ""))}},
        "inLanguage": "vi",
        "articleSection": p["cat"],
        "keywords": ", ".join(p.get("tags", [])),
    }
    if BASE: art["mainEntityOfPage"] = {"@type": "WebPage", "@id": url}
    if p.get("sources"):
        art["citation"] = [{"@type": "CreativeWork", "name": s["t"], "url": s["u"]} for s in p["sources"]]
    out = [art]
    if p.get("faq"):
        out.append({
            "@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in p["faq"]],
        })
    out.append({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": abs_url("index.html")},
            {"@type": "ListItem", "position": 2, "name": "Nhật ký trà", "item": abs_url("journal/index.html")},
            {"@type": "ListItem", "position": 3, "name": p["title"], "item": url},
        ],
    })
    return "".join(f'<script type="application/ld+json">{json.dumps(o, ensure_ascii=False)}</script>' for o in out)

def article_page(p):
    author = p.get("author") or SITE.get("author") or SITE["name"]
    meta = f'Đăng {vn_date(p["date"])}'
    if p.get("updated") and p["updated"] != p["date"]: meta += f' · Cập nhật {vn_date(p["updated"])}'
    meta += f' · {esc(author)}'
    faq = ""
    if p.get("faq"):
        faq = '<section class="faq"><h2>Hỏi nhanh</h2>' + "".join(
            f'<details><summary>{esc(f["q"])}</summary><p>{esc(f["a"])}</p></details>' for f in p["faq"]) + "</section>"
    src = ""
    if p.get("sources"):
        src = '<section class="src"><h3>Nguồn</h3><ol>' + "".join(
            f'<li><a href="{esc(s["u"])}" rel="nofollow noopener" target="_blank">{esc(s["t"])}</a></li>' for s in p["sources"]) + "</ol></section>"
    rel = ""
    if p.get("products"):
        rel = '<section class="rel"><h3>Trà nhắc đến trong bài</h3>' + "".join(
            f'<a href="../index.html#/p/{esc(r["slug"])}">{esc(r["name"])}</a>' for r in p["products"]) + "</section>"
    body = f"""
<main class="wrap">
  <div class="crumb"><a href="../index.html">Trang chủ</a> / <a href="index.html">Nhật ký trà</a> / {esc(p["title"])}</div>
  <div class="ahero">
    <div class="tx"><span class="eyebrow">{esc(p["cat"])}</span><h1>{esc(p["title"])}</h1><p class="meta">{meta}</p></div>
    <div class="im"><img src="../img/{esc(p["img"])}.jpg" alt="{esc(p["title"])}" width="640" height="640"></div>
  </div>
  <article class="abody">
    <aside class="aside">
      <h4>Chủ đề</h4>{"".join(f'<a href="index.html#tag-{esc(t)}">{esc(t)}</a>' for t in p.get("tags", []))}
      <h4>Cùng mục</h4>{"".join(f'<a href="{esc(o["slug"])}.html">{esc(o["title"])}</a>' for o in posts if o["slug"] != p["slug"] and o["cat"] == p["cat"]) or '<span class="muted">—</span>'}
    </aside>
    <div>
      <div class="answer"><b>Trả lời nhanh</b>{esc(p["answer"])}</div>
      <div class="atext">{p["body"]}</div>
      {faq}{src}{rel}
    </div>
  </article>
</main>"""
    canonical = abs_url(f"journal/{p['slug']}.html") if BASE else None
    og = abs_url(f"img/{p['img']}.jpg") if BASE else None
    return shell(f'{p["title"]} — {SITE["name"]}', p["description"], body, canonical, jsonld_article(p), og, "article")

def list_page():
    cards = "".join(
        f'<a class="card" href="{esc(p["slug"])}.html"><div class="im"><img src="../img/{esc(p["img"])}.jpg" alt="" loading="lazy" width="640" height="400"></div>'
        f'<div class="cat">{esc(p["cat"])}</div><h2>{esc(p["title"])}</h2><p>{esc(p["excerpt"])}</p><time datetime="{p["date"]}">{vn_date(p["date"])}</time></a>'
        for p in posts)
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": f'Nhật ký trà — {SITE["name"]}',
          "hasPart": [{"@type": "Article", "headline": p["title"], "url": abs_url(f"journal/{p['slug']}.html"), "datePublished": p["date"]} for p in posts]}
    body = f"""
<main class="wrap">
  <div class="crumb"><a href="../index.html">Trang chủ</a> / Nhật ký trà</div>
  <div class="jhead"><h1>Nhật ký trà</h1><p>Tin trà Việt và thế giới mỗi tuần, cách pha, cách chọn — viết gọn, có nguồn.</p></div>
  <div class="list">{cards}</div>
</main>"""
    canonical = abs_url("journal/index.html") if BASE else None
    return shell(f'Nhật ký trà — {SITE["name"]}', "Tin tức trà đặc sản Việt Nam và thế giới mỗi tuần, cách pha và cách chọn trà — viết gọn, dễ hiểu, có nguồn.", body, canonical,
                 f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')

def update_index():
    with open(INDEX, encoding="utf-8") as f: s = f.read()
    a, b = "/* ==ARTICLES== */", "/* ==/ARTICLES== */"
    if a not in s or b not in s:
        print("! index.html không có mốc ARTICLES — bỏ qua"); return
    items = []
    for p in posts:
        items.append({"slug": p["slug"], "cat": p["cat"], "title": p["title"], "img": p["img"], "date": vn_date(p["date"]),
                      "author": p.get("author", ""), "tags": p.get("tags", []), "excerpt": p["excerpt"],
                      "body": p["body"], "url": f"journal/{p['slug']}.html"})
    js = a + "\nconst ARTICLES = " + json.dumps(items, ensure_ascii=False, indent=1) + ";\n" + b
    s = s[:s.index(a)] + js + s[s.index(b) + len(b):]
    with open(INDEX, "w", encoding="utf-8") as f: f.write(s)
    print(f"✓ index.html: {len(items)} bài")

def main():
    jd = os.path.join(ROOT, "journal")
    for p in posts:
        with open(os.path.join(jd, p["slug"] + ".html"), "w", encoding="utf-8") as f: f.write(article_page(p))
        print(f"✓ journal/{p['slug']}.html")
    with open(os.path.join(jd, "index.html"), "w", encoding="utf-8") as f: f.write(list_page())
    print("✓ journal/index.html")
    update_index()
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\n" + (f"Sitemap: {BASE}/sitemap.xml\n" if BASE else ""))
    if BASE:
        urls = [("index.html", date.today().isoformat()), ("journal/index.html", posts[0]["date"])] + [(f"journal/{p['slug']}.html", p.get("updated") or p["date"]) for p in posts]
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(
            f"  <url><loc>{BASE}/{u}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls) + "</urlset>\n"
        with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f: f.write(xml)
        print("✓ sitemap.xml")
    else:
        print("· Chưa có site.url trong posts.json → chưa sinh sitemap.xml và canonical. Điền tên miền rồi chạy lại.")

if __name__ == "__main__":
    main()
