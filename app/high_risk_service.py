import os

def get_default_high_risk_categories():
    """Read default high-risk categories from a text file."""
    file_path = os.path.join(os.path.dirname(__file__), '../default_high_risk_categories.txt')
    try:
        with open(file_path, 'r') as file:
            return [line.strip() for line in file if line.strip()]
    except Exception as e:
        raise ValueError(f"Error reading default high-risk categories: {str(e)}")

def is_high_risk_category(category, custom_high_risk_categories=None):
    """
    Check if a given category is high-risk.
    If custom high-risk categories are provided, use them; otherwise, use the default.
    """
    high_risk_categories = custom_high_risk_categories or get_default_high_risk_categories()
    return category in high_risk_categories
