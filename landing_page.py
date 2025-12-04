import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Premium Product Homepage", layout="wide")

# ------------------------------------------------------------------
# PREMIUM HTML + CSS CODE
# ------------------------------------------------------------------
html_code = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8" />
<style>

    body {
        margin: 0;
        background: #050505;
        font-family: 'Inter', sans-serif;
        color: #eee;
    }

    .container {
        max-width: 1200px;
        margin: auto;
        padding: 40px 20px;
    }

    /* HERO SECTION */
    .hero {
        text-align: center;
        padding: 100px 20px;
    }

    .hero-title {
        font-size: 58px;
        font-weight: 800;
        background: linear-gradient(90deg, #ffffff, #bcbcbc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
    }

    .hero-subtitle {
        font-size: 22px;
        color: #bbbbbb;
        max-width: 700px;
        margin: auto;
        margin-bottom: 40px;
    }

    .hero-btn {
        padding: 14px 26px;
        border-radius: 8px;
        background: #ff3b4d;
        color: white;
        font-weight: 700;
        text-decoration: none;
        box-shadow: 0 8px 22px rgba(255, 50, 70, 0.28);
    }

    /* PRODUCT CARDS */
    .product-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 26px;
        margin-top: 60px;
    }

    .card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.05);
        padding: 26px;
        border-radius: 14px;
        backdrop-filter: blur(6px);
        transition: 0.3s;
    }

    .card:hover {
        transform: translateY(-8px);
        background: rgba(255,255,255,0.06);
        box-shadow: 0 18px 40px rgba(0,0,0,0.5);
    }

    .card-title {
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .card-text {
        color: #cfcfcf;
        font-size: 15px;
        line-height: 1.5;
    }

    /* NEXT STEPS */
    .steps {
        margin-top: 80px;
        padding: 50px;
        border-radius: 16px;
        background: linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
        border: 1px solid rgba(255,255,255,0.04);
        text-align:center;
    }

    .steps-title {
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 20px;
    }

    .steps-links {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-top: 25px;
        flex-wrap: wrap;
    }

    .step-btn {
        padding: 12px 22px;
        border-radius: 8px;
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        text-decoration: none;
        color: #eee;
        font-weight: 600;
        transition: 0.3s;
    }

    .step-btn:hover {
        background: rgba(255,255,255,0.14);
        transform: translateY(-6px);
    }

    /* FOOTER */
    .footer {
        margin-top: 80px;
        padding: 40px;
        text-align:center;
        font-size: 14px;
        color: #8e8e8e;
        border-top: 1px solid rgba(255,255,255,0.06);
    }

</style>
</head>

<body>

<!-- HERO -->
<div class="container">
    <div class="hero">
        <div class="hero-title">Premium Product Homepage</div>
        <div class="hero-subtitle">
            A beautifully crafted modern interface for your product, platform, or AI solution.  
            Designed for clarity, elegance, and a world-class user experience.
        </div>
        <a href="#" class="hero-btn">Get Started</a>
    </div>

    <!-- PRODUCT CARDS -->
    <div class="product-grid">

        <div class="card">
            <div class="card-title">🚀 AI-Driven Insights</div>
            <div class="card-text">
                Use intelligent analytics powered by real-time data and AI automation.
            </div>
        </div>

        <div class="card">
            <div class="card-title">📊 Smart Dashboards</div>
            <div class="card-text">
                Monitor product metrics, KPIs, and critical business workflows effortlessly.
            </div>
        </div>

        <div class="card">
            <div class="card-title">⚙️ Automation Engine</div>
            <div class="card-text">
                Automate operations end-to-end with reliable, scalable, cloud-native tools.
            </div>
        </div>

    </div>

    <!-- NEXT STEPS -->
    <div class="steps">
        <div class="steps-title">Your Next Steps</div>
        <p style="color:#bcbcbc;">
            Follow these pathways to explore the platform, documentation, and advanced features.
        </p>

        <div class="steps-links">
            <a class="step-btn" href="#">📘 Documentation</a>
            <a class="step-btn" href="#">🧭 Product Tour</a>
            <a class="step-btn" href="#">📨 Contact Team</a>
            <a class="step-btn" href="#">⚡ Try Demo</a>
        </div>
    </div>

    <!-- FOOTER -->
    <div class="footer">
        © 2025 Premium Streamlit Experience — Designed with ❤️  
    </div>

</div>

</body>
</html>
"""

components.html(html_code, height=1500, scrolling=True)
