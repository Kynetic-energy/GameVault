"""Menu-based local tester for the supplied GameVault db.py.
Run from the project directory: python cli.py
Writes affect the configured database. This is a manual test tool, not a web API.
"""

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

# The supplied db.py reads os.environ but does not load .env itself.
load_dotenv(Path(__file__).resolve().parent / ".env")
import db


def encode(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"Cannot display {type(value).__name__}")


def show(result):
    print(json.dumps(result, indent=2, default=encode, ensure_ascii=False))


def ask_json(label, default=None):
    raw = input(f"{label} [Enter for {json.dumps(default)}]: ").strip()
    # Monetary inputs should be quoted strings. parse_float avoids binary floats.
    return json.loads(raw, parse_float=Decimal) if raw else default


def positive_id(label="Game ID"):
    number = int(input(f"{label}: ").strip())
    if number < 1:
        raise ValueError("ID must be positive.")
    return number


def confirm(label):
    return input(f"{label} Type YES to continue: ").strip() == "YES"


def require_actor(user_id):
    actor = db.load_actor(user_id) if user_id is not None else None
    if actor is None:
        raise ValueError("Log in first; your account must still exist.")
    return actor


def pick_operation():
    operations = db.list_operations()
    for index, name in enumerate(operations, 1):
        print(f"{index:2}. {name}")
    choice = input("Operation number or exact name: ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(operations):
        return operations[int(choice) - 1]
    if choice not in operations:
        raise ValueError("Choose a public operation listed above.")
    return choice


def generic_operation(actor, preview=False):
    print("\nExamples for this version of db.py:")
    print('  catalog.list filters: {"q":"ember","max_price":"1500.00"}')
    print('  catalog.detail filters: {"game_id":1}')
    print('  cart.add VALUES: {"game_id":5} (not filters)')
    print('  cart.remove FILTERS: {"game_id":5}')
    print('  genres.create VALUES: {"genre_name":"New genre"}')
    print('  genres.update FILTERS: {"genre_id":1}, VALUES: {"genre_name":"Action"}')
    print("  Nonpaginated lists such as cart.list require pagination=null.")
    print("  Use the workflow menus for game links, reviews, and checkout.")
    name = pick_operation()
    filters = ask_json("Filters JSON", {})
    values = ask_json("Values JSON", {})
    sort = input("Sort key [Enter for default]: ").strip() or None
    paging = ask_json('Pagination JSON, e.g. {"page":1,"page_size":12}', None)
    if not isinstance(filters, dict) or not isinstance(values, dict):
        raise ValueError("Filters and values must be JSON objects.")
    if paging is not None and (not isinstance(paging, dict) or set(paging) - {"page", "page_size"}):
        raise ValueError("Pagination must be null or an object with page/page_size only.")
    kwargs = dict(actor=actor, filters=filters, values=values, sort=sort, **(paging or {}))
    if preview:
        query, params = db.build_operation(name, **kwargs)
        print("\nSQL (not executed):\n" + query)
        print("Parameters:")
        show(params)
        print("A successful preview does not prove records exist or writes will succeed.")
        return
    action = name.rsplit(".", 1)[-1]
    if action in {"create", "update", "delete", "add", "remove"}:
        print("Operation:", name)
        show({"filters": filters, "values": values})
        if not confirm("This writes to your configured database."):
            return
    show(db.execute_operation(name, **kwargs))


def cart_menu(actor):
    choice = input("1 Show cart | 2 Add | 3 Remove | 4 Preview checkout | 5 Checkout: ").strip()
    if choice == "1":
        show(db.get_cart(actor))
    elif choice in {"2", "3"}:
        gid = positive_id()
        if not confirm("Change your cart?"):
            return
        if choice == "2":
            show(db.execute_operation("cart.add", actor=actor, values={"game_id": gid}))
        else:
            show(db.execute_operation("cart.remove", actor=actor, filters={"game_id": gid}))
    elif choice == "4":
        show(db.checkout_preview(actor))
    elif choice == "5":
        show(db.checkout_preview(actor))
        result = input("Simulated result (success/failure): ").strip().lower()
        if result not in {"success", "failure"}:
            raise ValueError("Choose success or failure.")
        if confirm("Create an order/payment (failure also records an attempt)?"):
            show(db.checkout(actor, result))
    else:
        raise ValueError("Unknown cart action.")


def review_menu(actor):
    choice = input("1 List game reviews | 2 My review | 3 Save review | 4 Delete review: ").strip()
    gid = positive_id()
    if choice == "1":
        show(db.execute_operation("reviews.list", actor=actor, filters={"game_id": gid}))
    elif choice == "2":
        show(db.execute_operation("reviews.own", actor=actor, filters={"game_id": gid}))
    elif choice == "3":
        rating = input("Rating (0–5, half-star increments): ").strip()
        text = input("Review text [optional]: ").strip() or None
        if confirm("Save your review?"):
            show(db.save_review(actor, gid, rating, text))
    elif choice == "4":
        if confirm("Delete your review?"):
            show(db.delete_review(actor, gid))
    else:
        raise ValueError("Unknown review action.")


def management_menu(actor):
    print("1 Manageable games | 2 Create game | 3 Update game | 4 Delete game")
    print("5 Save lookup record | 6 Delete lookup record | 7 Sales summary")
    print("8 Game sales | 9 Recalculate average ratings")
    choice = input("Choose: ").strip()
    if choice == "1":
        show(db.execute_operation("games.manage_list", actor=actor))
    elif choice in {"2", "3"}:
        gid = positive_id() if choice == "3" else None
        print('Example: {"game_name":"Test game","developer_id":1,"publisher_id":1,')
        print('"standard_price":"499.00","genre_ids":[1],"platform_ids":[1]}')
        print("Publishers must omit publisher_id. Updates may contain only changed fields.")
        values = ask_json("Game values JSON", {})
        show(values)
        if confirm("Save game and supplied genre/platform links?"):
            show(db.create_game(actor, values) if gid is None else db.update_game(actor, gid, values))
    elif choice == "4":
        gid = positive_id()
        if confirm("Delete game and cascading related data?"):
            show(db.execute_operation("games.delete", actor=actor, filters={"game_id": gid}))
    elif choice in {"5", "6"}:
        entity = input("Entity (publishers/developers/genres/platforms): ").strip()
        if choice == "5":
            eid = input("Record ID [blank to create]: ").strip() or None
            name = input("Name: ").strip()
            if confirm("Save lookup record?"):
                show(db.save_catalog_entity(actor, entity, eid, name))
        else:
            eid = positive_id("Record ID")
            if confirm("Delete lookup record and any cascading links?"):
                show(db.delete_catalog_entity(actor, entity, eid))
    elif choice == "7":
        start = input("Start inclusive (YYYY-MM-DD): ").strip()
        end = input("End exclusive (YYYY-MM-DD): ").strip()
        show(db.sales_summary(actor, start, end))
    elif choice == "8":
        show(db.execute_operation("reports.game_sales", actor=actor))
    elif choice == "9":
        if confirm("Recalculate every game's average rating?"):
            show(db.recalculate_average_ratings(actor))
    else:
        raise ValueError("Unknown management action.")


def main():
    user_id = None
    print("GameVault manual CLI — uses your real configured database.")
    print("Use a disposable development database. Writes are committed.")
    while True:
        try:
            # Reload roles on every menu cycle; do not accept role booleans.
            actor = db.load_actor(user_id) if user_id is not None else None
            if user_id is not None and actor is None:
                user_id = None
                print("Account no longer exists; logged out.")
            label = f"user {user_id}" if actor else "guest"
            print(f"\n--- GameVault [{label}] ---")
            print("1 Connection check     2 Register       3 Login")
            print("4 Logout               5 Catalog       6 Game details")
            print("7 Cart/checkout        8 Reviews       9 Orders with items")
            print("10 Management          11 Run operation (wishlist etc.)")
            print("12 Preview SQL         13 Current user 0 Exit")
            choice = input("Choose: ").strip()
            if choice == "0":
                break
            if choice == "1":
                conn = db.get_connection()
                try:
                    with conn.cursor(dictionary=True) as cur:
                        cur.execute("SELECT DATABASE() AS database_name, VERSION() AS server_version")
                        show(cur.fetchone())
                finally:
                    conn.close()
            elif choice == "2":
                username = input("Username: ").strip()
                email = input("Email: ").strip()
                password = input("Password: ")
                confirmation = input("Confirm password: ")
                if confirm(f"Create account {username!r}?"):
                    show(db.register_user(username, email, password, confirmation))
            elif choice == "3":
                username = input("Username: ").strip()
                password = input("Password: ")

                authenticated_id = db.authenticate(username, password)
                authenticated_actor = db.load_actor(authenticated_id)

                if authenticated_actor is None:
                    raise ValueError(
                        f"Login returned user ID {authenticated_id!r}, "
                        "but the account could not be loaded."
                    )

                user_id = authenticated_id
                actor = authenticated_actor

                print(f"Logged in as {username} (user ID: {user_id}).")
            elif choice == "4":
                user_id = None
                print("Logged out.")
            elif choice == "5":
                filters = ask_json("Catalog filters JSON", {})
                sort = input("Sort [name]: ").strip() or "name"
                show(db.execute_operation("catalog.list", actor=actor, filters=filters, sort=sort))
            elif choice == "6":
                gid = positive_id()
                for operation in ("catalog.detail", "game_genres.list", "game_platforms.list"):
                    print(operation)
                    show(db.execute_operation(operation, actor=actor, filters={"game_id": gid}))
            elif choice == "7":
                cart_menu(require_actor(user_id))
            elif choice == "8":
                review_menu(actor)
            elif choice == "9":
                show(db.get_orders_with_items(require_actor(user_id)))
            elif choice == "10":
                management_menu(require_actor(user_id))
            elif choice == "11":
                generic_operation(actor)
            elif choice == "12":
                generic_operation(actor, preview=True)
            elif choice == "13":
                show(db.load_current_user(user_id) if user_id is not None else None)
            else:
                print("Unknown option.")
        except (db.DBError, db.ConfigurationError, ValueError, TypeError) as exc:
            print(f"Error: {exc}")
        except KeyboardInterrupt:
            print("\nAction interrupted. Recheck database state before retrying writes.")
        except EOFError:
            print("\nGoodbye.")
            break
        except Exception as exc:
            # Surface unexpected implementation bugs without killing the manual test session.
            print(f"Unexpected {type(exc).__name__}: {exc}")
            print("This may be a db.py defect; inspect it before retrying a write.")


if __name__ == "__main__":
    main()