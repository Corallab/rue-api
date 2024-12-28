import openai
import json
from flask import Blueprint, request, jsonify
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI API Key from environment variables
openai.api_key = os.getenv('OPENAI_API_KEY')

# Blueprint for your API
main_bp = Blueprint('main', __name__)

@main_bp.route('/api/generate_sop', methods=['POST'])
def generate_sop():
    """Generate a formatted SOP document using OpenAI API based on user input."""
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json() or {}
    prompt = data.get("prompt", "").strip()  # User input (SOP request)

    if not prompt:
        return jsonify({"error": "The prompt is required."}), 400

    try:
        # OpenAI GPT model to generate SOP document based on the input prompt
        sop_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in generating well-structured SOPs for businesses."},
                {"role": "user", "content": f"Create a detailed and formatted SOP based on the following prompt: {prompt}"}
            ],
            max_tokens=1000,
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

# Example of loading OpenAI API key from environment
class Config:
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    @classmethod
    def validate(cls):
        """Validate required environment variables."""
        required_vars = ['OPENAI_API_KEY']
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Initialize and validate the configuration
Config.validate()
