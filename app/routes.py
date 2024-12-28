import re
import requests
from bs4 import BeautifulSoup
from flask import Blueprint, request, jsonify, make_response
import openai
import os
from dotenv import load_dotenv

# Load environment variables for OpenAI API key
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

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

@main_bp.route('/api/generate_sop', methods=['POST', 'OPTIONS'])
def generate_sop():
    """Generate a formatted SOP document using OpenAI API based on user input."""
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json() or {}
    prompt = data.get("prompt", "").strip()  # User input (SOP request)

    if not prompt:
        return jsonify({"error": "The prompt is required."}), 400

    try:
       # Updated SOP generation prompt to ask OpenAI for Markdown-formatted output
        sop_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in generating well-structured SOPs in Markdown format."},
                {"role": "user", "content": f"Create a detailed and formatted SOP in Markdown based on the following prompt. Use appropriate Markdown syntax for headers (## for subheadings), bullet points, numbering, and bold. Use /n for line breaks so I can parse the response: ${prompt}"}
            ],
            max_tokens=1500,
            temperature=0.7
        )

        # Extract the generated SOP document from the response
        sop_document = sop_response.choices[0].message['content']

        return jsonify({
            "status": "success",
            "sop_document": sop_document
        }), 200

    except openai.Error as e:
        # Catch OpenAI specific errors and return a message
        return jsonify({"error": f"OpenAI API call failed: {str(e)}"}), 500
    except Exception as e:
        # Catch any other general errors
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500


# Health Check Route for your API
@main_bp.route('/api/health-check', methods=['GET'])
def health_check():
    """Health check endpoint to ensure the API is operational."""
    try:
        return jsonify({"status": "healthy"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
