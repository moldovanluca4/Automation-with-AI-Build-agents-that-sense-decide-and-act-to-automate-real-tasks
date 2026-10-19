from urllib.parse import urlsplit


def hostname_matches(url, domains):
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
            return False
        host = (parsed.hostname or "").lower().rstrip(".")
        return any(host == domain or host.endswith("." + domain) for domain in domains)
    except (TypeError, ValueError):
        return False


def is_linkedin_url(url, company_only=False):
    if not hostname_matches(url, ["linkedin.com"]):
        return False
    return not company_only or urlsplit(url).path.startswith(("/company/", "/school/"))
