"""
GameVault tests for db.py.

Run:  python -m pytest tests.py

Part 1 (unit)         needs no database; inspects SQL text and parameters.
Part 2 (integration)  runs only when TEST_DB_NAME is set. That database must be
                      disposable (schema.sql -> operations.sql, seed optional),
                      its name must contain "test", and it must NOT be the
                      ordinary development database. Tests create uniquely
                      named rows and never reset anything.

Example:
    export TEST_DB_NAME=gamevault_test     # plus DB_HOST/DB_USER/DB_PASSWORD
    python -m pytest tests.py
"""

import os
import uuid
from decimal import Decimal

import pytest

import db
from db import (ConflictError, PermissionDenied, ResourceNotFound,
                ValidationError, build_count_query, build_operation)

ADMIN = {"user_id": 1, "is_admin": True, "affiliate_publisher_id": None}
PUBLISHER = {"user_id": 3, "is_admin": False, "affiliate_publisher_id": 1}
CUSTOMER = {"user_id": 2, "is_admin": False, "affiliate_publisher_id": None}


# ======================================================================
# Part 1: builder / policy unit tests (no database)
# ======================================================================

class TestCatalogBuilder:
    def test_values_are_parameters_not_sql_text(self):
        query, params = build_operation("catalog.list", filters={"max_price": "1000.00"})
        assert "1000" not in query
        assert Decimal("1000.00") in params

    def test_search_wildcards_are_literal(self):
        _, params = build_operation("catalog.list", filters={"q": "50%_off"})
        assert params[0] == "%50\\%\\_off%"

    def test_search_injection_text_stays_in_params(self):
        query, params = build_operation("catalog.list", filters={"q": "x'; DROP TABLE games;--"})
        assert "DROP" not in query
        assert any("DROP" in str(p) for p in params)

    def test_unsafe_sort_rejected(self):
        with pytest.raises(ValidationError):
            build_operation("catalog.list", sort="price_asc; DROP TABLE games")

    def test_every_sort_has_stable_tiebreaker(self):
        for key in ("name", "price_asc", "price_desc", "rating_desc", "newest"):
            query, _ = build_operation("catalog.list", sort=key)
            assert query.split("ORDER BY")[1].strip().startswith(db._CATALOG_SORTS[key])
            assert "game_id ASC LIMIT" in query

    def test_newest_puts_missing_release_dates_last(self):
        query, _ = build_operation("catalog.list", sort="newest")
        assert "release_date IS NULL ASC, release_date DESC" in query

    def test_unknown_filter_rejected(self):
        with pytest.raises(ValidationError):
            build_operation("catalog.list", filters={"is_admin": 1})

    def test_min_greater_than_max_rejected(self):
        with pytest.raises(ValidationError):
            build_operation("catalog.list", filters={"min_price": "9", "max_price": "1"})

    @pytest.mark.parametrize("bad", ["-1", "1.234", "abc", "1e3", "100000000"])
    def test_bad_prices_rejected(self, bad):
        with pytest.raises(ValidationError):
            build_operation("catalog.list", filters={"max_price": bad})

    def test_genre_filter_uses_exists_not_join(self):
        query, params = build_operation("catalog.list", filters={"genre_ids": ["2", "1", "2"]})
        assert "EXISTS" in query and "JOIN" not in query
        assert params[:2] == (1, 2)  # deduplicated + sorted

    def test_genre_and_platform_groups_are_anded(self):
        query, _ = build_operation(
            "catalog.list", filters={"genre_ids": [1], "platform_ids": [2]})
        assert query.count("EXISTS") == 2 and " AND EXISTS" in query

    @pytest.mark.parametrize("bad", [[0], [-1], ["x"], [True], "1"])
    def test_bad_id_lists_rejected(self, bad):
        with pytest.raises(ValidationError):
            build_operation("catalog.list", filters={"genre_ids": bad})

    def test_pagination_defaults_and_limits(self):
        _, params = build_operation("catalog.list")
        assert params[-2:] == (12, 0)
        _, params = build_operation("catalog.list", page=3, page_size=50)
        assert params[-2:] == (50, 100)
        for page, size in ((0, None), (None, 51), (None, 0), ("x", None)):
            with pytest.raises(ValidationError):
                build_operation("catalog.list", page=page, page_size=size)

    def test_count_query_has_same_where_and_no_limit(self):
        filters = {"genre_ids": [1, 2], "max_price": "500"}
        main_q, main_p = build_operation("catalog.list", filters=filters)
        count_q, count_p = build_count_query("catalog.list", filters=filters)
        assert count_q.startswith("SELECT COUNT(*) AS total FROM vw_game_catalog WHERE")
        assert "LIMIT" not in count_q
        assert count_p == main_p[:-2]


class TestAccessAndScope:
    def test_unknown_operation_rejected(self):
        with pytest.raises(ValidationError):
            build_operation("users.list")

    def test_anonymous_cannot_use_private_operations(self):
        for op in ("cart.list", "orders.list", "wishlist.list", "ownership.list"):
            with pytest.raises(PermissionDenied):
                build_operation(op)

    def test_user_scope_is_forced_from_actor(self):
        query, params = build_operation("orders.list", actor=CUSTOMER)
        assert "`user_id` = %s" in query and params[0] == 2

    def test_user_cannot_supply_user_id(self):
        with pytest.raises(ValidationError):
            build_operation("cart.add", actor=CUSTOMER, values={"game_id": 1, "user_id": 99})

    def test_cart_add_user_id_comes_from_actor(self):
        _, params = build_operation("cart.add", actor=CUSTOMER, values={"game_id": "4"})
        assert params == (4, 2)

    def test_scope_cannot_be_widened_by_filters(self):
        query, _ = build_operation("orders.detail", actor=CUSTOMER, filters={"order_id": 5})
        assert "WHERE `user_id` = %s AND (`order_id` = %s)" in query

    def test_admin_on_customer_routes_still_scoped_to_self(self):
        query, params = build_operation("orders.list", actor=ADMIN)
        assert "`user_id` = %s" in query and params[0] == ADMIN["user_id"]

    def test_role_spoofing_rejected(self):
        for forged in ({"user_id": 2, "is_admin": "1", "affiliate_publisher_id": None},
                       {"user_id": 2, "is_admin": "true", "affiliate_publisher_id": None},
                       {"user_id": 2, "affiliate_publisher_id": None},
                       {"user_id": "2", "is_admin": False, "affiliate_publisher_id": None}):
            with pytest.raises(PermissionDenied):
                build_operation("reports.game_sales", actor=forged)

    def test_reports_admin_only(self):
        for actor in (CUSTOMER, PUBLISHER):
            with pytest.raises(PermissionDenied):
                build_operation("reports.game_sales", actor=actor)
        build_operation("reports.game_sales", actor=ADMIN)

    def test_catalog_entity_management_admin_only(self):
        for actor in (CUSTOMER, PUBLISHER):
            with pytest.raises(PermissionDenied):
                build_operation("genres.create", actor=actor, values={"genre_name": "Puzzle"})
        build_operation("genres.create", actor=ADMIN, values={"genre_name": "Puzzle"})

    def test_games_delete_admin_only(self):
        with pytest.raises(PermissionDenied):
            build_operation("games.delete", actor=PUBLISHER, filters={"game_id": 1})

    def test_workflow_only_ops_not_executable_directly(self):
        for op in ("users._insert", "reviews._insert", "reviews._update",
                   "reviews._delete", "games._lock", "game_genres._insert"):
            with pytest.raises(PermissionDenied):
                db.execute_operation(op, actor=ADMIN, values={})
        assert not any(name.startswith("users.") for name in db.list_operations())


class TestPublisherPolicy:
    def test_publisher_scope_added_to_update(self):
        query, params = build_operation(
            "games.update", actor=PUBLISHER, filters={"game_id": 7},
            values={"game_name": "New"})
        assert "WHERE `publisher_id` = %s AND (`game_id` = %s)" in query
        assert params[-2:] == (1, 7)

    def test_admin_update_has_no_publisher_scope(self):
        query, _ = build_operation("games.update", actor=ADMIN, filters={"game_id": 7},
                                   values={"game_name": "New"})
        assert "`publisher_id` = %s" not in query

    def test_publisher_cannot_change_publisher_id(self):
        with pytest.raises(PermissionDenied):
            build_operation("games.update", actor=PUBLISHER, filters={"game_id": 7},
                            values={"publisher_id": 2})

    def test_publisher_create_forces_own_publisher(self):
        _, params = build_operation(
            "games.create", actor=PUBLISHER,
            values={"game_name": "G", "developer_id": 1, "standard_price": "10"})
        assert 1 in params  # actor.affiliate_publisher_id
        with pytest.raises(PermissionDenied):
            build_operation("games.create", actor=PUBLISHER, values={
                "game_name": "G", "developer_id": 1, "standard_price": "10", "publisher_id": 9})

    def test_admin_create_requires_publisher_id(self):
        with pytest.raises(ValidationError):
            build_operation("games.create", actor=ADMIN, values={
                "game_name": "G", "developer_id": 1, "standard_price": "10"})

    def test_user_without_affiliation_denied(self):
        with pytest.raises(PermissionDenied):
            build_operation("games.manage_list", actor=CUSTOMER)

    @pytest.mark.parametrize("field", ["average_rating", "game_id", "is_admin", "genre_ids"])
    def test_forbidden_fields_rejected(self, field):
        with pytest.raises(ValidationError):
            build_operation("games.update", actor=ADMIN, filters={"game_id": 1},
                            values={field: 1})

    def test_update_requires_selector_and_values(self):
        with pytest.raises(ValidationError):
            build_operation("games.update", actor=ADMIN, values={"game_name": "x"})
        with pytest.raises(ValidationError):
            build_operation("games.update", actor=ADMIN, filters={"game_id": 1}, values={})

    def test_empty_optional_becomes_none_empty_required_rejected(self):
        _, params = build_operation("games.update", actor=ADMIN, filters={"game_id": 1},
                                    values={"description": "  ", "release_date": ""})
        assert params[:2] == (None, None)
        with pytest.raises(ValidationError):
            build_operation("games.update", actor=ADMIN, filters={"game_id": 1},
                            values={"game_name": " "})

    def test_money_never_floats_or_rounds_silently(self):
        for bad in (10.5, "10.999", "-1", "1e2", True):
            with pytest.raises(ValidationError):
                build_operation("games.update", actor=ADMIN, filters={"game_id": 1},
                                values={"standard_price": bad})
        with pytest.raises(ValidationError):
            build_operation("games.update", actor=ADMIN, filters={"game_id": 1},
                            values={"discount_percent": "100.01"})

    def test_thumbnail_rules(self):
        ok = ["https://example.com/a.png", "/static/images/a.png"]
        for url in ok:
            build_operation("games.update", actor=ADMIN, filters={"game_id": 1},
                            values={"thumbnail_url": url})
        for url in ["javascript:alert(1)", "ftp://x/a.png", "/static/images/../x",
                    "//evil.com/a.png", "https://a b.com/x"]:
            with pytest.raises(ValidationError):
                build_operation("games.update", actor=ADMIN, filters={"game_id": 1},
                                values={"thumbnail_url": url})


class TestValidators:
    @pytest.mark.parametrize("good", ["0", "0.5", "1", "4.5", "5", 3, Decimal("2.5")])
    def test_half_star_accepts(self, good):
        assert db._v_rating("rating", good) in {Decimal(str(x)) for x in
                                                 [0, .5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5]}

    @pytest.mark.parametrize("bad", ["4.3", "5.5", "-1", "6", "abc", None, True, "4.25", "1e1"])
    def test_half_star_rejects(self, bad):
        with pytest.raises(ValidationError):
            db._v_rating("rating", bad)

    def test_line_price_rounds_half_up(self):
        assert db._line_price(Decimal("10.05"), Decimal("50")) == Decimal("5.03")
        assert db._line_price(Decimal("999.99"), Decimal("15")) == Decimal("849.99")
        assert db._line_price(Decimal("100.00"), Decimal("100")) == Decimal("0.00")

    def test_report_range_must_be_ordered(self):
        with pytest.raises(ValidationError):
            build_operation("reports.sales", actor=ADMIN,
                            values={"start": "2026-11-01", "end": "2026-10-01"})
        query, _ = build_operation("reports.sales", actor=ADMIN,
                                   values={"start": "2026-10-01", "end": "2026-11-01"})
        assert query == "CALL `sp_sales_summary`(%s, %s)"

    def test_registration_validation(self):
        good = ("player_new", "p@example.com", "a-long-password", "a-long-password")
        for args in (("ab", good[1], good[2], good[3]),
                     (good[0], "not-an-email", good[2], good[3]),
                     (good[0], good[1], "short", "short"),
                     (good[0], good[1], good[2], "different-password"),
                     (good[0], good[1], 123, 123)):
            with pytest.raises(ValidationError):
                db.register_user(*args)  # fails before any DB access

    def test_checkout_input_validated_before_db(self):
        with pytest.raises(ValidationError):
            db.checkout(CUSTOMER, "maybe")
        with pytest.raises(PermissionDenied):
            db.checkout(None, "success")

    def test_registry_identifiers_are_safe(self):
        for op in db._OPS.values():
            for ref in list(op.select.values()) + [f.column for f in op.filters.values() if f.column]:
                db._q(ref)


# ======================================================================
# Part 2: integration tests (isolated MySQL database only)
# ======================================================================

TEST_DB = os.environ.get("TEST_DB_NAME", "")
requires_db = pytest.mark.skipif(not TEST_DB, reason="TEST_DB_NAME not set")


@pytest.fixture(scope="module")
def database():
    ordinary = os.environ.get("DB_NAME", "gamevault")
    assert "test" in TEST_DB.lower(), "TEST_DB_NAME must contain 'test'"
    assert TEST_DB != ordinary and TEST_DB.lower() != "gamevault", \
        "Refusing to run against the ordinary database"
    saved = os.environ.get("DB_NAME")
    os.environ["DB_NAME"] = TEST_DB
    yield TEST_DB
    if saved is None:
        os.environ.pop("DB_NAME", None)
    else:
        os.environ["DB_NAME"] = saved


def _tag() -> str:
    return uuid.uuid4().hex[:10]


def _raw(sql, params=(), fetch=False):
    with db.transaction() as conn:
        cur = conn.cursor(dictionary=True, buffered=True)
        cur.execute(sql, params)
        rows = cur.fetchall() if fetch else cur.lastrowid
        cur.close()
        return rows


def _new_user(is_admin=0, publisher_id=None):
    tag = _tag()
    uid = _raw("INSERT INTO users (username, password_hash, email, is_admin, affiliate_publisher_id) "
               "VALUES (%s, 'x', %s, %s, %s)",
               (f"u_{tag}", f"{tag}@example.com", is_admin, publisher_id))
    return {"user_id": uid, "is_admin": bool(is_admin), "affiliate_publisher_id": publisher_id}


@pytest.fixture()
def world(database):
    """A publisher, developer, three games (prices 100.00 / 10.05@50% / 0.00)."""
    tag = _tag()
    pub = _raw("INSERT INTO publishers (publisher_name) VALUES (%s)", (f"pub_{tag}",))
    dev = _raw("INSERT INTO developers (dev_name) VALUES (%s)", (f"dev_{tag}",))
    games = []
    for name, price, disc in (("A", "100.00", "0"), ("B", "10.05", "50"), ("Free", "0.00", "0")):
        games.append(_raw(
            "INSERT INTO games (game_name, publisher_id, developer_id, standard_price, discount_percent) "
            "VALUES (%s, %s, %s, %s, %s)", (f"{name}_{tag}", pub, dev, price, disc)))
    return {"pub": pub, "dev": dev, "games": games, "tag": tag}


@requires_db
class TestIntegration:
    def test_catalog_pagination_has_no_duplicates(self, world):
        genre_a = _raw("INSERT INTO genres (genre_name) VALUES (%s)", (f"ga_{world['tag']}",))
        genre_b = _raw("INSERT INTO genres (genre_name) VALUES (%s)", (f"gb_{world['tag']}",))
        for gid in world["games"]:
            _raw("INSERT INTO game_genres VALUES (%s, %s)", (gid, genre_a))
            _raw("INSERT INTO game_genres VALUES (%s, %s)", (gid, genre_b))
        seen = []
        for page in (1, 2):
            result = db.execute_operation("catalog.list", filters={"genre_ids": [genre_a, genre_b]},
                                          page=page, page_size=2)
            assert result["total"] == 3
            seen += [r["game_id"] for r in result["rows"]]
        assert sorted(seen) == sorted(world["games"])

    def test_register_login_and_actor(self, database):
        tag = _tag()
        created = db.register_user(f"reg_{tag}", f"{tag}@example.com", "a-long-password", "a-long-password")
        assert db.authenticate(f"reg_{tag}", "a-long-password") == created["user_id"]
        with pytest.raises(ValidationError):
            db.authenticate(f"reg_{tag}", "wrong-password!!")
        with pytest.raises(ConflictError):
            db.register_user(f"reg_{tag}", f"o{tag}@example.com", "a-long-password", "a-long-password")
        assert db.load_actor(created["user_id"]) == {
            "user_id": created["user_id"], "is_admin": False, "affiliate_publisher_id": None}

    def test_cross_user_access_not_possible(self, world):
        alice, bob = _new_user(), _new_user()
        db.execute_operation("cart.add", actor=alice, values={"game_id": world["games"][0]})
        assert db.execute_operation("cart.list", actor=bob)["rows"] == []
        db.execute_operation("cart.remove", actor=bob, filters={"game_id": world["games"][0]})
        assert len(db.execute_operation("cart.list", actor=alice)["rows"]) == 1

    def test_duplicate_cart_item_conflicts(self, world):
        user = _new_user()
        db.execute_operation("cart.add", actor=user, values={"game_id": world["games"][0]})
        with pytest.raises(ConflictError):
            db.execute_operation("cart.add", actor=user, values={"game_id": world["games"][0]})

    def test_checkout_success_prices_and_cart(self, world):
        user = _new_user()
        for gid in world["games"]:
            db.execute_operation("cart.add", actor=user, values={"game_id": gid})
        result = db.checkout(user, "success")
        assert result["status"] == "PAID"
        assert result["total"] == Decimal("105.03")  # 100.00 + 5.03 + 0.00
        assert db.get_cart(user)["items"] == []
        orders = db.get_orders_with_items(user)
        assert orders["total"] == 1 and len(orders["rows"][0]["items"]) == 3
        assert orders["rows"][0]["order_total"] == Decimal("105.03")
        owned = db.execute_operation("ownership.list", actor=user)
        assert owned["total"] == 3

    def test_checkout_failure_keeps_cart_and_creates_no_ownership(self, world):
        user = _new_user()
        db.execute_operation("cart.add", actor=user, values={"game_id": world["games"][0]})
        result = db.checkout(user, "failure")
        assert result["status"] == "CANCELLED"
        assert len(db.get_cart(user)["items"]) == 1
        assert db.execute_operation("ownership.list", actor=user)["total"] == 0

    def test_empty_cart_and_owned_game_rejected(self, world):
        user = _new_user()
        with pytest.raises(ValidationError):
            db.checkout(user, "success")
        db.execute_operation("cart.add", actor=user, values={"game_id": world["games"][2]})
        db.checkout(user, "success")
        with pytest.raises(ConflictError):  # already owned: cannot re-add
            db.execute_operation("cart.add", actor=user, values={"game_id": world["games"][2]})

    def test_duplicate_checkout_cannot_double_charge(self, world):
        user = _new_user()
        db.execute_operation("cart.add", actor=user, values={"game_id": world["games"][0]})
        db.checkout(user, "success")
        with pytest.raises(ValidationError):  # cart already cleared
            db.checkout(user, "success")
        assert db.execute_operation("orders.list", actor=user)["total"] == 1

    def test_prices_are_historical_snapshots(self, world):
        user = _new_user()
        gid = world["games"][0]
        db.execute_operation("cart.add", actor=user, values={"game_id": gid})
        db.checkout(user, "success")
        db.execute_operation("games.update", actor=ADMIN_FOR(world), filters={"game_id": gid},
                             values={"standard_price": "999.00"})
        items = db.get_orders_with_items(user)["rows"][0]["items"]
        assert items[0]["price_paid"] == Decimal("100.00")

    def test_review_requires_ownership_and_updates_average(self, world):
        owner, stranger = _new_user(), _new_user()
        gid = world["games"][0]
        db.execute_operation("cart.add", actor=owner, values={"game_id": gid})
        with pytest.raises(PermissionDenied):
            db.save_review(owner, gid, "4.5", "not yet owned")
        db.checkout(owner, "success")
        with pytest.raises(PermissionDenied):
            db.save_review(stranger, gid, "5", "never bought it")
        db.save_review(owner, gid, "4.5", "great")
        game = db.execute_operation("catalog.detail", filters={"game_id": gid})
        assert game["average_rating"] == Decimal("4.50") and game["review_count"] == 1
        db.save_review(owner, gid, "3", None)  # update path
        assert db.execute_operation("catalog.detail", filters={"game_id": gid})["average_rating"] == Decimal("3.00")
        db.delete_review(owner, gid)  # last review deleted -> 0.00
        game = db.execute_operation("catalog.detail", filters={"game_id": gid})
        assert game["average_rating"] == Decimal("0.00") and game["review_count"] == 0
        with pytest.raises(ResourceNotFound):
            db.delete_review(owner, gid)

    def test_publisher_cannot_edit_other_company_game(self, world):
        other_pub = _raw("INSERT INTO publishers (publisher_name) VALUES (%s)", (f"other_{world['tag']}",))
        outsider = _new_user(publisher_id=other_pub)
        gid = world["games"][0]
        with pytest.raises(ResourceNotFound):
            db.update_game(outsider, gid, {"game_name": "Hijacked"})
        insider = _new_user(publisher_id=world["pub"])
        db.update_game(insider, gid, {"game_name": f"Renamed_{world['tag']}"})
        assert db.execute_operation("catalog.detail", filters={"game_id": gid})["game_name"].startswith("Renamed_")
        # no-op update on same values is not "not found"
        db.update_game(insider, gid, {"game_name": f"Renamed_{world['tag']}"})

    def test_game_junction_replace_and_clear(self, world):
        admin = _new_user(is_admin=1)
        genre = _raw("INSERT INTO genres (genre_name) VALUES (%s)", (f"gj_{world['tag']}",))
        gid = world["games"][1]
        db.update_game(admin, gid, {"genre_ids": [genre]})
        assert len(db.execute_operation("game_genres.list", filters={"game_id": gid})["rows"]) == 1
        db.update_game(admin, gid, {"game_name": f"Same_{world['tag']}"})  # list omitted => unchanged
        assert len(db.execute_operation("game_genres.list", filters={"game_id": gid})["rows"]) == 1
        db.update_game(admin, gid, {"genre_ids": []})  # explicit empty => cleared
        assert db.execute_operation("game_genres.list", filters={"game_id": gid})["rows"] == []
        with pytest.raises(ValidationError):
            db.update_game(admin, gid, {"genre_ids": [2_000_000_000]})  # FK failure

    def test_failed_game_create_rolls_back(self, world):
        admin = _new_user(is_admin=1)
        name = f"Rollback_{world['tag']}"
        with pytest.raises(ValidationError):
            db.create_game(admin, {"game_name": name, "developer_id": world["dev"],
                                   "standard_price": "5", "publisher_id": world["pub"],
                                   "genre_ids": [2_000_000_000]})
        assert _raw("SELECT 1 FROM games WHERE game_name = %s", (name,), fetch=True) == []

    def test_sales_summary_procedure(self, world):
        admin = _new_user(is_admin=1)
        row = db.execute_operation("reports.sales", actor=admin,
                                   values={"start": "2000-01-01", "end": "2100-01-01"})
        assert set(row) == {"paid_orders", "paying_customers", "payment_revenue"}


def ADMIN_FOR(world):
    return _new_user(is_admin=1)