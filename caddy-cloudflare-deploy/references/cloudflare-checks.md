# Cloudflare read-only preflight

Every check below is a GET. The same checklist works from panel screenshots when the user reads the values aloud; the API path just makes each fact an artifact.

## Token taxonomy

- `cfut_…` — user API token. Answers `GET /user/tokens/verify` with `status: active`.
- `cfat_…` and other dashboard-issued tokens — account/zone-scoped tokens. `/user/tokens/verify` answers `Invalid API Token` (code 1000) for these even when they work on their scoped endpoints; judge them by an actual endpoint call instead.
- A bare 32-hex string from the dashboard may be the Account ID, not a secret. A Global API Key needs `X-Auth-Key` plus `X-Auth-Email` together; confirm before treating either as a credential.

## Preflight endpoints

`Z` = zone id, `T` = token, all on `https://api.cloudflare.com/client/v4`.

| Call | Needs | Proof it yields |
| --- | --- | --- |
| `GET /zones?name=<apex>` | Zone · Zone · Read | zone id, status, account binding |
| `GET /zones/$Z/dns_records?name=<fqdn>` | Zone · DNS · Read | `content` (origin IP), `proxied` |
| `GET /zones/$Z/dns_records/export` | Zone · DNS · Read | zone-file text; `; cf_tags=cf-proxied:true` marks proxied records in one line |
| `GET /zones/$Z/settings/ssl` | Zone · Zone Settings · Read | `value: strict` is the deployable mode |
| `GET /zones/$Z/settings/websockets` | Zone · Zone Settings · Read | `value: on` required for realtime apps |

## Permission-error meanings

- Code `10000 Authentication error` on `dns_records` — the token lacks Zone · DNS · Read.
- Code `9109 Unauthorized to access requested resource` — scope missing for that endpoint family.
- A zone hosted but absent from `GET /zones` — the token's Zone Resources do not include it; edit the token's resource selection.

## Facts without any API

- `dig NS <apex>` answering `*.ns.cloudflare.com` — the zone is Cloudflare-hosted.
- `dig +short <fqdn>` answering Cloudflare anycast (104.21.x / 172.67.x) — the record exists and is proxied.
- `security_level medium` can serve browser challenges to API clients and app connections; realtime-heavy deployments read better at `low`.

## Hygiene

Read-only scopes cover this whole checklist; grant writes only for a specific disclosed fallback (e.g. DNS-01 challenge editing). Any token that has appeared in chat gets rotated when the task closes.
