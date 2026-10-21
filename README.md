# GameVault

Flask + MySQL game-store lab project. Frontend: server-rendered HTML, CSS, and JavaScript. Database access: a policy-driven, parameterized SQL builder, not an ORM.

## 1. Current State and Decisions

- Filled files: `database/schema.sql`, `database/operations.sql`, and `database/seed.sql`.
- Filling a script does not mean it has been executed or tested on MySQL. Verify locally before building against it.
- Python backend, templates, styles, JavaScript, and tests are planned, not implemented.
- This README defines the planned interface between teammates. Function names and route names below are contracts to implement, not existing APIs.
- Keep the compact directory below. Do not introduce additional packages/folders without team agreement.
- Payments are simulated; no real account/card details, payment gateways, or game downloads.
- All prices are INR. Purchases are game-level, not separate platform licenses.
- Admin and affiliated-publisher editing are planned. Developer accounts are not supported by the current user schema.

## 2. Directory Structure

```text
gamevault/
├── app.py
├── db.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── README.md
├── tests.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── game.html
│   ├── cart.html
│   ├── wishlist.html
│   ├── checkout.html
│   ├── orders.html
│   └── admin.html
├── static/
│   ├── style.css
│   ├── script.js
│   └── images/
├── database/
│   ├── schema.sql
│   ├── seed.sql
│   └── operations.sql
└── docs/
    ├── report.md
    ├── schema_diagram.png
    ├── er_diagram.png
    └── presentation.pptx
```

## 3. What Each File Does

| File | Responsibility |
|---|---|
| app.py | Flask configuration, HTTP routes, session authentication, CSRF setup, input extraction, rendering, and workflow coordination. Loads a trusted actor; never trusts browser role flags. |
| db.py | Connections; server-defined operation policies; validation; authorization; mandatory row scopes; SQL construction; execution; transaction helpers; approved custom reporting queries. No HTML or redirects. |
| tests.py | Builder/policy unit tests and isolated database/application integration tests. Never reset the ordinary development database. |
| requirements.txt | Shared Python dependency versions. Proposed packages: Flask, Werkzeug, mysql-connector-python, python-dotenv, Flask-WTF, pytest. |
| .env | Local secrets/settings. Never commit. |
| .env.example | Required variable names with dummy values. Commit this file. |
| .gitignore | Excludes .env, .venv/, __pycache__/, *.py[cod], .pytest_cache/. |
| README.md | Team contract: schema, input/output formats, access rules, and implementation plan. |
| templates/base.html | Shared layout, navigation, messages, asset links, content blocks. |
| templates/index.html | Catalog, search/filter controls, sorting, pagination, game cards. |
| templates/login.html | Login form and errors. |
| templates/register.html | Registration form and errors. |
| templates/game.html | Game details, genres/platforms, reviews, review form, cart/wishlist controls. |
| templates/cart.html | Cart contents, current prices, total, remove controls, checkout link. |
| templates/wishlist.html | Saved games and current offers. |
| templates/checkout.html | Server-calculated summary and explicit simulated success/failure controls. |
| templates/orders.html | Own order history/details and owned games derived from paid orders. |
| templates/admin.html | Admin/publisher catalog forms and permitted reports. |
| static/style.css | Shared styling and responsive layout. |
| static/script.js | Optional interactions; cannot authorize actions or decide prices/payment results. |
| static/images/ | Logo, local thumbnails, and placeholder images. |
| database/schema.sql | 14 tables, keys, constraints, defaults. No triggers. |
| database/operations.sql | Triggers, views, procedures; commented demonstration SQL and optional DCL setup. |
| database/seed.sql | Fictional demo records and hashed demo accounts. |
| docs/report.md | Required academic report sections and references. |
| docs/schema_diagram.png | Relational schema image matching final SQL. |
| docs/er_diagram.png | Entities, relationships, cardinalities. |
| docs/presentation.pptx | Evaluation presentation and screenshots. |

## 4. Local Configuration and Database Setup

Use MySQL 8.0.16+ for enforced CHECK constraints. Use one agreed Python version and dependency set across the team.

Expected `.env` names:

```dotenv
SECRET_KEY=replace-with-a-long-random-secret
DB_HOST=localhost
DB_PORT=3306
DB_NAME=gamevault
DB_USER=gamevault_app
DB_PASSWORD=replace-with-your-local-password
```

`app.py` loads environment configuration explicitly. No hardcoded database password or fallback secret key. Missing required configuration should cause a clear startup/configuration error.

Create a virtual environment and install the completed requirements file:

```bash
python -m venv .venv
# Activate using the command appropriate to your shell.
python -m pip install -r requirements.txt
```

Fresh database execution order:

```text
schema.sql → operations.sql → seed.sql
```

- Use a setup account for schema objects and account creation; the Flask account is not root.
- schema.sql does not overwrite existing tables. Its destructive reset line is commented out.
- seed.sql uses fixed IDs and is not repeatable on populated tables.
- operations.sql replaces its defined objects and reconciles averages; DDL is not one rollback-safe transaction.
- Correct both delimiter resets to `DELIMITER ;` if a locally edited operations.sql says `DELIMITER;`.
- No automatic schema/seed execution on Flask startup.

Verification examples:

```sql
USE gamevault;
SHOW TABLES;
SHOW TRIGGERS;
SELECT * FROM vw_game_catalog;
CALL sp_sales_summary('2026-10-01', '2026-11-01');
```

Expected original seed: 2 paid orders, 2 paying customers, revenue 2347.80.

Planned development commands once code exists:

```bash
python -m flask --app app run --debug
python -m pytest tests.py
```

Debug mode is local-only. Integration tests must use an explicitly configured separate database such as gamevault_test and reject the ordinary database name.

Demo accounts are local-only:

| Username | Password | Role |
|---|---|---|
| admin | AdminDemo@123 | Admin |
| player_one | PlayerDemo@123 | Customer |
| player_two | PlayerDemo@123 | Affiliated with publisher 1 |

Passwords are stored as Werkzeug-compatible PBKDF2 hashes. Use Werkzeug check_password_hash for verification. email_verified remains false; email delivery/verification is out of scope initially.

## 5. Revised Schema Tables

This section describes the revised schema.sql supplied for this project. Check the actual local script before assuming it matches. SQL is the source of truth.

PK = primary key; FK = foreign key; AI = AUTO_INCREMENT; NN = NOT NULL. Primary-key columns are non-null. All FK updates use ON UPDATE CASCADE. Tables use InnoDB; the database uses utf8mb4_unicode_ci.

### publishers

| Column | Type | Constraints |
|---|---|---|
| publisher_id | INT | PK, AI |
| publisher_name | VARCHAR(100) | NN, UNIQUE |



### developers

| Column | Type | Constraints |
|---|---|---|
| dev_id | INT | PK, AI |
| dev_name | VARCHAR(100) | NN, UNIQUE |



### users

| Column | Type | Constraints |
|---|---|---|
| user_id | INT | PK, AI |
| username | VARCHAR(50) | NN, UNIQUE |
| password_hash | VARCHAR(255) | NN |
| email | VARCHAR(100) | NN, UNIQUE |
| email_verified | BOOLEAN | NN, default FALSE, only 0/1 |
| is_admin | BOOLEAN | NN, default FALSE, only 0/1 |
| affiliate_publisher_id | INT | Nullable, FK → publishers.publisher_id |
| created_at | DATETIME | NN, default CURRENT_TIMESTAMP |



### genres

| Column | Type | Constraints |
|---|---|---|
| genre_id | INT | PK, AI |
| genre_name | VARCHAR(50) | NN, UNIQUE |



### platforms

| Column | Type | Constraints |
|---|---|---|
| platform_id | INT | PK, AI |
| platform_name | VARCHAR(50) | NN, UNIQUE |



### games

| Column | Type | Constraints |
|---|---|---|
| game_id | INT | PK, AI |
| game_name | VARCHAR(150) | NN |
| description | TEXT | Nullable |
| thumbnail_url | VARCHAR(255) | Nullable |
| publisher_id | INT | NN, FK → publishers.publisher_id |
| developer_id | INT | NN, FK → developers.dev_id |
| standard_price | DECIMAL(10,2) | NN, >= 0 |
| discount_percent | DECIMAL(5,2) | NN, default 0.00, range 0–100 |
| release_date | DATE | Nullable |
| average_rating | DECIMAL(3,2) | NN, default 0.00, range 0–5 |



### game_genres

| Column | Type | Constraints |
|---|---|---|
| game_id | INT | NN, FK → games.game_id |
| genre_id | INT | NN, FK → genres.genre_id |

Composite PK: (game_id, genre_id).

### game_platforms

| Column | Type | Constraints |
|---|---|---|
| game_id | INT | NN, FK → games.game_id |
| platform_id | INT | NN, FK → platforms.platform_id |

Composite PK: (game_id, platform_id).

### cart_items

| Column | Type | Constraints |
|---|---|---|
| cart_item_id | INT | PK, AI |
| user_id | INT | NN, FK → users.user_id |
| game_id | INT | NN, FK → games.game_id |
| added_at | DATETIME | NN, default CURRENT_TIMESTAMP |

UNIQUE (user_id, game_id).

### payments

| Column | Type | Constraints |
|---|---|---|
| transaction_id | INT | PK, AI |
| payee_account_no | VARCHAR(50) | NN, dummy reference only |
| recipient_account_no | VARCHAR(50) | NN, dummy reference only |
| payment_time | DATETIME | NN, default CURRENT_TIMESTAMP |
| amount | DECIMAL(10,2) | NN, >= 0 |
| payment_status | VARCHAR(20) | NN, NO DEFAULT, allowed SUCCESS / FAILED / REFUNDED |

The legacy payee_account_no name is ambiguous; this prototype uses it for a dummy payer reference. Do not rename it in one file without updating every caller.

### orders

| Column | Type | Constraints |
|---|---|---|
| order_id | INT | PK, AI |
| user_id | INT | NN, FK → users.user_id |
| order_date | DATETIME | NN, default CURRENT_TIMESTAMP |
| order_status | VARCHAR(20) | NN, default PENDING, allowed PENDING / PAID / CANCELLED / REFUNDED |
| transaction_id | INT | Nullable, UNIQUE, FK → payments.transaction_id |



### order_items

| Column | Type | Constraints |
|---|---|---|
| order_item_id | INT | PK, AI |
| order_id | INT | NN, FK → orders.order_id |
| game_id | INT | NN, FK → games.game_id |
| price_paid | DECIMAL(10,2) | NN, >= 0, historical line-price snapshot |

UNIQUE (order_id, game_id).

### reviews

| Column | Type | Constraints |
|---|---|---|
| user_id | INT | NN, FK → users.user_id |
| game_id | INT | NN, FK → games.game_id |
| rating | DECIMAL(2,1) | NN, allowed 0, 0.5, 1, …, 5 |
| review_text | TEXT | Nullable |
| review_date | DATETIME | NN, default CURRENT_TIMESTAMP |

Composite PK: (user_id, game_id). One current review per user/game.

### wishlists

| Column | Type | Constraints |
|---|---|---|
| wishlist_id | INT | PK, AI |
| user_id | INT | NN, FK → users.user_id |
| game_id | INT | NN, FK → games.game_id |
| added_at | DATETIME | NN, default CURRENT_TIMESTAMP |

UNIQUE (user_id, game_id).

### Deletion rules

| Child foreign key | ON DELETE |
|---|---|
| users.affiliate_publisher_id | SET NULL |
| games.publisher_id, games.developer_id | RESTRICT |
| Both keys in game_genres and game_platforms | CASCADE |
| Both keys in cart_items | CASCADE |
| orders.user_id, orders.transaction_id | RESTRICT |
| order_items.order_id | CASCADE |
| order_items.game_id | RESTRICT |
| Both keys in reviews and wishlists | CASCADE |

Do not expose completed-order deletion in the UI. Delete referenced games only when constraints permit; no archive flag exists yet. A user/publisher affiliation is one publisher per user. There is no affiliate_developer_id.

### Database objects already defined in operations.sql

| Object | Purpose |
|---|---|
| Three review triggers | Recalculate affected averages after explicit review insert/update/delete; update handles OLD and NEW game IDs. |
| vw_game_catalog | Game/publisher/developer details, current_price, cached average, review_count. |
| vw_paid_order_items | Items whose order is PAID and payment SUCCESS. |
| vw_owned_games | Deduplicated user/game ownership and first_purchase_date. |
| vw_order_summary | One row per order, payment details, item_count and order_total. |
| vw_game_sales | Copies sold and line-item revenue by game. |
| vw_discounted_wishlist | Discounted saved games with current prices. |
| sp_sales_summary(start, end) | Paid-order count, paying-customer count, payment revenue; start inclusive, end exclusive. |
| sp_recalculate_average_ratings() | Administrative full average reconciliation. |

Foreign-key cascades do not activate the review triggers. Reconcile averages after administrative changes that bypass them. Keep normal user/game identifiers immutable in application editing. Serialize normal review writes per game and test concurrency; the aggregate cache is not automatically production-grade concurrency-safe.

## 6. Request-to-Database Architecture

```text
Browser form / query string
    ↓
app.py: extract inputs, authenticate session, validate CSRF for writes
    ↓
db.py: named operation policy + validation + authorization
    ↓
mandatory user/publisher scope added by server
    ↓
query builder produces SQL + separate parameters
    ↓
executor uses MySQL connection / transaction
    ↓
app.py renders a template or sends a controlled error
```

There is no unrestricted SQL endpoint. Browser input cannot choose arbitrary tables, columns, SQL fragments, roles, user identities, procedure names, or joins.

### Trusted actor contract

app.py stores only the signed-in user ID in the session as the principal identifier, then loads current user permissions from the database through a private authentication helper. Re-read privilege information for protected operations; do not rely on browser flags or stale UI state.

Server-internal example:

```python
actor = {
    "user_id": 3,
    "is_admin": False,
    "affiliate_publisher_id": 1,
}
```

Public catalog requests use actor=None. Never construct this dictionary from request.form or request.json. The authentication lookup is private backend infrastructure, not a publicly selectable generic users query.

Browser-submitted is_admin, is_publisher, is_developer, user_id, average_rating, payment amount, or order status must not establish permissions or trusted state. Reject unknown fields rather than silently accepting them.

## 7. Shared db.py Interface (Planned)

```python
execute_operation(
    operation="catalog.list",
    actor=None,
    filters={"max_price": "1000.00"},
    values={},
    sort="price_asc",
    page=1,
    page_size=12,
    connection=None,
)
```

Use None defaults in actual function signatures instead of mutable dictionary defaults. Defaults above illustrate a call, not a required signature definition.

### Input meanings

| Input | Contract |
|---|---|
| operation | Fixed server-known operation name. Unknown names are rejected. Normally chosen by the route, not freely forwarded from the browser. |
| actor | Trusted server-loaded identity; None for public operations. |
| filters | Named supported fields/operators defined for that operation. No arbitrary WHERE strings. |
| values | Writable fields only; policy validates types/ranges and protected fields. |
| sort | Key mapped to a server-defined ORDER BY fragment. |
| page / page_size | List reads only; positive integers. Default 12 items, maximum 50. Invalid values rejected. |
| connection | Internal-only optional existing transaction connection; never browser input. |

Do not use positional arrays for unrelated fields. Lists are appropriate for multiple genre/platform IDs.

### Builder contract

```python
query, params = build_operation(...)
cursor.execute(query, params)
```

Example result:

```python
query = "SELECT * FROM vw_game_catalog WHERE current_price <= %s"
params = (Decimal("1000.00"),)
```

Never interpolate values into SQL. Identifiers, operators, selected fields, joins, and sort expressions come from developer-owned definitions. Clients cannot override mandatory security scopes. If OR groups are supported later, always combine the entire client expression as `mandatory_scope AND (client_expression)`.

### Result contract

For list reads:

```python
{
    "rows": [{"game_id": 1, "game_name": "Emberfall Odyssey"}],
    "page": 1,
    "page_size": 12,
    "total": 8,
}
```

- total means matching records before pagination; count queries must preserve deduplication.
- Detail reads return a dictionary or None when no permitted record matches.
- Writes return `{"affected_rows": 1, "insert_id": None}`; insert_id is supplied only for inserts that generate an ID.
- MySQL may report zero changed rows for an update setting existing values. Do not automatically interpret zero as unauthorized/not found; distinguish matched existence from changed values.
- Business workflows can return a documented result such as `{"order_id": 6, "status": "PAID"}`.
- Keep Decimal/date/datetime objects in Python results used by templates. If JSON is added, serialize money as two-decimal strings and timestamps as documented ISO strings; never solve serialization by converting money to float.

### Errors

Use clear internal exception categories, implemented in db.py: ValidationError, PermissionDenied, ResourceNotFound, ConflictError. app.py translates them to form messages or appropriate HTTP responses. Unexpected database errors are logged without credentials and returned as generic server failures.

A missing private resource may intentionally return 404 rather than reveal another user's record exists. Unit tests must cover the chosen policy.

## 8. Operation Policies and Access Rules

Every operation defines its target, allowed input keys, result fields, validators, access check, and mandatory scope. Deny by default. Broad database grants do not replace application checks.

| Operation | Access / required restriction |
|---|---|
| catalog.list / catalog.detail | Public, catalog fields only. |
| cart.list / cart.add / cart.remove | Signed-in user; user_id fixed from actor. |
| wishlist.list / wishlist.add / wishlist.remove | Signed-in user; user_id fixed from actor. |
| orders.list / orders.detail | Signed-in user; own orders only, including for admins on customer routes. |
| ownership.list | Signed-in user; own paid purchases only. |
| reviews.list | Public output excludes email/password/financial information. |
| reviews.save / reviews.delete | Own review; save additionally requires ownership through a currently paid successful order. |
| games.create / games.update | Admin or affiliated publisher, with the scope below. |
| games.delete | Admin only initially; foreign keys may prevent deletion. |
| publishers/developers/genres/platforms management | Admin only. |
| reports.sales / reports.game_sales | Admin only initially. |
| checkout | Signed-in workflow, not unrestricted table writes. |

### Publisher policy

- Publisher permissions derive from users.affiliate_publisher_id.
- For existing games, add games.publisher_id = actor.affiliate_publisher_id to reads/updates intended for publisher management.
- For creation, publisher_id is supplied by the server from the actor's affiliation.
- Publisher edits cannot change publisher_id or grant themselves a different affiliation.
- Allowed publisher fields: game_name, description, thumbnail_url, developer_id, standard_price, discount_percent, release_date, genre_ids, platform_ids.
- Admins may also choose publisher_id, with foreign-key validation.
- genre_ids/platform_ids are virtual input fields processed into junction tables; they are NOT columns in games.
- Never allow edits to game_id or average_rating through these forms.
- Company/genre/platform creation is admin-only; publishers select existing records.
- There is no developer role yet. Adding it requires an explicit schema and policy decision.

The builder handles ordinary CRUD. Authentication, password hashing, checkout, verified review writes, and compound game/junction updates use explicit workflow functions that call the shared engine internally. Do not expose generic writes to users/orders/payments merely because they are tables.

## 9. Browser-to-Flask Data Contract

First version uses ordinary HTML forms and query strings, not a separate JSON API. JavaScript is optional enhancement. Build URLs with url_for(). Include CSRF tokens in all state-changing forms.

### Catalog GET parameters

```text
/?q=ember&max_price=1000.00&genre_ids=1&genre_ids=2&sort=price_asc&page=1
```

| Name | Meaning |
|---|---|
| q | Trimmed search text, maximum 150 characters; search game_name. Treat % and _ as literal search characters unless explicitly documented otherwise. |
| min_price / max_price | Optional nonnegative decimal amounts, max two fractional digits; min <= max. Filter current_price. |
| genre_ids / platform_ids | Repeated positive integer IDs, parsed using request.args.getlist(). Deduplicate; reject invalid IDs. |
| sort | One of name, price_asc, price_desc, rating_desc, newest. |
| page | Positive integer; default 1. |
| page_size | Positive integer; default 12, maximum 50. |

Within one selected category list, match ANY chosen ID. Across genre and platform groups, use AND. Prefer EXISTS filters to avoid duplicate game cards from junction joins. All sorting adds game_id as a stable tie-breaker. For newest, place missing release dates last.

### Form payloads

| Form | Browser fields | Server-supplied values |
|---|---|---|
| Register | username, email, password, confirm_password | Hash; is_admin=false; affiliation=NULL; email_verified=false. |
| Login | username, password | Authenticated session user_id after verification. |
| Cart/wishlist add/remove | Game ID in URL, csrf_token | Acting user_id. |
| Review save | rating, review_text, csrf_token; game ID in URL | Author user_id; purchase eligibility. |
| Review delete | csrf_token; game ID in URL | Author user_id. |
| Game create/edit | Allowed game fields; repeated genre_ids/platform_ids; csrf_token | Publisher scope; cached rating excluded. |
| Checkout | simulation_result=success or failure; csrf_token | Cart contents, prices, total, order/payment statuses, dummy references. |

Text/number conversion rules:

- Empty optional text/date values become None; absent update fields mean leave unchanged.
- Creation requires documented required fields. An empty required value is rejected.
- IDs must be positive integers. Prices/discounts use Decimal, not float; reject excessive fractional digits instead of silently rounding input into another permitted value.
- Ratings must be exact half-star choices from 0 through 5 before database conversion.
- Enforce database string lengths and foreign-key existence. Review text maximum for the UI is 5000 characters; description maximum is 10000.
- Proposed local registration rule: username 3–50 characters, email <=100, password 12–128 characters with matching confirmation. Validate email format; do not claim that format validation verifies ownership.
- For game updates, omitted genre/platform list leaves it unchanged; an explicit empty list clears it. HTML routes must deliberately translate submitted controls into that convention, e.g. with a presence marker for each list.
- thumbnail_url may be an http/https image URL or a project-local /static/images/ path. Blank values use a placeholder. Do not fetch arbitrary submitted URLs on the backend.

### Proposed routes

| Method | URL | Purpose |
|---|---|---|
| GET | / | Catalog |
| GET, POST | /register | Registration |
| GET, POST | /login | Login |
| POST | /logout | Logout |
| GET | /game/<int:game_id> | Game details |
| GET | /cart | Own cart |
| POST | /cart/add/<int:game_id> | Add game |
| POST | /cart/remove/<int:game_id> | Remove game |
| GET | /wishlist | Own wishlist |
| POST | /wishlist/add/<int:game_id> | Save game |
| POST | /wishlist/remove/<int:game_id> | Remove saved game |
| GET, POST | /checkout | Preview / simulate checkout |
| GET | /orders | Own orders and library section |
| POST | /game/<int:game_id>/review | Create/update own review |
| POST | /game/<int:game_id>/review/delete | Delete own review |
| GET | /admin | Admin or publisher management page, scoped content |
| POST | /admin/game/save | Create game or edit supplied game_id |
| POST | /admin/game/<int:game_id>/delete | Admin-only deletion |
| POST | /admin/catalog/<entity>/save | Admin-only allowlisted company/tag management |

An existing game_id on the save form is only a record selector, not proof of permission. Avoid arbitrary dispatch from the URL entity: map supported values to server operation definitions.

After successful form submissions, redirect to a GET page. Use flashed messages. GET routes must not change state. Proposed errors: 400 invalid input, 403 denied access, 404 missing/permitted-record-not-found, 409 conflicting state. Unauthenticated page requests redirect to login using only validated local next URLs.

## 10. Flask-to-Template Data Contract

Use dictionary-style rows. Keep context names consistent across routes and templates.

| Template | Planned context |
|---|---|
| base.html | current_user public subset or None; flashed messages; CSRF helpers. |
| index.html | games, filters, genres, platforms, pagination. |
| login.html / register.html | errors and non-secret submitted fields; never echo passwords. |
| game.html | game, game_genres, game_platforms, reviews, own_review, owns_game. |
| cart.html | items, total. |
| wishlist.html | items. |
| checkout.html | items, total, errors. |
| orders.html | orders, owned_games; each order includes its items. |
| admin.html | manageable_games, publishers, developers, genres, platforms; admin-only reports where permitted. |

Catalog game dictionaries expose view fields such as game_id, game_name, thumbnail_url, standard_price, discount_percent, current_price, average_rating, review_count. Missing thumbnails show a placeholder. Display 'No reviews' when review_count is zero.

current_user may expose user_id, username, is_admin, affiliate_publisher_id for UI decisions. Password hashes and payment account references must never reach templates. Hiding buttons is not an access check. Jinja escaping stays enabled for user text; do not apply safe to reviews/descriptions.

## 11. Transactions and Business Rules

### Execution ownership

- build_operation returns SQL and parameter values; it never commits.
- For standalone execution, execute_operation opens/cleans up its own connection, commits successful writes, rolls back failed writes, and finalizes read transactions before closing.
- When a connection is supplied, the executor does not commit/rollback/close it. The workflow owns that transaction.
- One checkout must not use several independently committed helper connections.
- Any transaction error is propagated after rollback; never return success after a partial failure.

### Checkout

1. Authenticate user, validate CSRF and simulation choice.
2. Begin one transaction; lock the user's row to serialize their checkouts.
3. Read/lock cart rows, reject empty cart, and reject games already owned.
4. Lock relevant game rows in consistent ID order and calculate prices from current database values.
5. Use Decimal and the same two-decimal half-up rounding rule for every line; total is the sum of rounded lines.
6. Insert PENDING order and snapshot items.
7. Insert finalized simulated payment with explicit status and link it.
8. Success: order PAID, remove purchased cart entries, commit.
9. Simulated failure: payment FAILED, order CANCELLED, keep cart, commit that deliberate result.
10. Unexpected database error: rollback everything and show a controlled failure.

One payment result per order. Retrying a failed attempt creates a new order. No refund UI initially. Free/100%-discounted games may have successful zero-amount simulated payments. Recheck price changes at final POST; preview totals are not authoritative. Serialize cart mutations with the same user-lock convention, and handle deadlocks/timeouts safely.

### Reviews

Only currently owned games may receive new/updated reviews. Check ownership from paid successful orders; author comes from actor. Users may delete their own reviews. Review writes use one transaction, lock the game row before review mutation, and let the trigger update the average. Do not separately calculate the average in Python.

### Game edits

Validate all game fields and selected genre/platform IDs. Update the game and junction rows in one transaction. Enforce publisher scope before editing any related records. Admin/publisher assignment changes and checkout game locks need consistent handling; permissions cannot be checked once and then ignored if the record changes concurrently.

### Reporting

Payment revenue sums one payment per qualifying order, not payment amounts after joining to item rows. Item revenue sums price_paid for qualifying orders. Genre totals overlap because a game can belong to multiple genres; label them as non-additive. Historical prices must not change when catalog prices change.

## 12. Security and Testing Requirements

- SQL values always use parameter binding. Identifiers and operators are allowlisted.
- Deny unknown operations/fields and enforce server scopes on every protected operation.
- Registration cannot grant roles or affiliations. No generic public user-management operation.
- Load privilege information from trusted server state. Website roles differ from MySQL accounts.
- CSRF protection on writes, password hashing, safe session configuration, no secrets in logs/Git.
- Use minimal session data; Flask's default signed cookies are not encrypted secret storage.
- Runtime database account has required data permissions and selected procedure execution, not root/setup privileges.
- Builder unit tests inspect SQL and parameters. Integration tests use isolated MySQL data.
- Required tests: role spoofing, cross-user resource access, publisher cross-company edits, forbidden fields, unsafe sort/filter inputs, half-star validation, duplicate cart/order items, checkout rollback, duplicate/concurrent checkout, average triggers and last-review deletion.
- Tests must distinguish no-op updates from missing records and verify pagination does not duplicate games.

## 13. Implementation Order

1. Verify SQL scripts and synchronize this README/diagrams with local schema.
2. Fill requirements.txt, .gitignore, .env.example and local .env.
3. Implement db.py connection handling and exceptions.
4. Implement operation registry, validation, actor policies and SQL/parameter builder.
5. Test catalog.list, catalog.detail and games.update policies before exposing writes.
6. Implement app.py and minimal base/index pages; prove real games load from MySQL.
7. Implement registration/login/logout and trusted actor loading.
8. Add publisher/admin CRUD, wishlist/cart, then transactional checkout/orders.
9. Add review workflows, reporting, and integration tests.
10. Complete styling, screenshots, diagrams, report, and presentation.

Update operation definitions, routes, SQL, tests, and documentation together when contracts change. The goal is reusable query construction with visible policies—not an unrestricted browser-controlled database console.

## 14. Technical References

- Flask: https://flask.palletsprojects.com/en/stable/
- MySQL Connector/Python execution: https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursor-execute.html
- OWASP authorization: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- OWASP SQL injection prevention: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html
- OWASP mass assignment: https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html
- Werkzeug password helpers: https://werkzeug.palletsprojects.com/en/stable/utils/
