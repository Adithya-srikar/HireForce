import os
import httpx

GITHUB_API = "https://api.github.com"


async def fetch_github_profile(username: str) -> dict:
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=20.0) as client:
        profile_resp = await client.get(
            f"{GITHUB_API}/users/{username}", headers=headers
        )
        # If token causes auth failure, retry without it
        if profile_resp.status_code in (401, 403) and token:
            headers.pop("Authorization", None)
            profile_resp = await client.get(
                f"{GITHUB_API}/users/{username}", headers=headers
            )
        if profile_resp.status_code == 404:
            return {"error": f"GitHub user '{username}' not found", "username": username}
        if profile_resp.status_code != 200:
            return {
                "error": f"GitHub returned {profile_resp.status_code} for user '{username}'",
                "username": username,
            }
        profile = profile_resp.json()

        repos_resp = await client.get(
            f"{GITHUB_API}/users/{username}/repos",
            headers=headers,
            params={"sort": "updated", "per_page": 30, "type": "owner"},
        )
        repos = repos_resp.json() if repos_resp.status_code == 200 else []

        events_resp = await client.get(
            f"{GITHUB_API}/users/{username}/events/public",
            headers=headers,
            params={"per_page": 30},
        )
        events = events_resp.json() if events_resp.status_code == 200 else []

    processed_repos = []
    languages = {}
    total_stars = 0

    for repo in repos:
        if isinstance(repo, dict) and not repo.get("fork"):
            repo_data = {
                "name": repo.get("name"),
                "description": repo.get("description"),
                "language": repo.get("language"),
                "stars": repo.get("stargazers_count", 0),
                "forks": repo.get("forks_count", 0),
                "url": repo.get("html_url"),
                "updated_at": repo.get("updated_at"),
                "topics": repo.get("topics", []),
            }
            processed_repos.append(repo_data)

            if repo.get("language"):
                languages[repo["language"]] = languages.get(repo["language"], 0) + 1
            total_stars += repo.get("stargazers_count", 0)

    event_types = {}
    for event in events:
        if isinstance(event, dict):
            etype = event.get("type", "Unknown")
            event_types[etype] = event_types.get(etype, 0) + 1

    return {
        "username": username,
        "name": profile.get("name"),
        "bio": profile.get("bio"),
        "company": profile.get("company"),
        "location": profile.get("location"),
        "public_repos": profile.get("public_repos"),
        "followers": profile.get("followers"),
        "following": profile.get("following"),
        "avatar_url": profile.get("avatar_url"),
        "profile_url": profile.get("html_url"),
        "created_at": profile.get("created_at"),
        "repos": processed_repos,
        "languages": languages,
        "total_stars": total_stars,
        "recent_activity": event_types,
    }
