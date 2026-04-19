# 🚀 Specter UI Deployment Guide

Specter UI is designed to run anywhere you can host a Docker container. Because it uses **Playwright** to capture UI snapshots, it requires a server with the Chromium browser installed.

## 🛰️ Cloud Hosting Options

### 1. Railway (Recommended)
Railway is the fastest way to deploy Specter UI. It supports Docker natively and has excellent performance.

1.  **Clone / Fork**: Ensure your repo is on GitHub.
2.  **Create Project**: Log in to [Railway.app](https://railway.app/) and select "New Project" -> "Deploy from GitHub repo".
3.  **Variables**: Add the following Environment Variables:
    *   `ANTHROPIC_API_KEY`: Your Claude API Key.
    *   `GITHUB_TOKEN`: Your Personal Access Token.
4.  **Deploy**: Railway will automatically detect the `Dockerfile` and start the deployment.

### 2. Render
Render is another great option for Docker-based swarms.

1.  Create a **Web Service** on [Render.com](https://render.com/).
2.  Connect your GitHub repository.
3.  Set the **Environment** to `Docker`.
4.  Add your secrets under "Environment Variables".

### 3. VPS / Self-Hosted (Docker)
If you have your own server (DigitalOcean, AWS EC2, etc.):

```bash
# Build the image
docker build -t specter-ui .

# Run the container
docker run -d \
  -p 8765:8765 \
  -e ANTHROPIC_API_KEY=your_key \
  -e GITHUB_TOKEN=your_token \
  --name specter-ui \
  specter-ui
```

---

## 🔑 Required Environment Variables

| Variable | Description | Source |
| :--- | :--- | :--- |
| `ANTHROPIC_API_KEY` | Required for the vision audit (Sonnet 4.5/Latest). | [Anthropic Console](https://console.anthropic.com/) |
| `GITHUB_TOKEN` | Required for cloning and creating PRs. | [GitHub Settings](https://github.com/settings/tokens) |
| `PORT` | (Optional) The port for the dashboard server. | Default: `8765` |

---

## 🛡️ Production Security
*   **Private Repos**: Ensure your `GITHUB_TOKEN` has the `repo` scope to access private projects.
*   **Rate Limits**: If running high-frequency audits, monitor your Anthropic token usage tiers.

## 📺 Monitoring
Once deployed, your dashboard will be available at:
`https://your-service-url.com` (Note: Ensure you expose port `8765`).
