"""
UI Helpers, custom CSS styling, and visual rendering utilities.
Designed for a professional, clean blue and white theme suitable for hackathons.
"""

import streamlit as st


def load_custom_css():
    """Injects high quality modern CSS styling for a professional blue & white theme."""
    st.markdown(
        """
        <style>
        /* Base typography and theme colors */
        :root {
            --primary-color: #1E40AF;       /* Deep corporate blue */
            --primary-light: #3B82F6;       /* Vibrant accent blue */
            --primary-bg: #EFF6FF;          /* Soft light blue tint */
            --secondary-color: #0F172A;     /* Dark slate */
            --accent-green: #10B981;        /* Success green */
            --accent-amber: #F59E0B;        /* Warning amber */
            --card-border: #E2E8F0;         /* Slate border */
            --bg-card: #FFFFFF;
        }

        /* Hero / Header banner */
        .hero-banner {
            background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 50%, #3B82F6 100%);
            color: #FFFFFF !important;
            padding: 2.2rem 2rem;
            border-radius: 14px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.25);
        }
        .hero-banner h1 {
            color: #FFFFFF !important;
            font-size: 2.2rem !important;
            font-weight: 800 !important;
            margin-bottom: 0.5rem !important;
        }
        .hero-banner p {
            color: #E0E7FF !important;
            font-size: 1.1rem !important;
            margin-bottom: 0 !important;
        }

        /* Metric cards */
        .metric-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
            border-left: 5px solid #2563EB;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(37, 99, 235, 0.12);
        }
        .metric-title {
            color: #64748B;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .metric-value {
            color: #0F172A;
            font-size: 1.9rem;
            font-weight: 700;
            margin-top: 0.25rem;
        }

        /* Recommendation course card */
        .rec-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            border-top: 4px solid #2563EB;
        }
        .rec-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }
        .rec-title {
            color: #1E3A8A;
            font-size: 1.3rem;
            font-weight: 700;
            margin: 0;
        }
        .rec-score-badge {
            background-color: #EFF6FF;
            color: #1D4ED8;
            font-size: 0.95rem;
            font-weight: 700;
            padding: 0.35rem 0.75rem;
            border-radius: 9999px;
            border: 1px solid #BFDBFE;
            display: inline-block;
        }
        .reason-box {
            background: #F8FAFC;
            border-left: 4px solid #3B82F6;
            padding: 0.75rem 1rem;
            border-radius: 0 8px 8px 0;
            margin: 0.75rem 0;
            color: #334155;
            font-size: 0.92rem;
            line-height: 1.5;
        }

        /* Badges */
        .skill-tag {
            display: inline-block;
            background-color: #EEF2F6;
            color: #1E293B;
            font-size: 0.78rem;
            font-weight: 600;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
            margin: 0.15rem 0.25rem 0.15rem 0;
            border: 1px solid #CBD5E1;
        }
        .badge-beginner {
            background-color: #ECFDF5;
            color: #065F46;
            border: 1px solid #A7F3D0;
            font-size: 0.8rem;
            font-weight: 600;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
        }
        .badge-intermediate {
            background-color: #EFF6FF;
            color: #1E40AF;
            border: 1px solid #BFDBFE;
            font-size: 0.8rem;
            font-weight: 600;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
        }
        .badge-advanced {
            background-color: #FAF5FF;
            color: #6B21A8;
            border: 1px solid #E9D5FF;
            font-size: 0.8rem;
            font-weight: 600;
            padding: 0.2rem 0.6rem;
            border-radius: 6px;
        }

        /* Info notice boxes */
        .alert-box {
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
            font-size: 0.95rem;
        }
        .alert-info {
            background-color: #EFF6FF;
            color: #1E40AF;
            border: 1px solid #BFDBFE;
        }
        .alert-success {
            background-color: #ECFDF5;
            color: #065F46;
            border: 1px solid #A7F3D0;
        }
        .alert-warning {
            background-color: #FFFBEB;
            color: #92400E;
            border: 1px solid #FDE68A;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def render_stars(rating: float) -> str:
    """Renders gold star icons for a numeric rating."""
    if not rating or rating <= 0:
        return "Not yet rated"
    rounded = round(rating)
    full_stars = "★" * rounded
    empty_stars = "☆" * (5 - rounded)
    return f"{full_stars}{empty_stars} ({rating:.1f}/5)"


def get_difficulty_badge(difficulty: str) -> str:
    """Returns HTML formatted difficulty badge."""
    diff = (difficulty or "Beginner").capitalize()
    if diff == "Beginner":
        return f'<span class="badge-beginner">🌱 {diff}</span>'
    elif diff == "Intermediate":
        return f'<span class="badge-intermediate">⚡ {diff}</span>'
    else:
        return f'<span class="badge-advanced">🚀 {diff}</span>'
