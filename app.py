import io
import os
import html
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from flask import Flask, request, send_file, abort
from playwright.sync_api import sync_playwright
from PIL import Image

app = Flask(__name__)

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "templates", "yyc-news-card-dusk.html")
with open(TEMPLATE_PATH, encoding="utf-8") as f:
    TEMPLATE = f.read()

OUT = 1080          # final published square size
SCALE = 2           # supersample factor, then downscale for crisp text
DEFAULT_FOOTER = "Full report in comments \u00b7 yycrentalstudio.ca"
try:
    TZ = ZoneInfo("America/Edmonton")
except Exception:
    TZ = timezone(timedelta(hours=-6))


def headline_size(text):
    n = len(text)
    if n <= 45:
        return 72
    if n <= 65:
        return 64
    if n <= 85:
        return 56
    return 50


def build_html(headline, source, date, footer):
    page = TEMPLATE
    page = page.replace("{{HEADLINE}}", html.escape(headline))
    page = page.replace("{{SOURCE}}", html.escape(source))
    page = page.replace("{{DATE}}", html.escape(date))
    page = page.replace("{{FOOTER}}", html.escape(footer))
    fs = headline_size(headline)
    page = page.replace("</style>", ".headline{font-size:%dpx}</style>" % fs)
    return page


def render_png(html_str):
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page(
            viewport={"width": OUT, "height": OUT},
            device_scale_factor=SCALE,
        )
        page.set_content(html_str, wait_until="networkidle")
        page.evaluate("async () => { await document.fonts.ready; }")
        el = page.query_selector("#card")
        raw = el.screenshot(type="png")
        browser.close()
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    if img.size != (OUT, OUT):
        img = img.resize((OUT, OUT), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


@app.route("/health")
def health():
    return {"ok": True}


@app.route("/dusk")
def dusk():
    headline = request.args.get("headline", "").strip()
    if not headline:
        abort(400, "headline is required")
    source = request.args.get("source", "").strip()
    footer = request.args.get("footer", DEFAULT_FOOTER).strip() or DEFAULT_FOOTER
    date = request.args.get("date", "").strip()
    if not date:
        now = datetime.now(TZ)
        date = now.strftime("%A \u00b7 %B ") + str(now.day)
    png = render_png(build_html(headline, source, date, footer))
    return send_file(png, mimetype="image/png", download_name="yyc-card.png")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
