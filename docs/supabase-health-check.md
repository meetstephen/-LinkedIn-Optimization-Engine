# Supabase health check

The `LinkedBoost Supabase Health Check` workflow queries project `avmbwrxlmybnfxzphkur` every six hours: 00:17, 06:17, 12:17 and 18:17 UTC (01:17, 07:17, 13:17 and 19:17 WAT). GitHub may delay scheduled runs.

## Configuration

- Workflow: `.github/workflows/supabase_health.yml` on `main`.
- Repository secret: `SUPABASE_PUBLISHABLE_KEY`, containing the existing Supabase publishable key. Do not use a service-role or secret key.
- The query reads `lb_posts` with `id=is.null` and a limit of one. Since the ID is a primary key, the expected response is an empty JSON array. No application records are changed or logged.
- The job retries transient failures up to three times and fails visibly if the database check cannot succeed. It needs no repository write permissions or third-party packages.

## Check and recover

Open https://github.com/meetstephen/-LinkedIn-Optimization-Engine/actions/workflows/supabase_health.yml and confirm recent scheduled runs are green. Use **Run workflow** on `main` for a manual test.

If runs fail, check Supabase project status, the repository secret, and the existence/accessibility of `lb_posts`. Do not disable row-level security to fix this check. If the project is paused, resume it from the Supabase dashboard, then run the workflow again.

Public-repository scheduled workflows can be disabled after 60 days without repository activity. If the workflow is disabled, use **Enable workflow** on its Actions page and run a manual check. A successful manual run alone does not prove the schedule remains enabled. See https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule.

For email alerts, check personal GitHub notification settings under **Actions** and enable notifications for failed workflows. Delivery depends on the account's notification preferences.

This workflow runs on GitHub, independently of the owner's computer. A separate Codex maintenance monitor, if enabled, requires the desktop host to be available; it is not required for this GitHub job to execute.

## Limits and data protection

Activity reduces inactivity risk but does not guarantee exemption from Supabase Free-plan pausing. See https://supabase.com/docs/guides/platform/free-project-pausing.

The workflow is not a backup. Keep database exports and Storage-object backups separately; never commit private exports or credentials to this public repository. A database backup alone does not contain Storage file contents.
