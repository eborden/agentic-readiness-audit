# MR: Initial commit — claude-md-audit tool

## What

- Introduces a CLI tool that scans all GitLab group projects and checks for the presence of `CLAUDE.md` / `AGENTS.md` at the repository root
- Captures commit activity signals per repo (last commit date, 90-day commit count, unique contributors) to distinguish active vs stale repos
- Outputs a CSV of every project's status and prints a prioritised console summary categorising repos as healthy, needing grooming, artifact, or legacy
- Packages the tool in a Docker image for consistent, portable execution

## Why

- As we roll out agentic coding practices across engineering, we need visibility into which repos already have agent context files and which active repos should get them next
- Combining file-presence checks with activity data lets us prioritise grooming effort on repos that are actually being worked on, rather than applying effort uniformly across hundreds of projects
