from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, inspect
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# Берём подключение к базе из файла .env
# В .env должна быть строка примерно такая:
# DATABASE_URL=postgresql://USER:PASSWORD@localhost:5436/led_price_tags
#app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
# TODO на сервере DATABASE_URL не находит
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:cnfkrth@localhost:5432/led_price_tags"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Island(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    sides = db.relationship(
        "Side",
        backref="island",
        cascade="all, delete-orphan",
        lazy=True
    )


class Side(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    island_id = db.Column(
        db.Integer,
        db.ForeignKey("island.id"),
        nullable=False
    )

    number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    size = db.Column(db.String(20), nullable=False)

    width_px = db.Column(db.Integer, default=256)
    height_px = db.Column(db.Integer, default=32)

    shelf_count = db.Column(db.Integer, default=4)

    price_position = db.Column(db.String(20), default="right")
    text_align = db.Column(db.String(20), default="center")

    product_font_size = db.Column(db.Integer, default=8)
    price_font_size = db.Column(db.Integer, default=12)

    template_name = db.Column(db.String(30), default="standard")

    background_color = db.Column(db.String(20), default="#000000")
    product_color = db.Column(db.String(20), default="#ffffff")
    price_color = db.Column(db.String(20), default="#ffde00")
    font_family = db.Column(db.String(50), default="Arial")

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    shelves = db.relationship(
        "Shelf",
        backref="side",
        cascade="all, delete-orphan",
        order_by="Shelf.number",
        lazy=True
    )


class Shelf(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    side_id = db.Column(
        db.Integer,
        db.ForeignKey("side.id"),
        nullable=False
    )

    number = db.Column(db.Integer, nullable=False)

    products = db.relationship(
        "Product",
        backref="shelf",
        cascade="all, delete-orphan",
        order_by="Product.id",
        lazy=True
    )


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    shelf_id = db.Column(
        db.Integer,
        db.ForeignKey("shelf.id"),
        nullable=False
    )

    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.String(50), nullable=False)


def safe_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def add_column_if_missing(table_name, column_name, column_sql):
    inspector = inspect(db.engine)
    columns = [column["name"] for column in inspector.get_columns(table_name)]

    if column_name not in columns:
        db.session.execute(
            text(f"ALTER TABLE {table_name} ADD COLUMN {column_sql}")
        )
        db.session.commit()


def run_light_migrations():
    add_column_if_missing(
        "side",
        "width_px",
        "width_px INTEGER DEFAULT 256"
    )

    add_column_if_missing(
        "side",
        "height_px",
        "height_px INTEGER DEFAULT 32"
    )

    add_column_if_missing(
        "side",
        "shelf_count",
        "shelf_count INTEGER DEFAULT 4"
    )

    add_column_if_missing(
        "side",
        "price_position",
        "price_position VARCHAR(20) DEFAULT 'right'"
    )

    add_column_if_missing(
        "side",
        "text_align",
        "text_align VARCHAR(20) DEFAULT 'center'"
    )

    add_column_if_missing(
        "side",
        "product_font_size",
        "product_font_size INTEGER DEFAULT 8"
    )

    add_column_if_missing(
        "side",
        "price_font_size",
        "price_font_size INTEGER DEFAULT 12"
    )

    add_column_if_missing(
        "side",
        "template_name",
        "template_name VARCHAR(30) DEFAULT 'standard'"
    )

    add_column_if_missing(
        "side",
        "background_color",
        "background_color VARCHAR(20) DEFAULT '#000000'"
    )

    add_column_if_missing(
        "side",
        "product_color",
        "product_color VARCHAR(20) DEFAULT '#ffffff'"
    )

    add_column_if_missing(
        "side",
        "price_color",
        "price_color VARCHAR(20) DEFAULT '#ffde00'"
    )

    add_column_if_missing(
        "side",
        "font_family",
        "font_family VARCHAR(50) DEFAULT 'Arial'"
    )


def sync_side_shelves(side):
    target_count = side.shelf_count or 4

    if target_count < 1:
        target_count = 1

    if target_count > 8:
        target_count = 8

    existing_shelves = Shelf.query.filter_by(
        side_id=side.id
    ).order_by(Shelf.number).all()

    existing_numbers = [shelf.number for shelf in existing_shelves]

    for shelf_number in range(1, target_count + 1):
        if shelf_number not in existing_numbers:
            shelf = Shelf(
                side_id=side.id,
                number=shelf_number
            )
            db.session.add(shelf)

    extra_shelves = Shelf.query.filter(
        Shelf.side_id == side.id,
        Shelf.number > target_count
    ).all()

    for shelf in extra_shelves:
        db.session.delete(shelf)

    side.shelf_count = target_count


def create_island_with_structure(name):
    island = Island(name=name)
    db.session.add(island)
    db.session.flush()

    side_settings = [
        (1, "Сторона 1", "small", 256, 32),
        (2, "Сторона 2", "small", 256, 32),
        (3, "Сторона 3", "large", 384, 32),
        (4, "Сторона 4", "large", 384, 32),
    ]

    for number, side_name, size, width_px, height_px in side_settings:
        side = Side(
            island_id=island.id,
            number=number,
            name=side_name,
            size=size,
            width_px=width_px,
            height_px=height_px,
            shelf_count=4,
            price_position="right",
            text_align="center",
            product_font_size=8,
            price_font_size=12,
            template_name="standard",
            background_color="#000000",
            product_color="#ffffff",
            price_color="#ffde00",
            font_family="Arial"
        )

        db.session.add(side)
        db.session.flush()

        for shelf_number in range(1, 5):
            shelf = Shelf(
                side_id=side.id,
                number=shelf_number
            )
            db.session.add(shelf)

    db.session.commit()
    return island


@app.route("/")
def home():
    return redirect(url_for("admin"))


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        island_name = request.form.get("island_name", "").strip()

        if island_name:
            create_island_with_structure(island_name)

        return redirect(url_for("admin"))

    islands = Island.query.order_by(Island.id.desc()).all()

    return render_template(
        "admin.html",
        islands=islands
    )


@app.route("/create-island", methods=["POST"])
def create_island():
    island_name = request.form.get("island_name", "").strip()

    if island_name:
        create_island_with_structure(island_name)

    return redirect(url_for("admin"))


@app.route("/delete-island/<int:island_id>", methods=["POST"])
def delete_island(island_id):
    island = Island.query.get_or_404(island_id)

    db.session.delete(island)
    db.session.commit()

    return redirect(url_for("admin"))


@app.route("/island/<int:island_id>")
def island_detail(island_id):
    island = Island.query.get_or_404(island_id)

    sides = Side.query.filter_by(
        island_id=island.id
    ).order_by(Side.number).all()

    for side in sides:
        if not side.shelf_count:
            side.shelf_count = 4

        sync_side_shelves(side)

    db.session.commit()

    sides = Side.query.filter_by(
        island_id=island.id
    ).order_by(Side.number).all()

    return render_template(
        "island_detail.html",
        island=island,
        sides=sides
    )


@app.route("/save-shelf", methods=["POST"])
def save_shelf():
    island_id = safe_int(request.form.get("island_id"), 0)
    shelf_id = safe_int(request.form.get("shelf_id"), 0)

    shelf = Shelf.query.get_or_404(shelf_id)
    side = shelf.side

    Product.query.filter_by(shelf_id=shelf.id).delete()

    for i in range(15):
        name = request.form.get(f"product_name_{i}", "").strip()
        price = request.form.get(f"product_price_{i}", "").strip()

        if name or price:
            product = Product(
                shelf_id=shelf.id,
                name=name,
                price=price
            )
            db.session.add(product)

    side.updated_at = datetime.utcnow()
    db.session.commit()

    return redirect(url_for("island_detail", island_id=island_id))


@app.route("/save-side-style", methods=["POST"])
def save_side_style():
    island_id = safe_int(request.form.get("island_id"), 0)
    side_id = safe_int(request.form.get("side_id"), 0)

    side = Side.query.get_or_404(side_id)

    side.width_px = safe_int(request.form.get("width_px"), 256)
    side.height_px = safe_int(request.form.get("height_px"), 32)

    side.shelf_count = safe_int(request.form.get("shelf_count"), 4)

    if side.shelf_count < 1:
        side.shelf_count = 1

    if side.shelf_count > 8:
        side.shelf_count = 8

    side.template_name = request.form.get("template_name", "standard")

    side.background_color = request.form.get("background_color", "#000000")
    side.product_color = request.form.get("product_color", "#ffffff")
    side.price_color = request.form.get("price_color", "#ffde00")

    side.font_family = request.form.get("font_family", "Arial")

    side.price_position = request.form.get("price_position", "right")
    side.text_align = request.form.get("text_align", "center")

    side.product_font_size = safe_int(request.form.get("product_font_size"), 8)
    side.price_font_size = safe_int(request.form.get("price_font_size"), 12)

    side.updated_at = datetime.utcnow()

    sync_side_shelves(side)
    db.session.commit()

    return redirect(url_for("island_detail", island_id=island_id))


@app.route("/display/<int:island_id>/<int:side_number>")
def display_side(island_id, side_number):
    island = Island.query.get_or_404(island_id)

    side = Side.query.filter_by(
        island_id=island.id,
        number=side_number
    ).first_or_404()

    shelves = Shelf.query.filter_by(
        side_id=side.id
    ).order_by(Shelf.number).all()

    return render_template(
        "display.html",
        island=island,
        side=side,
        shelves=shelves
    )


@app.route("/display/<int:island_id>/<int:side_number>/shelf/<int:shelf_number>")
def display_single_shelf(island_id, side_number, shelf_number):
    island = Island.query.get_or_404(island_id)

    side = Side.query.filter_by(
        island_id=island.id,
        number=side_number
    ).first_or_404()

    shelf = Shelf.query.filter_by(
        side_id=side.id,
        number=shelf_number
    ).first_or_404()

    return render_template(
        "single_shelf.html",
        island=island,
        side=side,
        shelf=shelf
    )


@app.route("/api/side/<int:side_id>/updated")
def check_side_updated(side_id):
    side = Side.query.get_or_404(side_id)

    updated_at = side.updated_at.isoformat() if side.updated_at else ""

    return jsonify({
        "updated_at": updated_at
    })


@app.route("/api/side/<int:side_id>/data")
def side_data(side_id):
    side = Side.query.get_or_404(side_id)

    shelves = Shelf.query.filter_by(
        side_id=side.id
    ).order_by(Shelf.number).all()

    updated_at = side.updated_at.isoformat() if side.updated_at else ""

    data = {
        "id": side.id,
        "number": side.number,
        "name": side.name,
        "size": side.size,
        "width_px": side.width_px,
        "height_px": side.height_px,
        "shelf_count": side.shelf_count,
        "price_position": side.price_position,
        "text_align": side.text_align,
        "product_font_size": side.product_font_size,
        "price_font_size": side.price_font_size,
        "styles": {
            "background_color": side.background_color,
            "product_color": side.product_color,
            "price_color": side.price_color,
            "font_family": side.font_family,
        },
        "updated_at": updated_at,
        "shelves": []
    }

    for shelf in shelves:
        products = Product.query.filter_by(
            shelf_id=shelf.id
        ).order_by(Product.id).limit(15).all()

        shelf_data = {
            "id": shelf.id,
            "number": shelf.number,
            "products": []
        }

        for product in products:
            shelf_data["products"].append({
                "name": product.name,
                "price": product.price
            })

        data["shelves"].append(shelf_data)

    return jsonify(data)


if __name__ == "__main__":
    if not app.config["SQLALCHEMY_DATABASE_URI"]:
        raise RuntimeError("DATABASE_URL не найден. Проверь файл .env")

    with app.app_context():
        db.create_all()
        run_light_migrations()

    app.run(
        host="0.0.0.0",
        port=5050,
        debug=True
    )