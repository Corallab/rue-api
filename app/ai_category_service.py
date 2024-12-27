import openai
import json
from app.default_categories import get_default_categories

def categorize_and_summarize(domain, metadata, homepage_content, user_categories=None):
    """
    Categorize the business and generate a summary using OpenAI.
    """
    categories = user_categories or get_default_categories()

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


def calculate_high_risk_similarity(ai_category, high_risk_categories):
    """
    Calculate the similarity score of the AI-generated category against high-risk categories.
    """
    prompt = (
        f"AI-Generated Category: {ai_category}\n"
        f"High-Risk Categories: {', '.join(high_risk_categories)}\n\n"
        "Determine the similarity of the AI-generated category to each high-risk category. "
        "Provide a similarity score (from 0.0 to 1.0) for the closest match.\n"
        "If the AI-generated category exactly matches one of the high-risk categories, the score should be 1.0.\n"
        "Respond with valid JSON only in this exact format:\n"
        "{\n"
        "  \"high_risk_similarity_score\": 0.8\n"
        "}"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that responds only in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.5,
        )

        return json.loads(response.choices[0].message.content)["high_risk_similarity_score"]
    except json.JSONDecodeError:
        raise ValueError("OpenAI did not return valid JSON for high-risk similarity score.")
    except Exception as e:
        raise ValueError(f"OpenAI API call failed: {str(e)}")
