import re
import requests
from bs4 import BeautifulSoup
from flask import Blueprint, request, jsonify, make_response

# Sample valid API keys for testing
VALID_KEYS = {
    "staging_api_key_12345abcde67890xyz": "staging_secret_key_abcd1234xyz7890qwe",
    "staging_api_key_zxcvbnm09876lkjhg": "staging_secret_key_qwerty12345asdfghjkl"
}

def validate_api_keys(api_key, secret_key):
    """Validate the API key and secret key."""
    if api_key not in VALID_KEYS or VALID_KEYS[api_key] != secret_key:
        return False
    return True

def scrape_website_metadata(domain):
    """Scrape metadata, phone numbers, emails, and social links from a given domain."""
    for scheme in ["http://", "https://"]:
        url = f"{scheme}{domain}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            metadata = {
                "title": soup.title.string if soup.title else "No title found",
                "description": "",
                "keywords": "",
                "phoneNumbers": [],
                "emails": [],
                "socialMediaLinks": [],
            }

            # Extract description and keywords
            desc_tag = soup.find("meta", attrs={"name": "description"})
            if desc_tag and "content" in desc_tag.attrs:
                metadata["description"] = desc_tag["content"]

            keywords_tag = soup.find("meta", attrs={"name": "keywords"})
            if keywords_tag and "content" in keywords_tag.attrs:
                metadata["keywords"] = keywords_tag["content"]

            # Extract phone numbers
            phone_numbers = re.findall(r"\+?\d[\d\s().-]{7,}\d", soup.get_text())
            metadata["phoneNumbers"] = list(set(phone_numbers))

            # Extract emails
            emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", soup.get_text())
            metadata["emails"] = list(set(emails))

            # Extract social media links
            social_links = [
                a_tag["href"] for a_tag in soup.find_all("a", href=True)
                if any(social in a_tag["href"] for social in ["facebook.com", "twitter.com", "linkedin.com", "instagram.com"])
            ]
            metadata["socialMediaLinks"] = list(set(social_links))

            return metadata
        except requests.RequestException as e:
            print(f"RequestException while fetching {url}: {e}")
            continue

    raise ValueError(f"Could not fetch metadata for domain: {domain}")

main_bp = Blueprint('main', __name__)

@main_bp.before_request
def require_api_keys():
    """Validate API keys for every request except health check route."""
    if request.endpoint == 'main.health_check':  # Skip API key validation for health check route
        return None

    if request.method == "OPTIONS":
        return make_response()
    api_key = request.headers.get("X-API-Key")
    secret_key = request.headers.get("X-Secret-Key")
    if not api_key or not secret_key or not validate_api_keys(api_key, secret_key):
        return jsonify({"error": "Invalid API key or secret key"}), 403

@main_bp.after_request
def add_cors_headers(response):
    """Add CORS headers to every response."""
    response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key, X-Secret-Key"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

@main_bp.route('/api/scrape_metadata', methods=['POST', 'OPTIONS'])
def scrape_metadata():
    from app.ai_category_service import categorize_and_summarize, calculate_high_risk_similarity
    from app.utils import parse_or_strip, fetch_whois_data
    from app.default_categories import get_default_categories
    from app.adverse_media_service import check_adverse_media

    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json() or {}
    input_string = data.get("input_string", "").strip()
    custom_categories = data.get("custom_categories", [])
    custom_high_risk_categories = data.get("custom_high_risk_categories", [])
    include_whois = data.get("include_whois", False)
    include_adverse_media = data.get("include_adverse_media", True)
    selected_fields = data.get("selected_fields", {})

    if not input_string:
        return jsonify({"error": "input_string is required"}), 400

    input_type, domain = parse_or_strip(input_string)

    try:
        # Step 1: Scrape website metadata
        metadata = scrape_website_metadata(domain)
        homepage_content = metadata.get("description", "")

        # Step 2: Categorize and summarize
        ai_response = categorize_and_summarize(domain, metadata, homepage_content, custom_categories)

        # Step 3: Calculate high-risk similarity
        high_risk_categories = custom_high_risk_categories or get_default_categories()
        high_risk_similarity_score = calculate_high_risk_similarity(ai_response["category"], high_risk_categories)
        ai_response["high_risk_similarity_score"] = high_risk_similarity_score

        # Step 4: Prepare full response
        response = {
            "type": input_type,
            "domain": domain,
            "metadata": metadata,
            "ai_response": ai_response,
        }

        if include_whois:
            response["whois_data"] = fetch_whois_data(domain)

        if include_adverse_media:
            business_name = domain.split('.')[0]
            adverse_media_result = check_adverse_media(business_name, domain)
            response["adverse_media"] = adverse_media_result

        # Step 5: Filter response based on selected fields
        def filter_fields(data, allowed_fields):
            if isinstance(data, dict):
                return {key: filter_fields(value, allowed_fields) for key, value in data.items() if allowed_fields.get(key, True)}
            return data

        filtered_response = filter_fields(response, selected_fields)

        return jsonify(filtered_response), 200
    except Exception as e:
        print(f"Error processing request: {e}")  # Debugging log
        return jsonify({"error": str(e)}), 500


# Health Check Route
@main_bp.route('/api/health-check', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
