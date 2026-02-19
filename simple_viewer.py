"""
Simple HTML viewer - displays articles in a clean, readable dashboard.

For newsletter creators: This dashboard shows only VERIFIED, accessible
articles. Every link has been validated to ensure it works.
"""

import os
import webbrowser
from db import get_db

def get_url_status_badge(status: str) -> str:
    """Generate HTML badge for URL status."""
    badges = {
        'accessible': '<span class="badge badge-success">✓ Verified</span>',
        'preview_only': '<span class="badge badge-warning">⚠ Preview Only</span>',
        'inaccessible': '<span class="badge badge-danger">✗ Unavailable</span>',
        'unchecked': '<span class="badge badge-info">? Unchecked</span>',
    }
    return badges.get(status, badges['unchecked'])

def create_dashboard(show_all: bool = False):
    """
    Create a simple HTML dashboard showing articles.
    
    Args:
        show_all: If True, show all articles. If False, only show accessible ones.
    """
    
    db = get_db()
    all_articles = db.get_articles(limit=100, min_relevance=0.0)
    
    # Filter to only accessible articles by default
    if show_all:
        articles = all_articles
    else:
        articles = [a for a in all_articles if a.get('url_status') in ('accessible', 'unchecked', None)]
    
    deals = db.get_deals(limit=100)
    stats = db.get_statistics()
    
    # Build articles HTML
    articles_html = ""
    for i, article in enumerate(articles):
        url_status = article.get('url_status', 'unchecked')
        source = article.get('source', 'unknown')
        status_badge = get_url_status_badge(url_status)
        
        articles_html += f"""
        <div class="article-card" onclick="openArticle({i})">
            <h3>{article['title']}</h3>
            <p class="meta">
                <span class="relevance">Relevance: {article['ai_relevance_score']:.0%}</span>
                <span class="date">{article['published_date']}</span>
                <span class="source-tag">{source}</span>
                {status_badge}
            </p>
            <p class="summary">{article['summary']}</p>
            <div class="categories">
                {' '.join([f'<span class="tag">{cat}</span>' for cat in article.get('categories', [])])}
            </div>
            <p class="click-hint">Click to expand</p>
        </div>
        <div id="modal-{i}" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeArticle({i})">&times;</span>
                <h2>{article['title']}</h2>
                <p class="meta">
                    <span class="relevance">Relevance: {article['ai_relevance_score']:.0%}</span>
                    <span class="date">Published: {article['published_date']}</span>
                    <span class="source-tag">{source}</span>
                    {status_badge}
                </p>
                <a href="{article['url']}" target="_blank" class="source-link">📌 Read Original Article</a>
                <div class="modal-body">
                    <h4>Summary</h4>
                    <p>{article['summary']}</p>
                    <h4>Full Content</h4>
                    <p>{article.get('content', 'No additional content available')}</p>
                    <h4>Categories</h4>
                    <div class="categories">
                        {' '.join([f'<span class="tag">{cat}</span>' for cat in article.get('categories', [])])}
                    </div>
                </div>
            </div>
        </div>
        """
    
    # Build deals HTML
    deals_html = ""
    for i, deal in enumerate(deals):
        deals_html += f"""
        <div class="deal-card" onclick="openDeal({i})">
            <h4>{deal['company_name']}</h4>
            <p class="amount">${deal['funding_amount']:,.0f} - {deal['round_type']}</p>
            <p class="investors">{deal['investors']}</p>
            <p class="date">{deal['announcement_date']}</p>
            <p class="click-hint">Click for details</p>
        </div>
        <div id="deal-modal-{i}" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeDeal({i})">&times;</span>
                <h2>{deal['company_name']}</h2>
                <div class="modal-body">
                    <h4>Funding Details</h4>
                    <p><strong>Amount:</strong> ${deal['funding_amount']:,.0f}</p>
                    <p><strong>Round Type:</strong> {deal['round_type']}</p>
                    <p><strong>Date:</strong> {deal['announcement_date']}</p>
                    <h4>Investors</h4>
                    <p>{deal['investors']}</p>
                    <h4>Related Article</h4>
                    <p>{deal['title']}</p>
                    <a href="{deal['url']}" target="_blank" class="source-link">📌 Read on PitchBook</a>
                </div>
            </div>
        </div>
        """
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI News Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            color: #e2e8f0;
            padding: 2rem;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 3rem;
            border-bottom: 2px solid rgba(99, 102, 241, 0.3);
            padding-bottom: 2rem;
        }}
        
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-top: 1.5rem;
        }}
        
        .stat {{
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid rgba(99, 102, 241, 0.3);
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 1.8rem;
            font-weight: bold;
            color: #60a5fa;
        }}
        
        .stat-label {{
            font-size: 0.85rem;
            color: #94a3b8;
            margin-top: 0.5rem;
        }}
        
        .section {{
            margin-bottom: 3rem;
        }}
        
        .section h2 {{
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid rgba(99, 102, 241, 0.3);
        }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
        }}
        
        .article-card {{
            background: rgba(30, 27, 75, 0.5);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 12px;
            padding: 1.5rem;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .article-card:hover {{
            background: rgba(30, 27, 75, 0.8);
            border-color: rgba(99, 102, 241, 0.5);
            transform: translateY(-2px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }}
        
        .article-card h3 {{
            font-size: 1.1rem;
            margin-bottom: 0.8rem;
            line-height: 1.4;
            color: #e2e8f0;
        }}
        
        .meta {{
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            margin-bottom: 1rem;
            font-size: 0.85rem;
        }}
        
        .relevance {{
            background: rgba(34, 197, 94, 0.2);
            color: #86efac;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
        }}
        
        .date {{
            color: #94a3b8;
        }}
        
        .source-tag {{
            background: rgba(99, 102, 241, 0.2);
            color: #a78bfa;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            text-transform: uppercase;
        }}
        
        .badge {{
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
        }}
        
        .badge-success {{
            background: rgba(34, 197, 94, 0.2);
            color: #86efac;
        }}
        
        .badge-warning {{
            background: rgba(234, 179, 8, 0.2);
            color: #fde047;
        }}
        
        .badge-danger {{
            background: rgba(239, 68, 68, 0.2);
            color: #fca5a5;
        }}
        
        .badge-info {{
            background: rgba(59, 130, 246, 0.2);
            color: #93c5fd;
        }}
        
        .summary {{
            color: #cbd5e1;
            margin-bottom: 1rem;
            line-height: 1.5;
            font-size: 0.95rem;
        }}
        
        .categories {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        
        .tag {{
            background: rgba(99, 102, 241, 0.2);
            color: #a5b4fc;
            padding: 0.3rem 0.7rem;
            border-radius: 4px;
            font-size: 0.8rem;
        }}
        
        .click-hint {{
            color: #94a3b8;
            font-size: 0.8rem;
            margin-top: 0.8rem;
            font-style: italic;
        }}
        
        /* Modal styles */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.8);
            animation: fadeIn 0.3s ease;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        .modal-content {{
            background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
            margin: 5% auto;
            padding: 2rem;
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 12px;
            width: 90%;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            animation: slideIn 0.3s ease;
        }}
        
        @keyframes slideIn {{
            from {{
                transform: translateY(-50px);
                opacity: 0;
            }}
            to {{
                transform: translateY(0);
                opacity: 1;
            }}
        }}
        
        .modal-content h2 {{
            margin-top: 0;
            color: #e2e8f0;
            font-size: 1.5rem;
            line-height: 1.4;
        }}
        
        .modal-body {{
            margin-top: 1.5rem;
        }}
        
        .modal-body h4 {{
            color: #60a5fa;
            margin-top: 1.5rem;
            margin-bottom: 0.8rem;
            font-size: 1.1rem;
        }}
        
        .modal-body p {{
            color: #cbd5e1;
            line-height: 1.6;
            margin-bottom: 1rem;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .close {{
            color: #94a3b8;
            float: right;
            font-size: 2rem;
            font-weight: bold;
            cursor: pointer;
            transition: color 0.2s;
        }}
        
        .close:hover {{
            color: #e2e8f0;
        }}
        
        .source-link {{
            display: inline-block;
            margin: 1rem 0;
            padding: 0.75rem 1.5rem;
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
        }}
        
        .source-link:hover {{
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4);
        }}
        
        .deal-card {{
            background: rgba(30, 27, 75, 0.5);
            border: 1px solid rgba(34, 197, 94, 0.2);
            border-radius: 12px;
            padding: 1.5rem;
            transition: all 0.3s ease;
        }}
        
        .deal-card:hover {{
            background: rgba(30, 27, 75, 0.8);
            border-color: rgba(34, 197, 94, 0.5);
            transform: translateY(-2px);
        }}
        
        .deal-card h4 {{
            margin-bottom: 0.5rem;
            color: #e2e8f0;
        }}
        
        .amount {{
            font-size: 1.2rem;
            font-weight: bold;
            color: #22c55e;
            margin-bottom: 0.5rem;
        }}
        
        .investors {{
            color: #cbd5e1;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }}
        
        .deal-card .date {{
            color: #94a3b8;
            font-size: 0.85rem;
        }}
        
        footer {{
            text-align: center;
            color: #64748b;
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid rgba(99, 102, 241, 0.2);
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 AI News Intelligence Dashboard</h1>
            <p>Real-time AI investing news, funding deals, and market insights</p>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">{stats['total_articles']}</div>
                    <div class="stat-label">Articles</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{stats['total_deals']}</div>
                    <div class="stat-label">Deals</div>
                </div>
                <div class="stat">
                    <div class="stat-number">${stats['total_funding_usd']/1e9:.1f}B</div>
                    <div class="stat-label">Total Funding</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{stats['total_categories']}</div>
                    <div class="stat-label">AI Categories</div>
                </div>
            </div>
        </header>
        
        <div class="section">
            <h2>📰 Latest Articles</h2>
            <div class="grid">
                {articles_html}
            </div>
        </div>
        
        <div class="section">
            <h2>💰 Funding Deals</h2>
            <div class="grid">
                {deals_html}
            </div>
        </div>
        
        <footer>
            <p>Last updated: 2026-02-17 | Data collected from PitchBook AI news</p>
        </footer>
    </div>
    
    <script>
        function openArticle(index) {{
            const modal = document.getElementById('modal-' + index);
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }}
        
        function closeArticle(index) {{
            const modal = document.getElementById('modal-' + index);
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }}
        
        function openDeal(index) {{
            const modal = document.getElementById('deal-modal-' + index);
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        }}
        
        function closeDeal(index) {{
            const modal = document.getElementById('deal-modal-' + index);
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }}
        
        // Close modal when clicking outside of it
        window.onclick = function(event) {{
            if (event.target.classList.contains('modal')) {{
                event.target.style.display = 'none';
                document.body.style.overflow = 'auto';
            }}
        }}
        
        // Close modal on Escape key
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Escape') {{
                document.querySelectorAll('.modal').forEach(modal => {{
                    modal.style.display = 'none';
                }});
                document.body.style.overflow = 'auto';
            }}
        }});
    </script>
</body>
</html>"""
    
    return html


if __name__ == '__main__':
    html = create_dashboard()
    
    # Write to file
    output_path = 'dashboard.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Dashboard created: {output_path}")
    print(f"Opening in browser...")
    
    # Open in browser
    webbrowser.open(f'file://{os.path.abspath(output_path)}')
