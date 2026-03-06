def _truthy(val) -> bool:
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() == "true"


def print_summary(rows: list[dict]) -> None:
    healthy = 0
    needs_grooming = []
    artifact = 0
    legacy = 0
    maturity_counts: dict[str, int] = {}

    for row in rows:
        is_stale = _truthy(row.get("is_stale", False))
        has_either = _truthy(row.get("has_either", False))

        if not is_stale and has_either:
            healthy += 1
        elif not is_stale and not has_either:
            needs_grooming.append(row)
        elif is_stale and has_either:
            artifact += 1
        else:
            legacy += 1

        tier = row.get("test_maturity")
        if tier:
            maturity_counts[tier] = maturity_counts.get(tier, 0) + 1

    needs_grooming_count = len(needs_grooming)

    print("\n=== Agentic Grooming Summary ===\n")
    print(f"Active + has CLAUDE.md  : {healthy:3d} repos  (healthy)")
    print(f"Active + no CLAUDE.md   : {needs_grooming_count:3d} repos  (needs grooming)")
    print(f"Stale  + has CLAUDE.md  : {artifact:3d} repos  (possible artifact)")
    print(f"Stale  + no CLAUDE.md   : {legacy:3d} repos  (legacy/low-priority)")

    if maturity_counts:
        print("\n--- Test Maturity ---")
        for tier in ("measured", "automated", "has_tests", "none"):
            count = maturity_counts.get(tier, 0)
            print(f"  {tier:<12s}: {count:3d} repos")

    ranked = [
        r for r in needs_grooming
        if r.get("days_since_last_commit") is not None and r.get("days_since_last_commit") != ""
    ]
    ranked.sort(key=lambda r: int(r.get("recent_commit_count") or 0), reverse=True)
    top20 = ranked[:20]

    if top20:
        print("\n--- Top 20 Active Repos Needing CLAUDE.md ---")
        for i, row in enumerate(top20, 1):
            path = row.get("project_path", "")
            commits = row.get("recent_commit_count", 0)
            authors = row.get("unique_contributors_90d", 0)
            days = row.get("days_since_last_commit", "?")
            print(f"  {i:2d}. {path:<50s} ({commits} commits, {authors} authors, {days}d ago)")
