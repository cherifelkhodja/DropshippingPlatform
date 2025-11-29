"""Mock HTTP server for integration tests.

Serves mock responses for sitemap and HTML scraping tests.
"""

from flask import Flask, Response

app = Flask(__name__)

SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap>
    <loc>http://localhost:8080/sitemap_products_1.xml</loc>
  </sitemap>
  <sitemap>
    <loc>http://localhost:8080/sitemap_pages.xml</loc>
  </sitemap>
</sitemapindex>
"""

SITEMAP_PRODUCTS = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>http://localhost:8080/products/product-1</loc></url>
  <url><loc>http://localhost:8080/products/product-2</loc></url>
  <url><loc>http://localhost:8080/products/product-3</loc></url>
  <url><loc>http://localhost:8080/products/product-4</loc></url>
  <url><loc>http://localhost:8080/products/product-5</loc></url>
</urlset>
"""

SITEMAP_PAGES = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>http://localhost:8080/about</loc></url>
  <url><loc>http://localhost:8080/contact</loc></url>
</urlset>
"""

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Test Store</title>
    <meta name="generator" content="Shopify">
</head>
<body>
    <h1>Welcome to Test Store</h1>
    <p>This is a mock Shopify store for testing.</p>
    <script src="https://cdn.shopify.com/s/shopify.js"></script>
</body>
</html>
"""

PRODUCT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Product - Test Store</title>
</head>
<body>
    <h1>Test Product</h1>
    <p class="price">$29.99</p>
    <button>Add to Cart</button>
</body>
</html>
"""


@app.route("/")
def index() -> str:
    return INDEX_HTML


@app.route("/sitemap.xml")
def sitemap_index() -> Response:
    return Response(SITEMAP_INDEX, mimetype="application/xml")


@app.route("/sitemap_products_1.xml")
def sitemap_products() -> Response:
    return Response(SITEMAP_PRODUCTS, mimetype="application/xml")


@app.route("/sitemap_pages.xml")
def sitemap_pages() -> Response:
    return Response(SITEMAP_PAGES, mimetype="application/xml")


@app.route("/products/<product_id>")
def product(product_id: str) -> str:
    return PRODUCT_HTML


@app.route("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
