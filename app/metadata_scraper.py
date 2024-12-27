import openai
import json
from app.default_categories import get_default_categories

def categorize_and_summarize(domain, metadata, homepage_content, categories=None):
    """
    Categorize the business and generate a summary using OpenAI.
    """
    # Use default categories if none provided
    if not categories:
        categories = get_default_categories()

    prompt = (
        f"Domain: {domain}\n"
        f"Metadata: {metadata}\n"
        f"Homepage Content (truncated to 1000 chars): {homepage_content[:1000]}\n\n"
        "You must choose exactly one category from the list below. Use only the categories provided:\n"
        f"{', '.join(categories)}\n\n"
        "Additionally, provide a two-sentence summary of the business and the product/service it offers.\n"
        "Assign a confidence score (from 0.0 to 1.0) indicating how certain you are about the selected category.\n"
        "Respond with valid JSON only in this exact format:\n"
        "{\n"
        "  \"category\": \"ChosenCategory\",\n"
        "  \"summary\": \"Two-sentence summary here.\",\n"
        "  \"category_confidence_score\": 0.85\n"
        "}"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that responds only in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.5,
        )

        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        raise ValueError("OpenAI did not return valid JSON.")
    except Exception as e:
        raise ValueError(f"OpenAI API call failed: {str(e)}")
