"""
Data viewer — generates a local HTML dashboard from scraped JSON data
and SQLite database.

Opens in your default browser so you can explore companies, investors,
people, and news/deals visually.
"""

import json
import os
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config
from db import get_db


def load_json(filename: str) -> list[dict]:
    """Load a JSON file from the output directory, return [] if missing."""
    path = os.path.join(config.OUTPUT_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def load_articles_from_db() -> list[dict]:
    """Load news articles from SQLite database."""
    try:
        db = get_db()
        articles = db.get_articles(limit=200, min_relevance=0.0)
        deals = db.get_deals(limit=100)
        return articles, deals
    except Exception as e:
        print(f"Warning: Could not load articles from database: {e}")
        return [], []


def generate_dashboard() -> str:
    """Generate an HTML dashboard from all scraped data."""
    companies = load_json("companies.json")
    investors = load_json("investors.json")
    people = load_json("people.json")
    articles, deals = load_articles_from_db()
    
    # Fallback to JSON if DB empty
    if not articles:
        news = load_json("news.json")
        articles = news
        deals = []

    # Stats
    total_records = len(companies) + len(investors) + len(people) + len(articles)
    principal_count = sum(1 for i in investors if i.get("is_principal_investor"))

    # Count deals
    deals_count = len(deals) if deals else sum(1 for a in articles if a.get("deal_info") and a.get("deal_info", {}).get("amount"))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PitchBook AI Investing Dashboard</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #0a0e1a;
    color: #e2e8f0;
    line-height: 1.6;
  }}

  /* ── Header ─────────────────────────── */
  .header {{
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    border-bottom: 1px solid rgba(99, 102, 241, 0.2);
    padding: 2rem 3rem;
  }}
  .header h1 {{
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #818cf8, #c084fc, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}
  .header p {{
    color: #94a3b8;
    font-size: 0.9rem;
    margin-top: 0.3rem;
  }}

  /* ── Stats Bar ──────────────────────── */
  .stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    padding: 1.5rem 3rem;
    background: #0d1117;
  }}
  .stat-card {{
    background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.05));
    border: 1px solid rgba(99,102,241,0.15);
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    transition: transform 0.2s, border-color 0.2s;
  }}
  .stat-card:hover {{
    transform: translateY(-2px);
    border-color: rgba(99,102,241,0.4);
  }}
  .stat-num {{
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #818cf8, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}
  .stat-label {{
    font-size: 0.8rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.3rem;
  }}

  /* ── Tabs ────────────────────────────── */
  .tabs {{
    display: flex;
    gap: 0;
    padding: 0 3rem;
    background: #0d1117;
    border-bottom: 1px solid rgba(99,102,241,0.15);
  }}
  .tab {{
    padding: 0.8rem 1.5rem;
    cursor: pointer;
    color: #64748b;
    font-weight: 500;
    font-size: 0.9rem;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
    user-select: none;
  }}
  .tab:hover {{ color: #c4b5fd; }}
  .tab.active {{
    color: #a78bfa;
    border-bottom-color: #a78bfa;
  }}

  /* ── Content ─────────────────────────── */
  .content {{
    padding: 2rem 3rem;
    max-width: 1400px;
  }}
  .tab-panel {{ display: none; }}
  .tab-panel.active {{ display: block; }}

  /* ── Search ──────────────────────────── */
  .search-bar {{
    width: 100%;
    padding: 0.8rem 1.2rem;
    background: #1e293b;
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 10px;
    color: #e2e8f0;
    font-size: 0.95rem;
    font-family: inherit;
    outline: none;
    margin-bottom: 1.5rem;
    transition: border-color 0.2s;
  }}
  .search-bar:focus {{
    border-color: #818cf8;
  }}
  .search-bar::placeholder {{ color: #475569; }}

  /* ── Cards ───────────────────────────── */
  .card-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 1rem;
  }}
  .card {{
    background: linear-gradient(135deg, #1e293b, #1a1f35);
    border: 1px solid rgba(99,102,241,0.12);
    border-radius: 12px;
    padding: 1.3rem;
    transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
  }}
  .card:hover {{
    transform: translateY(-2px);
    border-color: rgba(99,102,241,0.35);
    box-shadow: 0 8px 25px rgba(99,102,241,0.08);
  }}
  .card-title {{
    font-size: 1.05rem;
    font-weight: 600;
    color: #c4b5fd;
    margin-bottom: 0.5rem;
  }}
  .card-title a {{
    color: inherit;
    text-decoration: none;
  }}
  .card-title a:hover {{ text-decoration: underline; }}

  .card-meta {{
    font-size: 0.8rem;
    color: #64748b;
    margin-bottom: 0.6rem;
  }}
  .card-body {{
    font-size: 0.88rem;
    color: #94a3b8;
    line-height: 1.5;
  }}
  .card-body p {{ margin-bottom: 0.4rem; }}

  /* ── Tags / Badges ──────────────────── */
  .badge {{
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 500;
    margin: 0.15rem 0.2rem 0.15rem 0;
  }}
  .badge-purple {{ background: rgba(139,92,246,0.15); color: #c4b5fd; }}
  .badge-blue {{ background: rgba(59,130,246,0.15); color: #93c5fd; }}
  .badge-green {{ background: rgba(34,197,94,0.15); color: #86efac; }}
  .badge-amber {{ background: rgba(245,158,11,0.15); color: #fcd34d; }}
  .badge-pink {{ background: rgba(236,72,153,0.15); color: #f9a8d4; }}

  .field {{ margin-bottom: 0.3rem; }}
  .field-label {{
    font-size: 0.75rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  .field-value {{ color: #cbd5e1; font-size: 0.88rem; }}

  /* ── News-specific ──────────────────── */
  .article-card {{
    grid-column: span 1;
  }}
  .deal-box {{
    margin-top: 0.6rem;
    padding: 0.6rem 0.8rem;
    background: rgba(34,197,94,0.06);
    border: 1px solid rgba(34,197,94,0.15);
    border-radius: 8px;
  }}
  .deal-amount {{
    font-size: 1.1rem;
    font-weight: 700;
    color: #86efac;
  }}
  
  .relevance-score {{
    display: inline-block;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.7rem;
    background: rgba(99,102,241,0.1);
    border: 1px solid rgba(99,102,241,0.2);
    color: #a5f3fc;
  }}

  .empty-state {{
    text-align: center;
    padding: 3rem;
    color: #475569;
    font-size: 1rem;
  }}

  /* ── Scrollbar ──────────────────────── */
  ::-webkit-scrollbar {{ width: 8px; }}
  ::-webkit-scrollbar-track {{ background: #0a0e1a; }}
  ::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 4px; }}
  ::-webkit-scrollbar-thumb:hover {{ background: #475569; }}
</style>
</head>
<body>

<div class="header">
  <h1>📊 AI News Intelligence Platform</h1>
  <p>Real-time market data for AI investors and reporters — PitchBook AI market intelligence</p>
</div>

<div class="stats">
  <div class="stat-card">
    <div class="stat-num">{len(companies)}</div>
    <div class="stat-label">Companies</div>
  </div>
  <div class="stat-card">
    <div class="stat-num">{len(investors)}</div>
    <div class="stat-label">Investors</div>
  </div>
  <div class="stat-card">
    <div class="stat-num">{principal_count}</div>
    <div class="stat-label">Principal Investors</div>
  </div>
  <div class="stat-card">
    <div class="stat-num">{len(people)}</div>
    <div class="stat-label">People</div>
  </div>
  <div class="stat-card">
    <div class="stat-num">{len(articles)}</div>
    <div class="stat-label">News Articles</div>
  </div>
  <div class="stat-card">
    <div class="stat-num">{deals_count}</div>
    <div class="stat-label">Deals Tracked</div>
  </div>
</div>

<div class="tabs">
  <div class="tab active" onclick="showTab('companies')">Companies</div>
  <div class="tab" onclick="showTab('investors')">Investors</div>
  <div class="tab" onclick="showTab('people')">People</div>
  <div class="tab" onclick="showTab('news')">News & Deals</div>
</div>

<div class="content">

  <!-- COMPANIES TAB -->
  <div id="companies" class="tab-panel active">
    <input type="text" class="search-bar" placeholder="Search companies…" oninput="filterCards(this, 'companies')">
    <div class="card-grid" id="companies-grid">
      {_render_companies(companies)}
    </div>
  </div>

  <!-- INVESTORS TAB -->
  <div id="investors" class="tab-panel">
    <input type="text" class="search-bar" placeholder="Search investors & accelerators…" oninput="filterCards(this, 'investors')">
    <div class="card-grid" id="investors-grid">
      {_render_investors(investors)}
    </div>
  </div>

  <!-- PEOPLE TAB -->
  <div id="people" class="tab-panel">
    <input type="text" class="search-bar" placeholder="Search people…" oninput="filterCards(this, 'people')">
    <div class="card-grid" id="people-grid">
      {_render_people(people)}
    </div>
  </div>

  <!-- NEWS TAB -->
  <div id="news" class="tab-panel">
    <input type="text" class="search-bar" placeholder="Search articles & deals…" oninput="filterCards(this, 'news')">
    <div class="card-grid" id="news-grid">
      {_render_news(articles, deals)}
    </div>
  </div>

</div>

<script>
function showTab(tabId) {{
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById(tabId).classList.add('active');
  event.target.classList.add('active');
}}

function filterCards(input, gridId) {{
  const q = input.value.toLowerCase();
  const cards = document.querySelectorAll('#' + gridId + '-grid .card');
  cards.forEach(card => {{
    card.style.display = card.textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}}
</script>
</body>
</html>"""
    return html

  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #0a0e1a;
    color: #e2e8f0;
    line-height: 1.6;
  }}

  /* ── Header ─────────────────────────── */
  .header {{
    background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
    border-bottom: 1px solid rgba(99, 102, 241, 0.2);
    padding: 2rem 3rem;
  }}
  .header h1 {{
    font-size: 1.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #818cf8, #c084fc, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}
  .header p {{
    color: #94a3b8;
    font-size: 0.9rem;
    margin-top: 0.3rem;
  }}

  /* ── Stats Bar ──────────────────────── */
  .stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    padding: 1.5rem 3rem;
    background: #0d1117;
  }}
  .stat-card {{
    background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(139,92,246,0.05));
    border: 1px solid rgba(99,102,241,0.15);
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    transition: transform 0.2s, border-color 0.2s;
  }}
  .stat-card:hover {{
    transform: translateY(-2px);
    border-color: rgba(99,102,241,0.4);
  }}
  .stat-num {{
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #818cf8, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}
  .stat-label {{
    font-size: 0.8rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.3rem;
  }}

  /* ── Tabs ────────────────────────────── */
  .tabs {{
    display: flex;
    gap: 0;
    padding: 0 3rem;
    background: #0d1117;
    border-bottom: 1px solid rgba(99,102,241,0.15);
  }}
  .tab {{
    padding: 0.8rem 1.5rem;
    cursor: pointer;
    color: #64748b;
    font-weight: 500;
    font-size: 0.9rem;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
    user-select: none;
  }}
  .tab:hover {{ color: #c4b5fd; }}
  .tab.active {{
    color: #a78bfa;
    border-bottom-color: #a78bfa;
  }}

  /* ── Content ─────────────────────────── */
  .content {{
    padding: 2rem 3rem;
    max-width: 1400px;
  }}
  .tab-panel {{ display: none; }}
  .tab-panel.active {{ display: block; }}

  /* ── Search ──────────────────────────── */
  .search-bar {{
    width: 100%;
    padding: 0.8rem 1.2rem;
    background: #1e293b;
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 10px;
    color: #e2e8f0;
    font-size: 0.95rem;
    font-family: inherit;
    outline: none;
    margin-bottom: 1.5rem;
    transition: border-color 0.2s;
  }}
  .search-bar:focus {{
    border-color: #818cf8;
  }}
  .search-bar::placeholder {{ color: #475569; }}

  /* ── Cards ───────────────────────────── */
  .card-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
    gap: 1rem;
  }}
  .card {{
    background: linear-gradient(135deg, #1e293b, #1a1f35);
    border: 1px solid rgba(99,102,241,0.12);
    border-radius: 12px;
    padding: 1.3rem;
    transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
  }}
  .card:hover {{
    transform: translateY(-2px);
    border-color: rgba(99,102,241,0.35);
    box-shadow: 0 8px 25px rgba(99,102,241,0.08);
  }}
  .card-title {{
    font-size: 1.05rem;
    font-weight: 600;
    color: #c4b5fd;
    margin-bottom: 0.5rem;
  }}
  .card-title a {{
    color: inherit;
    text-decoration: none;
  }}
  .card-title a:hover {{ text-decoration: underline; }}

  .card-meta {{
    font-size: 0.8rem;
    color: #64748b;
    margin-bottom: 0.6rem;
  }}
  .card-body {{
    font-size: 0.88rem;
    color: #94a3b8;
    line-height: 1.5;
  }}
  .card-body p {{ margin-bottom: 0.4rem; }}

  /* ── Tags / Badges ──────────────────── */
  .badge {{
    display: inline-block;
    padding: 0.15rem 0.6rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 500;
    margin: 0.15rem 0.2rem 0.15rem 0;
  }}
  .badge-purple {{ background: rgba(139,92,246,0.15); color: #c4b5fd; }}
  .badge-blue {{ background: rgba(59,130,246,0.15); color: #93c5fd; }}
  .badge-green {{ background: rgba(34,197,94,0.15); color: #86efac; }}
  .badge-amber {{ background: rgba(245,158,11,0.15); color: #fcd34d; }}
  .badge-pink {{ background: rgba(236,72,153,0.15); color: #f9a8d4; }}

  .field {{ margin-bottom: 0.3rem; }}
  .field-label {{
    font-size: 0.75rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  .field-value {{ color: #cbd5e1; font-size: 0.88rem; }}

  /* ── News-specific ──────────────────── */
  .article-card {{
    grid-column: span 1;
  }}
  .deal-box {{
    margin-top: 0.6rem;
    padding: 0.6rem 0.8rem;
    background: rgba(34,197,94,0.06);
    border: 1px solid rgba(34,197,94,0.15);
    border-radius: 8px;
  }}
  .deal-amount {{
    font-size: 1.1rem;
    font-weight: 700;
    color: #86efac;
  }}

  .empty-state {{
    text-align: center;
    padding: 3rem;
    color: #475569;
    font-size: 1rem;
  }}

  /* ── Scrollbar ──────────────────────── */
  ::-webkit-scrollbar {{ width: 8px; }}
  ::-webkit-scrollbar-track {{ background: #0a0e1a; }}
  ::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 4px; }}
  ::-webkit-scrollbar-thumb:hover {{ background: #475569; }}
</style>
</head>
<body>

<div class="header">
  <h1>📊 PitchBook AI Investing Dashboard</h1>
  <p>Scraped data from PitchBook, Crunchbase, and SEC EDGAR — AI market intelligence</p>
</div>

<div class="stats">
  <div class="stat-card">
    <div class="stat-num">{len(companies)}</div>
    <div class="stat-label">Companies</div>
  </div>
  <div class="stat-card">
    <div class="stat-num">{len(investors)}</div>
    <div class="stat-label">Investors</div>
  </div>
  <div class="stat-card">
    <div class="stat-num">{principal_count}</div>
    <div class="stat-label">Principal Investors</div>
  </div>
  <div class="stat-card">
    <div class="stat-num">{len(people)}</div>
    <div class="stat-label">People</div>
  </div>
  <div class="stat-card">
    <div class="stat-num">{len(news)}</div>
    <div class="stat-label">Articles</div>
  </div>
  <div class="stat-card">
    <div class="stat-num">{deals_with_amount}</div>
    <div class="stat-label">Deals Found</div>
  </div>
</div>

<div class="tabs">
  <div class="tab active" onclick="showTab('companies')">Companies</div>
  <div class="tab" onclick="showTab('investors')">Investors</div>
  <div class="tab" onclick="showTab('people')">People</div>
  <div class="tab" onclick="showTab('news')">News & Deals</div>
</div>

<div class="content">

  <!-- COMPANIES TAB -->
  <div id="companies" class="tab-panel active">
    <input type="text" class="search-bar" placeholder="Search companies…" oninput="filterCards(this, 'companies')">
    <div class="card-grid" id="companies-grid">
      {_render_companies(companies)}
    </div>
  </div>

  <!-- INVESTORS TAB -->
  <div id="investors" class="tab-panel">
    <input type="text" class="search-bar" placeholder="Search investors & accelerators…" oninput="filterCards(this, 'investors')">
    <div class="card-grid" id="investors-grid">
      {_render_investors(investors)}
    </div>
  </div>

  <!-- PEOPLE TAB -->
  <div id="people" class="tab-panel">
    <input type="text" class="search-bar" placeholder="Search people…" oninput="filterCards(this, 'people')">
    <div class="card-grid" id="people-grid">
      {_render_people(people)}
    </div>
  </div>

  <!-- NEWS TAB -->
  <div id="news" class="tab-panel">
    <input type="text" class="search-bar" placeholder="Search articles & deals…" oninput="filterCards(this, 'news')">
    <div class="card-grid" id="news-grid">
      {_render_news(news)}
    </div>
  </div>

</div>

<script>
function showTab(tabId) {{
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById(tabId).classList.add('active');
  event.target.classList.add('active');
}}

function filterCards(input, gridId) {{
  const q = input.value.toLowerCase();
  const cards = document.querySelectorAll('#' + gridId + '-grid .card');
  cards.forEach(card => {{
    card.style.display = card.textContent.toLowerCase().includes(q) ? '' : 'none';
  }});
}}
</script>
</body>
</html>"""
    return html


def _render_companies(companies: list[dict]) -> str:
    if not companies:
        return '<div class="empty-state">No companies scraped yet. Run: <code>python main.py --companies</code></div>'

    cards = []
    for c in companies:
        loc = c.get("location", {})
        loc_str = ", ".join(filter(None, [loc.get("city"), loc.get("state"), loc.get("country")]))
        investors_html = "".join(f'<span class="badge badge-blue">{i}</span>' for i in c.get("investors", [])[:5])

        # Link to PitchBook profile
        name_html = _esc(c.get('name', 'Unknown'))
        if c.get("url"):
            name_html = f'<a href="{_esc(c["url"])}" target="_blank">{name_html}</a>'

        cards.append(f"""<div class="card">
  <div class="card-title">{name_html}</div>
  <div class="card-meta">{_esc(loc_str)} · Founded {_esc(c.get('founded', '—'))}</div>
  <div class="card-body">
    <div class="field"><span class="badge badge-purple">{_esc(c.get('status', 'unknown'))}</span>
    <span class="badge badge-amber">{_esc(c.get('industry', ''))}</span></div>
    <p>{_esc(c.get('description', '')[:200])}</p>
    {"<div class='field'><span class='field-label'>Funding</span> <span class='field-value'>" + _esc(c.get('total_funding', '')) + "</span></div>" if c.get('total_funding') else ""}
    {"<div class='field'><span class='field-label'>Last Round</span> <span class='field-value'>" + _esc(c.get('last_funding_round', '')) + " · " + _esc(c.get('last_funding_date', '')) + "</span></div>" if c.get('last_funding_round') else ""}
    {f"<div class='field' style='margin-top:0.4rem'><span class='field-label'>Investors</span><br>{investors_html}</div>" if investors_html else ""}
  </div>
</div>""")
    return "\n".join(cards)


def _render_investors(investors: list[dict]) -> str:
    if not investors:
        return '<div class="empty-state">No investors scraped yet. Run: <code>python main.py --investors</code></div>'

    cards = []
    for i in investors:
        loc = i.get("location", {})
        loc_str = ", ".join(filter(None, [loc.get("city"), loc.get("state"), loc.get("country")]))
        type_badge = "badge-pink" if i.get("is_principal_investor") else "badge-purple"
        type_label = "👑 Principal" if i.get("is_principal_investor") else i.get("investor_type", "")
        portfolio_html = "".join(f'<span class="badge badge-blue">{p}</span>' for p in i.get("portfolio_companies", [])[:6])
        focus_html = "".join(f'<span class="badge badge-green">{f}</span>' for f in i.get("focus_areas", [])[:4])

        # Link to PitchBook profile
        name_html = _esc(i.get('name', 'Unknown'))
        if i.get("url"):
            name_html = f'<a href="{_esc(i["url"])}" target="_blank">{name_html}</a>'

        cards.append(f"""<div class="card">
  <div class="card-title">{name_html}</div>
  <div class="card-meta">{_esc(loc_str)}</div>
  <div class="card-body">
    <div class="field"><span class="badge {type_badge}">{_esc(type_label)}</span></div>
    <p>{_esc(i.get('description', '')[:200])}</p>
    {"<div class='field'><span class='field-label'>AUM</span> <span class='field-value'>" + _esc(i.get('aum', '')) + "</span></div>" if i.get('aum') else ""}
    {f"<div class='field' style='margin-top:0.4rem'><span class='field-label'>Focus</span><br>{focus_html}</div>" if focus_html else ""}
    {f"<div class='field' style='margin-top:0.4rem'><span class='field-label'>Portfolio</span><br>{portfolio_html}</div>" if portfolio_html else ""}
  </div>
</div>""")
    return "\n".join(cards)


def _render_people(people: list[dict]) -> str:
    if not people:
        return '<div class="empty-state">No people scraped yet. Run: <code>python main.py --people</code></div>'

    cards = []
    for p in people:
        # Link to PitchBook profile (if available - usually no direct URL for people unless scraped from profile page)
        # Note: Person schema has 'url' field? Let's check. Yes.
        name_html = _esc(p.get('name', 'Unknown'))
        # If there is a PitchBook profile URL (not just LinkedIn)
        if p.get("url"):
             name_html = f'<a href="{_esc(p["url"])}" target="_blank">{name_html}</a>'

        cards.append(f"""<div class="card">
  <div class="card-title">{name_html}</div>
  <div class="card-meta">{_esc(p.get('title', ''))} @ {_esc(p.get('company', ''))}</div>
  <div class="card-body">
    <span class="badge badge-purple">{_esc(p.get('company_type', ''))}</span>
    {"<span class='badge badge-blue'>" + _esc(p.get('location', '')) + "</span>" if p.get('location') else ""}
    <p style="margin-top:0.4rem">{_esc(p.get('bio', '')[:200])}</p>
    {"<a href='" + _esc(p.get('linkedin', '')) + "' target='_blank' style='color:#818cf8;font-size:0.85rem'>LinkedIn →</a>" if p.get('linkedin') else ""}
  </div>
</div>""")
    return "\n".join(cards)


def _render_news(articles: list[dict], deals: list[dict]) -> str:
    if not articles and not deals:
        return '<div class="empty-state">No articles scraped yet. Run: <code>python main.py --news</code></div>'

    cards = []
    
    # Render deals
    for d in deals[:50]:
        company = d.get("company_name", "Unknown Company")
        amount = d.get("funding_amount", 0)
        currency = d.get("funding_currency", "USD")
        round_type = d.get("round_type", "Funding")
        investors = d.get("investors", "")
        title = d.get("title", "")
        url = d.get("url", "#")
        date = d.get("announcement_date") or d.get("published_date", "")
        
        amount_str = f"${amount:,.0f}" if amount else "Amount TBD"
        investors_str = f" from {investors}" if investors else ""
        
        cards.append(f"""<div class="card article-card">
  <div class="card-title"><a href="{_esc(url)}" target="_blank">{_esc(company)} raises {amount_str}</a></div>
  <div class="card-meta">{_esc(date)} · {_esc(round_type)}</div>
  <div class="card-body">
    <p>{_esc(title[:200])}</p>
    <div class="deal-box">
      <div class="deal-amount">{_esc(amount_str)}</div>
      <div style="font-size:0.82rem;color:#94a3b8;margin-top:0.2rem">{_esc(round_type)}{_esc(investors_str)}</div>
    </div>
  </div>
</div>""")
    
    # Render articles
    for a in articles[:100]:
        url = a.get("url", "#")
        title = a.get("title", "Untitled")
        published_date = a.get("published_date", "")
        summary = a.get("summary", "") or (a.get("content", "")[:250] + "…" if a.get("content") else "")
        relevance = a.get("ai_relevance_score", 0)
        is_deal = a.get("is_deal_news", 0)
        
        deal_badge = '<span class="badge badge-green">💰 Deal News</span>' if is_deal else ""
        relevance_badge = f'<span class="relevance-score">Relevance: {relevance:.0%}</span>'
        
        cards.append(f"""<div class="card article-card">
  <div class="card-title"><a href="{_esc(url)}" target="_blank">{_esc(title)}</a></div>
  <div class="card-meta">{_esc(published_date)}</div>
  <div class="card-body">
    {deal_badge}
    {relevance_badge}
    <p style="margin-top:0.5rem">{_esc(summary[:300])}</p>
  </div>
</div>""")
    
    return "\n".join(cards) if cards else '<div class="empty-state">No articles found.</div>'


def _esc(text: str) -> str:
    """HTML-escape a string."""
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def open_dashboard():
    """Generate and open the dashboard in the default browser."""
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    html = generate_dashboard()
    path = os.path.join(config.OUTPUT_DIR, "dashboard.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    abs_path = os.path.abspath(path)
    print(f"[OK] Dashboard saved to: {abs_path}")
    print("   Opening in browser …")
    webbrowser.open(f"file:///{abs_path}")


if __name__ == "__main__":
    open_dashboard()
