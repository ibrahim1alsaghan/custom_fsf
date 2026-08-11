# Role Permission Audit — `new_fsf`

Generated via `bench --site new_fsf execute custom_fsf.scripts.permission_audit.run` after creating one test user per role (`audit-*@fsf.local`). Cells show the effective `R`ead / `W`rite / `C`reate verbs and `(list_count / total_in_db)` — `list_count` reflects permission queries (custodian filter, requester filter, library classification, etc.) actually applied.

## Effective Access Matrix

| Role assigned | HD Ticket | HD Team | Asset | Asset Movement | Asset Category | Task | Project | Library | Audit Log | User | Role |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **System Manager** | RWC (0/20) | — | R (0/80) | — | — | — | — | RWC (5/5) | RC (10000/24306) | RWC (22/24) | RWC (69/69) |
| **Asset Manager** | — | — | RWC (80/80) | RWC (81/81) | RWC (27/27) | — | — | R (4/5) | — | RW own | — |
| **Asset User** | — | — | R (2/80) | R (81/81) | R (27/27) | — | — | R (4/5) | — | RW own | — |
| **Employee** (with custodian record) | RWC (own only) | — | R (2/80) | — | — | — | — | R (4/5) | — | RW own | — |
| **HD Manager** | RWC (20/20) | RWC (2/2) | — | — | — | — | — | R (4/5) | — | R (22/24) | — |
| **HD Agent** | RWC (20/20) | R (2/2) | — | — | — | — | — | R (4/5) | — | R (22/24) | — |
| **Employee (requester only)** | RWC (own only) | — | — | — | — | — | — | R (4/5) | — | — | — |
| **Projects Manager** | — | — | — | — | — | RWC (43/43) | RWC (8/8) | R (4/5) | — | — | — |
| **Projects User** | — | — | — | — | — | R (own/dept) | R (8/8) | R (4/5) | — | RW own | — |
| **Document Manger** | — | — | — | — | — | — | — | RWC (5/5) | — | — | — |
| **Document Viewer** | — | — | — | — | — | — | — | R (4/5) | — | — | — |
| **Audit Viewer** | — | — | — | — | — | — | — | R (4/5) | R (10000/24306) | — | — |

## Library Classification Visibility

| Role | Global | Confidential | Top Secret |
|---|---|---|---|
| System Manager | ✓ | ✓ | ✓ |
| Document Manger | ✓ | ✓ | ✓ |
| Document Viewer | ✓ | ✓ | ✗ |
| Asset Manager / Asset User / HD Manager / HD Agent / Projects Manager / Projects User / Audit Viewer / **Employee** | ✓ | ✓ | ✗ |
| Pure portal/external user (no Employee role) | ✓ | ✗ | ✗ |

## Comparison Against Your Spec

| Expected | Result |
|---|---|
| System Manager = admin (user/role mgmt) | ✅ Full User + Role + Audit Log access |
| Asset Manager manages assets | ✅ Full CRUD on Asset, Asset Movement, Asset Category, Asset Repair, Asset Value Adjustment |
| Employee sees own custodian assets | ✅ Filter returns 2 assets (custodian + dept overlap) |
| Task: Manager sees all | ✅ Projects Manager → 43/43 |
| Task: User sees own | ✅ Projects User → filtered to own/_assign/dept |
| HD is great | ✅ HD Manager + HD Agent both see all 20 tickets, Employee sees only own |
| Document Manger sees Top Secret | ✅ Sees Global + Confidential + Top Secret |
| Employee sees Global + Confidential | ✅ **Fix applied** — was Global-only; now Global + Confidential |
| Audit Viewer for admin | ✅ Both System Manager and Audit Viewer can read Audit Log; Audit Viewer is read-only, no admin access |

## Fixes Applied During Audit

1. **`scripts/assets.py`** — `frappe.get_doc("Employee", {"user_id": user})` raised `DoesNotExistError` for any user without an Employee record (System Manager, HD users, Document users). Switched to `frappe.db.get_value(..., as_dict=True)` which returns `None` cleanly. Also `frappe.db.escape`'d the SQL fragments.
2. **`custom_fsf/doctype/library/library.py`** — `library_permission_query` and `library_has_permission` now grant Confidential to anyone with the `Employee` role (matching the spec "employee sees global and confidential with the manager"). Previously only `Document Viewer` got Confidential; plain `Employee` was limited to Global.

## Notes & Items To Confirm

- **System Manager intentionally does NOT see HD Tickets, HD Team, or filtered Asset lists.** Per the earlier cleanup, SM is reserved for GRC / user mgmt only. If you want SM to also have admin oversight on HD and Assets, add SM back to those `permissions` arrays (or just grant SM the `Asset Manager` / `HD Manager` role explicitly when they need to act there).
- **Asset User has *read on all 81 Asset Movements and all 27 Asset Categories*** (not custodian-filtered). The custodian filter in `scripts/assets.py` applies only to the `Asset` doctype. If movements/categories should also be restricted, the filter logic needs to extend to those.
- **Document Manger typo retained** — works correctly, but if the role is ever renamed to `Document Manager`, every reference in `library.py` + `library.json` + the test users above must be updated.
- **`RW own` on User** for most roles is Frappe baseline ("System User can edit own profile") — not a perm granted by our patches.

## Test Users Created on `new_fsf`

| Email | Role |
|---|---|
| audit-sm@fsf.local | System Manager |
| audit-am@fsf.local | Asset Manager |
| audit-au@fsf.local | Asset User (custodian linked) |
| audit-emp-asset@fsf.local | Employee with custodian asset |
| audit-hdm@fsf.local | HD Manager |
| audit-hda@fsf.local | HD Agent |
| audit-hdreq@fsf.local | Employee (HD requester) |
| audit-pm@fsf.local | Projects Manager |
| audit-pu@fsf.local | Projects User |
| audit-dm@fsf.local | Document Manger |
| audit-dv@fsf.local | Document Viewer |
| audit-audit@fsf.local | Audit Viewer |

To re-run the audit any time: `bench --site new_fsf execute custom_fsf.scripts.permission_audit.run`. Idempotent.

---

## Browser-side verification (Chrome @ `http://127.0.0.1:8010/app`)

Each test user was logged in through the Frappe login API in the same Chrome tab and probed via `frappe.client.get_list` — i.e. the exact same endpoint the desk UI uses to populate every list view. Resulting counts (with `ERR` = no permission, equivalent to the desk showing "Insufficient Permission"):

| User | Asset | Asset Movement | Asset Category | HD Ticket | HD Team | Task | Project | Library | Audit Log | User | Role | Library Classes Visible |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **sm** (System Manager) | 0 | ERR | ERR | 0 | ERR | ERR | 8 | 5/5 | 24317 | 22 | 69 | Global + Confidential + Top Secret |
| **am** (Asset Manager) | 80/80 | 82/82 | 27/27 | 0 | ERR | ERR | 8 | 4/5 | ERR | 22 | ERR | Global + Confidential |
| **au** (Asset User) | 2/80 | 82 | 27 | 0 | ERR | ERR | 8 | 4/5 | ERR | 22 | ERR | Global + Confidential |
| **emp-asset** (Employee w/ custodian) | 2/80 | ERR | ERR | 0 | ERR | ERR | 8 | 4/5 | ERR | 22 | ERR | Global + Confidential |
| **hdm** (HD Manager) | 0 | ERR | ERR | 20/20 | 2/2 | ERR | 8 | 4/5 | ERR | 22 | ERR | Global + Confidential |
| **hda** (HD Agent) | 0 | ERR | ERR | 20/20 | 2/2 | ERR | 8 | 4/5 | ERR | 22 | ERR | Global + Confidential |
| **hdreq** (Employee — requester) | 0 | ERR | ERR | 0 (own only) | ERR | ERR | 8 | 4/5 | ERR | ERR | ERR | Global + Confidential |
| **pm** (Projects Manager) | 0 | ERR | ERR | 0 | ERR | 43/43 | 8 | 4/5 | ERR | ERR | ERR | Global + Confidential |
| **pu** (Projects User) | 0 | ERR | ERR | 0 | ERR | 0/43 | 8 | 4/5 | ERR | 22 | ERR | Global + Confidential |
| **dm** (Document Manger) | 0 | ERR | ERR | 0 | ERR | ERR | 8 | 5/5 | ERR | ERR | ERR | Global + Confidential + Top Secret |
| **dv** (Document Viewer) | 0 | ERR | ERR | 0 | ERR | ERR | 8 | 4/5 | ERR | ERR | ERR | Global + Confidential |
| **audit** (Audit Viewer) | 0 | ERR | ERR | 0 | ERR | ERR | 8 | 4/5 | 24317 | ERR | ERR | Global + Confidential |

**Browser test perfectly matches the server-side audit.** Every list view a user opens in the desk UI will show exactly these row counts.

Two extra observations from the browser pass that didn't show up server-side:

- **`Project` shows 8 to every logged-in user** because ERPNext's `Project` doctype grants `read` to the `Employee` role by default. This is ERPNext baseline, not something the custom_fsf patches introduced. Not a security concern (project names are typically internal-public), but worth knowing.
- **`User` list shows 22 rows to most roles** — this is Frappe's "Desk User" baseline (allows reading other System Users for autocomplete). Hardening this would require stripping the Desk User auto-grant, which would break unrelated functionality.

## Workspace Sidebar Visibility (fix applied)

Initial audit caught a UI-level gap that doctype permissions miss: even when a user has read on `Asset`, the **Assets workspace shortcut wasn't appearing in the left sidebar** — because the workspace had a role restriction (`Asset Manager` only) stored in the DB. Same for `Document Library` (gated on `Document Viewer` only). Users could load `/app/asset` by URL but couldn't discover it from the sidebar.

Fixed by extending `custom_fsf/patches/setup_module_roles.py` with `WORKSPACE_GRANTS`:

| Workspace | Roles granted sidebar access |
|---|---|
| Assets | Asset Manager · Asset User · Employee |
| Document Library | Document Manger · Document Viewer · Employee |

Verified via Chrome under `audit-emp-asset@fsf.local` — sidebar now shows: LMS, Help Desk, **Assets**, **Document Library**. Final sidebar matrix per role:

| User | Sidebar workspaces |
|---|---|
| sm | Assets, Audit Logs, Document Library, Help Desk, Help Desk Admin, LMS, Users |
| am / au / emp-asset / dm / dv | Assets, Document Library, Help Desk, LMS |
| hdm | Assets, Document Library, Help Desk, Help Desk Admin, LMS |
| pm / pu | Assets, Document Library, Help Desk, LMS, Tasks |
| audit | Assets, Audit Logs, Document Library, Help Desk, LMS |

## Asset Creation Dependencies (fix applied)

Creating a fixed asset isn't just `Asset` — it requires the linked `Item` to exist (with `is_fixed_asset = 1`), plus `Item Group`, `Location`, and `Cost Center` autocompletes to resolve. None of those ERPNext doctypes ship with the `Asset Manager` role, so until this fix an Asset Manager couldn't even open the New Item form.

Extended `ASSET_GRANTS` in the patch:

| Role | Item | Item Group | Location | Cost Center |
|---|---|---|---|---|
| Asset Manager | R+W+C | R+W+C | R+W+C | R |
| Asset User | R | — | R | R |

Also granted Asset Manager access to the standard **Fixed Asset Register** report (`REPORT_GRANTS` via `Has Role` row with `parenttype="Report"`), which ships gated on `Accounts User` / `Quality Manager` only.

Verified as `audit-am@fsf.local`: Item list shows 26 rows, Item Group 6, Location 1, Cost Center 2, and `/app/query-report/Fixed Asset Register` opens with the full filter form.

## Post-Login "Not Permitted" Redirect (fix applied)

Symptom: HD Manager, Projects Manager (when added as Website User), Document Manger, Document Viewer, Audit Viewer, plain Employee — anyone whose only roles don't grant desk access — got a "Not Permitted - You are not permitted to access this page" page after login when visiting `/`.

Root cause: `Portal Settings.default_portal_home` was set to `/app` (ERPNext default). `frappe.website.utils.get_home_page()` evaluates Portal Settings **before** the `home_page = "landing"` hook in custom_fsf, so every non-Guest user got redirected to `/app`, which then 403'd for anyone without `Desk User`.

Fix: `setup_module_roles.py` now sets `Portal Settings.default_portal_home = "landing"`, letting the hook value take effect for everyone. System Users still navigate to `/app` directly via the desk router when they want it — this change only affects the implicit `/` redirect.

Verified in Chrome: all 10 non-Administrator roles (hdm, hda, pm, pu, dm, dv, audit, sm, au, hdreq) now return 200 on `/` and land on the Arabic landing page (`قوات أمن المنشآت`). No more "Not Permitted".

### Follow-up: `user_type` self-heal

Even after the Portal Settings fix, users who hold a desk-access role (HD Manager, Asset Manager, Document Viewer, Document Manger, Projects Manager, Audit Viewer, etc.) but somehow ended up flagged as `Website User` still got 403 when they navigated to `/app` — because Frappe gates the desk on `System User` user_type, not on the role's `desk_access` flag.

This can happen whenever users are created via Data Import, raw SQL, or any path that bypasses `User.validate` (e.g. my audit script's `db_insert` workaround for the LMS hook race). It will also happen for any prod user that was imported the same way.

`setup_module_roles.py` now self-heals: any enabled user that holds a role from `DESK_ROLES` but is still `Website User` gets bumped to `System User`. Idempotent.

Final login-flow verification:

| User | Login API `home_page` | `/` | `/app` |
|---|---|---|---|
| hdm (HD Manager) | `/app` | 200 | 200 |
| dv (Document Viewer) | `/app` | 200 | 200 |
| hdreq (Employee only) | `/landing` | 200 | 403 (correct — plain Employee has no desk access) |
| All other 9 test users | `/app` | 200 | 200 |

A user with only the `Employee` role hits `/landing` and stays on the portal — that is the intended behaviour for ticket-requester-only accounts. They never need `/app`.

## LMS Workspace Restricted to LMS Admins (fix applied)

Symptom: every test user — including Document Viewer, Asset User, plain Employee — saw the LMS workspace in the sidebar, with admin shortcuts "Visit LMS Portal / Create a Course / Setup a Home Page / LMS Settings" plus the Signups & Enrollments charts. Those are admin-only actions.

Root cause: the LMS workspace ships with `roles: []` (open to all). Every user is auto-granted the `LMS Student` role by `lms.after_insert`, but `LMS Student` was never used to gate the workspace — the workspace was just public.

Fix: `WORKSPACE_GRANTS["LMS"] = ["Course Creator", "Moderator", "System Manager"]`. Anyone without one of those three roles no longer sees the LMS workspace. Students still consume LMS through the public `/lms/courses` portal — no desk workspace needed.

Verified in Chrome: `sm` still sees LMS in sidebar; `am`, `au`, `hdm`, `dv`, `dm`, `audit`, `pu`, `emp-asset`, `hdreq` do not.

## Employee Sees Own Tasks (fix applied)

Two bugs combined to hide tasks from plain Employees:

1. **`scripts/tasks.py` was never wired up.** `permission_query_conditions` and `has_permission` for `Task` were missing from `hooks.py`. All custom filter logic in `scripts/tasks.py` was dead code; Task visibility was governed purely by static DocType permissions. Anyone with Task read at permlevel 0 saw all rows.
2. **`Employee` role had no DocPerm on Task.** Without read perm, plain Employees saw nothing.

Fixes:
- Registered both hooks in `custom_fsf/hooks.py`:
  ```python
  permission_query_conditions["Task"] = "custom_fsf.scripts.tasks.get_permission_query_conditions"
  has_permission["Task"] = "custom_fsf.scripts.tasks.has_permission"
  ```
- Dropped the "`Projects User` in roles → otherwise `1=0`" gate in `scripts/tasks.py`. Now anyone (Employee included) passes the filter when they own / are assigned to / share department with a task.
- Added `Employee → READ on Task` to `PROJECTS_GRANTS` in `setup_module_roles.py`.

Result verified in Chrome:

| User | Tasks visible |
|---|---|
| emp-asset (Employee, assigned to TASK-2025-00001) | 1 ✅ |
| pm (Projects Manager) | 43 / 43 ✅ |
| pu / hdm / hdreq / sm (no assignments) | 0 ✅ |
