import requests
import openai
from config import Config


def check_adverse_media(business_name, business_url):
    """
    Check NewsAPI for articles mentioning the business name or URL and analyze their sentiment.
    """
    try:
        base_url = "https://newsapi.org/v2/everything"
        params = {
            "apiKey": Config.NEWSAPI_KEY,
            "q": f'"{business_name}" OR "{business_url}"',
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": 5,
        }
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])

        if articles:
            analyzed_articles = analyze_articles_sentiment(articles)
            return {
                "has_adverse_media": bool(analyzed_articles),
                "adverse_media_articles": analyzed_articles,
                "overall_adverse_score": calculate_overall_adverse_score(analyzed_articles),
            }
        return {"has_adverse_media": False, "adverse_media_articles": [], "overall_adverse_score": 0.0}
    except requests.RequestException as e:
        return {"error": f"NewsAPI request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to check adverse media: {str(e)}"}


def analyze_articles_sentiment(articles):
    """
    Analyze the sentiment of each article using OpenAI GPT.
    """
    analyzed_articles = []

    for article in articles:
        title = article.get("title", "")
        description = article.get("description", "")
        url = article.get("url", "")
        source = article.get("source", {}).get("name", "")
        published_at = article.get("publishedAt", "")

        # Skip articles with [Removed] or invalid data
        if title == "[Removed]" or description == "[Removed]":
            analyzed_articles.append({
                "title": title,
                "description": description,
                "url": url,
                "publishedAt": published_at,
                "source": source,
                "sentiment_score": None,
                "error": "Article content was removed or unavailable.",
            })
            continue

        sentiment_score = get_sentiment_score(title, description)

        if sentiment_score is not None:
            analyzed_articles.append({
                "title": title,
                "description": description,
                "url": url,
                "publishedAt": published_at,
                "source": source,
                "sentiment_score": sentiment_score,
            })
        else:
            analyzed_articles.append({
                "title": title,
                "description": description,
                "url": url,
                "publishedAt": published_at,
                "source": source,
                "sentiment_score": None,
                "error": "Failed to analyze sentiment after multiple attempts.",
            })

    return analyzed_articles


def get_sentiment_score(title, description, retries=3):
    """
    Fetch sentiment score using OpenAI GPT. Retry on failure.
    """
    prompt = (
        f"Analyze the following article for adverse sentiment and return a numerical score from 0.0 (not adverse) "
        f"to 1.0 (highly adverse). Respond with only the score:\n\n"
        f"Title: {title}\n"
        f"Description: {description}\n\n"
        "Adverse Sentiment Score:"
    )

    for attempt in range(retries):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a sentiment analysis assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.0,
            )
            sentiment_score = float(response.choices[0].message.content.strip())
            return max(0.0, min(1.0, sentiment_score))  # Ensure valid score
        except ValueError as ve:
            print(f"Invalid response on attempt {attempt + 1}: {ve}")
        except Exception as e:
            print(f"Failed to analyze sentiment on attempt {attempt + 1}: {e}")

    return None  # Return None if all attempts fail


def calculate_overall_adverse_score(analyzed_articles):
    """
    Calculate the overall adverse score as the average of valid article sentiment scores.
    """
    valid_scores = [article["sentiment_score"] for article in analyzed_articles if article.get("sentiment_score") is not None]
    if not valid_scores:
        return 0.0
    return sum(valid_scores) / len(valid_scores)
