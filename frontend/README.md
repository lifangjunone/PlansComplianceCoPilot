# React + Vite SSO template

Every React application created by `aime_create_web_app --complex_template` uses ByteCloud SSO on
startup. It uses `@bytecloud/common-lib` to obtain a JWT, then attaches that
token to calls that need authentication.

## Environment

| Mode | File | SSO host |
| --- | --- | --- |
| Development | `.env.dev` | `sso.bytedance.net` |
| BOE | `.env.boe` | `sso.bytedance.net` |
| Production | `.env.prod` | `sso.bytedance.com` |

Every environment must provide `VITE_PARTITION`, `VITE_SSO_HOST`, and
`VITE_AUTH_SERVICE_HOST`.

After SSO succeeds, the template loads the signed-in user's deployment profile
from `/api/agents/v2/deployment/user` on the matching backend host:

| Frontend host | Backend host |
| --- | --- |
| `*.aime-app.tiktok-row.net` | `aime.tiktok-row.net` |
| All other hosts | `aime.bytedance.net` |

For example, local development also calls
`https://aime.bytedance.net/api/agents/v2/deployment/user`.

That request includes the `x-jwt-token` header. If the backend returns `403`
with an `owner` field, the page shows a no-permission message that points the
user to that owner. If the browser blocks the request before the `GET` response
is readable, for example because a cross-origin `OPTIONS` preflight returns
`403`, the protected `App.tsx` access gate still blocks business content and
shows the no-permission fallback.

If your application also has its own business backend, use the base template's
`VITE_API_PROXY_TARGET` setting for those `/api/*` requests.

## Where to write business code

`src/App.tsx` is the platform shell. It wires up SSO login, current-user
loading, the no-permission access gate, the optional watermark, and the
top-right user menu, and must not be edited. Write all application UI and logic
in `src/business.tsx` (and any files it imports). `App.tsx` renders
`<Business user={user} />` only after the access gate passes, so the signed-in
user profile (`UserResponse | null`, exported from `src/lib/auth.ts`) is
available through the `user` prop.

## Calling authenticated APIs

Use `fetchWithAuth` from `src/lib/auth.ts` for protected routes. It sends the
JWT as `x-jwt-token`, retries once after a `401`, and redirects to SSO if the
request remains unauthorized. The default page fetches
the mapped deployment user endpoint after SSO succeeds and exposes the user
profile through the top-right user menu.

## Optional watermark

Create the React application with `--complex_template --watermark_enable` when a
page-wide signed-in user watermark is required:

```bash
aime_create_web_app my_app "My awesome app" --complex_template --watermark_enable
```

The watermark contains the user's Chinese display name and email prefix. It is
rendered with a lighter color and wider spacing, and is removed automatically
when the user changes, logs out, or the page unmounts. Without this flag, the
generated application contains neither watermark behavior nor the watermark
package dependency.
