"""Visual styling and design system for Trợ lý AI Thực Chiến."""

import streamlit as st


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        /* Google Fonts & Base Typography */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {
            --primary: #2563EB;
            --primary-dark: #1E40AF;
            --primary-light: #EEF2FF;
            --primary-border: #DBEAFE;
            --surface: #FFFFFF;
            --background: #F8FAFC;
            --surface-hover: #F1F5F9;
            --ink: #0F172A;
            --ink-muted: #64748B;
            --ink-subtle: #94A3B8;
            --border: #E2E8F0;
            --border-light: #F1F5F9;
            --success: #10B981;
            --success-bg: #ECFDF5;
            --warning: #F59E0B;
            --warning-bg: #FFFBEB;
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-xl: 20px;
            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.05);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -4px rgb(0 0 0 / 0.03);
        }

        /* Global App Styling */
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
            color: var(--ink);
        }

        .stApp {
            background-color: var(--background) !important;
        }

        /* Streamlit Header / Decoration Bar */
        header[data-testid="stHeader"] {
            background: transparent !important;
        }

        .block-container {
            padding-top: 1.8rem !important;
            padding-bottom: 5.5rem !important;
            max-width: 1200px !important;
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: var(--surface) !important;
            border-right: 1px solid var(--border) !important;
            box-shadow: var(--shadow-sm);
        }

        [data-testid="stSidebar"] > div:first-child {
            padding-top: 1.5rem;
            padding-left: 1.1rem;
            padding-right: 1.1rem;
        }

        .sidebar-brand {
            padding-bottom: 1.2rem;
            margin-bottom: 1.2rem;
            border-bottom: 1px solid var(--border);
        }

        .brand-badge {
            display: inline-block;
            font-size: 0.68rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--primary);
            background: var(--primary-light);
            padding: 3px 8px;
            border-radius: 6px;
            margin-bottom: 0.4rem;
        }

        .brand-title {
            font-size: 1.08rem;
            font-weight: 800;
            color: var(--ink);
            margin: 0;
            line-height: 1.25;
            letter-spacing: -0.015em;
        }

        .brand-subtitle {
            font-size: 0.8rem;
            color: var(--ink-muted);
            margin-top: 2px;
            margin-bottom: 0;
        }

        /* Sidebar Navigation Radio Styling */
        [data-testid="stSidebar"] .stRadio > div {
            gap: 6px;
        }

        [data-testid="stSidebar"] .stRadio label {
            background: transparent;
            border-radius: var(--radius-md);
            padding: 0.6rem 0.85rem !important;
            border: 1px solid transparent;
            transition: all 0.15s ease-in-out;
            cursor: pointer;
            margin-bottom: 2px;
        }

        [data-testid="stSidebar"] .stRadio label:hover {
            background: var(--surface-hover);
            border-color: var(--border);
        }

        [data-testid="stSidebar"] .stRadio label[data-checked="true"],
        [data-testid="stSidebar"] .stRadio div[aria-checked="true"] {
            background: var(--primary-light) !important;
            border-color: var(--primary-border) !important;
            color: var(--primary-dark) !important;
            font-weight: 600 !important;
        }

        /* Hero Banner */
        .hero-banner {
            background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 60%, #3B82F6 100%);
            border-radius: var(--radius-lg);
            padding: 1.6rem 1.8rem;
            color: #FFFFFF;
            margin-bottom: 1.4rem;
            box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.25);
            position: relative;
            overflow: hidden;
        }

        .hero-banner::after {
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 300px;
            height: 300px;
            background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0) 70%);
            border-radius: 50%;
            pointer-events: none;
        }

        .hero-eyebrow {
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #BFDBFE;
            margin-bottom: 0.35rem;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .hero-title {
            font-size: clamp(1.6rem, 3.5vw, 2.2rem);
            font-weight: 800;
            margin: 0 0 0.4rem 0;
            line-height: 1.2;
            letter-spacing: -0.025em;
            color: #FFFFFF !important;
        }

        .hero-subtitle {
            font-size: 0.95rem;
            color: #DBEAFE;
            margin: 0 0 1rem 0;
            line-height: 1.5;
            max-width: 680px;
        }

        .hero-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .hero-badge {
            background: rgba(255, 255, 255, 0.16);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.22);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.74rem;
            font-weight: 600;
            color: #FFFFFF;
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }

        .badge-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: #34D399;
            box-shadow: 0 0 6px #34D399;
        }

        /* Cards & Containers */
        .saas-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 1.2rem;
            box-shadow: var(--shadow-sm);
            transition: all 0.2s ease;
        }

        .saas-card:hover {
            border-color: #CBD5E1;
            box-shadow: var(--shadow-md);
        }

        /* Metric Cards */
        .metric-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 1rem 1.1rem;
            box-shadow: var(--shadow-sm);
            display: flex;
            flex-direction: column;
            gap: 4px;
        }

        .metric-label {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--ink-muted);
        }

        .metric-value {
            font-size: 1.6rem;
            font-weight: 800;
            color: var(--ink);
            line-height: 1.15;
            font-family: 'JetBrains Mono', monospace;
        }

        .metric-subtext {
            font-size: 0.74rem;
            color: var(--ink-subtle);
        }

        /* Chat Message Presentation */
        .chat-bubble-user {
            background: #F1F5F9;
            border: 1px solid var(--border);
            border-radius: 16px 16px 4px 16px;
            padding: 0.85rem 1.1rem;
            margin-bottom: 0.9rem;
            color: var(--ink);
            line-height: 1.55;
            box-shadow: var(--shadow-sm);
        }

        .chat-bubble-assistant {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px 16px 16px 4px;
            padding: 1.1rem 1.25rem;
            margin-bottom: 0.9rem;
            color: var(--ink);
            line-height: 1.6;
            box-shadow: var(--shadow-sm);
        }

        /* Citation Badge Pill */
        .citation-badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background: var(--primary-light);
            color: var(--primary-dark);
            border: 1px solid var(--primary-border);
            padding: 2px 7px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            margin: 0 2px;
            cursor: default;
            vertical-align: middle;
        }

        /* Source Reference Cards */
        .source-card {
            background: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 0.85rem 1rem;
            margin: 0.5rem 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.03);
            transition: border-color 0.15s ease;
        }

        .source-card:hover {
            border-color: #CBD5E1;
        }

        .source-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.35rem;
        }

        .source-title {
            font-weight: 700;
            color: var(--ink);
            font-size: 0.92rem;
        }

        .source-tags {
            display: flex;
            gap: 6px;
        }

        .tag-pill {
            font-size: 0.7rem;
            font-weight: 600;
            padding: 2px 7px;
            border-radius: 4px;
            background: #F1F5F9;
            color: var(--ink-muted);
            border: 1px solid #E2E8F0;
        }

        .tag-pill-highlight {
            background: var(--primary-light);
            color: var(--primary-dark);
            border-color: var(--primary-border);
        }

        .source-snippet {
            font-size: 0.82rem;
            color: #475569;
            line-height: 1.5;
            background: #F8FAFC;
            padding: 0.6rem 0.75rem;
            border-radius: var(--radius-sm);
            border-left: 3px solid var(--primary);
            margin: 0.4rem 0;
            font-style: normal;
        }

        .source-meta-row {
            font-size: 0.76rem;
            color: var(--ink-subtle);
            margin-top: 0.35rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        /* Comparison Mode Styling */
        .technique-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: var(--surface);
            border: 1.5px solid var(--border);
            padding: 0.5rem 0.9rem;
            border-radius: 30px;
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--ink);
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .technique-chip.active {
            background: var(--primary-light);
            border-color: var(--primary);
            color: var(--primary-dark);
        }

        .technique-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 1.15rem;
            box-shadow: var(--shadow-sm);
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .technique-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: 0.85rem;
            padding-bottom: 0.65rem;
            border-bottom: 1px solid var(--border-light);
        }

        .technique-name {
            font-size: 1.05rem;
            font-weight: 800;
            color: var(--ink);
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .latency-badge {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 6px;
            background: #F1F5F9;
            color: #334155;
            border: 1px solid #E2E8F0;
        }

        .latency-fast {
            background: #ECFDF5;
            color: #065F46;
            border-color: #A7F3D0;
        }

        .doc-item-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.45rem 0.6rem;
            margin: 0.25rem 0;
            border-radius: var(--radius-sm);
            background: #F8FAFC;
            font-size: 0.82rem;
            border: 1px solid var(--border-light);
        }

        .doc-rank {
            font-weight: 700;
            color: var(--primary);
            margin-right: 6px;
            font-size: 0.78rem;
        }

        .doc-name {
            flex-grow: 1;
            font-weight: 600;
            color: var(--ink);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            padding-right: 8px;
        }

        .doc-score {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.76rem;
            color: var(--ink-muted);
            white-space: nowrap;
        }

        /* Ranking Comparison Table */
        .ranking-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.84rem;
            margin-top: 0.6rem;
            background: var(--surface);
            border-radius: var(--radius-md);
            overflow: hidden;
            box-shadow: var(--shadow-sm);
            border: 1px solid var(--border);
        }

        .ranking-table th {
            background: #F8FAFC;
            color: var(--ink-muted);
            font-weight: 700;
            text-align: left;
            padding: 0.65rem 0.9rem;
            border-bottom: 1px solid var(--border);
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .ranking-table td {
            padding: 0.65rem 0.9rem;
            border-bottom: 1px solid var(--border-light);
            color: var(--ink);
        }

        .ranking-table tr:last-child td {
            border-bottom: none;
        }

        .rank-pill {
            display: inline-block;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.74rem;
            font-weight: 700;
            padding: 2px 7px;
            border-radius: 4px;
            background: #F1F5F9;
            color: #475569;
        }

        .rank-pill-1 {
            background: #FEF3C7;
            color: #92400E;
            border: 1px solid #FDE68A;
        }

        .rank-pill-none {
            color: #CBD5E1;
            background: transparent;
        }

        /* Flow Diagram Container */
        .query-flow-box {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 1rem 1.2rem;
            margin: 1rem 0;
            box-shadow: var(--shadow-sm);
        }

        /* Educational Explanation Cards */
        .expl-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            padding: 0.9rem 1rem;
            height: 100%;
            box-shadow: var(--shadow-sm);
        }

        .expl-card-title {
            font-size: 0.88rem;
            font-weight: 700;
            color: var(--primary-dark);
            margin-bottom: 0.3rem;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .expl-card-desc {
            font-size: 0.78rem;
            color: var(--ink-muted);
            line-height: 1.45;
            margin: 0;
        }

        /* Streamlit Input & Button Polish */
        .stButton button {
            border-radius: var(--radius-md) !important;
            font-weight: 600 !important;
            padding: 0.5rem 1rem !important;
            transition: all 0.15s ease !important;
        }

        .stButton button:hover {
            box-shadow: var(--shadow-sm) !important;
        }

        /* Chat input fixed positioning polish */
        [data-testid="stChatInput"] {
            border-radius: var(--radius-lg) !important;
            box-shadow: var(--shadow-md) !important;
            border: 1.5px solid var(--border) !important;
            background: var(--surface) !important;
        }

        [data-testid="stChatInput"]:focus-within {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
        }

        /* Responsive tweaks */
        @media (max-width: 768px) {
            .block-container {
                padding-left: 0.8rem !important;
                padding-right: 0.8rem !important;
            }
            .hero-banner {
                padding: 1.2rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
