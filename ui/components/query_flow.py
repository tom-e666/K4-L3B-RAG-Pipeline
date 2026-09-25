"""Technical query flow diagram component for Comparison dashboard."""

import streamlit as st


def render_query_flow() -> None:
    """Render a compact, professional SVG technical pipeline flow diagram."""
    st.markdown(
        """
        <div class="query-flow-box">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
                <span style="font-size: 0.76rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #64748B;">
                    📐 Kiến trúc dòng xử lý (Unified Query Multi-strategy Flow)
                </span>
                <span style="font-size: 0.72rem; color: #10B981; font-weight: 600; background: #ECFDF5; padding: 2px 8px; border-radius: 4px;">
                    Concurrent / Isolated
                </span>
            </div>
            <div style="overflow-x: auto; text-align: center; padding: 0.4rem 0;">
                <svg width="680" height="110" viewBox="0 0 680 110" style="max-width: 100%; height: auto; font-family: 'Plus Jakarta Sans', sans-serif;">
                    <!-- Query node -->
                    <rect x="270" y="5" width="140" height="28" rx="6" fill="#1E3A8A" />
                    <text x="340" y="23" fill="#FFFFFF" font-size="11" font-weight="700" text-anchor="middle">Input Query</text>

                    <!-- Fork Lines -->
                    <path d="M 340 33 L 340 42 L 70 42 L 70 52" stroke="#94A3B8" stroke-width="1.5" fill="none" />
                    <path d="M 340 33 L 340 42 L 250 42 L 250 52" stroke="#94A3B8" stroke-width="1.5" fill="none" />
                    <path d="M 340 33 L 340 42 L 430 42 L 430 52" stroke="#94A3B8" stroke-width="1.5" fill="none" />
                    <path d="M 340 33 L 340 42 L 610 42 L 610 52" stroke="#94A3B8" stroke-width="1.5" fill="none" />

                    <!-- Strategies -->
                    <rect x="15" y="52" width="110" height="26" rx="5" fill="#EFF6FF" stroke="#3B82F6" stroke-width="1.2" />
                    <text x="70" y="69" fill="#1E40AF" font-size="10.5" font-weight="600" text-anchor="middle">Dense (Chroma)</text>

                    <rect x="195" y="52" width="110" height="26" rx="5" fill="#EFF6FF" stroke="#3B82F6" stroke-width="1.2" />
                    <text x="250" y="69" fill="#1E40AF" font-size="10.5" font-weight="600" text-anchor="middle">BM25 (Lexical)</text>

                    <rect x="375" y="52" width="110" height="26" rx="5" fill="#EFF6FF" stroke="#3B82F6" stroke-width="1.2" />
                    <text x="430" y="69" fill="#1E40AF" font-size="10.5" font-weight="600" text-anchor="middle">Hybrid Search</text>

                    <rect x="555" y="52" width="110" height="26" rx="5" fill="#EFF6FF" stroke="#3B82F6" stroke-width="1.2" />
                    <text x="610" y="69" fill="#1E40AF" font-size="10.5" font-weight="600" text-anchor="middle">Hybrid + RRF</text>

                    <!-- Join Lines -->
                    <path d="M 70 78 L 70 88 L 340 88 L 340 95" stroke="#94A3B8" stroke-width="1.5" fill="none" />
                    <path d="M 250 78 L 250 88" stroke="#94A3B8" stroke-width="1.5" fill="none" />
                    <path d="M 430 78 L 430 88" stroke="#94A3B8" stroke-width="1.5" fill="none" />
                    <path d="M 610 78 L 610 88 L 340 88" stroke="#94A3B8" stroke-width="1.5" fill="none" />

                    <!-- Comparison Bottom node -->
                    <rect x="250" y="93" width="180" height="17" rx="4" fill="#0F172A" />
                    <text x="340" y="105" fill="#FFFFFF" font-size="9.5" font-weight="700" text-anchor="middle">Side-by-Side Analysis & Ranking</text>
                </svg>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

