import re
import whois

def parse_or_strip(input_string):
    """Determine if input is an email or a domain and extract the domain part."""
    if "@" in input_string:
        return "email", input_string.split("@")[-1]
    pattern = re.compile(r"https?://(www\.)?")
    domain = pattern.sub("", input_string).split("/")[0]
    return "domain", domain

def fetch_whois_data(domain):
    """Fetch WHOIS information for a domain."""
    try:
        domain_info = whois.whois(domain)
        return {
            "creation_date": str(domain_info.creation_date),
            "last_updated": str(domain_info.updated_date),
            "expiration_date": str(domain_info.expiration_date),
            "registrar": domain_info.registrar,
            "name_servers": domain_info.name_servers,
        }
    except Exception as e:
        return {"error": f"WHOIS lookup failed: {str(e)}"}
