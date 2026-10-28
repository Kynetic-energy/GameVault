"""GameVault database layer: operation registry -> validated plan -> SQL + params -> execute."""

import os
import re
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib.parse import urlsplit

try:
    import mysql.connector
    from mysql.connector.constants import ClientFlag
except ImportError:
    mysql = None


# ---------------------------------------------------------------- constants

CENT = Decimal("0.01")
ZERO = Decimal("0")
MAX_MONEY = Decimal("99999999.99")
MAX_ID = 2_147_483_647
DEFAULT_PAGE_SIZE = 12
MAX_PAGE_SIZE = 50
MAX_LIST = 100


# ---------------------------------------------------------------- errors

class DBError(Exception):
    pass


class ValidationError(DBError):
    pass


class PermissionDenied(DBError):
    pass


class ResourceNotFound(DBError):
    pass


class ConflictError(DBError):
    pass


class DatabaseFailure(DBError):
    pass


class ConfigurationError(RuntimeError):
    pass


# ---------------------------------------------------------------- connection

def get_connection():
    if mysql is None:
        raise ConfigurationError("mysql-connector-python is not installed.")
    missing = [n for n in ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD") if n not in os.environ]
    if missing:
        raise ConfigurationError("Missing environment variables: " + ", ".join(missing))
    try:
        return mysql.connector.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ.get("DB_PORT", "3306")),
            database=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            charset="utf8mb4",
            collation="utf8mb4_unicode_ci",
            autocommit=False,
            client_flags=[ClientFlag.FOUND_ROWS],
        )
    except mysql.connector.Error as exc:
        raise DatabaseFailure(f"Could not connect to MySQL: {exc}") from exc


def _translate(exc):
    errno, message = getattr(exc, "errno", None), str(exc)
    if errno == 1062:
        if "username" in message:
            return ConflictError("That username is already taken.")
        if "email" in message:
            return ConflictError("That email is already registered.")
        return ConflictError("That record already exists.")
    if errno == 1451:
        return ConflictError("This record is still referenced by other data.")
    if errno == 1452:
        return ValidationError("A referenced record does not exist.")
    return DatabaseFailure(message)


@contextmanager
def transaction():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except mysql.connector.Error as exc:
        conn.rollback()
        raise _translate(exc) from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------- validators

def _fail(name, message):
    raise ValidationError(f"{name.replace('_', ' ').capitalize()} {message}")


def _check_id(name, value):
    if isinstance(value, bool):
        _fail(name, "must be a positive whole number.")
    if isinstance(value, str) and re.fullmatch(r"[0-9]{1,10}", value.strip()):
        value = int(value.strip())
    if not isinstance(value, int) or not 1 <= value <= MAX_ID:
        _fail(name, "must be a positive whole number.")
    return value


def _check_id_list(name, value):
    if not isinstance(value, (list, tuple, set)) or len(value) > MAX_LIST:
        _fail(name, "must be a short list of IDs.")
    return sorted({_check_id(name, v) for v in value})


def _check_text(name, value, max_len):
    if not isinstance(value, str):
        _fail(name, "must be text.")
    text = value.strip()
    if "\x00" in text or len(text) > max_len:
        _fail(name, f"must be at most {max_len} characters.")
    return text


def _check_decimal(name, value, low=ZERO, high=MAX_MONEY):
    if isinstance(value, (bool, float)):
        _fail(name, "must be a decimal amount.")
    if isinstance(value, str) and re.fullmatch(r"[0-9]{1,10}(\.[0-9]{1,2})?", value.strip()):
        value = Decimal(value.strip())
    elif isinstance(value, int):
        value = Decimal(value)
    if (not isinstance(value, Decimal) or not value.is_finite()
            or not low <= value <= high or value != value.quantize(CENT)):
        _fail(name, f"must be an amount from {low} to {high} with at most two decimals.")
    return value.quantize(CENT)


def _check_rating(name, value):
    try:
        if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
            raise InvalidOperation
        if isinstance(value, str) and not re.fullmatch(r"[0-9](\.[0-9]{1,2})?", value.strip()):
            raise InvalidOperation
        number = Decimal(str(value).strip())
    except InvalidOperation:
        _fail(name, "must be a half-star value from 0 to 5.")
    if not number.is_finite() or not 0 <= number <= 5 or number * 2 != (number * 2).to_integral_value():
        _fail(name, "must be a half-star value from 0 to 5.")
    return number.quantize(Decimal("0.1"))


def _check_date(name, value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()):
        try:
            return date.fromisoformat(value.strip())
        except ValueError:
            pass
    _fail(name, "must be a valid date (YYYY-MM-DD).")


def _check_datetime(name, value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.strip())
        except ValueError:
            pass
    _fail(name, "must be a valid date or datetime.")


def _check_thumbnail(name, value):
    text = _check_text(name, value, 255)
    if text.startswith("/static/images/"):
        if ".." in text or not re.fullmatch(r"/static/images/[A-Za-z0-9._/-]+", text):
            _fail(name, "is not a valid local image path.")
        return text
    parts = urlsplit(text)
    if parts.scheme not in ("http", "https") or not parts.netloc or re.search(r"\s", text):
        _fail(name, "must be an http/https URL or a /static/images/ path.")
    return text


def _check_page(name, value, default, high):
    if value is None:
        return default
    if isinstance(value, str) and re.fullmatch(r"[0-9]{1,9}", value.strip()):
        value = int(value.strip())
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= high:
        _fail(name, f"must be a whole number from 1 to {high}.")
    return value


@dataclass(frozen=True)
class F:
    kind: str
    nullable: bool = False
    max_len: int = 255
    low: Decimal = ZERO
    high: Decimal = MAX_MONEY
    admin_only: bool = False


def _check_field(spec, name, raw):
    if spec.kind != "hash" and (raw is None or (isinstance(raw, str) and not raw.strip())):
        if spec.nullable:
            return None
        _fail(name, "is required.")
    if spec.kind == "text":
        return _check_text(name, raw, spec.max_len)
    if spec.kind == "decimal":
        return _check_decimal(name, raw, spec.low, spec.high)
    if spec.kind == "hash":
        if not isinstance(raw, str) or not raw:
            _fail(name, "is invalid.")
        return raw
    checks = {"id": _check_id, "thumbnail": _check_thumbnail, "date": _check_date,
              "datetime": _check_datetime, "rating": _check_rating}
    return checks[spec.kind](name, raw)


def _line_price(standard_price, discount_percent):
    price = Decimal(standard_price) * (Decimal(100) - Decimal(discount_percent)) / Decimal(100)
    return price.quantize(CENT, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------- registry

_OPS = {}
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_FILTER_OPERATORS = {
    "=",
    "!=",
    ">",
    "<",
    ">=",
    "<=",
    "contains",
    "in",
    "exists",
    "not_exists",
}
_FILTER_CHECKS = {
    "id": _check_id,
    "id_list": _check_id_list,
    "search": lambda name, value: _check_text(name, value, 150),
    "decimal": _check_decimal,
}


def _q(ref):
    parts = ref.split(".")
    if not 1 <= len(parts) <= 2 or not all(_IDENT.match(p) for p in parts):
        raise RuntimeError(f"Unsafe identifier in operation definition: {ref!r}")
    return ".".join(f"`{p}`" for p in parts)


def _add(name, kind, source, **options):
    op = {"name": name, "kind": kind, "source": source, "access": "user", "internal": False,
          "select": {}, "filters": {}, "required_filters": (), "sorts": {}, "default_sort": "",
          "tiebreak": "", "paginated": True, "fields": {}, "required": (), "scope": None, "fixed": None}
    op.update(options)
    for ref in op["select"].values():
        _q(ref)
    for alias in list(op["select"]) + list(op["fields"]):
        _q(alias)
    for _kind, column, operator in op["filters"].values():
        _q(column)
        assert operator in _FILTER_OPERATORS
    _OPS[name] = op


def _cols(*names):
    return {n: n for n in names}


def _own(column="user_id"):
    return lambda actor: [(column, actor["user_id"])]


def _own_publisher(actor):
    return [] if actor["is_admin"] else [("publisher_id", actor["affiliate_publisher_id"])]


def _fixed_user(actor, values):
    return {"user_id": actor["user_id"]}


def _fixed_publisher(actor, values):
    return {} if actor["is_admin"] else {"publisher_id": actor["affiliate_publisher_id"]}


# ---- catalog

_CATALOG_COLS = _cols("game_id", "game_name", "thumbnail_url", "publisher_id", "publisher_name",
                      "developer_id", "developer_name", "standard_price", "discount_percent",
                      "current_price", "release_date", "average_rating", "review_count")
_CATALOG_SORTS = {
    "name": "game_name ASC",
    "price_asc": "current_price ASC",
    "price_desc": "current_price DESC",
    "rating_desc": "average_rating DESC",
    "newest": "release_date IS NULL ASC, release_date DESC",
}
_GAME_ID = {"game_id": ("id", "game_id", "=")}
_GAME_FIELDS = {
    "game_name": F("text", max_len=150),
    "description": F("text", nullable=True, max_len=10000),
    "thumbnail_url": F("thumbnail", nullable=True),
    "publisher_id": F("id", admin_only=True),
    "developer_id": F("id"),
    "standard_price": F("decimal"),
    "discount_percent": F("decimal", high=Decimal("100")),
    "release_date": F("date", nullable=True),
}

_add("catalog.list", "list", "vw_game_catalog", access="public", select=_CATALOG_COLS,
     filters={
         "q": ("search", "game_name", "contains"),
         "min_price": ("decimal", "current_price", ">="),
         "max_price": ("decimal", "current_price", "<="),
         "genre_ids": ("id_list", "game_genres.genre_id", "exists"),
         "platform_ids": ("id_list", "game_platforms.platform_id", "exists"),
         "exclude_genre_ids": ("idlist", "game_genres.genre_id", "not_exists"),
         "exclude_platform_ids": ("idlist", "game_platforms.platform_id", "not_exists"),
         "publisher_id": ("id", "publisher_id", "="),
     },
     sorts=_CATALOG_SORTS, default_sort="name", tiebreak="game_id ASC")
_add("catalog.detail", "detail", "vw_game_catalog", access="public",
     select={**_CATALOG_COLS, "description": "description"},
     filters=_GAME_ID, required_filters=("game_id",))
_add("game_genres.list", "list", "game_genres AS gg JOIN genres AS g ON g.genre_id = gg.genre_id",
     access="public", select={"genre_id": "g.genre_id", "genre_name": "g.genre_name"},
     filters={"game_id": ("id", "gg.game_id", "=")}, required_filters=("game_id",),
     sorts={"name": "g.genre_name ASC"}, default_sort="name", tiebreak="g.genre_id ASC", paginated=False)
_add("game_platforms.list", "list", "game_platforms AS gp JOIN platforms AS p ON p.platform_id = gp.platform_id",
     access="public", select={"platform_id": "p.platform_id", "platform_name": "p.platform_name"},
     filters={"game_id": ("id", "gp.game_id", "=")}, required_filters=("game_id",),
     sorts={"name": "p.platform_name ASC"}, default_sort="name", tiebreak="p.platform_id ASC", paginated=False)

# ---- lookup tables managed by admins

_ENTITIES = {
    "publishers": ("publisher_id", "publisher_name", 100, "admin"),
    "developers": ("dev_id", "dev_name", 100, "publisher"),
    "genres": ("genre_id", "genre_name", 50, "public"),
    "platforms": ("platform_id", "platform_name", 50, "public"),
}
CATALOG_ENTITIES = {e: {a: f"{e}.{a}" for a in ("list", "create", "update", "delete")} for e in _ENTITIES}

for _table, (_pk, _name, _length, _list_access) in _ENTITIES.items():
    _add(f"{_table}.list", "list", _table, access=_list_access, select=_cols(_pk, _name),
         sorts={"name": f"{_name} ASC"}, default_sort="name", tiebreak=f"{_pk} ASC", paginated=False)
    _add(f"{_table}.create", "insert", _table, access="admin",
         fields={_name: F("text", max_len=_length)}, required=(_name,))
    _add(f"{_table}.update", "update", _table, access="admin",
         fields={_name: F("text", max_len=_length)}, filters={_pk: ("id", _pk, "=")}, required_filters=(_pk,))
    _add(f"{_table}.delete", "delete", _table, access="admin",
         filters={_pk: ("id", _pk, "=")}, required_filters=(_pk,))

# ---- games (publisher/admin management)

_add("games.manage_list", "list", "vw_game_catalog", access="publisher", select=_CATALOG_COLS,
     filters={"q": ("search", "game_name", "contains")},
     sorts=_CATALOG_SORTS, default_sort="name", tiebreak="game_id ASC", scope=_own_publisher)
_add("games.manage_detail", "detail", "vw_game_catalog", access="publisher",
     select={**_CATALOG_COLS, "description": "description"},
     filters=_GAME_ID, required_filters=("game_id",), scope=_own_publisher)
_add("games.create", "insert", "games", access="publisher", fields=_GAME_FIELDS,
     required=("game_name", "developer_id", "standard_price", "publisher_id"), fixed=_fixed_publisher)
_add("games.update", "update", "games", access="publisher", fields=_GAME_FIELDS,
     filters=_GAME_ID, required_filters=("game_id",), scope=_own_publisher)
_add("games.delete", "delete", "games", access="admin", filters=_GAME_ID, required_filters=("game_id",))

GAME_LINKS = {"genre_ids": ("game_genres", "genre_id"), "platform_ids": ("game_platforms", "platform_id")}
for _table, _column in GAME_LINKS.values():
    _add(f"{_table}._insert", "insert", _table, access="publisher", internal=True,
         fields={"game_id": F("id"), _column: F("id")}, required=("game_id", _column))

# ---- cart and wishlist

_GAME_JOIN = {"game_id": "c.game_id", "game_name": "c.game_name", "thumbnail_url": "c.thumbnail_url",
              "standard_price": "c.standard_price", "discount_percent": "c.discount_percent",
              "current_price": "c.current_price"}

_add("cart.list", "list", "cart_items AS ci JOIN vw_game_catalog AS c ON c.game_id = ci.game_id",
     select={"cart_item_id": "ci.cart_item_id", **_GAME_JOIN, "added_at": "ci.added_at"},
     sorts={"added": "ci.added_at ASC"}, default_sort="added", tiebreak="ci.cart_item_id ASC",
     scope=_own("ci.user_id"), paginated=False)
_add("cart.add", "insert", "cart_items", fields={"game_id": F("id")}, required=("game_id",), fixed=_fixed_user)
_add("cart.remove", "delete", "cart_items", filters={"game_id": ("id", "game_id", "=")},
     required_filters=("game_id",), scope=_own())
_add("wishlist.list", "list", "wishlists AS w JOIN vw_game_catalog AS c ON c.game_id = w.game_id",
     select={"wishlist_id": "w.wishlist_id", **_GAME_JOIN, "added_at": "w.added_at"},
     sorts={"added_desc": "w.added_at DESC"}, default_sort="added_desc", tiebreak="w.wishlist_id DESC",
     scope=_own("w.user_id"), paginated=False)
_add("wishlist.add", "insert", "wishlists", fields={"game_id": F("id")}, required=("game_id",), fixed=_fixed_user)
_add("wishlist.remove", "delete", "wishlists", filters={"game_id": ("id", "game_id", "=")},
     required_filters=("game_id",), scope=_own())

# ---- orders and ownership

_ORDER_COLS = _cols("order_id", "order_date", "order_status", "payment_status",
                    "payment_amount", "item_count", "order_total")

_add("orders.list", "list", "vw_order_summary", select=_ORDER_COLS,
     sorts={"date_desc": "order_date DESC"}, default_sort="date_desc", tiebreak="order_id DESC", scope=_own())
_add("orders.detail", "detail", "vw_order_summary", select=_ORDER_COLS,
     filters={"order_id": ("id", "order_id", "=")}, required_filters=("order_id",), scope=_own())
_add("orders.items", "list",
     "order_items AS oi JOIN orders AS o ON o.order_id = oi.order_id JOIN games AS g ON g.game_id = oi.game_id",
     select={"order_item_id": "oi.order_item_id", "order_id": "oi.order_id", "game_id": "oi.game_id",
             "game_name": "g.game_name", "thumbnail_url": "g.thumbnail_url", "price_paid": "oi.price_paid"},
     filters={"order_id": ("id", "oi.order_id", "="), "order_ids": ("id_list", "oi.order_id", "in")},
     sorts={"default": "oi.order_item_id ASC"}, default_sort="default", tiebreak="oi.order_item_id ASC",
     scope=_own("o.user_id"), paginated=False)
_add("ownership.list", "list", "vw_owned_games AS og JOIN vw_game_catalog AS c ON c.game_id = og.game_id",
     select={"game_id": "og.game_id", "game_name": "og.game_name", "thumbnail_url": "c.thumbnail_url",
             "first_purchase_date": "og.first_purchase_date"},
     sorts={"name": "og.game_name ASC", "recent": "og.first_purchase_date DESC"},
     default_sort="name", tiebreak="og.game_id ASC", scope=_own("og.user_id"))
_add("ownership.detail", "detail", "vw_owned_games", select=_cols("game_id", "first_purchase_date"),
     filters=_GAME_ID, required_filters=("game_id",), scope=_own())

# ---- reviews

_REVIEW_TEXT = F("text", nullable=True, max_len=5000)

_add("reviews.list", "list", "reviews AS r JOIN users AS u ON u.user_id = r.user_id", access="public",
     select={"username": "u.username", "rating": "r.rating", "review_text": "r.review_text",
             "review_date": "r.review_date"},
     filters={"game_id": ("id", "r.game_id", "=")}, required_filters=("game_id",),
     sorts={"newest": "r.review_date DESC", "rating_desc": "r.rating DESC"},
     default_sort="newest", tiebreak="r.user_id ASC")
_add("reviews.own", "detail", "reviews", select=_cols("game_id", "rating", "review_text", "review_date"),
     filters=_GAME_ID, required_filters=("game_id",), scope=_own())
_add("reviews._insert", "insert", "reviews", internal=True,
     fields={"game_id": F("id"), "rating": F("rating"), "review_text": _REVIEW_TEXT},
     required=("game_id", "rating"), fixed=_fixed_user)
_add("reviews._update", "update", "reviews", internal=True,
     fields={"rating": F("rating"), "review_text": _REVIEW_TEXT, "review_date": F("datetime")},
     filters=_GAME_ID, required_filters=("game_id",), scope=_own())
_add("reviews._delete", "delete", "reviews", internal=True,
     filters=_GAME_ID, required_filters=("game_id",), scope=_own())

# ---- users and reports

_add("users._insert", "insert", "users", access="public", internal=True,
     fields={"username": F("text", max_len=50), "email": F("text", max_len=100), "password_hash": F("hash")},
     required=("username", "email", "password_hash"),
     fixed=lambda actor, values: {"is_admin": 0, "email_verified": 0, "affiliate_publisher_id": None})
_add("users._by_username", "detail", "users", access="public", internal=True,
     select=_cols("user_id", "password_hash"), filters={"username": ("search", "username", "=")},
     required_filters=("username",))
_add("users._actor", "detail", "users", access="public", internal=True,
     select=_cols("user_id", "username", "is_admin", "affiliate_publisher_id"),
     filters={"user_id": ("id", "user_id", "=")}, required_filters=("user_id",))
_add("reports.game_sales", "list", "vw_game_sales", access="admin",
     select=_cols("game_id", "game_name", "copies_sold", "sales_revenue"),
     sorts={"revenue_desc": "sales_revenue DESC", "copies_desc": "copies_sold DESC", "name": "game_name ASC"},
     default_sort="revenue_desc", tiebreak="game_id ASC")


def list_operations():
    return sorted(name for name, op in _OPS.items() if not op["internal"])


# ---------------------------------------------------------------- planning

class Plan:
    def __init__(self, op, actor):
        self.op = op
        self.actor = actor
        self.where = ""
        self.where_params = ()
        self.values = {}
        self.order = ""
        self.page = 1
        self.page_size = DEFAULT_PAGE_SIZE


def _clean_actor(actor):
    if actor is None:
        return None
    if not isinstance(actor, Mapping):
        raise PermissionDenied("Invalid actor.")
    user_id, admin, publisher = actor.get("user_id"), actor.get("is_admin"), actor.get("affiliate_publisher_id")

    def valid_id(v):
        return isinstance(v, int) and not isinstance(v, bool) and v > 0

    if not valid_id(user_id) or admin not in (True, False) or (publisher is not None and not valid_id(publisher)):
        raise PermissionDenied("Invalid actor.")
    return {"user_id": user_id, "is_admin": bool(admin), "affiliate_publisher_id": publisher}


def _require_actor(actor):
    actor = _clean_actor(actor)
    if actor is None:
        raise PermissionDenied("Sign in required.")
    return actor


def _authorize(op, actor):
    level = op["access"]
    if level == "public":
        return
    if actor is None:
        raise PermissionDenied("Sign in required.")
    if level == "admin" and not actor["is_admin"]:
        raise PermissionDenied("Administrator access required.")
    if level == "publisher" and not (actor["is_admin"] or actor["affiliate_publisher_id"]):
        raise PermissionDenied("Publisher or administrator access required.")


def _escape_like(text):
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _client_conditions(op, filters):
    unknown = [k for k in filters if k not in op["filters"]]
    if unknown:
        raise ValidationError("Unsupported filter(s): " + ", ".join(sorted(map(str, unknown)))[:100])

    clean = {}
    for name, raw in filters.items():
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            continue
        value = _FILTER_CHECKS[op["filters"][name][0]](name, raw)
        if value != []:
            clean[name] = value
    for name in op["required_filters"]:
        if name not in clean:
            _fail(name, "is required.")
    if "min_price" in clean and "max_price" in clean and clean["min_price"] > clean["max_price"]:
        raise ValidationError("Min price must not be greater than max price.")

    conditions, params = [], []
    for name, (kind, column, operator) in op["filters"].items():
        if name not in clean:
            continue
        value = clean[name]
        if operator == "contains":
            conditions.append(f"{_q(column)} LIKE %s")
            params.append("%" + _escape_like(value) + "%")
        elif operator == "in":
            conditions.append(f"{_q(column)} IN ({', '.join(['%s'] * len(value))})")
            params.extend(value)
        elif operator == "exists":
            table, link_column = column.split(".")
            conditions.append(
                f"EXISTS (SELECT 1 FROM {_q(table)} AS `j` WHERE `j`.`game_id` = {_q(op['source'])}.`game_id` "
                f"AND `j`.{_q(link_column)} IN ({', '.join(['%s'] * len(value))}))")
            params.extend(value)
        elif operator == "not_exists":
            table, link_column = column.split(".")
            conditions.append(
                f"NOT EXISTS (SELECT 1 FROM {q(table)} AS j "
                f"WHERE j.game_id = {q(op['source'])}.game_id "
                f"AND j.{q(link_column)} IN ({placeholders}))"
            )
        else:
            conditions.append(f"{_q(column)} {operator} %s")
            params.append(value)
    return conditions, params


def _build_where(plan, filters):
    op = plan.op
    parts, params = [], []
    for column, value in (op["scope"](plan.actor) if op["scope"] else []):
        if value is None:
            raise PermissionDenied("You do not have access to this resource.")
        parts.append(f"{_q(column)} = %s")
        params.append(value)
    client_sql, client_params = _client_conditions(op, filters)
    if client_sql:
        parts.append("(" + " AND ".join(client_sql) + ")")
    if not parts and op["kind"] in ("update", "delete"):
        raise RuntimeError(f"{op['name']} would run without a WHERE clause")
    plan.where = " WHERE " + " AND ".join(parts) if parts else ""
    plan.where_params = tuple(params + client_params)


def _build_values(plan, values):
    op, actor = plan.op, plan.actor
    unknown = [k for k in values if k not in op["fields"]]
    if unknown:
        raise ValidationError("Unsupported field(s): " + ", ".join(sorted(map(str, unknown)))[:100])
    clean = {}
    for name, raw in values.items():
        spec = op["fields"][name]
        if spec.admin_only and not (actor and actor["is_admin"]):
            raise PermissionDenied(f"You may not set {name.replace('_', ' ')}.")
        clean[name] = _check_field(spec, name, raw)
    if op["kind"] == "update" and not clean:
        raise ValidationError("No fields to update.")
    if op["kind"] == "insert":
        if op["fixed"]:
            clean.update(op["fixed"](actor, clean))
        for name in op["required"]:
            if clean.get(name) is None:
                _fail(name, "is required.")
    plan.values = clean


def _prepare(op, actor, filters, values, sort, page, page_size):
    actor = _clean_actor(actor)
    _authorize(op, actor)
    filters = {} if filters is None else filters
    values = {} if values is None else values
    if not isinstance(filters, Mapping) or not isinstance(values, Mapping):
        raise ValidationError("filters and values must be mappings.")

    kind = op["kind"]
    if kind != "list" and (sort is not None or page is not None or page_size is not None):
        raise ValidationError("sort and pagination apply to list operations only.")
    if kind == "list" and not op["paginated"] and (page is not None or page_size is not None):
        raise ValidationError("This list is not paginated.")
    if kind == "insert" and filters:
        raise ValidationError("Insert operations do not accept filters.")
    if kind in ("list", "detail", "delete") and values:
        raise ValidationError(f"{kind} operations do not accept values.")

    plan = Plan(op, actor)
    if kind != "insert":
        _build_where(plan, filters)
    if kind in ("insert", "update"):
        _build_values(plan, values)
    if kind == "list":
        key = sort if sort else op["default_sort"]
        if not isinstance(key, str) or key not in op["sorts"]:
            raise ValidationError("Unsupported sort option.")
        plan.order = f"{op['sorts'][key]}, {op['tiebreak']}"
        if op["paginated"]:
            plan.page = _check_page("page", page, 1, 1_000_000)
            plan.page_size = _check_page("page_size", page_size, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE)
    return plan


# ---------------------------------------------------------------- SQL rendering

def _render(plan):
    op, kind = plan.op, plan.op["kind"]
    if kind == "list":
        select = ", ".join(f"{_q(ref)} AS {_q(alias)}" for alias, ref in op["select"].items())
        sql = f"SELECT {select} FROM {op['source']}{plan.where} ORDER BY {plan.order}"
        params = plan.where_params
        if op["paginated"]:
            sql += " LIMIT %s OFFSET %s"
            params += (plan.page_size, (plan.page - 1) * plan.page_size)
        return sql, params
    if kind == "detail":
        select = ", ".join(f"{_q(ref)} AS {_q(alias)}" for alias, ref in op["select"].items())
        return f"SELECT {select} FROM {op['source']}{plan.where} LIMIT 1", plan.where_params
    if kind == "insert":
        columns = [c for c in op["fields"] if c in plan.values] + [c for c in plan.values if c not in op["fields"]]
        sql = (f"INSERT INTO {_q(op['source'])} ({', '.join(_q(c) for c in columns)}) "
               f"VALUES ({', '.join(['%s'] * len(columns))})")
        return sql, tuple(plan.values[c] for c in columns)
    if kind == "update":
        names = [c for c in op["fields"] if c in plan.values]
        assignments = ", ".join(f"{_q(c)} = %s" for c in names)
        return (f"UPDATE {_q(op['source'])} SET {assignments}{plan.where}",
                tuple(plan.values[c] for c in names) + plan.where_params)
    return f"DELETE FROM {_q(op['source'])}{plan.where}", plan.where_params


def _render_count(plan):
    return f"SELECT COUNT(*) AS total FROM {plan.op['source']}{plan.where}", plan.where_params


def _get_op(name):
    if not isinstance(name, str) or name not in _OPS:
        raise ValidationError("Unknown operation.")
    return _OPS[name]


def build_operation(operation, actor=None, filters=None, values=None, sort=None, page=None, page_size=None):
    return _render(_prepare(_get_op(operation), actor, filters, values, sort, page, page_size))


def build_count_query(operation, actor=None, filters=None):
    return _render_count(_prepare(_get_op(operation), actor, filters, None, None, None, None))


# ---------------------------------------------------------------- execution

def _run_query(conn, plan):
    op, kind = plan.op, plan.op["kind"]
    cur = conn.cursor(dictionary=True, buffered=True)
    try:
        sql, params = _render(plan)
        cur.execute(sql, params)
        if kind == "list":
            rows = cur.fetchall()
            if not op["paginated"]:
                return {"rows": rows, "page": 1, "page_size": len(rows), "total": len(rows)}
            count_sql, count_params = _render_count(plan)
            cur.execute(count_sql, count_params)
            return {"rows": rows, "page": plan.page, "page_size": plan.page_size,
                    "total": cur.fetchone()["total"]}
        if kind == "detail":
            return cur.fetchone()
        if kind in ("update", "delete") and cur.rowcount == 0:
            raise ResourceNotFound("Record not found.")
        return {"affected_rows": cur.rowcount, "insert_id": (cur.lastrowid or None) if kind == "insert" else None}
    finally:
        cur.close()


def _run(operation, actor=None, filters=None, values=None, sort=None, page=None, page_size=None, connection=None):
    plan = _prepare(_get_op(operation), actor, filters, values, sort, page, page_size)
    if connection is not None:
        return _run_query(connection, plan)
    with transaction() as conn:
        return _run_query(conn, plan)


def execute_operation(operation, actor=None, filters=None, values=None, sort=None, page=None, page_size=None,
                      connection=None):
    if _get_op(operation)["internal"]:
        raise PermissionDenied("This operation is only available through its workflow function.")
    return _run(operation, actor, filters, values, sort, page, page_size, connection)


# ---------------------------------------------------------------- accounts

def register_user(username, email, password, confirm_password):
    if not all(isinstance(v, str) for v in (username, email, password, confirm_password)):
        raise ValidationError("Invalid registration data.")
    username, email = username.strip(), email.strip()
    if not 3 <= len(username) <= 50:
        raise ValidationError("Username must be 3 to 50 characters.")
    if len(email) > 100 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise ValidationError("Enter a valid email address.")
    if not 12 <= len(password) <= 128:
        raise ValidationError("Password must be 12 to 128 characters.")
    if password != confirm_password:
        raise ValidationError("Passwords do not match.")
    from werkzeug.security import generate_password_hash
    result = _run("users._insert", values={"username": username, "email": email,
                                           "password_hash": generate_password_hash(password, method="pbkdf2:sha256")})
    return {"user_id": result["insert_id"]}


def authenticate(username, password):
    from werkzeug.security import check_password_hash
    if not isinstance(username, str) or not isinstance(password, str) or not username.strip():
        raise ValidationError("Invalid username or password.")
    row = _run("users._by_username", filters={"username": username})
    if row is None or not check_password_hash(row["password_hash"], password):
        raise ValidationError("Invalid username or password.")
    return row["user_id"]


def load_current_user(user_id):
    try:
        user_id = _check_id("user_id", user_id)
    except ValidationError:
        return None
    row = _run("users._actor", filters={"user_id": user_id})
    if row is None:
        return None
    return {"user_id": row["user_id"], "username": row["username"], "is_admin": bool(row["is_admin"]),
            "affiliate_publisher_id": row["affiliate_publisher_id"]}


def load_actor(user_id):
    user = load_current_user(user_id)
    if user is None:
        return None
    return {key: user[key] for key in ("user_id", "is_admin", "affiliate_publisher_id")}


# ---------------------------------------------------------------- cart, checkout, orders

def get_cart(actor):
    actor = _require_actor(actor)
    rows = _run("cart.list", actor=actor)["rows"]
    for row in rows:
        row["line_price"] = _line_price(row["standard_price"], row["discount_percent"])
    return {"items": rows, "total": sum((row["line_price"] for row in rows), ZERO)}


def checkout_preview(actor):
    cart = get_cart(actor)
    return {"items": cart["items"], "total": cart["total"],
            "errors": [] if cart["items"] else ["Your cart is empty."]}


def checkout(actor, simulation_result):
    actor = _require_actor(actor)
    if simulation_result not in ("success", "failure"):
        raise ValidationError("Choose a simulated payment result.")
    succeeded = simulation_result == "success"
    user_id = actor["user_id"]

    with transaction() as conn:
        cart = _run("cart.list", actor=actor, connection=conn)["rows"]
        if not cart:
            raise ValidationError("Your cart is empty.")
        game_ids = [row["game_id"] for row in cart]
        marks = ", ".join(["%s"] * len(game_ids))

        cur = conn.cursor(dictionary=True, buffered=True)
        cur.execute(f"SELECT game_name FROM vw_owned_games WHERE user_id = %s AND game_id IN ({marks})",
                    (user_id, *game_ids))
        owned = [row["game_name"] for row in cur.fetchall()]
        if owned:
            raise ConflictError("You already own: " + ", ".join(owned) + ".")

        lines = [(row["game_id"], _line_price(row["standard_price"], row["discount_percent"])) for row in cart]
        total = sum((price for _, price in lines), ZERO)

        cur.execute("INSERT INTO orders (user_id, order_status) VALUES (%s, 'PENDING')", (user_id,))
        order_id = cur.lastrowid
        cur.executemany("INSERT INTO order_items (order_id, game_id, price_paid) VALUES (%s, %s, %s)",
                        [(order_id, game_id, price) for game_id, price in lines])
        cur.execute("INSERT INTO payments (payee_account_no, recipient_account_no, amount, payment_status) "
                    "VALUES (%s, %s, %s, %s)",
                    (f"SIM-PAYER-{user_id}", "GAMEVAULT-SIM-MERCHANT", total, "SUCCESS" if succeeded else "FAILED"))
        status = "PAID" if succeeded else "CANCELLED"
        cur.execute("UPDATE orders SET transaction_id = %s, order_status = %s WHERE order_id = %s",
                    (cur.lastrowid, status, order_id))
        if succeeded:
            cur.execute(f"DELETE FROM cart_items WHERE user_id = %s AND game_id IN ({marks})",
                        (user_id, *game_ids))
    return {"order_id": order_id, "status": status, "total": total}


def get_orders_with_items(actor, page=None, page_size=None):
    actor = _require_actor(actor)
    with transaction() as conn:
        result = _run("orders.list", actor=actor, page=page, page_size=page_size, connection=conn)
        order_ids = [row["order_id"] for row in result["rows"]]
        items = []
        if order_ids:
            items = _run("orders.items", actor=actor, filters={"order_ids": order_ids}, connection=conn)["rows"]
        for row in result["rows"]:
            row["items"] = [item for item in items if item["order_id"] == row["order_id"]]
    return result


# ---------------------------------------------------------------- reviews

def save_review(actor, game_id, rating, review_text=None):
    actor = _require_actor(actor)
    game_id = _check_id("game_id", game_id)
    rating = _check_rating("rating", rating)
    review_text = _check_field(_REVIEW_TEXT, "review_text", review_text)
    with transaction() as conn:
        if _run("ownership.detail", actor=actor, filters={"game_id": game_id}, connection=conn) is None:
            raise PermissionDenied("You can only review games you own.")
        if _run("reviews.own", actor=actor, filters={"game_id": game_id}, connection=conn) is None:
            _run("reviews._insert", actor=actor, connection=conn,
                 values={"game_id": game_id, "rating": rating, "review_text": review_text})
        else:
            _run("reviews._update", actor=actor, filters={"game_id": game_id}, connection=conn,
                 values={"rating": rating, "review_text": review_text, "review_date": datetime.now()})
    return {"game_id": game_id, "rating": rating}


def delete_review(actor, game_id):
    actor = _require_actor(actor)
    return _run("reviews._delete", actor=actor, filters={"game_id": _check_id("game_id", game_id)})


# ---------------------------------------------------------------- games and lookup tables

def _split_game_values(values):
    if not isinstance(values, Mapping):
        raise ValidationError("values must be a mapping.")
    scalar = {k: v for k, v in values.items() if k not in GAME_LINKS}
    links = {k: _check_id_list(k, values[k]) for k in GAME_LINKS if k in values}
    return scalar, links


def _save_links(conn, actor, game_id, links):
    for key, ids in links.items():
        table, column = GAME_LINKS[key]
        conn.cursor().execute(f"DELETE FROM {table} WHERE game_id = %s", (game_id,))
        for item_id in ids:
            _run(f"{table}._insert", actor=actor, values={"game_id": game_id, column: item_id}, connection=conn)


def create_game(actor, values):
    actor = _require_actor(actor)
    scalar, links = _split_game_values(values)
    with transaction() as conn:
        game_id = _run("games.create", actor=actor, values=scalar, connection=conn)["insert_id"]
        _save_links(conn, actor, game_id, links)
    return {"game_id": game_id}


def update_game(actor, game_id, values):
    actor = _require_actor(actor)
    game_id = _check_id("game_id", game_id)
    scalar, links = _split_game_values(values)
    if not scalar and not links:
        raise ValidationError("No fields to update.")
    with transaction() as conn:
        if _run("games.manage_detail", actor=actor, filters={"game_id": game_id}, connection=conn) is None:
            raise ResourceNotFound("Game not found.")
        if scalar:
            _run("games.update", actor=actor, filters={"game_id": game_id}, values=scalar, connection=conn)
        _save_links(conn, actor, game_id, links)
    return {"game_id": game_id}


def save_catalog_entity(actor, entity, entity_id, name):
    if entity not in _ENTITIES:
        raise ResourceNotFound("Unknown catalog entity.")
    pk, name_column = _ENTITIES[entity][:2]
    ops = CATALOG_ENTITIES[entity]
    if entity_id is None or (isinstance(entity_id, str) and not entity_id.strip()):
        return execute_operation(ops["create"], actor=actor, values={name_column: name})
    return execute_operation(ops["update"], actor=actor, filters={pk: entity_id}, values={name_column: name})


def delete_catalog_entity(actor, entity, entity_id):
    if entity not in _ENTITIES:
        raise ResourceNotFound("Unknown catalog entity.")
    pk = _ENTITIES[entity][0]
    return execute_operation(CATALOG_ENTITIES[entity]["delete"], actor=actor, filters={pk: entity_id})


# ---------------------------------------------------------------- admin reports

def sales_summary(actor, start, end):
    actor = _require_actor(actor)
    if not actor["is_admin"]:
        raise PermissionDenied("Administrator access required.")
    start, end = _check_datetime("start", start), _check_datetime("end", end)
    if start >= end:
        raise ValidationError("Start must be earlier than end.")
    with transaction() as conn:
        cur = conn.cursor()
        cur.callproc("sp_sales_summary", (start, end))
        for result in cur.stored_results():
            return dict(zip(result.column_names, result.fetchone()))


def recalculate_average_ratings(actor):
    actor = _require_actor(actor)
    if not actor["is_admin"]:
        raise PermissionDenied("Administrator access required.")
    with transaction() as conn:
        conn.cursor().callproc("sp_recalculate_average_ratings")