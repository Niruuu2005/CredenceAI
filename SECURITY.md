# Security Policy

## Reporting a vulnerability

If you discover a security issue, please report it responsibly. Do not open public GitHub issues for undisclosed vulnerabilities.

Contact the maintainers through your organization's preferred private channel.

## Secure development practices

- Never commit `.env` files or real API keys.
- Use `backend/.env.example`, `frontend/.env.example`, and `sdk/.env.example` as templates only.
- Set strong `JWT_SECRET` in production.
- Configure `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` for production OAuth — mock auth is disabled when `APP_ENV=production`.
- `DEV_LOGIN_USERNAME` / `DEV_LOGIN_PASSWORD` work only when `APP_ENV=local`.
- Enable `ENABLE_API_KEY_AUTH=true` for programmatic API access in production.
- Configure Google OAuth (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`) and/or GitHub OAuth (`GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GITHUB_REDIRECT_URI`) — at least one provider required in production.

## Known operational surfaces

- Legacy ops dashboard at `GET /dashboard` (inline HTML in backend).
- FastAPI auto-generated docs at `/docs` — restrict in production if needed.
