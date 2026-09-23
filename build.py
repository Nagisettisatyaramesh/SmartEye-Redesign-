"""Builds the SmartEye site into static HTML.

Run:  python build.py
Pages share one header, footer and demo form; long-form content comes from content/source.json
(extracted from the current eqms-smarteye.com pages).
"""
import json, re, math, datetime, pathlib
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).parent
SRC = json.loads((ROOT / "content" / "source.json").read_text(encoding="utf-8"))
UP = "https://eqms-smarteye.com/wp-content/uploads"
VIDEO = "YjVfsjdiYAY"
EMAIL = "info@scube-technologies.com"

ARROW = '<svg class="arrow" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8h10M9 4l4 4-4 4" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>'
PLAY = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M5 3.5v9l7-4.5z" fill="currentColor"/></svg>'
CHECK = '<svg viewBox="0 0 18 18" aria-hidden="true"><path d="M3 9.5l4 4 8-9" fill="none" stroke="currentColor" stroke-width="2"/></svg>'

ARTICLES = [  # newest first
    "how-an-eqms-simplifies-iso-13485-compliance-for-uk-medical-device-startups",
    "why-uk-medical-device-startups-are-adopting-eqms-to-accelerate-iso-13485-compliance",
    "iso-13485-explained-in-plain-english",
    "why-most-medical-device-startups-fail-their-first-audit",
    "iso-13485-qms-a-complete-guide-for-medical-device-companies-and-startups",
]
JOBS = {
    "data-engineer-software-engineer": dict(title="Data Engineer / Software Engineer", location="125 Deansgate, Manchester", pay="To be confirmed", type="Permanent", posted="2025-07-07", closes=None),
    "content-writer-digital-marketing-blog-writer": dict(title="Content Writer / Digital Marketing", location="125 Deansgate, Manchester", pay="To be confirmed", type="Permanent", posted="2025-07-07", closes=None),
    "software-test-engineer": dict(title="Software Test Engineer", location="Bizspace Altrincham, WA14 5NQ", pay="£35,063 – £41,911 a year", type="Permanent", posted="2024-09-30", closes="2024-10-10"),
}
LEGAL = [
    ("privacy-policy", "Privacy policy"),
    ("terms-and-conditions", "Terms and conditions"),
    ("website-cookie-policy", "Cookie policy"),
    ("quality-policy", "Quality policy"),
    ("security-policy", "Security policy"),
]
TODAY = datetime.date(2026, 9, 23)


def nice_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B %Y')}"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ---------------------------------------------------------------- content cleaning
def soup_of(html):
    s = BeautifulSoup(html, "lxml")
    body = s.body
    wrapper = body.find(True)
    if wrapper and wrapper.name == "div":
        wrapper.unwrap()
    return s, body


def inner(body):
    return "".join(str(c) for c in body.contents)


def bullets_to_lists(s, body):
    """Paragraphs that start with a bullet character become real list items."""
    for p in list(body.find_all("p")):
        t = p.get_text()
        if not t.strip().startswith(("•", "·", "•")) or p.parent is None:
            continue
        prev = p.find_previous_sibling()
        if prev is not None and prev.name == "ul" and prev.get("data-b"):
            ul = prev
        else:
            ul = s.new_tag("ul"); ul["data-b"] = "1"; p.insert_before(ul)
        li = s.new_tag("li")
        for c in list(p.contents):
            li.append(c.extract())
        first = li.find(string=True)
        if first:
            first.replace_with(re.sub(r"^\s*[•·•]\s*", "", str(first)))
        ul.append(li); p.decompose()
    for ul in body.find_all("ul", attrs={"data-b": True}):
        del ul["data-b"]


def norm(t):
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def clean_article(html, title=""):
    s, body = soup_of(html)
    for h in body.find_all("h1"):
        h.name = "h2"
    # a leading heading that repeats the page title is dropped
    first = body.find(True)
    if first and first.name in ("h2", "h3") and norm(first.get_text()) == norm(title):
        first.decompose()
    # articles written with h3 sections: lift the outline one level so the contents list works
    if len(body.find_all("h2")) < 2 and len(body.find_all("h3")) >= 2:
        for h in body.find_all("h3"): h.name = "h2"
        for h in body.find_all("h4"): h.name = "h3"
    for h5 in body.find_all("h5"):
        if h5.find("a", href=re.compile("/author/")):
            h5.decompose(); continue
        h5.name = "div"; h5["class"] = "callout"
    for a in body.find_all("a"):
        if a.get_text(strip=True).lower() == "get a demo" and a.parent is body:
            a.decompose()
    for a in body.find_all("a", href=True):
        a["href"] = localise(a["href"], "../")
    # drop a leading "Introduction" heading — the page title already introduces the piece
    first = body.find(True)
    if first and first.name == "h2" and first.get_text(strip=True).lower() == "introduction":
        first.decompose()
    bullets_to_lists(s, body)
    for li in body.find_all("li"):
        t = li.find(string=True)
        if t and re.match(r"^\s*-\s*", t):
            t.replace_with(re.sub(r"^\s*-\s*", "", str(t)))
    return inner(body)


def clean_job(html):
    s, body = soup_of(html)
    for h5 in body.find_all("h5"):
        h5.decompose()
    # everything up to and including "Full job description" repeats the page header
    marker = body.find(lambda t: t.name == "p" and t.get_text(strip=True).lower() == "full job description")
    if marker:
        for sib in list(marker.find_previous_siblings()):
            sib.decompose()
        marker.decompose()
    for st in body.find_all("strong"):
        txt = st.get_text(strip=True)
        if txt.lower().startswith(("pay:", "work location:", "application deadline:")):
            st.parent.decompose() if st.parent and st.parent.name == "p" else None
    bullets_to_lists(s, body)
    return inner(body)


def clean_legal(html):
    s, body = soup_of(html)
    updated = ""
    h1 = body.find("h1")
    if h1: h1.decompose()
    for p in body.find_all("p")[:3]:
        m = re.search(r"Last updated:\s*([\w\-]+)", p.get_text())
        if m:
            updated = m.group(1); p.decompose(); break
    bullets_to_lists(s, body)
    for a in body.find_all("a", href=True):
        a["href"] = localise(a["href"], "../")
    return inner(body), updated


LOCAL = {
    "quality-management-system-qms-for-medical-devices-and-samd": "why-smarteye.html",
    "powered-by-s-cube": "about.html",
    "resources": "resources.html",
    "contact": "contact.html",
    "category/jobs": "careers.html",
}


def localise(href, root):
    m = re.match(r"https?://(?:www\.)?eqms-smarteye\.com/?(.*?)/?(#.*)?$", href)
    if not m:
        return href
    path, frag = m.group(1), m.group(2) or ""
    if path == "":
        return root + "index.html" + frag
    if path in LOCAL:
        return root + LOCAL[path] + frag
    if path in ARTICLES:
        return root + f"resources/{path}.html"
    if path in dict(LEGAL):
        return root + f"legal/{path}.html"
    return href


def words(html):
    return len(re.sub(r"<[^>]+>", " ", html).split())


# ---------------------------------------------------------------- shared chrome
NAV = [("why-smarteye.html", "Why SmartEye"), ("about.html", "Who we are"), ("resources.html", "Resources"),
       ("careers.html", "Careers"), ("contact.html", "Contact")]


def head(title, desc, root):
    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="icon" href="https://eqms-smarteye.com/wp-content/uploads/2025/01/Logo-Light-1.svg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Martian+Mono:wght@400;500&family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;0,6..72,500;1,6..72,300;1,6..72,400&family=Public+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{root}assets/site.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="progress" aria-hidden="true"><i></i></div>"""


def header(root, current, demo_href=None):
    links = "".join(
        f'<a href="{root}{href}"{" aria-current=\"page\"" if href == current else ""}>{label}</a>' for href, label in NAV)
    demo_href = demo_href or f"{root}contact.html#demo"
    return f"""
<header class="top">
  <div class="wrap">
    <a class="logo" href="{root}index.html" aria-label="SmartEye eQMS home"><img src="{UP}/2025/01/Logo-Dark.png" alt="SmartEye" width="122" height="34"></a>
    <button class="menu-btn" aria-expanded="false" aria-controls="nav">Menu</button>
    <nav class="nav" id="nav" aria-label="Main">
      {links}
      <a class="btn btn-primary" href="{demo_href}">Book a demo</a>
    </nav>
  </div>
</header>
<main id="main">"""


def footer(root):
    legal = "".join(f'<li><a href="{root}legal/{slug}.html">{label}</a></li>' for slug, label in LEGAL)
    return f"""</main>
<footer>
  <div class="wrap">
    <div class="foot-grid">
      <div>
        <img src="{UP}/2025/01/Logo-Dark.png" alt="SmartEye" style="height:30px;width:auto">
        <address>S-Cube Technologies Limited<br>125 Deansgate, Manchester M3 2LH<br>United Kingdom<br><a href="mailto:{EMAIL}">{EMAIL}</a></address>
      </div>
      <div><h4>Product</h4><ul><li><a href="{root}why-smarteye.html">Why SmartEye</a></li><li><a href="{root}contact.html#demo">Book a demo</a></li><li><a href="{root}resources.html#video">Watch the overview</a></li></ul></div>
      <div><h4>Company</h4><ul><li><a href="{root}about.html">Who we are</a></li><li><a href="{root}resources.html">Resources</a></li><li><a href="{root}careers.html">Careers</a></li><li><a href="{root}contact.html">Contact</a></li></ul></div>
      <div><h4>Policies</h4><ul>{legal}</ul></div>
    </div>
    <div class="foot-base">
      <span>© S-Cube Technologies Limited 2026</span>
      <span class="social"><a href="https://www.linkedin.com/company/s-cubetechnologies/">LinkedIn</a><a href="https://twitter.com/i_SCubeTech">X</a><a href="https://www.facebook.com/i.scubetechnologies/">Facebook</a><a href="https://www.instagram.com/i.scubetech/">Instagram</a></span>
    </div>
  </div>
</footer>
<script src="{root}assets/site.js" defer></script>
</body>
</html>
"""


def demo_form(root, heading='See your own design process <em>in SmartEye</em>'):
    return f"""
<section class="section dark demo" id="demo">
  <div class="wrap">
    <div data-reveal>
      <p class="eyebrow">Book a demo</p>
      <h2>{heading}</h2>
      <p class="lede" style="margin-top:22px">We'll tailor a free demo to your device, your team and your stage of development.</p>
      <ul>
        <li>{CHECK}A walkthrough built around your SaMD or hardware project</li>
        <li>{CHECK}A full view of traceability, from user need to DHF</li>
        <li>{CHECK}Answers on migration, deployment and licensing</li>
      </ul>
    </div>
    <form class="form" data-demo-form novalidate data-reveal>
      <div class="field"><label for="f-name">Your name</label><input id="f-name" name="name" autocomplete="name" required></div>
      <div class="field"><label for="f-email">Work email</label><input id="f-email" name="email" type="email" autocomplete="email" required></div>
      <div class="field"><label for="f-phone">Phone number</label><input id="f-phone" name="phone" type="tel" autocomplete="tel"></div>
      <div class="field"><label for="f-company">Company</label><input id="f-company" name="company" autocomplete="organization"></div>
      <div class="field full"><label for="f-country">Country</label><select id="f-country" name="country" data-countries><option value="">Select your country</option></select></div>
      <div class="field full"><label for="f-req">What would you like to see?</label><textarea id="f-req" name="requirement" placeholder="For example: design control for a Class IIa SaMD, moving off spreadsheets"></textarea></div>
      <div class="form-foot">
        <small>See our <a href="{root}legal/privacy-policy.html">Privacy policy</a> and <a href="{root}legal/terms-and-conditions.html">Terms</a>.</small>
        <button class="btn btn-primary" type="submit">Book a demo</button>
      </div>
      <p class="form-status" role="status"></p>
    </form>
  </div>
</section>"""


def cta_band(root, title='Find out what SmartEye could do <em>for your product</em>', text="Book a free demo, tailored to your device and your team."):
    return f"""
<section class="section section-tight">
  <div class="wrap">
    <div class="cta-band" data-reveal>
      <div><h2>{title}</h2><p>{text}</p></div>
      <a class="btn btn-primary" href="{root}contact.html#demo">Book a demo {ARROW}</a>
    </div>
  </div>
</section>"""


def post_card(slug, root, excerpt=False):
    a = SRC[slug]
    img = a["img"].replace("-scaled", "")
    ex = f'<p>{esc(a["desc"])}</p>' if excerpt and a["desc"] else ""
    return f"""<a class="post" href="{root}resources/{slug}.html">
        <figure><img loading="lazy" src="{img}" alt=""></figure>
        <time datetime="{a['date']}">{nice_date(a['date'])}</time>
        <h3>{esc(a['title'])}</h3>{ex}
      </a>"""


def page_hero(crumb, eyebrow, h1, lede, aside=""):
    crumbs = f'<nav class="crumbs" aria-label="Breadcrumb">{crumb}</nav>' if crumb else ""
    aside_html = f"<aside data-reveal>{aside}</aside>" if aside else "<div></div>"
    return f"""
<section class="page-hero">
  <div class="wrap">
    <div>
      {crumbs}
      {f'<p class="eyebrow">{eyebrow}</p>' if eyebrow else ''}
      <h1 class="rise">{h1}</h1>
      <p class="lede" data-reveal>{lede}</p>
    </div>
    {aside_html}
  </div>
</section>"""


def write(path, html):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")
    print("wrote", path)


# ---------------------------------------------------------------- HOME
def build_home():
    r = ""
    steps = [
        ("User needs", "Start with the people who'll use the device.", "Capture what clinicians, patients and operators need, and link each need to the device's intended use.", "Linked to intended use"),
        ("Design input", "Turn each need into a requirement you can measure.", "Write requirements in SmartEye's requirement manager. Hazards you identify here start your ISO 14971 risk file.", "ISO 13485 7.3.3 · ISO 14971"),
        ("Design output", "Build to the requirement, and keep the link.", "Specifications, drawings, code and software units each link back to the input they satisfy.", "ISO 13485 7.3.4 · IEC 62304"),
        ("Verification", "Did you build it right?", "Tests trace to requirements and results are filed automatically. Any requirement without a passing test shows up as a gap.", "ISO 13485 7.3.6"),
        ("Validation", "Did you build the right thing?", "Clinical and usability evidence is checked against the original user needs. Your DHF and DMR are compiled from the linked records.", "ISO 13485 7.3.7 · 7.3.10"),
    ]
    step_html = "".join(
        f'<div class="step{" on" if k == 0 else ""}"><span class="id">STEP {k+1} OF 5 · {t.upper()}</span><h3>{h}</h3><p>{p}</p><span class="std">{std}</span></div>'
        for k, (t, h, p, std) in enumerate(steps))
    static_html = "".join(f'<li><span class="id">STEP {k+1} · {t.upper()}</span><h3>{h}</h3><p>{p}</p></li>' for k, (t, h, p, _) in enumerate(steps))
    rails = "".join("<i><b></b></i>" for _ in steps)
    boxes = [("USER NEEDS", "What people need", 20, 20, 0), ("DESIGN INPUT", "Measurable requirements", 130, 130, 1),
             ("DESIGN OUTPUT", "Specs, code, drawings", 240, 240, 2), ("MEDICAL DEVICE", "Validated and transferred", 350, 350, 4)]
    box_svg = "".join(
        f'<g class="box" data-at="{at}"><rect x="{x}" y="{y}" width="200" height="64" rx="10"/><text x="{x+18}" y="{y+27}">{a}</text><text class="sub" x="{x+18}" y="{y+47}">{b}</text></g>'
        for a, b, x, y, at in boxes)
    waterfall = f"""<svg class="waterfall" viewBox="0 0 640 440" role="img" aria-label="Design control waterfall: user needs, design input, design output and medical device, with verification and validation loops">
      <path class="flow-bg" d="M120 84 V162 H130 M230 194 V272 H240 M340 304 V382 H350"/>
      <path class="flow" d="M120 84 V162 H130 M230 194 V272 H240 M340 304 V382 H350"/>
      <path class="loop" data-from="3" d="M440 272 C 500 272, 500 162, 330 162"/>
      <text class="loop-label" data-from="3" x="486" y="222">VERIFICATION</text>
      <path class="loop" data-from="4" d="M550 382 C 630 382, 630 52, 220 52"/>
      <text class="loop-label" data-from="4" x="560" y="140">VALIDATION</text>
      {box_svg}
    </svg>"""

    faqs = [
        ("Cloud data security", "SmartEye is a cloud, web-based platform built and run by a team certified to ISO/IEC 27001. Ask for our security documentation when you book your demo."),
        ("Compliance for hardware devices and SaMD", "SmartEye supports design control for physical medical devices and for software as a medical device, with workflows set up for ISO 13485, ISO 14971, IEC 62304 and FDA 21 CFR Part 11."),
        ("Templates", "Hundreds of ready-made SOPs and templates are included, covering QMS, DHF and technical files, along with checklists."),
        ("Team collaboration", "Invite colleagues, reviewers and external users with role-based access, and run reviews and approvals in the platform."),
        ("Data migration", "Our team can help you move existing documents and records into SmartEye. We'll scope this with you during onboarding."),
        ("Target markets", "SmartEye is designed for medical device and SaMD companies in the UK and worldwide working to ISO 13485 and preparing for regulatory submissions."),
        ("Deployment and licensing", "SmartEye is delivered as a cloud service. We'll talk you through licensing during your demo, based on your team size and projects."),
        ("Onboarding", "Admin screens and our team help you set up your organisation, projects and users."),
        ("Software upgrades", "Platform improvements are included, with no additional cost to upgrade."),
    ]
    faq_html = "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in faqs)
    posts = "".join(post_card(s, r) for s in ARTICLES[:3])

    body = f"""
<section class="hero">
  <div class="wrap">
    <div>
      <p class="eyebrow">eQMS for medical devices &amp; SaMD</p>
      <h1 class="rise">Every requirement, <em>traced</em> to its proof.</h1>
      <p class="lede" data-reveal>SmartEye replaces paper and spreadsheet quality systems with one platform for design control. It links requirements, risks, tests and your Design History File, so you can show an auditor how a need became a verified device.</p>
      <div class="cta-row" data-reveal style="--d:.1s">
        <a class="btn btn-primary" href="#demo">Book a demo {ARROW}</a>
        <a class="btn btn-quiet" href="resources.html#video">{PLAY}Watch the overview</a>
      </div>
      <div class="hero-note" data-reveal style="--d:.2s"><span>ISO 13485-ready templates</span><span>Automatic DHF &amp; DMR</span><span>Microsoft Office built in</span></div>
    </div>
    <div class="record" aria-label="Example traceability record" data-reveal style="--d:.15s">
      <div class="record-head"><span class="id">TRACE VIEW</span><span class="id">PRJ · CardioView SaMD</span></div>
      <div class="tabs" role="tablist" aria-label="Choose a requirement">
        <button class="tab" role="tab" aria-selected="true" data-chain="0">SRS-014</button>
        <button class="tab" role="tab" aria-selected="false" data-chain="1">SRS-022</button>
        <button class="tab" role="tab" aria-selected="false" data-chain="2">SRS-031</button>
      </div>
      <ol class="chain" id="chain" aria-live="polite"></ol>
      <div class="record-foot"><span id="trace-status"></span><span class="meter" id="meter"><i></i></span></div>
    </div>
  </div>
</section>

<section class="story" data-story aria-label="Design control, step by step">
  <div class="story-stage">
    <div class="wrap">
      <div>
        <p class="eyebrow">Design control, step by step</p>
        <h2>Follow one need all the way to <em>proof</em>.</h2>
        <div class="steps">{step_html}</div>
        <div class="rail" aria-hidden="true">{rails}</div>
        <ol class="story-static">{static_html}</ol>
      </div>
      {waterfall}
    </div>
  </div>
</section>

<section class="section" id="why">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <div><p class="eyebrow">What changes</p><h2>Transform the way you <em>manage compliance</em></h2></div>
      <p class="lede">Our team has spent their careers building quality management software for medical device and healthcare companies. SmartEye is what they built for the teams who carry the regulatory load.</p>
    </div>
    <div class="pillars" data-stagger>
      <div class="pillar"><h3>Mitigate risk</h3><p>Hazards, risk controls and their verification stay linked, so nothing sits unresolved at design review.</p></div>
      <div class="pillar"><h3>Accelerate compliance</h3><p>Start from ready-made SOPs, templates and checklists instead of writing your QMS from a blank page.</p></div>
      <div class="pillar"><h3>Enhance quality</h3><p>Review and approval happen in one place, with a record of who signed what and when.</p></div>
    </div>
    <ul class="outcomes" data-stagger>
      <li><b>Faster</b>quality processes</li><li><b>Less</b>quality admin</li><li><b>Quicker</b>product releases</li><li><b>Shorter</b>external audits</li>
    </ul>
  </div>
</section>

<section class="section dark" id="platform">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <div><p class="eyebrow">One platform</p><h2>From design input to <em>post-market</em>, in one place</h2></div>
      <p class="lede">SmartEye covers QA/RA across the whole device lifecycle, so you don't need a separate tool for each stage.</p>
    </div>
    <ol class="stages" data-stagger>
      <li><span class="id">STAGE 1</span><h3>Design control</h3><p>Requirements, test and risk management with end-to-end traceability.</p></li>
      <li><span class="id">STAGE 2</span><h3>Cyber security</h3><p>Threats and controls tracked alongside the design they protect.</p></li>
      <li><span class="id">STAGE 3</span><h3>Clinical trials</h3><p>Evidence that links back to the claims it supports.</p></li>
      <li><span class="id">STAGE 4</span><h3>Post-market surveillance</h3><p>Field feedback that feeds into your risk file.</p></li>
    </ol>
    <div class="features" data-stagger>
      <div class="feature"><h3>Bi-directional traceability</h3><p>Web grids show links in both directions, from a user need down to its test and from a failed test back up to the need.</p></div>
      <div class="feature"><h3>Microsoft Office, built in</h3><p>Edit Word and Excel documents inside SmartEye without exporting and re-uploading files.</p></div>
      <div class="feature"><h3>Review and approval</h3><p>Send documents for review, collect approvals and keep the history in one place.</p></div>
      <div class="feature"><h3>Analytics dashboards</h3><p>Track progress through each compliance phase and filter by user, team or project.</p></div>
      <div class="feature"><h3>Global navigator</h3><p>Go to any requirement, risk or document from anywhere in the platform.</p></div>
      <div class="feature"><h3>Guided onboarding</h3><p>Admin screens help you set up projects, users and permissions on day one.</p></div>
    </div>
  </div>
</section>

<section class="section" id="roles">
  <div class="wrap split">
    <div data-reveal>
      <p class="eyebrow">Access and permissions</p>
      <h2>Everyone sees <em>what they should</em></h2>
      <p class="lede" style="margin-top:22px">Give your whole team access, and your auditors and suppliers too, each with a role that fits their work.</p>
    </div>
    <div data-reveal>
      <div class="table-card">
        <table>
          <caption class="sr">Typical permissions by role</caption>
          <thead><tr><th scope="col">Role</th><th scope="col">Configure org</th><th scope="col">Manage projects</th><th scope="col">Author &amp; review</th><th scope="col">View shared</th></tr></thead>
          <tbody>
            <tr><th scope="row">Organisation Admin</th><td class="y">✓</td><td class="y">✓</td><td class="y">✓</td><td class="y">✓</td></tr>
            <tr><th scope="row">Project Admin</th><td class="n">–</td><td class="y">✓</td><td class="y">✓</td><td class="y">✓</td></tr>
            <tr><th scope="row">Standard User</th><td class="n">–</td><td class="n">–</td><td class="y">✓</td><td class="y">✓</td></tr>
            <tr><th scope="row">External User</th><td class="n">–</td><td class="n">–</td><td class="n">–</td><td class="y">✓</td></tr>
          </tbody>
        </table>
      </div>
      <p class="caption">A typical setup. You can adjust permissions for each project.</p>
    </div>
  </div>
</section>

<hr class="rule">

<section class="section" id="templates">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <div><p class="eyebrow">Ready on day one</p><h2>Hundreds of SOPs and templates, <em>already written</em></h2></div>
      <p class="lede">SmartEye comes with ready-made documents and checklists written to industry standards and guidance. Your DHF and DMR are generated from the work you're already doing.</p>
    </div>
    <div class="shelf" data-stagger>
      <div class="doc"><span class="id">QMS</span><h3>Quality manual &amp; SOPs</h3><p>Procedures for the whole quality system.</p></div>
      <div class="doc"><span class="id">DHF</span><h3>Design History File</h3><p>Design inputs, outputs, reviews and V&amp;V.</p></div>
      <div class="doc"><span class="id">TF</span><h3>Technical file</h3><p>Structured for conformity assessment.</p></div>
      <div class="doc"><span class="id">CHK</span><h3>Checklists</h3><p>Check each document against the standard.</p></div>
      <div class="doc auto"><span class="id">AUTO</span><h3>DHF &amp; DMR generation</h3><p>Compiled automatically from linked records.</p></div>
    </div>
  </div>
</section>

<section class="section section-tight">
  <div class="wrap">
    <div class="trust" data-reveal>
      <div>
        <p class="eyebrow">Certified</p>
        <h2>Built by a team audited to the <em>same standards</em> as you</h2>
        <p>S-Cube Technologies is certified to ISO 9001 for quality management and ISO/IEC 27001 for information security. <a class="text-link" href="about.html#certifications">See our certificates {ARROW}</a></p>
      </div>
      <div class="badges">
        <img src="{UP}/2023/09/mark-of-trust-certified-ISO-9001-quality-management-systems-white-logo-En-GB-1019-300x152.png" alt="BSI certified ISO 9001">
        <img src="{UP}/2023/09/mark-of-trust-certified-ISOIEC-27001-information-security-management-white-logo-En-GB-1019-300x152.png" alt="BSI certified ISO/IEC 27001">
      </div>
    </div>
  </div>
</section>

<section class="section section-tight" id="faq">
  <div class="wrap split">
    <div data-reveal class="sticky-col">
      <p class="eyebrow">Questions</p>
      <h2>Before you <em>book a demo</em></h2>
      <p class="lede" style="margin-top:22px">If your question isn't here, ask us during your demo.</p>
    </div>
    <div class="faq" data-reveal>{faq_html}</div>
  </div>
</section>

<hr class="rule">

<section class="section" id="resources">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <div><p class="eyebrow">Resources</p><h2>Learn about <em>ISO 13485</em> and eQMS</h2></div>
      <p class="lede">Practical guides from the S-Cube team, written for medical device founders and quality leads.</p>
    </div>
    <div class="posts" data-stagger>{posts}</div>
    <div class="more"><a class="btn btn-quiet" href="resources.html">See all resources {ARROW}</a></div>
  </div>
</section>
{demo_form(r)}"""
    write("index.html", head("SmartEye eQMS — design control for medical devices & SaMD",
                             "eQMS for medical device and SaMD design control: requirements, risk, testing and traceability in one platform. Book a demo.", r)
          + header(r, "index.html", "#demo") + body + footer(r))


# ---------------------------------------------------------------- WHY SMARTEYE
def build_why():
    r = ""
    ticker_items = ["ISO 13485:2016", "ISO 14971", "IEC 62304", "FDA 21 CFR Part 820", "FDA 21 CFR Part 11", "EU MDR", "UK MDR"]
    t = "".join(f"<span>{x}</span>" for x in ticker_items)
    checklist = [
        ("Design inputs and outputs", "Capture requirements and link each one to the output that satisfies it."),
        ("Risk management and hazard analysis", "Identify hazards, record controls and keep your ISO 14971 file up to date."),
        ("Design verification and validation", "Trace every test to its requirement and every validation to a user need."),
        ("Design reviews and approvals", "Run reviews with electronic signatures and keep a full audit trail."),
        ("Software development life cycle documentation", "Keep the IEC 62304 records for SaMD alongside the rest of your design file."),
    ]
    cl = "".join(f'<li><span class="tick">{CHECK}</span><div><h3>{h}</h3><p>{p}</p></div></li>' for h, p in checklist)
    groups = [
        ("Management", "Strategic alignment, resource allocation and continuous improvement.",
         [("Management responsibility", "Setting the quality policy and objectives"), ("Quality planning", "Defining how quality will be achieved"),
          ("Management review", "Regular evaluation of QMS performance"), ("Resource management", "Adequate people, infrastructure and environment")]),
        ("Product realisation & lifecycle control", "Turning ideas into compliant, safe and effective medical devices.",
         [("Design & development control", "Managing the product design lifecycle"), ("Risk management (ISO 14971)", "Identifying and mitigating risks"),
          ("Purchasing & supplier management", "Qualifying and monitoring suppliers"), ("Production & process control", "Validated manufacturing, traceability, labelling"),
          ("Change management", "Controlled updates to product, process or documents")]),
        ("Compliance & documentation", "Accurate, controlled documentation and electronic records.",
         [("Document control", "Approval, revision and version tracking"), ("Record control", "Secure handling of training, audit and complaint records"),
          ("Electronic records & signatures", "Compliant with FDA 21 CFR Part 11")]),
        ("Monitoring & improvement", "Identifying, correcting and preventing problems.",
         [("Internal audits", "Periodic review of QMS compliance"), ("Nonconformance management", "Identifying and handling deviations"),
          ("CAPA", "Root cause analysis and resolution"), ("Feedback analysis", "Learning from user and field feedback"),
          ("Post-market surveillance (EU MDR)", "Real-world performance and vigilance")]),
        ("Support & compliance enablement", "Keeping your QMS usable, compliant and scalable.",
         [("Training & competence", "Qualified, knowledgeable staff"), ("Calibration & equipment control", "Maintaining measurement accuracy"),
          ("Software validation", "Tools used in the QMS are fit for purpose"), ("Labelling & UDI compliance", "Accurate, compliant product identification")]),
    ]
    panels = "".join(
        f'<article class="panel"><span class="id">GROUP {k+1} OF 5</span><h3>{name}</h3><p>{desc}</p><ul>'
        + "".join(f"<li><b>{a}</b><span>{b}</span></li>" for a, b in items) + "</ul></article>"
        for k, (name, desc, items) in enumerate(groups))
    topics = [
        ("Expertise and innovation", "Built by S-Cube Technologies, a team with long experience in medical device quality and regulatory affairs."),
        ("Cloud-based security and accessibility", "Web-based and hosted in the cloud, run by a team certified to ISO/IEC 27001."),
        ("Comprehensive regulatory compliance", "Workflows come set up for ISO 13485, ISO 14971, IEC 62304 and FDA 21 CFR Part 11."),
        ("Ready-to-use templates and customisation", "Hundreds of SOPs and templates to use as they are or adapt to your processes."),
        ("Global collaboration and integration", "Invite colleagues, suppliers and auditors, and work in Microsoft Office inside the platform."),
        ("Seamless data migration", "Bring your existing documents and records with you when you move to SmartEye."),
        ("International application and scalability", "Use SmartEye wherever your teams and markets are, and grow from one project to many."),
        ("Licensing and accessibility", "Licences that fit your team, with access levels for every kind of user."),
        ("Customer-centric onboarding and support", "Guided setup and support from the people who built the platform."),
        ("Continuous improvements without additional costs", "New features and updates are included, with nothing extra to pay to upgrade."),
    ]
    tp = "".join(f'<div class="topic"><h3>{h}</h3><p>{p}</p></div>' for h, p in topics)
    aside = """<dl>
      <div><dt>Built for</dt><dd>Hardware devices and standalone medical software</dd></div>
      <div><dt>Standards</dt><dd>ISO 13485 · ISO 14971 · IEC 62304 · 21 CFR Part 11</dd></div>
      <div><dt>Delivery</dt><dd>Cloud, web-based</dd></div>
    </dl>"""
    body = page_hero('<a href="index.html">Home</a><span>/</span><span>Why SmartEye</span>',
                     "QMS for medical device design control &amp; SaMD",
                     "Ready for your next audit, <em>before it's announced</em>.",
                     "SmartEye is an all-in-one quality management system built for medical device design control and SaMD compliance. Whether you make hardware devices or standalone medical software, it keeps your product lifecycle moving while you stay compliant with global regulations.", aside)
    body += f"""
<div class="ticker" aria-label="Standards SmartEye supports"><div class="ticker-track">{t}{t}</div></div>

<section class="section">
  <div class="wrap split">
    <div class="sticky-col" data-reveal>
      <p class="eyebrow">Why SmartEye for design control and SaMD</p>
      <h2>Configured for the rules <em>you already follow</em></h2>
      <p class="lede" style="margin-top:22px">Developing a medical device, especially software, means following FDA 21 CFR Part 820, ISO 13485 and IEC 62304. SmartEye brings your design control together in one place and automates the busywork.</p>
      <p style="margin-top:28px"><a class="btn btn-primary" href="contact.html#demo">Book a demo {ARROW}</a></p>
    </div>
    <ul class="checklist" data-focus-list>{cl}</ul>
  </div>
</section>

<section class="hscroll" data-hscroll aria-label="Core processes of a medical device QMS">
  <div class="hscroll-stage">
    <div class="wrap hscroll-head">
      <div><p class="eyebrow">All-in-one QMS</p><h2>The core processes of a medical device QMS, <em>in one system</em></h2></div>
      <span class="hscroll-count" aria-hidden="true"><b>1</b> / {len(groups)}</span>
    </div>
    <div class="hscroll-track">{panels}</div>
    <div class="wrap"><div class="hscroll-bar" aria-hidden="true"><i></i></div></div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <div><p class="eyebrow">Transforming medical compliance</p><h2>Ten reasons teams <em>choose SmartEye</em></h2></div>
      <p class="lede">S-Cube Technologies has built its quality and regulatory experience into SmartEye's workflows, already configured to follow medical device standards.</p>
    </div>
    <div class="topics" data-stagger>{tp}</div>
  </div>
</section>
{cta_band(r, 'Arrange your free, <em>tailored demo</em>', 'See for yourself how a 360° view could benefit your SaMD design and development.')}"""
    write("why-smarteye.html", head("Why SmartEye — QMS for medical devices & SaMD",
                                    "SmartEye is an all-in-one QMS for medical device design control and SaMD compliance.", r)
          + header(r, "why-smarteye.html") + body + footer(r))


# ---------------------------------------------------------------- ABOUT
def build_about():
    r = ""
    statement = ("S-Cube Technologies connects leading innovators in the medical device and healthcare sector with specialist advice and facilities. "
                 "We help forward-thinking organisations find and enter new markets with our software and digital solutions, "
                 "and offer tailored support that strengthens how they build and manage innovation.")
    st = " ".join(f'<span class="dim">{w}</span>' for w in statement.split())
    aside = """<dl>
      <div><dt>Headquarters</dt><dd>Manchester, United Kingdom</dd></div>
      <div><dt>Certified</dt><dd>ISO 9001 · ISO/IEC 27001</dd></div>
      <div><dt>Backed by</dt><dd>Innovate UK</dd></div>
    </dl>"""
    body = page_hero('<a href="index.html">Home</a><span>/</span><span>Who we are</span>', "",
                     "SmartEye is <em>powered by</em> S-Cube Technologies.",
                     "We're committed to making a meaningful difference to your business, with quality solutions built from innovation.", aside)
    body += f"""
<hr class="rule">
<section class="section">
  <div class="wrap">
    <p class="eyebrow">What we do</p>
    <p class="statement" data-read>{st}</p>
  </div>
</section>

<section class="section section-tight">
  <div class="wrap split">
    <div data-reveal>
      <p class="eyebrow">Your growth, driven by our innovation</p>
      <h2>We handle the processes, <em>you build the product</em></h2>
    </div>
    <div data-reveal>
      <p class="lede" style="margin:0 0 20px">We help you grow your ideas by taking care of the groundwork: putting management processes in place and providing the services you need, so you don't have to worry about them.</p>
      <p class="lede" style="margin:0">You can trust us to support each step of your business with solutions built for your innovation.</p>
    </div>
  </div>
</section>

<section class="section" id="certifications" style="padding-top:0">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <div><p class="eyebrow">Certifications</p><h2>Held to the standards <em>we build for</em></h2></div>
      <p class="lede">We're audited by BSI. Download our certificates below.</p>
    </div>
    <div class="certs" data-stagger>
      <a class="cert" href="{UP}/2023/09/FS-749038-001.pdf" target="_blank" rel="noopener"><span class="id">BSI · FS 749038</span><h3>ISO 9001:2015</h3><p>Quality management system</p><span class="text-link">View certificate (PDF) {ARROW}</span></a>
      <a class="cert" href="{UP}/2023/09/IS-749037-001.pdf" target="_blank" rel="noopener"><span class="id">BSI · IS 749037</span><h3>ISO/IEC 27001:2013</h3><p>Information security management system</p><span class="text-link">View certificate (PDF) {ARROW}</span></a>
      <div class="cert"><span class="id">DATA PROTECTION</span><h3>GDPR compliant</h3><p>How we handle personal data is set out in our <a href="legal/privacy-policy.html">privacy policy</a>.</p></div>
      <div class="cert"><span class="id">FUNDING</span><h3>Innovate UK backed</h3><p>Supported by the UK's national innovation agency.</p></div>
    </div>
  </div>
</section>

<section class="section section-tight">
  <div class="wrap place">
    <div data-reveal>
      <p class="eyebrow">Where we are</p>
      <h2>Based in <em>Manchester</em>, working worldwide</h2>
      <p class="lede" style="margin-top:22px">Our team works with medical device companies in the UK and abroad. Come and see us, or book a demo online.</p>
      <p style="margin-top:28px"><a class="btn btn-quiet" href="contact.html">Contact us {ARROW}</a></p>
    </div>
    <div class="place-card" data-reveal>
      <div class="grid-lines" aria-hidden="true"></div><span class="pin" aria-hidden="true"></span>
      <span class="id">HEAD OFFICE</span>
      <address>125 Deansgate<br>Manchester M3 2LH<br>United Kingdom</address>
    </div>
  </div>
</section>
{cta_band(r)}"""
    write("about.html", head("Who we are — S-Cube Technologies", "SmartEye eQMS is powered by S-Cube Technologies, an ISO 9001 and ISO/IEC 27001 certified team in Manchester.", r)
          + header(r, "about.html") + body + footer(r))


# ---------------------------------------------------------------- RESOURCES
def build_resources():
    r = ""
    first = ARTICLES[0]; a = SRC[first]
    mins = max(1, round(words(a["html"]) / 220))
    featured = f"""<a class="featured" href="resources/{first}.html" data-reveal>
      <figure><img src="{a['img'].replace('-scaled','')}" alt=""></figure>
      <div><p class="meta">Latest · {nice_date(a['date'])} · {mins} min read</p><h2>{esc(a['title'])}</h2><p>{esc(a['desc'])}</p><span class="text-link">Read the article {ARROW}</span></div>
    </a>"""
    rest = "".join(post_card(s, r, excerpt=True) for s in ARTICLES[1:])
    body = page_hero('<a href="index.html">Home</a><span>/</span><span>Resources</span>', "",
                     "Guides for getting to <em>ISO 13485</em>, and staying there.",
                     "Everyone learns in their own way. Read our guides, or watch a short overview of SmartEye.")
    body += f"""
<section class="section section-tight">
  <div class="wrap">
    {featured}
    <div class="posts" data-stagger style="grid-template-columns:repeat(2,1fr)">{rest}</div>
  </div>
</section>

<section class="section dark" id="video">
  <div class="wrap split">
    <div data-reveal>
      <p class="eyebrow">Videos and media</p>
      <h2>See SmartEye <em>in action</em></h2>
      <p class="lede" style="margin-top:22px">A short tour of the platform: requirements, risk, testing and traceability in one place.</p>
    </div>
    <button class="video" data-video="{VIDEO}" aria-label="Play the SmartEye overview video" data-reveal>
      <img src="https://i.ytimg.com/vi/{VIDEO}/hqdefault.jpg" alt="">
      <span class="play"><span>{PLAY} Play the overview</span></span>
    </button>
  </div>
</section>
{cta_band(r)}"""
    write("resources.html", head("Resources — SmartEye eQMS", "Guides on ISO 13485 and eQMS for medical device startups and quality teams.", r)
          + header(r, "resources.html") + body + footer(r))


def build_articles():
    r = "../"
    for slug in ARTICLES:
        a = SRC[slug]
        html = clean_article(a["html"], a["title"])
        mins = max(1, round(words(html) / 220))
        others = [s for s in ARTICLES if s != slug][:3]
        related = "".join(post_card(s, r) for s in others)
        body = f"""
<article>
  <header class="article-hero">
    <div class="wrap">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="{r}resources.html">Resources</a><span>/</span><span>Article</span></nav>
      <h1 class="rise">{esc(a['title'])}</h1>
      <p class="meta"><time datetime="{a['date']}">{nice_date(a['date'])}</time><span>{mins} min read</span><span>S-Cube Technologies</span></p>
    </div>
  </header>
  <div class="cover"><figure><img data-parallax="0.08" src="{a['img']}" alt=""></figure></div>
  <div class="reading">
    <nav class="toc" aria-label="In this article"><p class="eyebrow">In this article</p><ol id="toc-list"></ol></nav>
    <div class="prose" data-toc>{html}</div>
  </div>
</article>
{cta_band(r, 'Need help with <em>ISO 13485</em>?', 'Book a free demo of SmartEye, tailored to your device and your team.')}
<hr class="rule">
<section class="section">
  <div class="wrap">
    <div class="section-head" data-reveal><div><p class="eyebrow">Keep reading</p><h2>More from <em>Resources</em></h2></div></div>
    <div class="posts" data-stagger>{related}</div>
  </div>
</section>"""
        write(f"resources/{slug}.html", head(f"{a['title']} — SmartEye", a["desc"] or a["title"], r) + header(r, "resources.html") + body + footer(r))


# ---------------------------------------------------------------- CAREERS
def build_careers():
    r = ""
    items = ""
    for slug, j in JOBS.items():
        status = f"Closed {nice_date(j['closes'])}" if j["closes"] and datetime.date.fromisoformat(j["closes"]) < TODAY else f"Posted {nice_date(j['posted'])}"
        items += f"""<li class="job"><a href="careers/{slug}.html">
          <h3>{j['title']}</h3><span class="meta">{j['location']}</span><span class="meta">{j['type']} · {status}</span>
          <span class="arrow-c">{ARROW}</span></a></li>"""
    body = page_hero('<a href="index.html">Home</a><span>/</span><span>Careers</span>', "",
                     "Build the tools that keep <em>medical devices</em> safe.",
                     "Join the team behind SmartEye, working from Manchester with medical device companies around the world.")
    body += f"""
<section class="section section-tight">
  <div class="wrap">
    <ul class="jobs" data-stagger>{items}</ul>
    <div class="empty-note" data-reveal>
      <p>Don't see a role that fits? Send your CV and a note about what you'd like to work on.</p>
      <a class="btn btn-quiet" href="mailto:{EMAIL}?subject=Careers%20at%20S-Cube">Email {EMAIL}</a>
    </div>
  </div>
</section>
{cta_band(r)}"""
    write("careers.html", head("Careers — S-Cube Technologies", "Open roles at S-Cube Technologies, the team behind SmartEye eQMS.", r)
          + header(r, "careers.html") + body + footer(r))

    rr = "../"
    for slug, j in JOBS.items():
        html = clean_job(SRC[slug]["html"])
        closed = j["closes"] and datetime.date.fromisoformat(j["closes"]) < TODAY
        note = f'<p class="stale">Applications for this role closed on {nice_date(j["closes"])}.</p>' if closed else ""
        apply = (f'<a class="btn btn-quiet" href="{rr}careers.html">See other roles {ARROW}</a>' if closed else
                 f'<a class="btn btn-primary" href="mailto:{EMAIL}?subject=Application%3A%20{j["title"].replace(" ", "%20").replace("/", "%2F")}">Apply by email {ARROW}</a>')
        body = f"""
<article>
  <header class="article-hero">
    <div class="wrap">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="{rr}careers.html">Careers</a><span>/</span><span>Role</span></nav>
      <h1 class="rise">{j['title']}</h1>
      {note}
      <dl class="job-facts" data-reveal>
        <div><dt>Company</dt><dd>TKM Intelligence Limited</dd></div>
        <div><dt>Location</dt><dd>{j['location']}</dd></div>
        <div><dt>Pay</dt><dd>{j['pay']}</dd></div>
        <div><dt>Type</dt><dd>{j['type']} · posted {nice_date(j['posted'])}</dd></div>
      </dl>
    </div>
  </header>
  <div class="reading" style="padding-top:24px">
    <nav class="toc" aria-label="In this listing"><p class="eyebrow">Apply</p><p style="margin:0 0 16px;color:var(--ink-2)">Send your CV to {EMAIL}.</p>{apply}</nav>
    <div class="prose">{html}<p style="margin-top:2em">{apply}</p></div>
  </div>
</article>"""
        write(f"careers/{slug}.html", head(f"{j['title']} — Careers at S-Cube", f"{j['title']} at S-Cube Technologies.", rr) + header(rr, "careers.html") + body + footer(rr))


# ---------------------------------------------------------------- CONTACT
def build_contact():
    r = ""
    body = page_hero('<a href="index.html">Home</a><span>/</span><span>Contact</span>', "",
                     "Talk to the people who <em>built</em> SmartEye.",
                     "Want to know how SmartEye could change the way you manage SaMD design and development? Get in touch for a free demo from the team who built it.")
    body += f"""
<section class="section section-tight">
  <div class="wrap contact-grid">
    <ul class="channels" data-stagger>
      <li><span class="id">Email</span><a href="mailto:{EMAIL}">{EMAIL}</a></li>
      <li><span class="id">Phone · United Kingdom</span><a href="tel:+447459153907">+44 (0)7459 153907</a></li>
      <li><span class="id">Phone · Switzerland</span><a href="tel:+41799036836">+41 79 903 68 36</a></li>
      <li><span class="id">Office</span><address>125 Deansgate, Manchester<br>M3 2LH, United Kingdom</address></li>
      <li><span class="id">Video</span><a href="resources.html#video">Watch the SmartEye overview</a></li>
    </ul>
    <button class="video" data-video="{VIDEO}" aria-label="Play the SmartEye overview video" data-reveal>
      <img src="https://i.ytimg.com/vi/{VIDEO}/hqdefault.jpg" alt="">
      <span class="play"><span>{PLAY} Play the overview</span></span>
    </button>
  </div>
</section>
{demo_form(r, 'Book your <em>free demo</em>')}"""
    write("contact.html", head("Contact — SmartEye eQMS", "Contact the SmartEye eQMS team or book a free demo.", r)
          + header(r, "contact.html") + body + footer(r))


# ---------------------------------------------------------------- LEGAL
def build_legal():
    r = "../"
    for slug, label in LEGAL:
        html, updated = clean_legal(SRC[slug]["html"])
        nav = "".join(f'<li><a href="{s}.html"{" aria-current=\"page\"" if s == slug else ""}>{l}</a></li>' for s, l in LEGAL)
        meta = f'<p class="meta">Last updated {updated}</p>' if updated else ""
        body = f"""
<article>
  <header class="article-hero">
    <div class="wrap">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="{r}index.html">Home</a><span>/</span><span>Policies</span></nav>
      <h1 class="rise">{label}</h1>
      {meta}
    </div>
  </header>
  <div class="reading" style="padding-top:24px">
    <nav class="toc keep legal-nav" aria-label="Policies"><p class="eyebrow">Policies</p><ol>{nav}</ol></nav>
    <div class="prose">{html}</div>
  </div>
</article>"""
        write(f"legal/{slug}.html", head(f"{label} — SmartEye eQMS", f"S-Cube Technologies {label.lower()}.", r) + header(r, None) + body + footer(r))


if __name__ == "__main__":
    build_home(); build_why(); build_about(); build_resources(); build_articles()
    build_careers(); build_contact(); build_legal()
