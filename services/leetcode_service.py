import httpx

LEETCODE_API = "https://leetcode-api-faisalshohag.vercel.app"


async def fetch_leetcode_profile(username: str) -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        try:
            resp = await client.get(f"{LEETCODE_API}/{username}")

            if resp.status_code != 200:
                return {
                    "error": f"Failed to fetch LeetCode profile for '{username}'",
                    "username": username,
                }

            data = resp.json()

            if not data or data.get("errors"):
                return {"error": f"LeetCode user '{username}' not found", "username": username}

            total_solved = data.get("totalSolved", 0)
            easy_solved = data.get("easySolved", 0)
            medium_solved = data.get("mediumSolved", 0)
            hard_solved = data.get("hardSolved", 0)

            total_easy = data.get("totalEasy", 0)
            total_medium = data.get("totalMedium", 0)
            total_hard = data.get("totalHard", 0)
            total_questions = data.get("totalQuestions", 0)

            recent = []
            for sub in data.get("recentSubmissions", [])[:15]:
                recent.append({
                    "title": sub.get("title"),
                    "status": sub.get("statusDisplay"),
                    "language": sub.get("lang"),
                    "timestamp": sub.get("timestamp"),
                })

            submission_calendar = data.get("submissionCalendar", {})
            active_days = len(submission_calendar) if isinstance(submission_calendar, dict) else 0

            return {
                "username": username,
                "ranking": data.get("ranking"),
                "reputation": data.get("reputation", 0),
                "contribution_points": data.get("contributionPoint", 0),
                "total_solved": total_solved,
                "total_questions": total_questions,
                "easy_solved": easy_solved,
                "total_easy": total_easy,
                "medium_solved": medium_solved,
                "total_medium": total_medium,
                "hard_solved": hard_solved,
                "total_hard": total_hard,
                "acceptance_rate": round(total_solved / total_questions * 100, 1) if total_questions else 0,
                "recent_submissions": recent,
                "active_days": active_days,
            }
        except Exception as e:
            return {"error": str(e), "username": username}
