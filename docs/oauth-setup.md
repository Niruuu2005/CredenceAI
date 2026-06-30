# OAuth Setup (Google + GitHub)

> **Full manual checklist (accounts, env vars, CI secrets, validation):** [manual-setup.md](manual-setup.md)

Use this document after deploying the frontend (Vercel) and API (Render). Replace placeholders with your real URLs:

```
FRONTEND_URL=https://your-app.vercel.app
API_URL=https://your-api.onrender.com
```

The OAuth **redirect URI** always points to the **frontend** callback route. The frontend exchanges the code with the API.

---

## Google OAuth

### 1. Google Cloud Console

1. Open [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services** → **Credentials**.
2. **Create Credentials** → **OAuth 2.0 Client ID** → type **Web application**.
3. **Authorized JavaScript origins:**
   - `FRONTEND_URL`
   - `http://localhost:3000` (local dev)
4. **Authorized redirect URIs** (must match exactly):
   - `FRONTEND_URL/auth/google/callback`
   - `http://localhost:3000/auth/google/callback`
5. Copy **Client ID** and **Client Secret**.

### 2. OAuth consent screen

1. **APIs & Services** → **OAuth consent screen**
2. User type: **External** (public) or **Internal** (Google Workspace)
3. Scopes: `openid`, `email`, `profile`
4. While in **Testing** mode, add test users; **Publish** when ready for production.

### 3. Render environment variables

```env
GOOGLE_CLIENT_ID=<from Google Console>
GOOGLE_CLIENT_SECRET=<from Google Console>
GOOGLE_REDIRECT_URI=FRONTEND_URL/auth/google/callback
```

### 4. Verify

1. Open `FRONTEND_URL/auth/sign-in` → **Google**
2. Complete Google login → redirected to `/auth/google/callback`
3. Land on `/app/dashboard` with session active

| Error | Fix |
|-------|-----|
| `redirect_uri_mismatch` | Redirect URI in Google Console must exactly match `GOOGLE_REDIRECT_URI` |
| `503 Google OAuth not configured` | Set all three `GOOGLE_*` vars on Render and redeploy |
| CORS error | `CORS_ALLOWED_ORIGINS` must include `FRONTEND_URL` (no trailing slash) |

---

## GitHub OAuth

### 1. GitHub OAuth App

1. GitHub → **Settings** → **Developer settings** → **OAuth Apps** → **New OAuth App**
2. **Application name:** CredenceAI
3. **Homepage URL:** `FRONTEND_URL`
4. **Authorization callback URL:** `FRONTEND_URL/auth/github/callback`
5. Copy **Client ID**; generate a **Client Secret**

For local dev, add a second OAuth app or use the same app with callback `http://localhost:3000/auth/github/callback`.

### 2. Render environment variables

```env
GITHUB_CLIENT_ID=<from GitHub>
GITHUB_CLIENT_SECRET=<from GitHub>
GITHUB_REDIRECT_URI=FRONTEND_URL/auth/github/callback
```

### 3. Verify

1. Open `FRONTEND_URL/auth/sign-in` → **GitHub**
2. Authorize on GitHub → `/auth/github/callback`
3. Land on `/app/dashboard`

| Error | Fix |
|-------|-----|
| Redirect URI not associated | Callback URL in GitHub app must match `GITHUB_REDIRECT_URI` |
| `incorrect_client_credentials` | Regenerate client secret |
| Missing email | Ensure `user:email` scope (configured in backend) and grant email access on GitHub |

---

## Production requirements

- `APP_ENV=production`
- `JWT_SECRET` — generate with `openssl rand -hex 32`
- **At least one** OAuth provider fully configured (Google or GitHub)
- `CORS_ALLOWED_ORIGINS=["FRONTEND_URL"]`
- `ENABLE_API_KEY_AUTH=true`

On **Vercel**:

```env
VITE_API_BASE_URL=API_URL/api
```

---

## API key flow (after OAuth)

1. Sign in with Google or GitHub
2. Go to **Settings** → **Create API Key**
3. Copy `cred_sk_...` (shown once)
4. Use programmatically:

```bash
curl -X POST API_URL/api/jobs \
  -H "X-API-Key: cred_sk_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"job_type":"search_query","query":"test","input":"test"}'

curl API_URL/api/auth/validate -H "X-API-Key: cred_sk_YOUR_KEY"
```

---

## Custom domain (later)

When you add a domain:

1. Point `app.yourdomain.com` → Vercel, `api.yourdomain.com` → Render
2. Update redirect URIs in **both** Google Console and GitHub OAuth App
3. Update `GOOGLE_REDIRECT_URI`, `GITHUB_REDIRECT_URI`, `CORS_ALLOWED_ORIGINS`, `VITE_API_BASE_URL`
4. Redeploy frontend and API
