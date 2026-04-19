#!/usr/bin/env python3
"""
run.py — Specter UI: Autonomous Visual Auditor & Refactor Swarm
"""
import os
import sys
import json
import time
import subprocess
import shutil
import click
import threading
import webbrowser
import re
import base64
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from github import Github, Auth
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
import anthropic

# Import our new vision engine
import core.vision as vision

console = Console()
load_dotenv()

WORKSPACE = Path(__file__).parent / "workspace"

def get_repo_name(repo_url: str) -> str:
    url = repo_url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    return url.split("github.com/")[-1]

def git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()

def _start_dashboard_server(state_file: Path):
    """Start the dashboard server in a background thread."""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        import ui.server as srv
        t = threading.Thread(
            target=srv.start, args=(state_file,), daemon=True
        )
        t.start()
        threading.Timer(1.5, lambda: webbrowser.open("http://localhost:8765")).start()
    except Exception as e:
        console.print(f"[yellow]⚠️ Could not start dashboard: {e}[/yellow]")

def update_state(state_file: Path, **kwargs):
    state = {}
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text())
        except:
            pass
    state.update(kwargs)
    state_file.write_text(json.dumps(state, indent=2))

def perform_visual_audit(url: str, snapshot_path: Path, state_file: Path):
    """
    Uses Claude 3.5 Sonnet to 'look' at the snapshot and provide a UX critique.
    """
    console.print(f"\n[bold magenta]👁️  Specter is auditing visuals for {url}...[/bold magenta]")
    update_state(state_file, status="visual_auditing", log=[{"time": datetime.now().strftime("%H:%M:%S"), "agent": "Specter-Vision", "msg": f"Performing visual audit on {url}"}])
    
    # Capture snapshot
    vision.sync_capture_screenshot(url, snapshot_path)
    
    # Display snapshot in dashboard
    rel_snapshot = str(snapshot_path).split("workspace/")[-1]
    update_state(state_file, snapshot_url=f"/workspace/{rel_snapshot}")

    # Initialize Anthropic for Vision
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    # Read image as base64
    with open(snapshot_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    prompt = """Analyze this UI screenshot. 
    1. Identify any visual bugs (misalignment, overlapping elements, broken images).
    2. Suggest 3 specific 'Premium/WOW' improvements (e.g., adding glassmorphism, improving typography, adding glows or gradients).
    3. Be concise and focus on actionable engineering feedback."""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )
        
        critique = message.content[0].text
        console.print(f"\n[bold cyan]💎 Specter Audit Result:[/bold cyan]\n{critique}")
        update_state(state_file, critique=critique, log=[{"time": datetime.now().strftime("%H:%M:%S"), "agent": "Specter-Vision", "msg": "Audit complete: Identified premium polish opportunities"}])
        return critique
    except Exception as e:
        console.print(f"[bold red]❌ Vision Audit Failed: {e}[/bold red]")
        return "Audit failed. Proceeding with standard coding task."

def parse_claude_stream(process, state_file: Path):
    logs = []
    def log_to_state(agent, msg):
        time_str = datetime.now().strftime("%H:%M:%S")
        logs.append({"time": time_str, "agent": agent, "msg": msg})
        update_state(state_file, log=logs)

    for line in iter(process.stdout.readline, ""):
        if not line: break
        try:
            data = json.loads(line)
        except json.JSONDecodeError: continue

        if data.get("type") == "assistant" and "message" in data:
            for item in data["message"].get("content", []):
                if item.get("type") == "text":
                    text = item.get("text", "").strip()
                    if text:
                        console.print(f"[dim]{text}[/dim]")
                        log_to_state("Omni-Agent", text[:100] + ("..." if len(text) > 100 else ""))
                elif item.get("type") == "tool_use":
                    tool = item.get("name")
                    tool_input = item.get("input", {})
                    detail = f": {tool_input.get('command') or tool_input.get('path') or tool_input.get('query') or ''}"
                    console.print(f"[bold magenta]🛠️  Tool: {tool}[/bold magenta][magenta]{detail}[/magenta]")
                    log_to_state("Omni-Agent", f"Tool: {tool}{detail}")
        elif data.get("type") == "result":
            console.print(f"[bold green]✅ Agent cycle completed[/bold green]")
            log_to_state("Omni-Agent", "Finished cycle")

@click.command()
@click.option("--repo", "-r", help="GitHub repository URL")
@click.option("--task", "-t", help="Task description")
@click.option("--url", "-u", help="Direct URL to audit (optional)")
@click.option("--reviewer", "-R", help="GitHub username to assign reviewer")
def main(repo, task, url, reviewer):
    console.print(Panel.fit(
        "[bold cyan]👁️ SPECTER UI — Visual Auditor Swarm[/bold cyan]\n"
        "[dim]Enter details below. Specter will 'see' the app and fix it.[/dim]",
        border_style="cyan"
    ))

    if not repo: repo = Prompt.ask("[bold blue]📦 GitHub Repo URL[/bold blue]")
    if not task: task = Prompt.ask("[bold yellow]🎯 Your Task (e.g. 'Make the UI more premium')[/bold yellow]")
    if not url: url = Prompt.ask("[bold magenta]🌐 Live URL to audit[/bold magenta] [dim](optional)[/dim]", default="")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    gh_token = os.environ.get("GITHUB_TOKEN", "")

    if not api_key or not gh_token:
        console.print("[bold red]❌ API keys missing in .env[/bold red]"); sys.exit(1)

    repo_name = get_repo_name(repo)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = WORKSPACE / f"specter_{repo_name.split('/')[-1]}_{run_id}"
    repo_dir = run_dir / "repo"
    state_file = run_dir / "state.json"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    update_state(state_file, task=task, repo_url=repo, status="init", started_at=datetime.utcnow().isoformat())
    _start_dashboard_server(state_file)

    # 1. Clone
    console.print(f"\n[cyan]📦 Cloning {repo}...[/cyan]")
    clone_url = repo.replace("https://", f"https://{gh_token}@")
    subprocess.run(["git", "clone", clone_url, str(repo_dir)], check=True, stdout=subprocess.DEVNULL)

    # 2. Visual Audit (Only if URL is provided)
    critique = ""
    if url:
        snapshot_path = run_dir / "audit_snapshot.png"
        critique = perform_visual_audit(url, snapshot_path, state_file)

    # 3. Hand off to Claude Code CLI
    console.print("\n[magenta]🧠 Launching Spectral Refactor...[/magenta]\n")
    update_state(state_file, status="refactoring")
    
    spectral_prompt = f"""You are Specter UI. 
You are performing this task: {task}

CRITICAL VISUAL FEEDBACK:
{critique if critique else "No visual snapshot provided. Focus on standard engineering."}

Improve the aesthetics and resolve any issues found. Test your changes. Branch name should start with 'spectral-fix/'."""

    claude_bin = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude")
    process = subprocess.Popen(
        [claude_bin, "--print", "--dangerously-skip-permissions", "--effort", "medium", 
         "--model", "claude-3-5-haiku-20241022", "--output-format", "stream-json", spectral_prompt],
        cwd=str(repo_dir), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    parse_claude_stream(process, state_file)
    process.wait()

    # 4. Commit & PR
    status_str = git(["status", "--porcelain"], repo_dir)
    if not status_str:
        console.print("[yellow]⚠️ No visual changes applied.[/yellow]"); update_state(state_file, status="done"); sys.exit(0)

    branch_name = f"spectral-fix/{run_id}"
    git(["checkout", "-b", branch_name], repo_dir)
    git(["add", "-A"], repo_dir)
    git(["commit", "-m", f"spectral: {task[:50]}"], repo_dir)
    git(["push", "-u", "origin", branch_name], repo_dir)

    gh = Github(auth=Auth.Token(gh_token))
    github_repo = gh.get_repo(repo_name)
    pr = github_repo.create_pull(
        title=f"Spectral Fix: {task[:60]}",
        body=f"Automated Visual Refactor by **Specter UI**.\n\n### 👁️ Visual Audit Results:\n{critique}",
        head=branch_name, base=github_repo.default_branch
    )
    console.print(f"\n[bold green]✅ Success! Spectral PR created:[/bold green] {pr.html_url}")
    update_state(state_file, status="done", pr_url=pr.html_url)

if __name__ == "__main__":
    main()
