import os
import re
import httpx

APIFY_ACTOR = "supreme_coder~linkedin-profile-scraper"
APIFY_URL = f"https://api.apify.com/v2/acts/{APIFY_ACTOR}/run-sync-get-dataset-items"


async def fetch_linkedin_profile(url: str) -> dict:
    username = None
    match = re.search(r"linkedin\.com/in/([a-zA-Z0-9_-]+)", url)
    if match:
        username = match.group(1)

    if not username:
        return {"error": "Invalid LinkedIn URL", "url": url}

    profile_url = f"https://www.linkedin.com/in/{username}/"
    token = os.getenv("APIFY_TOKEN")

    if not token:
        return {
            "error": "APIFY_TOKEN not set in .env — cannot scrape LinkedIn",
            "username": username,
            "profile_url": profile_url,
        }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                APIFY_URL,
                params={"token": token},
                json={"urls": [{"url": profile_url}]},
                headers={"Content-Type": "application/json"},
            )

            if resp.status_code not in (200, 201):
                body = resp.text[:300]
                return {
                    "error": f"Apify returned {resp.status_code}: {body}",
                    "username": username,
                    "profile_url": profile_url,
                }

            items = resp.json()
            if not items or not isinstance(items, list) or len(items) == 0:
                return {
                    "error": "No data returned from LinkedIn scraper",
                    "username": username,
                    "profile_url": profile_url,
                }

            return _parse_profile(items[0], username, profile_url)

    except Exception as e:
        return {"error": f"Apify error: {e}", "username": username, "profile_url": profile_url}


def _parse_profile(raw: dict, username: str, profile_url: str) -> dict:
    """Normalise supreme_coder/linkedin-profile-scraper output."""

    # --- Experiences ---
    experiences = []
    for pos in raw.get("positions", []):
        company_info = pos.get("company") or {}
        company_name = company_info.get("name") if isinstance(company_info, dict) else str(company_info)

        tp = pos.get("timePeriod") or {}
        start_y = (tp.get("startDate") or {}).get("year", "")
        end_y = (tp.get("endDate") or {}).get("year", "Present")

        experiences.append({
            "title": pos.get("title"),
            "company": company_name,
            "duration": pos.get("totalDuration") or (f"{start_y}–{end_y}" if start_y else ""),
            "location": pos.get("locationName"),
            "description": (pos.get("description") or "")[:300],
        })

    # --- Education ---
    education = []
    for edu in raw.get("educations", []):
        school_name = edu.get("schoolName")
        if not school_name:
            school_info = edu.get("school") or {}
            school_name = school_info.get("name") if isinstance(school_info, dict) else str(school_info)

        tp = edu.get("timePeriod") or {}
        start = (tp.get("startDate") or {}).get("year", "")
        end = (tp.get("endDate") or {}).get("year", "")
        duration = f"{start}–{end}" if start else edu.get("totalDuration", "")

        education.append({
            "school": school_name,
            "degree": edu.get("degreeName") or None,
            "field": edu.get("fieldOfStudy") or None,
            "duration": duration,
        })

    # --- Skills ---
    skills_raw = raw.get("skills", [])
    skills = []
    for s in skills_raw:
        if isinstance(s, dict):
            skills.append(s.get("name") or s.get("skill") or "")
        elif isinstance(s, str):
            skills.append(s)

    # --- Certifications ---
    certifications = []
    for cert in raw.get("certifications", []):
        if isinstance(cert, dict):
            certifications.append(cert.get("name", ""))
        else:
            certifications.append(str(cert))

    # --- Languages ---
    languages = []
    for lang in raw.get("languages", []):
        if isinstance(lang, dict):
            languages.append(lang.get("name", ""))
        else:
            languages.append(str(lang))

    # --- Projects ---
    projects = []
    for proj in raw.get("projects", []):
        if isinstance(proj, dict):
            projects.append({
                "title": proj.get("title"),
                "description": (proj.get("description") or "")[:200],
            })

    # --- Creator hashtags / topics ---
    creator_info = raw.get("creatorInfo") or {}
    hashtags = creator_info.get("hashTags", [])

    return {
        "username": username,
        "profile_url": profile_url,
        "name": f"{raw.get('firstName', '')} {raw.get('lastName', '')}".strip(),
        "headline": raw.get("headline"),
        "summary": raw.get("summary"),
        "location": raw.get("geoLocationName"),
        "country": raw.get("geoCountryName"),
        "avatar_url": raw.get("pictureUrl"),
        "cover_url": raw.get("coverImageUrl"),
        "followers": raw.get("followerCount"),
        "connections": raw.get("connectionsCount"),
        "is_creator": raw.get("creator", False),
        "is_influencer": raw.get("influencer", False),
        "is_premium": raw.get("premium", False),
        "current_company": raw.get("companyName"),
        "job_title": raw.get("jobTitle"),
        "experiences": experiences,
        "education": education,
        "skills": skills[:25],
        "certifications": certifications[:10],
        "languages": languages,
        "projects": projects[:10],
        "hashtags": hashtags,
    }
