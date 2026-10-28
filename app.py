import os

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

import db


load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

csrf = CSRFProtect(app)


def get_current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None

    return db.load_current_user(user_id)


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


@app.route("/cart")
def cart():
    return render_template("cart.html", items=[], total=0)


@app.route("/wishlist")
def wishlist():
    return render_template("wishlist.html", items=[])


@app.route("/orders")
def orders():
    return render_template("orders.html", orders=[], owned_games=[])


@app.route("/admin")
def admin():
    return render_template("admin.html")


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