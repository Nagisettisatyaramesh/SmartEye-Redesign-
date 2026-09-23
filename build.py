"""Builds the SmartEye site into static HTML.

Run:  python build.py

All wording on the site is copied from the original eqms-smarteye.com pages.
Long-form content (articles, jobs, policies) comes from content/source.json,
which was extracted from those pages; short page copy is kept verbatim below.
"""
import json, re, datetime, pathlib
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).parent
SRC = json.loads((ROOT / "content" / "source.json").read_text(encoding="utf-8"))
UP = "https://eqms-smarteye.com/wp-content/uploads"
VIDEO = "YjVfsjdiYAY"
EMAIL = "info@scube-technologies.com"

ARROW = '<svg class="arrow" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 8h10M9 4l4 4-4 4" fill="none" stroke="currentColor" stroke-width="1.6"/></svg>'
PLAY = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M5 3.5v9l7-4.5z" fill="currentColor"/></svg>'
TICK = '<svg viewBox="0 0 18 18" aria-hidden="true"><path d="M3 9.5l4 4 8-9" fill="none" stroke="currentColor" stroke-width="2"/></svg>'

ARTICLES = [  # newest first, as listed on the original Resources page
    "how-an-eqms-simplifies-iso-13485-compliance-for-uk-medical-device-startups",
    "why-uk-medical-device-startups-are-adopting-eqms-to-accelerate-iso-13485-compliance",
    "iso-13485-explained-in-plain-english",
    "why-most-medical-device-startups-fail-their-first-audit",
    "iso-13485-qms-a-complete-guide-for-medical-device-companies-and-startups",
]
# Job titles and summary lines exactly as shown on the original jobs listing
JOBS = {
    "data-engineer-software-engineer": dict(title="Data Engineer/Software Engineer", date="2025-07-07",
        summary="TKM Intelligence Limited · Pay -TBD- · Permanent · 125 Deansgate, Manchester M3 2LH United Kingdom"),
    "content-writer-digital-marketing-blog-writer": dict(title="Content writer / Digital marketing/ Blog writer", date="2025-07-07",
        summary="TKM Intelligence Limited · TBD – Permanent · 125 Deansgate, Manchester M3 2LH United Kingdom"),
    "software-test-engineer": dict(title="Software Test Engineer", date="2024-09-30",
        summary="TKM Intelligence Limited · Bizspace Altrincham, Unit 43 Atlantic Street, Broadheath, Altrincham, England, WA14 5NQ · £35,063 – £41,911 a year – Permanent"),
}
# Footer labels from the original site
LEGAL = [
    ("privacy-policy", "Privacy Policy"),
    ("terms-and-conditions", "Terms And Conditions"),
    ("website-cookie-policy", "Website Cookie Policy"),
    ("quality-policy", "Quality Policy"),
    ("security-policy", "Security Policy"),
]
DEMO_CTA = ("Arrange your free tailored demo of SmartEye eQMS today, and see for yourself how an enhanced "
            "360 view could benefit your SaMD design and development.")
RES_LEDE = "Everyone has their own way of learning. S-Cube's resources helps to learn more"


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


def norm(t):
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


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


def links_local(body, root):
    for a in body.find_all("a", href=True):
        a["href"] = localise(a["href"], root)


def clean_article(html, title):
    """Article text is kept as written. Only page furniture is removed: the author byline,
    a heading that repeats the page title, and the trailing demo button (the page has its own)."""
    s, body = soup_of(html)
    for h in body.find_all("h1"):
        h.name = "h2"
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
    links_local(body, "../")
    return inner(body)


def clean_job(html):
    s, body = soup_of(html)
    for h5 in body.find_all("h5"):  # author byline
        h5.decompose()
    return inner(body)


def clean_legal(html):
    s, body = soup_of(html)
    h1 = body.find("h1")
    title = h1.get_text(" ", strip=True) if h1 else ""
    if h1: h1.decompose()
    links_local(body, "../")
    return inner(body), title


def words(html):
    return len(re.sub(r"<[^>]+>", " ", html).split())


# ---------------------------------------------------------------- shared chrome
NAV = [("why-smarteye.html", "Why SmartEye eQMS"), ("about.html", "Who we are"), ("resources.html", "Resources"),
       ("careers.html", "Career"), ("contact.html", "Contact Us")]


def head(title, desc, root):
    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="icon" href="{UP}/2025/01/Logo-Light-1.svg">
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
    demo_href = demo_href or f"{root}index.html#demo"
    return f"""
<header class="top">
  <div class="wrap">
    <a class="logo" href="{root}index.html" aria-label="SmartEye eQMS home"><img src="{UP}/2025/01/Logo-Dark.png" alt="SmartEye" width="122" height="34"></a>
    <button class="menu-btn" aria-expanded="false" aria-controls="nav">Menu</button>
    <nav class="nav" id="nav" aria-label="Main">
      {links}
      <a class="btn btn-primary" href="{demo_href}">Get a Demo</a>
    </nav>
  </div>
</header>
<main id="main">"""


def footer(root):
    legal = "".join(f'<li><a href="{root}legal/{slug}.html">{label}</a></li>' for slug, label in LEGAL)
    nav = "".join(f'<li><a href="{root}{href}">{label}</a></li>' for href, label in NAV)
    return f"""</main>
<footer>
  <div class="wrap">
    <div class="foot-grid">
      <div>
        <img src="{UP}/2025/01/Logo-Dark.png" alt="SmartEye" style="height:30px;width:auto">
        <address>S-Cube Technologies Limited<br>125 Deansgate<br>Manchester<br>M3 2LH<br>United Kingdom<br><a href="mailto:{EMAIL}">{EMAIL}</a></address>
      </div>
      <div><ul><li><a href="{root}index.html#demo">Get a Demo</a></li>{nav}</ul></div>
      <div><ul>{legal}</ul></div>
      <div class="foot-badges">
        <img src="{UP}/2023/09/mark-of-trust-certified-ISO-9001-quality-management-systems-white-logo-En-GB-1019-300x152.png" alt="BSI certified ISO 9001">
        <img src="{UP}/2023/09/mark-of-trust-certified-ISOIEC-27001-information-security-management-white-logo-En-GB-1019-300x152.png" alt="BSI certified ISO/IEC 27001">
      </div>
    </div>
    <div class="foot-base">
      <span>© S-Cube Technologies Limited 2025</span>
      <span class="social"><a href="https://www.linkedin.com/company/s-cubetechnologies/">LinkedIn</a><a href="https://twitter.com/i_SCubeTech">X</a><a href="https://www.facebook.com/i.scubetechnologies/">Facebook</a><a href="https://www.instagram.com/i.scubetech/">Instagram</a></span>
    </div>
  </div>
</footer>
<script src="{root}assets/site.js" defer></script>
</body>
</html>
"""


def demo_form(root, fid="f"):
    """The original site's demo form: same fields, placeholders and button."""
    return f"""<form class="form" data-demo-form novalidate>
      <div class="field"><label for="{fid}-name">Name</label><input id="{fid}-name" name="name" placeholder="your Name" autocomplete="name" required></div>
      <div class="field"><label for="{fid}-email">Email</label><input id="{fid}-email" name="email" type="email" placeholder="your Email" autocomplete="email" required></div>
      <div class="field"><label for="{fid}-phone">Phone Number</label><input id="{fid}-phone" name="tel" type="tel" placeholder="Phone Number" autocomplete="tel"></div>
      <div class="field"><label for="{fid}-company">Company Name</label><input id="{fid}-company" name="company" placeholder="Company Name" autocomplete="organization"></div>
      <div class="field full"><label for="{fid}-country">Country</label><select id="{fid}-country" name="country" data-countries><option value="">Country</option></select></div>
      <div class="field full"><label for="{fid}-req">Your Requirement</label><textarea id="{fid}-req" name="req" placeholder="Your Requirement"></textarea></div>
      <div class="form-foot">
        <small>Please review our <a href="{root}legal/privacy-policy.html">Privacy Policy</a> and <a href="{root}legal/terms-and-conditions.html">Terms of Use</a>.</small>
        <button class="btn btn-primary" type="submit">Get a Demo</button>
      </div>
      <p class="form-status" role="status"></p>
    </form>"""


def cta_band(root, title=DEMO_CTA, buttons=None):
    buttons = buttons or f'<a class="btn btn-primary" href="{root}index.html#demo">Get a Demo {ARROW}</a>'
    return f"""
<section class="section section-tight">
  <div class="wrap">
    <div class="cta-band" data-reveal>
      <h2 class="cta-text">{title}</h2>
      <div class="cta-row">{buttons}</div>
    </div>
  </div>
</section>"""


def post_card(slug, root):
    a = SRC[slug]
    img = a["img"].replace("-scaled", "")
    return f"""<a class="post" href="{root}resources/{slug}.html">
        <figure><img loading="lazy" src="{img}" alt=""></figure>
        <time datetime="{a['date']}">{nice_date(a['date'])}</time>
        <h3>{esc(a['title'])}</h3>
        <span class="text-link">Read more {ARROW}</span>
      </a>"""


def page_hero(crumb, h1, lede="", extra=""):
    crumbs = f'<nav class="crumbs" aria-label="Breadcrumb">{crumb}</nav>' if crumb else ""
    lede_html = f'<p class="lede" data-reveal>{lede}</p>' if lede else ""
    return f"""
<section class="page-hero">
  <div class="wrap">
    <div>
      {crumbs}
      <h1 class="rise">{h1}</h1>
      {lede_html}
      {extra}
    </div>
  </div>
</section>"""


def video_button():
    return f"""<button class="video" data-video="{VIDEO}" aria-label="Watch a Video" data-reveal>
      <img src="https://i.ytimg.com/vi/{VIDEO}/hqdefault.jpg" alt="">
      <span class="play"><span>{PLAY} Watch a Video</span></span>
    </button>"""


def write(path, html):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")
    print("wrote", path)


# ---------------------------------------------------------------- HOME
HOME_POINTS = [  # "How can SmartEye eQMS work…" — six paragraphs, bold lead as on the original
    ("SmartEye eQMS allows you to access everything", " you need for requirement Management, Test Management, Risk Management and E2E Traceability within one interface", "E2E Traceability"),
    ("SmartEye eQMS has been designed to be a one-stop boutique for QARA,", " for everything from Design Control and Cyber Security, to Clinical Trials and Post-market Surveillance", "QARA"),
    ("SmartEye eQMS is adaptable for your entire workforce", " with different access levels, roles and permissions, including: Organisation Admin, Project Admin, Standard Users and External Users", "Roles and permissions"),
    ("With an easy-to-use analytics dashboards", " to measure the progress of different compliance phases within the SmartEye eQMS interface, you’ll be able to filter your view by user, team or project", "Analytics dashboards"),
    ("Focused on user experience,", " SmartEye eQMS is embedded with Microsoft Office, web grids for bi-directional traceability, global navigators and easy-to-use review and approval features – plus admin screens for a seamless onboarding experience", "Microsoft Office"),
    ("Pre-installed with 100s of ready-made SOPs and templates,", " including QMS, DHF and Technical files, as well as automatic DHF and DMR files generation - SmartEye eQMS ensures all your documents meet the necessary industry standards and guidelines, helped by our ready-made checklists", "SOPs and templates"),
]
FAQ = [  # topic, [(question, answer), ...] — verbatim from the original accordion
    ("CLOUD DATA SECURITY", [("Is my organization's data and information safe in the cloud?",
        "Absolutely! SmartEye’s software is hosted on Azure Web Services, which is the hosting service of choice for many fortune 100 companies, including NHS. Our team would be happy to share a system overview that covers data storage, disaster recovery and security in order to clarify any outstanding questions regarding security when using the cloud.")]),
    ("COMPLIANCE (HARDWARE DEVICE &amp; SaMD)", [("How does SmartEye help my company achieve quality &amp; regulatory compliance?",
        "Medical device specific Quality &amp; regulatory guidance and controls are blended into SmartEye’s eQMS software. The platform includes Part 11 compliant review and approval workflows, e-signatures, fully integrated ISO 14971 Risk Management standards, and facilitates your team’s ability to easily demonstrate compliance with both 21 CFR Part 820 and ISO 13485:2016."
        "</p><p><strong>SaMD COMPLIANCE</strong><br>SmartEye provides E2E Software life cycle frameworks supporting Agile methodologies. User can create user needs and link with Validation methods; create different levels of requirements (linking with parent requirements) and link with different levels &amp; types of verification tests; also link with safety related hazards. This is all represented in a Dynamic Trace Matrix , Risk Management Matrix and Test Execution report Matrix."
        "</p><p><strong>3RD PARTY TOOL INTEGRATION</strong><br>SmartEye supports 3rd party tool integration such as Jira, Microsoft Azure Board")]),
    ("TEMPLATES", [("Does your platform provide template for QMS, MDR, design control, risk management and human factors?",
        "SmartEye provides ready to use templates for ISO 13485, IEC 62304, ISO 14971, IEC 62366, MDR Technical File, FDA Design Control within the license cost. However, you can use your own or blend with our templates as well. Automatic conversion of all types of documents and forms into audit ready PDF files.")]),
    ("TEAM COLLABORATION", [("Can our team uses SmartEye's quality management software if we want to collaborate?",
        "Team across the globe works best on a software platform such as SmartEye. It offers them the best way to collaborate and integrate. Co-authoring, Co-reviewing and Co-approving among the members across different geographical locations is seamless and faster.")]),
    ("DATA MIGRATIONS", [("How do I migrate my existing QMS controlled documents and processes into SmartEye?",
        "SmartEye offers several different means of helping transition your existing QMS documents and data into our platform. During the onboarding process, we’ll work with you to define a plan for transitioning existing documentation into SmartEye.")]),
    ("TARGETED MARKETS", [("Can my medical device company benefit from SmartEye's software if we are internationally based or intend to sell our devices into international markets?",
        "Yes! We work with medical device companies around the globe, on 5 different continents. Regardless of where your headquarters location is or the end markets you intend to sell your devices into, SmartEye can streamline quality for your team. Our software platform can be used to navigate regulatory pathways and quality system requirements internationally, which allows your team to focus on scaling without worrying about the quality system being a bottleneck.")]),
    ("DEPLOYMENT &amp; LICENSING", [("How is the software licensed? Can I install it on my own server?",
        "SmartEye is a cloud-based software like most of the modern Customer Relationship Management (CRM) and Enterprise Resource Planning (ERP) platforms. Licenses are monthly or an annual subscription basis that can be accessed via all standard web browsers")]),
    ("ONBOARDING", [("How long does onboarding take?",
        "Depending on the primary use case each customer defines as their initial focus area, the time to value can range from two to four weeks."),
        ("Do you offer additional QARA services?",
        "Yes, every customer is paired with a dedicated medical device industry expert to guide you through the onboarding process and get your team up to speed. For customers that need QARA or training services that go beyond our standard offering, we can work with your team to define an extended scope of onboarding that guides your team to specific milestones in your quality transformation")]),
    # The original answer begins with a stray fragment ("Depending on the primary use case each customer defin")
    # left over from editing; it is omitted here and reported so the site owner can confirm.
    ("SOFTWARE UPGRADES", [("Will I have to pay for software upgrades?",
        "Never! SmartEye is cloud-based and built on a modern technology stack that allows us to release enhancements and features specifically built for the needs of medical device companies on a regular basis. In addition to not having to pay for the upgrades, SmartEye removes the burden of system validation for your team by providing 21 CFR Part 11 compliant IQ protocol/checklist and completed OQ and PQ reports at no additional charge.")]),
]


def hub_svg():
    import math
    cx, cy, R = 280, 270, 200
    nodes, spokes = "", ""
    for k, (_, _, label) in enumerate(HOME_POINTS):
        a = math.radians(-90 + k * 60)
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        sx, sy = cx + 78 * math.cos(a), cy + 78 * math.sin(a)
        ex, ey = cx + (R - 30) * math.cos(a), cy + (R - 30) * math.sin(a)
        spokes += f'<line class="spoke" data-at="{k}" x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}"/>'
        nodes += (f'<g class="node" data-at="{k}"><rect x="{x-88:.1f}" y="{y-22:.1f}" width="176" height="44" rx="22"/>'
                  f'<text x="{x:.1f}" y="{y+5:.1f}" text-anchor="middle">{label}</text></g>')
    return f"""<svg class="hub" viewBox="0 0 560 540" role="img" aria-label="SmartEye eQMS brings E2E traceability, QARA, roles and permissions, analytics dashboards, Microsoft Office, and SOPs and templates into one platform">
      <circle class="orbit" cx="{cx}" cy="{cy}" r="{R}"/>
      {spokes}
      <circle class="core" cx="{cx}" cy="{cy}" r="74"/>
      <text class="core-t" x="{cx}" y="{cy-2}" text-anchor="middle">SmartEye</text>
      <text class="core-s" x="{cx}" y="{cy+20}" text-anchor="middle">eQMS</text>
      {nodes}
    </svg>"""


def build_home():
    r = ""
    n = len(HOME_POINTS)
    steps = "".join(
        f'<div class="step{" on" if k == 0 else ""}"><span class="id">{k+1} / {n}</span><p class="step-text"><strong>{lead}</strong>{rest}</p></div>'
        for k, (lead, rest, _) in enumerate(HOME_POINTS))
    static = "".join(f'<li><p><strong>{lead}</strong>{rest}</p></li>' for lead, rest, _ in HOME_POINTS)
    rails = "".join("<i><b></b></i>" for _ in HOME_POINTS)
    faq = ""
    for topic, qas in FAQ:
        qa_html = "".join(f"<h4>{q}</h4><p>{a}</p>" for q, a in qas)
        faq += f'<details><summary><span class="faq-topic">{topic}</span><span class="faq-q">{qas[0][0]}</span></summary><div class="faq-a">{qa_html}</div></details>'
    posts = "".join(post_card(s, r) for s in ARTICLES[:3])

    body = f"""
<section class="hero" id="demo">
  <div class="wrap">
    <div>
      <h1 class="rise">Best E-QMS For SaMD And Medical Device Design Control</h1>
      <p class="lede" data-reveal>eQMS is the tool that a Medical Device company should have when they want to optimize their Quality Management System and keep track of any regulatory activity. We transform your manual and paper-based processes into one platform. In medical jargon, you can say we help you mitigate risk, accelerate compliance and improve quality</p>
      <ul class="gains" data-stagger>
        <li>faster quality processes</li>
        <li>reduction in quality admin</li>
        <li>increase in product release speed</li>
        <li>faster external audits and more.</li>
      </ul>
      <div class="cta-row" data-reveal style="--d:.2s">
        <a class="btn btn-quiet" href="https://youtu.be/{VIDEO}" target="_blank" rel="noopener">{PLAY}Watch a Video</a>
      </div>
    </div>
    <div class="hero-form" data-reveal style="--d:.15s">
      {demo_form(r, "h")}
    </div>
  </div>
</section>

<section class="section dark" id="why">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <h2>Transform the way you <em>Manage Compliance</em></h2>
      <p class="lede">Our team of experts have led experienced careers bringing meaningful difference to quality management software and digital solutions in the Medical Device and healthcare sector. It’s their passion for delivering life-changing QMS products and innovations, that has helped maintain the constant growth of S-Cube Technologies.</p>
    </div>
    <ul class="values" data-stagger>
      <li>Join Up Data</li><li>Go To Free</li><li>Mitigate Risk</li><li>Accelerate Compliance</li><li>Enhance Quality</li>
    </ul>
  </div>
</section>

<section class="story" data-story aria-label="How SmartEye eQMS works">
  <div class="story-stage">
    <div class="wrap">
      <div>
        <p class="eyebrow">Built to meet the highest of industry standards, without notice</p>
        <h2>How can SmartEye eQMS work to streamline your SaMD design and development in <em>one seamless platform?</em></h2>
        <div class="steps">{steps}</div>
        <div class="rail" aria-hidden="true">{rails}</div>
        <ul class="story-static">{static}</ul>
      </div>
      {hub_svg()}
    </div>
  </div>
</section>

<section class="section" id="faq">
  <div class="wrap split">
    <div data-reveal class="sticky-col">
      <h2>One Top QMS Solution, <em>For Medical Devices</em></h2>
      <p class="lede" style="margin-top:22px">SmartEye eQMS Built bespoke to join all documents related to medical device design, development and maintenance into one seamless platform</p>
      <p class="lede" style="margin-top:14px">Find Your All Questions Answer's Below.</p>
    </div>
    <div class="faq" data-reveal>{faq}</div>
  </div>
</section>

<hr class="rule">

<section class="section" id="resources">
  <div class="wrap">
    <div class="section-head" data-reveal>
      <h2>Our <em>Resource for QMS</em></h2>
      <p class="lede">{RES_LEDE}</p>
    </div>
    <div class="posts" data-stagger>{posts}</div>
    <div class="more"><a class="btn btn-quiet" href="resources.html">More Resources {ARROW}</a></div>
  </div>
</section>
{cta_band(r, DEMO_CTA, f'<a class="btn btn-primary" href="#demo">Get a Demo {ARROW}</a>')}"""
    write("index.html", head("Best eQMS for Medical Devices & SaMD Compliance",
                             "Explore the best Quality Management System eQMS medical devices to streamline compliance and enhance quality. Book a demo Today!", r)
          + header(r, "index.html", "#demo") + body + footer(r))


# ---------------------------------------------------------------- WHY SMARTEYE
def build_why():
    r = ""
    standards = ["FDA 21 CFR Part 820", "ISO 13485", "IEC 62304", "ISO 14971", "FDA 21 CFR Part 11", "EU MDR"]  # all named on this page
    t = "".join(f"<span>{x}</span>" for x in standards)
    manage = ["Design inputs and outputs", "Risk management and hazard analysis", "Design verification and validation (V&amp;V)",
              "Design reviews and approvals", "Software development life cycle (SDLC) documentation"]
    cl = "".join(f'<li><span class="tick">{TICK}</span><h3>{m}</h3></li>' for m in manage)
    groups = [
        ("1. Management", "These processes ensure strategic alignment, resource allocation, and continuous improvement:",
         [("Management Responsibility", "Setting the Quality Policy and Objectives"), ("Quality Planning", "Defining how quality will be achieved"),
          ("Management Review", "Regular evaluation of QMS performance"), ("Resource Management", "Ensuring adequate personnel, infrastructure, and environment")]),
        ("2. Product Realization &amp; Lifecycle Control", "Focuses on turning ideas into compliant, safe, and effective medical devices:",
         [("Design &amp; Development Control", "Managing the product design lifecycle"), ("Risk Management (ISO 14971)", "Identifying and mitigating risks"),
          ("Purchasing &amp; Supplier Management", "Qualifying and monitoring suppliers"), ("Production &amp; Process Control", "Validated manufacturing, traceability, labeling"),
          ("Change Management", "Controlled updates to product, process, or documents")]),
        ("3. Compliance &amp; Documentation", "Ensures accurate, controlled documentation and electronic records (if applicable):",
         [("Document Control", "Approval, revision, and version tracking of QMS documents"), ("Record Control", "Secure handling of quality records (training, audit, complaints)"),
          ("Electronic Records &amp; Signatures (eQMS)", "Compliant with FDA 21 CFR Part 11")]),
        ("4. Monitoring &amp; Improvement", "Processes focused on identifying, correcting, and preventing problems:",
         [("Internal Audits", "Periodic review of QMS compliance and effectiveness"), ("Nonconformance Management (NCs)", "Identifying and handling deviations"),
          ("Corrective &amp; Preventive Action (CAPA)", "Root cause analysis and resolution"), ("Feedback Analysis", "Learning from user and field feedback"),
          ("Post-Market Surveillance (EU MDR)", "Real-world performance and vigilance")]),
        ("5. Support &amp; Compliance Enablement", "These supporting processes ensure your QMS is usable, compliant, and scalable:",
         [("Training &amp; Competence", "Ensuring qualified, knowledgeable staff"), ("Calibration &amp; Equipment Control", "Maintaining measurement accuracy"),
          ("Software Validation (for tools/eQMS)", "Ensuring software used in QMS is fit for purpose"), ("Labeling &amp; UDI Compliance", "Accurate, compliant product identification")]),
    ]
    panels = "".join(
        f'<article class="panel"><h3>{name}</h3><p>{desc}</p><span class="id">Processes:</span><ul>'
        + "".join(f"<li><b>{a} –</b><span>{b}</span></li>" for a, b in items) + "</ul></article>"
        for name, desc, items in groups)
    topics = ["Expertise and Innovation", "Cloud-Based Security and Accessibility", "Comprehensive Regulatory Compliance",
              "Ready-to-Use Templates and Customization", "Global Collaboration and Integration", "Seamless Data Migration",
              "International Application and Scalability", "Licensing and Accessibility", "Customer-Centric Onboarding and Support",
              "Continuous Improvements Without Additional Costs"]
    tp = "".join(f'<li>{x}</li>' for x in topics)
    body = page_hero('<a href="index.html">Home</a><span>/</span><span>Why SmartEye eQMS</span>',
                     "Best QMS for Medical Device Design Control and <em>SaMD</em>",
                     "SmartEye is your all-in-one Quality Management System (QMS) solution, purpose-built for medical device design control and Software as a Medical Device (SaMD) compliance. Whether you're developing hardware-based devices or standalone medical software, SmartEye helps you streamline your product lifecycle while staying compliant with global regulatory standards.",
                     f'<p style="margin-top:32px" data-reveal><a class="btn btn-primary" href="index.html#demo">Get a Demo {ARROW}</a></p>')
    body += f"""
<div class="ticker" aria-hidden="true"><div class="ticker-track">{t}{t}</div></div>

<section class="section">
  <div class="wrap">
    <p class="eyebrow" data-reveal>SmartEye- QMS for Medical Devices</p>
    <h2 class="big-statement" data-reveal>SmartEye Quality Management Software (QMS) is ready for your <em>next audit inspection,</em> before you even know it’s happening</h2>
  </div>
</section>

<section class="section section-tight">
  <div class="wrap split">
    <div class="sticky-col" data-reveal>
      <h2>Why SmartEye for Design Control and <em>SaMD?</em></h2>
      <p class="lede" style="margin-top:22px">Developing a medical device—especially software-based solutions—requires strict adherence to regulations like FDA 21 CFR Part 820, ISO 13485, and IEC 62304. SmartEye centralizes and automates your design control processes, making it easy to manage :</p>
    </div>
    <ul class="checklist" data-focus-list>{cl}</ul>
  </div>
</section>

<section class="section section-tight">
  <div class="wrap split">
    <div data-reveal>
      <p class="lede" style="margin:0 0 18px">S-Cube Technologies with its experience in Quality and Regulatory Affairs has proved to know how to keep your company compliant. It has developed an electronic Quality Management System (eQMS) called SmartEye which will guide you to success with its workflows that are already configured to follow all the medical devices standards.</p>
      <p class="lede" style="margin:0">Check the different features that this solution can provide to your company. And don’t hesitate to <a class="text-link" href="index.html#demo">ask for a demo</a>.</p>
    </div>
    <div data-reveal>
      <h3 class="list-title">Transforming Medical Compliance</h3>
      <ul class="topic-list" data-stagger>{tp}</ul>
    </div>
  </div>
</section>

<section class="hscroll" data-hscroll aria-label="Core Processes of a Medical Device Quality Management System">
  <div class="hscroll-stage">
    <div class="wrap hscroll-head">
      <div>
        <h2>Core Processes of a Medical Device Quality Management System (QMS) <em>- SmartEye eQMS is the All in one Solution for your QMS .</em></h2>
        <p class="lede" style="margin-top:18px">These processes form the foundation of a compliant, effective QMS for medical device companies:</p>
      </div>
      <span class="hscroll-count" aria-hidden="true"><b>1</b> / {len(groups)}</span>
    </div>
    <div class="hscroll-track">{panels}</div>
    <div class="wrap"><div class="hscroll-bar" aria-hidden="true"><i></i></div></div>
  </div>
</section>
{cta_band(r)}"""
    write("why-smarteye.html", head("Quality Management System (QMS) for Medical Devices & Samd",
                                    "Optimize quality management and regulatory compliance with our Best QMS for medical devices and SaMD. Schedule a free demo now!", r)
          + header(r, "why-smarteye.html") + body + footer(r))


# ---------------------------------------------------------------- ABOUT
def build_about():
    r = ""
    statement = ("S-Cube Technologies connect leading innovators from the Medical device and Healthcare sector to the very best in specialist advise and facilities. "
                 "We help forward-thinking organisations to identify and access new markets with our software and digital solutions, "
                 "all whilst offering tailored support that enhances business capability and innovation management.")
    st = " ".join(f'<span class="dim">{w}</span>' for w in statement.split())
    body = page_hero('<a href="index.html">Home</a><span>/</span><span>Who we are</span>', "S-Cube <em>Technologies</em>",
                     "We are committed to bringing meaningful difference to your business, with quality solutions built from innovation.")
    body += f"""
<hr class="rule">
<section class="section">
  <div class="wrap">
    <p class="statement" data-read>{st}</p>
  </div>
</section>

<section class="section section-tight">
  <div class="wrap split">
    <div data-reveal>
      <p class="eyebrow">SmartEye eQMS: powered by S-Cube Technologies</p>
      <h2>Your growth, <em>driven by our innovation</em></h2>
    </div>
    <div data-reveal>
      <p class="lede" style="margin:0">We will help you grow your ideas by taking care of the growth, implementing management processes and providing you with necessary services so you don’t have to worry. We’re ISO 9001 BSI Certified, GDPR Compliant, ISO 27001 BSI Certified. You can trust us to build each step of your business with innovative solutions for your big innovation.</p>
    </div>
  </div>
</section>

<section class="section section-tight" id="certifications">
  <div class="wrap">
    <div class="certs" data-stagger>
      <a class="cert" href="{UP}/2023/09/FS-749038-001.pdf" target="_blank" rel="noopener">
        <img src="{UP}/2023/09/mark-of-trust-certified-ISO-9001-quality-management-systems-white-logo-En-GB-1019-300x152.png" alt="">
        <h3>Quality Management System - ISO 9001:2015</h3><span class="text-link">PDF {ARROW}</span></a>
      <a class="cert" href="{UP}/2023/09/IS-749037-001.pdf" target="_blank" rel="noopener">
        <img src="{UP}/2023/09/mark-of-trust-certified-ISOIEC-27001-information-security-management-white-logo-En-GB-1019-300x152.png" alt="">
        <h3>Information Security Management System - ISO/ICE 27001:2013</h3><span class="text-link">PDF {ARROW}</span></a>
    </div>
  </div>
</section>
{cta_band(r, "Find out what SmartEye eQMS could do for your product",
          f'<a class="btn btn-quiet on-dark" href="why-smarteye.html">Why SmartEye eQMS</a><a class="btn btn-primary" href="index.html#demo">Get a Demo {ARROW}</a>')}"""
    write("about.html", head("Powered by S-Cube - eQMS SmartEye",
                             "Explore the best eQMS medical devices solutions to streamline compliance and enhance quality. Book a demo and subscribe for insights!", r)
          + header(r, "about.html") + body + footer(r))


# ---------------------------------------------------------------- RESOURCES
def build_resources():
    r = ""
    first = ARTICLES[0]; a = SRC[first]
    featured = f"""<a class="featured" href="resources/{first}.html" data-reveal>
      <figure><img src="{a['img'].replace('-scaled','')}" alt=""></figure>
      <div><time class="meta" datetime="{a['date']}">{nice_date(a['date'])}</time><h2>{esc(a['title'])}</h2><span class="text-link">Read more {ARROW}</span></div>
    </a>"""
    rest = "".join(post_card(s, r) for s in ARTICLES[1:])
    body = page_hero('<a href="index.html">Home</a><span>/</span><span>Resources</span>', "Our <em>Resources</em>", RES_LEDE)
    body += f"""
<section class="section section-tight">
  <div class="wrap">
    <h2 class="sub-head" data-reveal>Blogs</h2>
    {featured}
    <div class="posts two" data-stagger>{rest}</div>
  </div>
</section>

<section class="section dark" id="video">
  <div class="wrap split">
    <div data-reveal>
      <h2>Videos and <em>Media</em></h2>
      <p class="lede" style="margin-top:22px">{RES_LEDE}</p>
    </div>
    {video_button()}
  </div>
</section>
{cta_band(r)}"""
    write("resources.html", head("Resources - eQMS SmartEye",
                                 "Explore the best eQMS medical devices solutions to streamline compliance and enhance quality. Book a demo and subscribe for insights!", r)
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
      <nav class="crumbs" aria-label="Breadcrumb"><a href="{r}resources.html">Resources</a><span>/</span><span>Blogs</span></nav>
      <h1 class="rise">{esc(a['title'])}</h1>
      <p class="meta"><time datetime="{a['date']}">{nice_date(a['date'])}</time><span>{mins} min read</span></p>
    </div>
  </header>
  <div class="cover"><figure><img data-parallax="0.08" src="{a['img']}" alt=""></figure></div>
  <div class="reading">
    <nav class="toc" aria-label="Contents"><ol id="toc-list"></ol></nav>
    <div class="prose" data-toc>{html}</div>
  </div>
</article>
{cta_band(r)}
<hr class="rule">
<section class="section">
  <div class="wrap">
    <div class="section-head" data-reveal><h2>Our <em>Resource for QMS</em></h2><p class="lede">{RES_LEDE}</p></div>
    <div class="posts" data-stagger>{related}</div>
  </div>
</section>"""
        write(f"resources/{slug}.html", head(f"{a['title']} - eQMS SmartEye", a["desc"] or a["title"], r) + header(r, "resources.html") + body + footer(r))


# ---------------------------------------------------------------- CAREERS
def build_careers():
    r = ""
    items = "".join(f"""<li class="job"><a href="careers/{slug}.html">
          <div><time class="meta" datetime="{j['date']}">{nice_date(j['date'])}</time><h3>{j['title']}</h3><p class="job-sum">{j['summary']}</p></div>
          <span class="read">Read more</span><span class="arrow-c">{ARROW}</span></a></li>""" for slug, j in JOBS.items())
    body = page_hero('<a href="index.html">Home</a><span>/</span><span>Career</span>', "Career")
    body += f"""
<section class="section section-tight">
  <div class="wrap">
    <ul class="jobs" data-stagger>{items}</ul>
  </div>
</section>
{cta_band(r)}"""
    write("careers.html", head("Jobs Archives - eQMS SmartEye", "Jobs at S-Cube Technologies.", r)
          + header(r, "careers.html") + body + footer(r))

    rr = "../"
    for slug, j in JOBS.items():
        html = clean_job(SRC[slug]["html"])
        body = f"""
<article>
  <header class="article-hero">
    <div class="wrap">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="{rr}careers.html">Career</a><span>/</span><span>Jobs</span></nav>
      <h1 class="rise">{j['title']}</h1>
      <p class="meta"><time datetime="{j['date']}">{nice_date(j['date'])}</time></p>
    </div>
  </header>
  <div class="reading single" style="padding-top:24px">
    <div class="prose">{html}</div>
  </div>
</article>"""
        write(f"careers/{slug}.html", head(f"{j['title']} - eQMS SmartEye", j["title"], rr) + header(rr, "careers.html") + body + footer(rr))


# ---------------------------------------------------------------- CONTACT
def build_contact():
    r = ""
    body = page_hero('<a href="index.html">Home</a><span>/</span><span>Contact Us</span>', "Talk to the <em>SmartEye eQMS</em> team",
                     "Want to understand more about how SmartEye eQMS could transform the way you manage your SaMD design and development process? Browse our selection of videos or get in touch with one of our expert team today for a free and easy demo from those who built it.")
    body += f"""
<section class="section section-tight">
  <div class="wrap contact-grid">
    <ul class="channels" data-stagger>
      <li><span class="id">Email us:</span><a href="mailto:{EMAIL}">{EMAIL}</a></li>
      <li><span class="id">Mobile:</span><span class="ch-val"><a href="tel:+447459153907">+44 (0) 7459153907</a>/ <a href="tel:+41799036836">+41 799036836</a></span></li>
      <li><span class="id">UK:</span><address>125 Deansgate, Manchester, M3 2LH, United Kingdom</address></li>
    </ul>
    {video_button()}
  </div>
</section>

<section class="section dark demo">
  <div class="wrap">
    <div data-reveal><h2>{DEMO_CTA}</h2></div>
    <div data-reveal>{demo_form(r, "c")}</div>
  </div>
</section>"""
    write("contact.html", head("Contact Us - eQMS SmartEye",
                               "Explore the best eQMS medical devices solutions to streamline compliance and enhance quality. Book a demo and subscribe for insights!", r)
          + header(r, "contact.html") + body + footer(r))


# ---------------------------------------------------------------- LEGAL
def build_legal():
    r = "../"
    for slug, label in LEGAL:
        html, title = clean_legal(SRC[slug]["html"])
        title = title or label
        nav = "".join(f'<li><a href="{s}.html"{" aria-current=\"page\"" if s == slug else ""}>{l}</a></li>' for s, l in LEGAL)
        body = f"""
<article>
  <header class="article-hero">
    <div class="wrap">
      <h1 class="rise">{esc(title)}</h1>
    </div>
  </header>
  <div class="reading" style="padding-top:24px">
    <nav class="toc keep legal-nav" aria-label="Policies"><ol>{nav}</ol></nav>
    <div class="prose">{html}</div>
  </div>
</article>"""
        write(f"legal/{slug}.html", head(f"{title} - eQMS SmartEye", title, r) + header(r, None) + body + footer(r))


if __name__ == "__main__":
    build_home(); build_why(); build_about(); build_resources(); build_articles()
    build_careers(); build_contact(); build_legal()
