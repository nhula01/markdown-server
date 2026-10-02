# Optional review accounts

The public project connection is configured for `bavhnsbjevyuptesntiy`.
The review-events table and RLS policies were applied on October 2, 2026.
Live rollback-only database checks passed: own-row read/insert, cross-account
read/insert/delete isolation, no UPDATE access, and no anonymous read access.
The unauthenticated REST read also returned permission denied.

Email sign-up and confirmation are enabled; the minimum password length is 12.
The production Site URL and exact production/local redirect URLs below were
saved. Google and anonymous sign-in are disabled. Custom SMTP is still disabled:
public registration, recovery-email delivery, and actual device-to-device login
must still be tested before publication. Guest reviews continue on the device.

1. Sign in at https://supabase.com/dashboard and create a **Free** project in your
   own organization. Choose a database password and keep it in your password
   manager; the website never needs it.
2. Run `supabase/review.sql` in the project's SQL Editor. This creates a private
   review-events table with row-level security. Do not disable RLS.
3. In Authentication → Providers, enable Email, keep email confirmation enabled,
   allow new sign-ups, and set the password minimum to 12 characters. Leave
   anonymous and Google sign-in disabled.
4. Under Authentication → URL Configuration, set Site URL and allow redirects to
   `https://nhula01.github.io/markdown-server/review/`. For the local preview, also
   allow `http://127.0.0.1:8787/markdown-server/review/`. Use exact URLs; remove the
   local entry after testing. Confirmation/reset links must open in the same
   browser where the request was started because the website uses PKCE.
5. Configure custom SMTP before opening registration to the public. Supabase's
   built-in mail service is for testing and restricts recipients to your team's
   addresses. A mail provider may offer a free tier; a verified sending domain
   may have a separate cost. Never put SMTP credentials in GitHub. Keep email
   confirmation enabled. Follow https://supabase.com/docs/guides/auth/auth-smtp.
6. Copy the project URL and **publishable** key from Project Settings → API Keys
   into `site/auth.json`. These two values are public. Do not copy the database
   password, secret key, service-role key, SMTP password, or account credentials.
   The builder rejects non-publishable keys and extra fields before publishing.
7. Build the local preview and test the account flow before deploying:
   ```sh
   .venv/bin/python scripts/build-pages.py --output /tmp/daily-review-preview/markdown-server
   ```

## Live acceptance checks (require your configured project)

- Create a new account; confirm its email; sign in. Its schedule starts empty.
- Complete a review; verify the account status reports synced.
- Sign in on a second device: the same progress and next review dates must appear.
- Create a second account: it must start empty and must not see the first user's
  events. Test REST calls as both users: select/delete targeting the other user's
  ID return no rows; insert using the other ID fails. An unauthenticated request
  to review_events must fail. Test a duplicate event UUID: no extra review.
- Disconnect after signing in, grade a note, reconnect and Sync again. Reload:
  the rating must appear once. Repeat with interruption after the insert but
  before the subsequent read. Pending events are cleared only after that read.
- Test Forgot password; open the link in the requesting browser; update password;
  sign out; sign in with the new password.
- Sign out: the browser returns to its separate guest schedule.

Database isolation has been verified on the live project. Browser sign-up,
confirmation, recovery, and cross-device sync still need acceptance testing.
Public-key configuration alone does not set up email delivery.

## Privacy and behavior

Supabase Auth holds email addresses and password hashes. review_events contains
only a random event ID, account ID, notebook ID, rating, review day, and server
recording time. Each authenticated reader can read, insert, or delete only their
own events. Existing events cannot be updated; two devices append rather than
replace one another's records. Schedule replay sorts by review day and then by
server recording time. Multiple recalls of one notebook count as separate
attempts. Typed recall answers and notebook contents are never uploaded.

Sessions and offline progress are cached in the browser, under a separate key
for each account. Signing out removes the active session; progress caches remain
on that device for offline continuity. Clear site data on a shared device after
signing out. Guest progress is separate and is not automatically imported.
Project administrators can access database records; private means protected
from other readers, not from the project owner or hosting provider.

To honor an account-deletion request, delete that user through Supabase Auth;
its database events cascade-delete. Ask the reader to clear the site's browser
data too. No administrator key is shipped to the website.
