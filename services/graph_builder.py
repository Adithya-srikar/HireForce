def build_knowledge_graph(
    github_data: dict, leetcode_data: dict, linkedin_data: dict, resume_text: str = ""
) -> dict:
    nodes = []
    edges = []
    node_id = 0

    def add_node(label, group, title="", size=25, extra=None):
        nonlocal node_id
        node_id += 1
        node = {
            "id": node_id,
            "label": label,
            "group": group,
            "title": title or label,
            "size": size,
        }
        if extra:
            node.update(extra)
        nodes.append(node)
        return node_id

    def add_edge(from_id, to_id, label="", width=1):
        edges.append({"from": from_id, "to": to_id, "label": label, "width": width})

    candidate_name = "Candidate"
    if github_data and not github_data.get("error") and github_data.get("name"):
        candidate_name = github_data["name"]
    elif linkedin_data and not linkedin_data.get("error") and linkedin_data.get("name"):
        candidate_name = linkedin_data["name"]

    candidate_id = add_node(candidate_name, "candidate", "Candidate Profile", size=50)

    # --- GitHub ---
    if github_data and not github_data.get("error"):
        gh_id = add_node(
            "GitHub", "github", f"@{github_data.get('username', '')}", size=38
        )
        add_edge(candidate_id, gh_id, "", width=3)

        stats_title = (
            f"Repos: {github_data.get('public_repos', 0)} | "
            f"Stars: {github_data.get('total_stars', 0)} | "
            f"Followers: {github_data.get('followers', 0)}"
        )
        stats_id = add_node("Overview", "stats", stats_title, size=20)
        add_edge(gh_id, stats_id)

        for lang, count in sorted(
            github_data.get("languages", {}).items(), key=lambda x: -x[1]
        ):
            lang_id = add_node(
                lang, "skill", f"{lang}: {count} repos", size=14 + min(count * 4, 16)
            )
            add_edge(gh_id, lang_id, f"{count}")

        for repo in github_data.get("repos", [])[:8]:
            desc = repo.get("description") or "No description"
            title = f"{repo['name']}\n★ {repo.get('stars', 0)} | {desc[:80]}"
            repo_id = add_node(repo["name"], "repo", title, size=17)
            add_edge(gh_id, repo_id)

            for topic in repo.get("topics", [])[:3]:
                existing = next((n for n in nodes if n["label"] == topic), None)
                if existing:
                    add_edge(repo_id, existing["id"])
                else:
                    topic_id = add_node(topic, "topic", topic, size=11)
                    add_edge(repo_id, topic_id)

    # --- LeetCode ---
    if leetcode_data and not leetcode_data.get("error"):
        lc_id = add_node(
            "LeetCode", "leetcode", f"@{leetcode_data.get('username', '')}", size=38
        )
        add_edge(candidate_id, lc_id, "", width=3)

        total = leetcode_data.get("total_solved", 0)
        easy = leetcode_data.get("easy_solved", 0)
        medium = leetcode_data.get("medium_solved", 0)
        hard = leetcode_data.get("hard_solved", 0)
        total_q = leetcode_data.get("total_questions", 0)

        solved_title = f"Solved {total}/{total_q}" if total_q else f"Solved: {total}"
        total_id = add_node(solved_title, "lc_total", solved_title, size=24)
        add_edge(lc_id, total_id)

        if easy:
            te = leetcode_data.get("total_easy", 0)
            eid = add_node(f"Easy: {easy}/{te}", "lc_easy", f"Easy: {easy}/{te}", size=16)
            add_edge(total_id, eid)
        if medium:
            tm = leetcode_data.get("total_medium", 0)
            mid = add_node(f"Med: {medium}/{tm}", "lc_medium", f"Medium: {medium}/{tm}", size=16)
            add_edge(total_id, mid)
        if hard:
            th = leetcode_data.get("total_hard", 0)
            hid = add_node(f"Hard: {hard}/{th}", "lc_hard", f"Hard: {hard}/{th}", size=16)
            add_edge(total_id, hid)

        if leetcode_data.get("ranking"):
            rid = add_node(
                f"Rank #{leetcode_data['ranking']:,}",
                "stats",
                f"Global ranking: #{leetcode_data['ranking']:,}",
                size=15,
            )
            add_edge(lc_id, rid)

    # --- LinkedIn ---
    if linkedin_data and not linkedin_data.get("error"):
        li_id = add_node(
            "LinkedIn",
            "linkedin",
            linkedin_data.get("name") or linkedin_data.get("username", ""),
            size=38,
        )
        add_edge(candidate_id, li_id, "", width=3)

        if linkedin_data.get("headline"):
            hl = linkedin_data["headline"]
            hl_id = add_node(hl[:40], "experience", hl, size=17)
            add_edge(li_id, hl_id, "headline")

        if linkedin_data.get("summary"):
            s = linkedin_data["summary"]
            sid = add_node("About", "info", s[:250], size=15)
            add_edge(li_id, sid)

        for exp in linkedin_data.get("experiences", [])[:5]:
            title = exp.get("title") or "Role"
            company = exp.get("company") or ""
            label = f"{title[:25]}"
            tip = f"{title} @ {company}" if company else title
            exp_id = add_node(label, "experience", tip, size=15)
            add_edge(li_id, exp_id, company[:20] if company else "")

        for skill in linkedin_data.get("skills", [])[:10]:
            s = skill if isinstance(skill, str) else str(skill)
            existing = next((n for n in nodes if n["label"] == s), None)
            if existing:
                add_edge(li_id, existing["id"])
            else:
                sk_id = add_node(s, "skill", s, size=13)
                add_edge(li_id, sk_id)

        for edu in linkedin_data.get("education", [])[:3]:
            school = edu.get("school") or "School"
            degree = edu.get("degree") or ""
            label = school[:25]
            tip = f"{degree} — {school}" if degree else school
            edu_id = add_node(label, "info", tip, size=14)
            add_edge(li_id, edu_id, "education")

        for proj in linkedin_data.get("projects", [])[:5]:
            title = proj.get("title") or "Project"
            pn_id = add_node(title[:25], "repo", (proj.get("description") or title)[:150], size=14)
            add_edge(li_id, pn_id, "project")

        for tag in linkedin_data.get("hashtags", [])[:6]:
            t = tag.lstrip("#")
            existing = next((n for n in nodes if n["label"] == t), None)
            if existing:
                add_edge(li_id, existing["id"])
            else:
                tid = add_node(t, "topic", tag, size=11)
                add_edge(li_id, tid)

    return {"nodes": nodes, "edges": edges}
