def generate_report(vulns, screenshots, diffs, pr_url):
    md = f"# AutoCTF - Autonomous Pentest Report\n\n"
    md += f"PR: {pr_url}\n\n"
    md += "## Vulnerabilities Found\n"
    for v in vulns:
        md += f"- {v['type']} on {v['endpoint']}\n"
    md += "\n## Proofs\n"
    for shot in screenshots:
        md += f"![poc]({shot})\n"
    md += "\n## Patches Applied\n```diff\n" + diffs + "\n```"
    return md