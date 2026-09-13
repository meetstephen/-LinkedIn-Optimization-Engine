# Security

## Supported configuration

LinkedEdge uses custom bcrypt authentication in the Streamlit server. It does
not issue Supabase Auth JWTs. Therefore a public multi-user deployment must use:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` stored only in Streamlit secrets
- the latest `supabase_schema.sql`, which revokes access from `anon` and
  `authenticated`
- `REQUIRE_AUTH=true`

Never expose the service-role key in a Streamlit widget, repository, browser
bundle, screenshot, client log, or support ticket. Rotate it immediately if it
is exposed.

`ALLOW_INSECURE_ANON_DB=true` exists only to keep a legacy private deployment
running during migration. In that mode the application cannot provide a secure
multi-user isolation guarantee.

## Upgrade from the former anonymous schema

1. Add `SUPABASE_SERVICE_ROLE_KEY` to server-side secrets while retaining the
   old key temporarily.
2. Deploy and confirm the app can read the library and authenticate.
3. Run the latest `supabase_schema.sql`. This removes every permissive anonymous
   policy and revokes public table/sequence privileges.
4. Replace `SUPABASE_PUBLISHABLE_KEY` with `SUPABASE_SERVICE_ROLE_KEY` in the
   repository health-check secret.
5. Remove the old `SUPABASE_KEY` and ensure `ALLOW_INSECURE_ANON_DB` is unset.
6. Test signup, login, reset, save, schedule, admin, and feedback flows.

## AI trust boundaries

User profile fields, topics, source notes, story beats, and web research are
untrusted data. They are sanitised and/or delimiter-wrapped before prompting.
Generated content is still probabilistic: review legal, medical, financial,
regulatory, employment, safety, and reputational claims before publishing.

## Reporting a vulnerability

Do not open a public issue containing secrets, personal data, or exploit steps.
Use GitHub's private vulnerability reporting feature when enabled, or contact
the repository owner privately. Include the affected commit, impact, and a
minimal reproduction with all credentials removed.
