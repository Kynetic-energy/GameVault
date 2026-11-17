import os

from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

import db


load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

csrf = CSRFProtect(app)

def get_current_user():
    if "current_user" not in g:
        user_id = session.get("user_id")

        g.current_user = (
            db.load_current_user(user_id)
            if user_id is not None
            else None
        )

        if user_id is not None and g.current_user is None:
            session.clear()

    return g.current_user


@app.context_processor
def inject_current_user():
    return {"current_user": get_current_user()}


def parse_catalog_filters():
    q = request.args.get("q", "").strip()
    if len(q) > 150:
        q = q[:150]

    min_price = request.args.get("min_price", "").strip() or None
    max_price = request.args.get("max_price", "").strip() or None

    genre_ids = request.args.getlist("genre_ids")
    platform_ids = request.args.getlist("platform_ids")
    exclude_genre_ids = request.args.getlist("exclude_genre_ids")
    exclude_platform_ids = request.args.getlist("exclude_platform_ids")

    sort = request.args.get("sort", "name")
    if sort not in {"name", "price_asc", "price_desc", "rating_desc", "newest"}:
        sort = "name"

    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1

    try:
        page_size = int(request.args.get("page_size", 12))
    except ValueError:
        page_size = 12

    page_size = min(max(page_size, 1), 50)

    filters = {
        "sort": sort,
        "page": page,
        "page_size": page_size,
    }

    if q:
        filters["q"] = q

    if min_price:
        filters["min_price"] = min_price

    if max_price:
        filters["max_price"] = max_price

    if genre_ids:
        filters["genre_ids"] = genre_ids

    if platform_ids:
        filters["platform_ids"] = platform_ids

    if exclude_genre_ids:
        filters["exclude_genre_ids"] = exclude_genre_ids

    if exclude_platform_ids:
        filters["exclude_platform_ids"] = exclude_platform_ids

    return filters


@app.route("/")
def index():
    parsed = parse_catalog_filters()

    catalog_filters = {
        key: value
        for key, value in parsed.items()
        if key not in {"sort", "page", "page_size"}
    }

    result = db.execute_operation(
        operation="catalog.list",
        actor=None,
        filters=catalog_filters,
        sort=parsed["sort"],
        page=parsed["page"],
        page_size=parsed["page_size"],
    )

    genres = db.execute_operation(
        operation="genres.list",
        actor=None,
    )["rows"]

    platforms = db.execute_operation(
        operation="platforms.list",
        actor=None,
    )["rows"]

    total = result["total"]
    page_size = result["page_size"]
    total_pages = max(1, (total + page_size - 1) // page_size)

    return render_template(
        "index.html",
        games=result["rows"],
        filters=parsed,
        genres=genres,
        platforms=platforms,
        pagination={
            "page": result["page"],
            "page_size": result["page_size"],
            "total": result["total"],
            "total_pages": total_pages,
        },
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        errors = []

        if not username:
            errors.append("Username is required.")

        if not password:
            errors.append("Password is required.")

        if not errors:
            try:
                user_id = db.authenticate(username, password)
                session.clear()
                session["user_id"] = user_id
                flash("Logged in successfully.", "success")
                return redirect(url_for("index"))

            except db.DBError as exc:
                errors.append(str(exc))

        return render_template(
            "login.html",
            errors=errors,
            username=username,
        )

    return render_template("login.html", errors=[], username="")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))

@app.route("/register")
def register():
    return render_template("register.html")


# ---------------------------------------------------------------- customer routes


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()

        if user is None:
            flash("Please sign in to continue.", "info")
            return redirect(url_for("login"), code=303)

        g.customer_actor = {
            "user_id": user["user_id"],
            "is_admin": user["is_admin"],
            "affiliate_publisher_id": user["affiliate_publisher_id"],
        }

        return view(*args, **kwargs)

    return wrapped

# ---------------------------------------------------------------- checkout


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    actor = g.customer_actor

    if request.method == "POST":
        try:
            check_form_fields({
                "csrf_token",
                "simulation_result",
            })

            simulation_result = request.form.get(
                "simulation_result",
                "",
            )

            result = db.checkout(
                actor=actor,
                simulation_result=simulation_result,
            )

        except db.PermissionDenied as exc:
            abort(403, description=str(exc))

        except db.DatabaseFailure:
            app.logger.error("Checkout database operation failed.")

            flash(
                "Checkout could not be completed. "
                "Check your orders before trying again.",
                "error",
            )

            return redirect(
                url_for("checkout"),
                code=303,
            )

        except (db.ValidationError, db.ConflictError) as exc:
            flash(str(exc), "error")

            return redirect(
                url_for("checkout"),
                code=303,
            )

        if result["status"] == "PAID":
            flash(
                f"Payment simulation successful. "
                f"Order #{result['order_id']} is paid. "
                f"Total: INR {result['total']:.2f}.",
                "success",
            )

            return redirect(
                url_for("orders"),
                code=303,
            )

        flash(
            f"Payment simulation failed. "
            f"Order #{result['order_id']} was cancelled. "
            "Your cart has been kept so you can try again.",
            "warning",
        )

        return redirect(
            url_for("checkout"),
            code=303,
        )

    try:
        preview = db.checkout_preview(actor)

        return render_template(
            "checkout.html",
            items=preview["items"],
            total=preview["total"],
            errors=preview["errors"],
        )

    except db.DatabaseFailure:
        app.logger.error("Checkout preview database read failed.")

        abort(
            503,
            description="Checkout is temporarily unavailable.",
        )
        
def cart_failure(exc):
    if isinstance(exc, db.PermissionDenied):
        abort(403, description=str(exc))

    if isinstance(exc, db.ResourceNotFound):
        abort(404, description=str(exc))

    if isinstance(exc, db.DatabaseFailure):
        app.logger.error("Cart database operation failed.")
        flash(
            "We could not update your cart. Please try again.",
            "error",
        )
    else:
        flash(str(exc), "error")

    return redirect(url_for("cart"), code=303)


@app.route("/cart")
@login_required
def cart():
    try:
        result = db.get_cart(g.customer_actor)

        return render_template(
            "cart.html",
            items=result["items"],
            total=result["total"],
        )

    except db.DatabaseFailure:
        app.logger.error("Cart database read failed.")
        abort(
            503,
            description="Your cart is temporarily unavailable.",
        )


@app.route("/cart/add/<int:game_id>", methods=["POST"])
@login_required
def cart_add(game_id):
    actor = g.customer_actor

    try:
        check_form_fields({"csrf_token"})

        game = db.execute_operation(
            "catalog.detail",
            filters={"game_id": game_id},
        )

        if game is None:
            raise db.ResourceNotFound("Game not found.")

        owned_game = db.execute_operation(
            "ownership.detail",
            actor=actor,
            filters={"game_id": game_id},
        )

        if owned_game is not None:
            flash(
                "You already own this game.",
                "info",
            )
            return redirect(url_for("cart"), code=303)

        try:
            db.execute_operation(
                "cart.add",
                actor=actor,
                values={"game_id": game_id},
            )
        except db.ConflictError:
            flash(
                "This game is already in your cart.",
                "info",
            )
        else:
            flash(
                f"{game['game_name']} added to your cart.",
                "success",
            )

    except db.DBError as exc:
        return cart_failure(exc)

    return redirect(url_for("cart"), code=303)


@app.route("/cart/remove/<int:game_id>", methods=["POST"])
@login_required
def cart_remove(game_id):
    try:
        check_form_fields({"csrf_token"})

        db.execute_operation(
            "cart.remove",
            actor=g.customer_actor,
            filters={"game_id": game_id},
        )

        flash("Game removed from your cart.", "success")

    except db.ResourceNotFound:
        flash(
            "That game is no longer in your cart.",
            "info",
        )

    except db.DBError as exc:
        return cart_failure(exc)

    return redirect(url_for("cart"), code=303)


@app.route("/wishlist")
def wishlist():
    return render_template("wishlist.html", items=[])


@app.route("/orders")
def orders():
    return render_template("orders.html", orders=[], owned_games=[])


# ---------------------------------------------------------------- management


def management_required(admin_only=False):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = get_current_user()

            if user is None:
                if request.method == "GET":
                    flash(
                        "Please sign in to access management.",
                        "info",
                    )
                    return redirect(url_for("login"))

                abort(401, description="Sign in required.")

            if admin_only:
                if not user["is_admin"]:
                    abort(
                        403,
                        description="Administrator access required.",
                    )

            elif not (
                user["is_admin"]
                or user["affiliate_publisher_id"] is not None
            ):
                abort(
                    403,
                    description=(
                        "Publisher or administrator access required."
                    ),
                )

            g.management_actor = {
                "user_id": user["user_id"],
                "is_admin": user["is_admin"],
                "affiliate_publisher_id": (
                    user["affiliate_publisher_id"]
                ),
            }

            return view(*args, **kwargs)

        return wrapped

    return decorator


def check_form_fields(allowed, repeated=()):
    unknown = set(request.form) - set(allowed)

    if unknown:
        raise db.ValidationError(
            "The form contains unsupported fields."
        )

    repeated = set(repeated)

    for field in request.form:
        if (
            field not in repeated
            and len(request.form.getlist(field)) != 1
        ):
            raise db.ValidationError(
                f"Multiple values are not allowed for {field}."
            )


def read_game_values(actor):
    scalar_fields = {
        "game_name",
        "description",
        "thumbnail_url",
        "developer_id",
        "standard_price",
        "discount_percent",
        "release_date",
    }

    if actor["is_admin"]:
        scalar_fields.add("publisher_id")

    allowed = scalar_fields | {
        "csrf_token",
        "game_id",
        "genre_ids",
        "platform_ids",
        "genre_ids_present",
        "platform_ids_present",
    }

    check_form_fields(
        allowed,
        repeated={"genre_ids", "platform_ids"},
    )

    values = {
        field: request.form[field]
        for field in scalar_fields
        if field in request.form
    }

    for field in ("genre_ids", "platform_ids"):
        marker = f"{field}_present"

        if marker in request.form:
            if request.form[marker] != "1":
                raise db.ValidationError(
                    "Invalid genre/platform presence marker."
                )

            values[field] = request.form.getlist(field)

        elif field in request.form:
            raise db.ValidationError(
                "The genre/platform presence marker is missing."
            )

    game_id = request.form.get("game_id", "").strip()

    if not game_id:
        required = {
            "game_name",
            "developer_id",
            "standard_price",
        }

        if actor["is_admin"]:
            required.add("publisher_id")

        for field in required:
            if not values.get(field, "").strip():
                raise db.ValidationError(
                    f"{field.replace('_', ' ').capitalize()} "
                    "is required."
                )

    return game_id, values


def management_failure(exc):
    if isinstance(exc, db.PermissionDenied):
        abort(403, description=str(exc))

    if isinstance(exc, db.ResourceNotFound):
        abort(404, description=str(exc))

    if isinstance(exc, db.DatabaseFailure):
        app.logger.error(
            "Management database operation failed (%s).",
            type(exc).__name__,
        )
        flash(
            "The database operation failed. Please try again.",
            "error",
        )

    else:
        flash(str(exc), "error")

    return redirect(url_for("admin"), code=303)


@app.route("/admin")
@management_required()
def admin():
    actor = g.management_actor

    try:
        page_text = request.args.get("page", "1")

        if (
            not page_text.isascii()
            or not page_text.isdigit()
            or not 1 <= int(page_text) <= 1_000_000
        ):
            raise db.ValidationError(
                "Page must be a positive whole number."
            )

        page = int(page_text)

        result = db.execute_operation(
            "games.manage_list",
            actor=actor,
            page=page,
            page_size=12,
        )

        manageable_games = []

        for row in result["rows"]:
            game = db.execute_operation(
                "games.manage_detail",
                actor=actor,
                filters={"game_id": row["game_id"]},
            )

            if game is None:
                continue

            genre_rows = db.execute_operation(
                "game_genres.list",
                filters={"game_id": game["game_id"]},
            )["rows"]

            platform_rows = db.execute_operation(
                "game_platforms.list",
                filters={"game_id": game["game_id"]},
            )["rows"]

            game["genre_ids"] = [
                genre["genre_id"]
                for genre in genre_rows
            ]

            game["platform_ids"] = [
                platform["platform_id"]
                for platform in platform_rows
            ]

            manageable_games.append(game)

        publishers = []

        if actor["is_admin"]:
            publishers = db.execute_operation(
                "publishers.list",
                actor=actor,
            )["rows"]

        developers = db.execute_operation(
            "developers.list",
            actor=actor,
        )["rows"]

        genres = db.execute_operation(
            "genres.list",
            actor=actor,
        )["rows"]

        platforms = db.execute_operation(
            "platforms.list",
            actor=actor,
        )["rows"]

        total_pages = max(
            1,
            (
                result["total"]
                + result["page_size"]
                - 1
            ) // result["page_size"],
        )

        return render_template(
            "admin.html",
            manageable_games=manageable_games,
            publishers=publishers,
            developers=developers,
            genres=genres,
            platforms=platforms,
            errors=[],
            management_pagination={
                "page": result["page"],
                "total": result["total"],
                "total_pages": total_pages,
            },
        )

    except db.ValidationError as exc:
        abort(400, description=str(exc))

    except db.PermissionDenied as exc:
        abort(403, description=str(exc))

    except db.DatabaseFailure:
        app.logger.error(
            "Management page database read failed."
        )
        abort(
            503,
            description=(
                "Management data is temporarily unavailable."
            ),
        )


@app.route("/admin/game/save", methods=["POST"])
@management_required()
def admin_game_save():
    actor = g.management_actor

    try:
        game_id, values = read_game_values(actor)

        if game_id:
            db.update_game(
                actor=actor,
                game_id=game_id,
                values=values,
            )
            flash(
                "Game updated successfully.",
                "success",
            )

        else:
            db.create_game(
                actor=actor,
                values=values,
            )
            flash(
                "Game created successfully.",
                "success",
            )

    except db.DBError as exc:
        return management_failure(exc)

    return redirect(url_for("admin"), code=303)


@app.route(
    "/admin/game/<int:game_id>/delete",
    methods=["POST"],
)
@management_required(admin_only=True)
def admin_game_delete(game_id):
    actor = g.management_actor

    try:
        check_form_fields({"csrf_token"})

        db.execute_operation(
            "games.delete",
            actor=actor,
            filters={"game_id": game_id},
        )

        flash(
            "Game deleted successfully.",
            "success",
        )

    except db.DBError as exc:
        return management_failure(exc)

    return redirect(url_for("admin"), code=303)


@app.route(
    "/admin/catalog/<entity>/save",
    methods=["POST"],
)
@management_required(admin_only=True)
def admin_catalog_save(entity):
    allowed_entities = {
        "publishers",
        "developers",
        "genres",
        "platforms",
    }

    if entity not in allowed_entities:
        abort(
            404,
            description="Unknown catalog entity.",
        )

    actor = g.management_actor

    try:
        check_form_fields({
            "csrf_token",
            "entity_id",
            "name",
        })

        name = request.form.get("name", "").strip()

        if not name:
            raise db.ValidationError(
                "Name is required."
            )

        entity_id = (
            request.form.get("entity_id", "").strip()
            or None
        )

        db.save_catalog_entity(
            actor=actor,
            entity=entity,
            entity_id=entity_id,
            name=name,
        )

        flash(
            "Catalog record updated."
            if entity_id is not None
            else "Catalog record created.",
            "success",
        )

    except db.DBError as exc:
        return management_failure(exc)

    return redirect(url_for("admin"), code=303)


@app.route("/game/<int:game_id>")
def game_detail(game_id):
    game = db.execute_operation(
        operation="catalog.detail",
        actor=None,
        filters={"game_id": game_id},
    )

    if game is None:
        return "Game not found", 404

    game_genres = db.execute_operation(
        operation="game_genres.list",
        actor=None,
        filters={"game_id": game_id},
    )

    game_platforms = db.execute_operation(
        operation="game_platforms.list",
        actor=None,
        filters={"game_id": game_id},
    )

    reviews = db.execute_operation(
        operation="reviews.list",
        actor=None,
        filters={"game_id": game_id},
    )

    return render_template(
        "game.html",
        game=game,
        game_genres=game_genres,
        game_platforms=game_platforms,
        reviews=reviews,
        owns_game=False,
        own_review=None,
    )

if __name__ == "__main__":
    app.run(debug=True)