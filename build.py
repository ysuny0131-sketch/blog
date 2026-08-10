#!/usr/bin/env python3
import json, re, html, shutil
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
OUT = ROOT / "site"
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
BASE = CFG["base_url"].rstrip("/")


def parse_frontmatter(text):
    if not text.startswith("---\n"):
        raise ValueError("Markdown file must begin with YAML-like front matter")
    _, fm, body = text.split("---", 2)
    data = {}
    for line in fm.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip()
    data["tags"] = [x.strip() for x in data.get("tags", "").split(",") if x.strip()]
    return data, body.strip()


def inline_md(s):
    s = html.escape(s, quote=False)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', s)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2" rel="noopener">\1</a>', s)
    return s


def markdown_to_html(md):
    lines = md.splitlines(); out=[]; i=0; in_list=False; in_code=False; code=[]
    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>"); in_list=False
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            close_list()
            if not in_code:
                in_code=True; code=[]
            else:
                out.append("<pre><code>"+html.escape("\n".join(code))+"</code></pre>"); in_code=False
            i += 1; continue
        if in_code:
            code.append(line); i += 1; continue
        if not line.strip(): close_list(); i += 1; continue
        if line.startswith("### "): close_list(); out.append(f"<h3>{inline_md(line[4:])}</h3>")
        elif line.startswith("## "): close_list(); out.append(f"<h2>{inline_md(line[3:])}</h2>")
        elif line.startswith("# "): close_list(); out.append(f"<h2>{inline_md(line[2:])}</h2>")
        elif line.startswith("> "): close_list(); out.append(f"<blockquote>{inline_md(line[2:])}</blockquote>")
        elif re.match(r"^[-*] ", line):
            if not in_list: out.append("<ul>"); in_list=True
            out.append(f"<li>{inline_md(line[2:])}</li>")
        else:
            close_list(); out.append(f"<p>{inline_md(line)}</p>")
        i += 1
    close_list()
    if in_code: out.append("<pre><code>"+html.escape("\n".join(code))+"</code></pre>")
    return "\n".join(out)


def iso_date(d):
    datetime.strptime(d, "%Y-%m-%d")
    return d


def build():
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copy2(ROOT / "style.css", OUT / "style.css")

    posts=[]
    for path in sorted(CONTENT.glob("*.md")):
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        for req in ["title", "date", "description", "slug"]:
            if not meta.get(req): raise ValueError(f"{path.name}: missing {req}")
        meta["date"] = iso_date(meta["date"])
        meta["url"] = f"{BASE}/#{meta['slug']}"
        meta["source_file"] = path.name
        meta["body_html"] = markdown_to_html(body)
        posts.append(meta)
    posts.sort(key=lambda p: p["date"], reverse=True)

    naver_verification = CFG.get("naver_site_verification", "").strip()
    google_verification = CFG.get("google_site_verification", "").strip()
    verification_tags = []
    if naver_verification:
        verification_tags.append(f'<meta name="naver-site-verification" content="{html.escape(naver_verification, quote=True)}">')
    if google_verification:
        verification_tags.append(f'<meta name="google-site-verification" content="{html.escape(google_verification, quote=True)}">')
    verify_tags = "\n".join(verification_tags)

    toc=[]; articles=[]
    for p in posts:
        tags=''.join(f'<span class="tag">#{html.escape(t)}</span>' for t in p["tags"])
        toc.append(f'<li><a href="#{html.escape(p["slug"])}">{html.escape(p["title"])}</a><time datetime="{p["date"]}">{p["date"]}</time></li>')
        articles.append(f'''<article class="post" id="{html.escape(p['slug'])}">
<h2>{html.escape(p['title'])}</h2>
<div class="meta"><time datetime="{p['date']}">{p['date']}</time></div>
<p class="summary">{html.escape(p['description'])}</p>
<div class="tags">{tags}</div>
<div class="post-body">{p['body_html']}</div>
<p class="top-link"><a href="#top">↑ 글 목록으로</a></p>
</article>''')

    ld = {
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": CFG["site_name"],
        "description": CFG["site_description"],
        "url": BASE + "/",
        "author": {"@type": "Person", "name": CFG["author"]},
        "blogPost": [
            {"@type":"BlogPosting", "headline":p["title"], "datePublished":p["date"], "url":p["url"], "description":p["description"]}
            for p in posts
        ]
    }

    doc=f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(CFG['site_name'])}</title>
<meta name="description" content="{html.escape(CFG['site_description'], quote=True)}">
<meta name="robots" content="index,follow">
<link rel="canonical" href="{BASE}/">
<link rel="alternate" type="application/rss+xml" title="RSS" href="{BASE}/rss.xml">
<link rel="stylesheet" href="{BASE}/style.css">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(CFG['site_name'], quote=True)}">
<meta property="og:description" content="{html.escape(CFG['site_description'], quote=True)}">
<meta property="og:url" content="{BASE}/">
{verify_tags}
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
</head>
<body id="top">
<header><div class="wrap"><a class="brand" href="#top">{html.escape(CFG['site_name'])}</a><p class="tagline">{html.escape(CFG['site_description'])}</p></div></header>
<main><div class="wrap">
<section class="index"><h1>글 목록</h1><ol>{''.join(toc) if toc else '<li>아직 글이 없습니다.</li>'}</ol></section>
<section class="posts">{''.join(articles)}</section>
</div></main>
<footer><div class="wrap">© {datetime.now().year} {html.escape(CFG['author'])} · <a href="{BASE}/rss.xml">RSS</a></div></footer>
</body>
</html>'''
    (OUT / "index.html").write_text(doc, encoding="utf-8")

    public_posts=[{k:p[k] for k in ["title","date","description","slug","tags","url","source_file"]} for p in posts]
    (OUT / "posts.json").write_text(json.dumps(public_posts, ensure_ascii=False, indent=2), encoding="utf-8")

    latest = posts[0]["date"] if posts else datetime.now().strftime("%Y-%m-%d")
    sitemap=f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{html.escape(BASE + '/')}</loc>
    <lastmod>{latest}</lastmod>
  </url>
</urlset>'''
    (OUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n", encoding="utf-8")

    rss=['<?xml version="1.0" encoding="UTF-8"?>','<rss version="2.0"><channel>',f'<title>{html.escape(CFG["site_name"])}</title>',f'<link>{BASE}/</link>',f'<description>{html.escape(CFG["site_description"])}</description>',f'<language>{CFG["language"]}</language>']
    for p in posts[:50]:
        dt=datetime.strptime(p["date"],"%Y-%m-%d").replace(tzinfo=timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")
        rss += ["<item>",f'<title>{html.escape(p["title"])}</title>',f'<link>{p["url"]}</link>',f'<guid>{p["url"]}</guid>',f'<pubDate>{dt}</pubDate>',f'<description>{html.escape(p["description"])}</description>',"</item>"]
    rss += ["</channel></rss>"]
    (OUT / "rss.xml").write_text("\n".join(rss), encoding="utf-8")
    print(f"Built one HTML page with {len(posts)} post(s) into {OUT}")

if __name__ == "__main__": build()
