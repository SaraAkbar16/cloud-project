import base64
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def render_gui(
    query="",
    results=None,
    dataset_info=None,
    error=None,
    message=None,
    embeddings_ready=False,
    embedding_model_name="",
    vector_store_name="",
    docs_path="data/docs",
):
    logo_html = ""
    logo_path = BASE_DIR / "logo_4.png"

    if logo_path.exists():
        encoded = base64.b64encode(logo_path.read_bytes()).decode()
        logo_html = f"""
        <div class="sidebar-logo">
            <img src="data:image/png;base64,{encoded}">
            <h3>Semantic Search</h3>
        </div>
        """

    error_html = f"<div class='alert error'>{error}</div>" if error else ""
    message_html = f"<div class='alert success'>{message}</div>" if message else ""

    stats_html = ""
    if dataset_info:
        stats_html = f"""
        <div class="card subtle">
            <h4>Dataset Info</h4>
            <div class="stats">
                <div><span>Docs</span><b>{dataset_info["doc_count"]}</b></div>
                <div><span>Chars</span><b>{dataset_info["char_count"]}</b></div>
                <div><span>MB</span><b>{dataset_info["size_mb"]}</b></div>
            </div>
        </div>
        """

    results_html = ""
    if results:
        results_html = "<div class='card'><h3>Search Results</h3>"
        for r in results:
            results_html += f"""
            <div class="result">
                <div class="result-top">
                    <span class="rank">#{r["rank"]}</span>
                    <span class="source">{r["source"]}</span>
                </div>
                <p>{r["content"]}...</p>
            </div>
            """
        results_html += "</div>"

    search_disabled = "" if embeddings_ready else "disabled"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Semantic Search</title>
        <style>
            body {{
                margin: 0;
                font-family: 'Segoe UI', system-ui, sans-serif;
                background: #EDEDCE;
                color: #0C2C55;
            }}

            .layout {{
                display: flex;
                min-height: 100vh;
            }}

            /* SIDEBAR */
            .sidebar {{
                width: 260px;
                background: linear-gradient(180deg, #0C2C55, #296374);
                padding: 28px 22px;
                color: white;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}

            .sidebar-logo {{
                margin-top: 60px;
                text-align: center;
            }}

            .sidebar-logo img {{
                width: 55px;
                margin-bottom: 10px;
            }}

            .sidebar-logo h3 {{
                margin: 0;
                font-weight: 600;
            }}

            .sidebar-controls {{
                margin-top: 50px;
                width: 100%;
            }}

            .sidebar label {{
                font-size: 13px;
                font-weight: 600;
                margin-top: 18px;
                display: block;
            }}

            .sidebar select,
            .sidebar input {{
                width: 100%;
                margin-top: 6px;
                padding: 9px;
                border-radius: 8px;
                border: none;
                font-size: 13px;
            }}

            /* MAIN */
            .main {{
                flex: 1;
                padding: 40px;
            }}

            .card {{
                background: white;
                border-radius: 18px;
                padding: 25px;
                margin-bottom: 25px;
                box-shadow: 0 12px 30px rgba(12,44,85,0.12);
            }}

            .card.subtle {{
                background: #EDEDCE;
                box-shadow: none;
            }}

            .action-bar {{
                display: flex;
                gap: 15px;
                margin-bottom: 25px;
            }}

            .action-bar button, .action-bar .btn-placeholder {{
                flex: 1;
                padding: 14px;
                border-radius: 14px;
                border: none;
                font-size: 15px;
                font-weight: 700;
                cursor: pointer;
                text-align: center;
            }}

            .primary {{
                background: #296374;
                color: white;
            }}

            .secondary {{
                background: #629FAD;
                color: #0C2C55;
            }}

            button:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
            }}

            .alert {{
                padding: 14px;
                border-radius: 12px;
                margin-bottom: 20px;
                font-weight: 600;
            }}

            .error {{
                background: #ffe1e1;
                color: #8b0000;
            }}

            .success {{
                background: #dff3ec;
            }}

            .stats {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 12px;
            }}

            .stats div {{
                background: white;
                padding: 12px;
                border-radius: 12px;
                text-align: center;
            }}

            .stats span {{
                font-size: 12px;
                color: #296374;
            }}

            .result {{
                margin-top: 12px;
                padding: 14px;
                border-radius: 14px;
                background: #f7f9fa;
                border-left: 5px solid #629FAD;
            }}

            .result-top {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 6px;
            }}

            .rank {{
                font-weight: 700;
                color: #296374;
            }}

            .source {{
                font-size: 13px;
            }}
            
            .search-input-group {{
                margin-bottom: 15px;
            }}
            
            .search-input-group input {{
                width: 100%;
                padding: 12px;
                border-radius: 8px;
                border: 1px solid #ccc;
                box-sizing: border-box;
            }}
        </style>
    </head>

    <body>
        <div class="layout">
            <aside class="sidebar">
                {logo_html}

                <div class="sidebar-controls">
                    <label>Embedding Model</label>
                    <input type="text" value="{embedding_model_name}" readonly>

                    <label>Vector Store</label>
                    <input type="text" value="{vector_store_name}" readonly>

                    <label>Data Source</label>
                    <input type="text" value="{docs_path}" readonly>

                    <label>Top-K</label>
                    <input type="number" name="top_k" value="3" min="1" max="10" form="search-form">
                </div>
            </aside>

            <main class="main">
                {error_html}
                {message_html}

                <div class="action-bar">
                    <button class="primary" type="submit" form="upload-form">
                        Generate / Refresh Embeddings
                    </button>

                    <button class="secondary" type="submit" form="search-form" {search_disabled}>
                        Search
                    </button>
                </div>

                <div class="card">
                    <form action="/upload" method="post" id="upload-form">
                        <label>Embeddings are created from files in <b>{docs_path}</b>.</label>
                    </form>
                </div>

                <div class="card">
                    <form action="/search" method="post" id="search-form">
                        <div class="search-input-group">
                            <label>Search Query</label>
                            <input type="text" name="query" value="{query}" placeholder="Enter your search terms..." required {search_disabled}>
                        </div>
                    </form>
                </div>

                {stats_html}

                {results_html}
            </main>
        </div>
    </body>
    </html>
    """