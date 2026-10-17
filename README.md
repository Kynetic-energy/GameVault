# GameVault

Flask + MySQL game-store lab project.

## 1. Directory Structure

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

## 2. Schema Tables

Matches the current SQL shared by the team, without silently applying proposed changes. PK = primary key; FK = foreign key. All primary-key columns are non-null.

### `publishers`

| Column | Data type | Constraints |
|---|---|---|
| `publisher_id` | `INT` | PK, AUTO_INCREMENT |
| `publisher_name` | `VARCHAR(100)` | NOT NULL, UNIQUE |



### `developers`

| Column | Data type | Constraints |
|---|---|---|
| `dev_id` | `INT` | PK, AUTO_INCREMENT |
| `dev_name` | `VARCHAR(100)` | NOT NULL, UNIQUE |



### `users`

| Column | Data type | Constraints |
|---|---|---|
| `user_id` | `INT` | PK, AUTO_INCREMENT |
| `username` | `VARCHAR(50)` | NOT NULL, UNIQUE |
| `password_hash` | `VARCHAR(255)` | NOT NULL |
| `email` | `VARCHAR(100)` | NOT NULL, UNIQUE |
| `email_verified` | `BOOLEAN` | NOT NULL, DEFAULT FALSE |
| `is_admin` | `BOOLEAN` | NOT NULL, DEFAULT FALSE |
| `affiliate_publisher_id` | `INT` | Nullable, FK → publishers.publisher_id |
| `created_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP |



### `genres`

| Column | Data type | Constraints |
|---|---|---|
| `genre_id` | `INT` | PK, AUTO_INCREMENT |
| `genre_name` | `VARCHAR(50)` | NOT NULL, UNIQUE |



### `platforms`

| Column | Data type | Constraints |
|---|---|---|
| `platform_id` | `INT` | PK, AUTO_INCREMENT |
| `platform_name` | `VARCHAR(50)` | NOT NULL, UNIQUE |



### `games`

| Column | Data type | Constraints |
|---|---|---|
| `game_id` | `INT` | PK, AUTO_INCREMENT |
| `game_name` | `VARCHAR(150)` | NOT NULL |
| `description` | `TEXT` | Nullable |
| `thumbnail_url` | `VARCHAR(255)` | Nullable |
| `publisher_id` | `INT` | NOT NULL, FK → publishers.publisher_id |
| `developer_id` | `INT` | NOT NULL, FK → developers.dev_id |
| `standard_price` | `DECIMAL(10,2)` | NOT NULL, >= 0 |
| `discount_percent` | `DECIMAL(5,2)` | NOT NULL, DEFAULT 0.00, range 0–100 |
| `release_date` | `DATE` | Nullable |
| `average_rating` | `DECIMAL(3,2)` | NOT NULL, DEFAULT 0.00, range 0–5 |



### `game_genres`

| Column | Data type | Constraints |
|---|---|---|
| `game_id` | `INT` | NOT NULL, FK → games.game_id |
| `genre_id` | `INT` | NOT NULL, FK → genres.genre_id |

Composite PK: `(game_id, genre_id)`.

### `game_platforms`

| Column | Data type | Constraints |
|---|---|---|
| `game_id` | `INT` | NOT NULL, FK → games.game_id |
| `platform_id` | `INT` | NOT NULL, FK → platforms.platform_id |

Composite PK: `(game_id, platform_id)`.

### `cart_items`

| Column | Data type | Constraints |
|---|---|---|
| `cart_item_id` | `INT` | PK, AUTO_INCREMENT |
| `user_id` | `INT` | NOT NULL, FK → users.user_id |
| `game_id` | `INT` | NOT NULL, FK → games.game_id |
| `added_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

UNIQUE `(user_id, game_id)`.

### `payments`

| Column | Data type | Constraints |
|---|---|---|
| `transaction_id` | `INT` | PK, AUTO_INCREMENT |
| `payee_account_no` | `VARCHAR(50)` | NOT NULL |
| `recipient_account_no` | `VARCHAR(50)` | NOT NULL |
| `payment_time` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| `amount` | `DECIMAL(10,2)` | NOT NULL, >= 0 |
| `payment_status` | `VARCHAR(20)` | NOT NULL, DEFAULT SUCCESS, allowed: SUCCESS / FAILED / REFUNDED |



### `orders`

| Column | Data type | Constraints |
|---|---|---|
| `order_id` | `INT` | PK, AUTO_INCREMENT |
| `user_id` | `INT` | NOT NULL, FK → users.user_id |
| `order_date` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| `order_status` | `VARCHAR(20)` | NOT NULL, DEFAULT PENDING, allowed: PENDING / PAID / CANCELLED / REFUNDED |
| `transaction_id` | `INT` | Nullable, FK → payments.transaction_id |



### `order_items`

| Column | Data type | Constraints |
|---|---|---|
| `order_item_id` | `INT` | PK, AUTO_INCREMENT |
| `order_id` | `INT` | NOT NULL, FK → orders.order_id |
| `game_id` | `INT` | NOT NULL, FK → games.game_id |
| `price_paid` | `DECIMAL(10,2)` | NOT NULL, >= 0, purchase-time price snapshot |



### `reviews`

| Column | Data type | Constraints |
|---|---|---|
| `user_id` | `INT` | NOT NULL, FK → users.user_id |
| `game_id` | `INT` | NOT NULL, FK → games.game_id |
| `rating` | `DECIMAL(2,1)` | NOT NULL, range 0–5 |
| `review_text` | `TEXT` | Nullable |
| `review_date` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

Composite PK: `(user_id, game_id)`. Current range check does not enforce half-star steps.

### `wishlists`

| Column | Data type | Constraints |
|---|---|---|
| `wishlist_id` | `INT` | PK, AUTO_INCREMENT |
| `user_id` | `INT` | NOT NULL, FK → users.user_id |
| `game_id` | `INT` | NOT NULL, FK → games.game_id |
| `added_at` | `DATETIME` | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

UNIQUE `(user_id, game_id)`.

### Foreign-key actions

All foreign keys use ON UPDATE CASCADE in the current script.

| Child column(s) | ON DELETE |
|---|---|
| users.affiliate_publisher_id | SET NULL |
| games.publisher_id, games.developer_id | RESTRICT |
| Both foreign keys in game_genres and game_platforms | CASCADE |
| Both foreign keys in cart_items | CASCADE |
| orders.user_id | CASCADE |
| orders.transaction_id | SET NULL |
| order_items.order_id | CASCADE |
| order_items.game_id | RESTRICT |
| Both foreign keys in reviews and wishlists | CASCADE |

## 3. What Each File Does

These are intended responsibilities, not a claim that implementation is already complete.

### Python files

| File | Responsibility |
|---|---|
| `app.py` | Creates/configures Flask, loads settings, defines routes, handles registration/login/logout, validates forms, checks permissions, renders templates, and coordinates checkout as one transaction. Calls db.py for SQL operations. |
| `db.py` | Handles MySQL connections and parameterized queries for users, catalog, cart, wishlist, orders, payments, reviews, and reports. Checkout queries share one connection so the operation can commit or roll back together. Contains no HTML or routes. |
| `tests.py` | Tests authentication, permissions, searches, cart/wishlist operations, checkout totals and rollback, reviews, and rating triggers. Database tests use a separate test database. |

### Root files

| File | Responsibility |
|---|---|
| `requirements.txt` | Lists Python dependencies and agreed versions. |
| `.env` | Local database credentials and Flask secret key. Never commit to Git. |
| `.env.example` | Required environment-variable names with dummy values for teammates. |
| `.gitignore` | Excludes secrets, virtual environments, caches, and other generated local files. |
| `README.md` | Shared directory, schema, and file-responsibility reference. |

### HTML templates

| File | Responsibility |
|---|---|
| `templates/base.html` | Shared layout, navigation, footer, messages, CSS/JS imports, and page-content blocks. |
| `templates/index.html` | Storefront: game cards, search, genre/platform filters, sorting, and offers. |
| `templates/login.html` | Login form and error messages. |
| `templates/register.html` | Registration form for username, email, and password. |
| `templates/game.html` | Game details, prices, tags, average rating, reviews, review form, and cart/wishlist buttons. |
| `templates/cart.html` | Cart items, current prices, total, remove controls, and checkout link. |
| `templates/wishlist.html` | Saved games, prices/discounts, removal controls, and add-to-cart options. |
| `templates/checkout.html` | Server-calculated order summary and clearly labeled simulated-payment controls. |
| `templates/orders.html` | Own order history, item details, statuses, and owned games derived from paid orders. |
| `templates/admin.html` | Admin catalog management, price/discount editing, order viewing, and reports. |

### Static assets

| File / folder | Responsibility |
|---|---|
| `static/style.css` | Shared styling for pages, cards, forms, tables, buttons, and responsive layouts. |
| `static/script.js` | Optional browser interactions such as confirmation prompts and rating controls; does not replace server-side validation. |
| `static/images/` | Folder for the logo, placeholder thumbnails, and other local images. |

### Database files

| File | Responsibility |
|---|---|
| `database/schema.sql` | Creates the database and 14 tables with keys, constraints, and defaults. The original DROP DATABASE statement destroys existing data, so use it deliberately. |
| `database/seed.sql` | Inserts synthetic sample records for development and demos. Seed passwords must be stored as hashes. |
| `database/operations.sql` | Defines average-rating triggers, views, stored procedures, and clearly separated demonstration queries and DCL examples. Keep triggers here instead of duplicating them in schema.sql. |

### Documentation files

| File | Responsibility |
|---|---|
| `docs/report.md` | Required written sections: problem, objectives, modules, similar systems, gaps/novelty, diagrams, and references. |
| `docs/schema_diagram.png` | Relational schema image showing tables, columns, keys, and relationships. |
| `docs/er_diagram.png` | ER diagram showing entities, relationships, and cardinalities. |
| `docs/presentation.pptx` | Evaluation slides covering the project, database design, SQL demonstrations, and screenshots. |
