from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    flash,
    url_for
)

from flask_sqlalchemy import SQLAlchemy

from functools import wraps
from datetime import datetime


# ============================================================
# 1. CONFIGURATION
# ============================================================

app = Flask(__name__)

# Secret key untuk session dan flash message
# TODO:
# Pindahkan ke .env sebelum production.
app.config["SECRET_KEY"] = "inventory-secret-key"

# Database SQLite
# Flask-SQLAlchemy akan menyimpan database di:
# instance/inventory.db
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///inventory.db"

# Mematikan tracking object yang tidak diperlukan
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ============================================================
# 2. DATABASE MODELS
# ============================================================


# ------------------------------------------------------------
# CATEGORY
# ------------------------------------------------------------

class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    # Satu kategori dapat memiliki banyak produk
    products = db.relationship(
        "Product",
        backref="category",
        lazy=True
    )


# ------------------------------------------------------------
# SUPPLIER
# ------------------------------------------------------------

class Supplier(db.Model):
    __tablename__ = "suppliers"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    phone = db.Column(
        db.String(30)
    )

    email = db.Column(
        db.String(100)
    )

    address = db.Column(
        db.Text
    )

    notes = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    # Satu supplier dapat memiliki banyak riwayat stock movement
    stock_movements = db.relationship(
        "StockMovement",
        back_populates="supplier"
    )


# ------------------------------------------------------------
# PRODUCT
# ------------------------------------------------------------

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=False
    )

    sku = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    barcode = db.Column(
        db.String(100),
        unique=True,
        nullable=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    purchase_price = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    selling_price = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    stock = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    minimum_stock = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    unit = db.Column(
        db.String(30),
        default="pcs"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now()
    )

    # Satu produk dapat memiliki banyak stock movement
    stock_movements = db.relationship(
        "StockMovement",
        back_populates="product"
    )


# ------------------------------------------------------------
# STOCK MOVEMENT
# ------------------------------------------------------------

class StockMovement(db.Model):
    __tablename__ = "stock_movements"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    # Supplier boleh kosong.
    # Contoh:
    # - Stock In      -> biasanya memiliki supplier
    # - Stock Out     -> tidak perlu supplier
    # - Penjualan     -> tidak perlu supplier
    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("suppliers.id"),
        nullable=True
    )

    # Jenis movement:
    # in  = stock masuk
    # out = stock keluar
    # adjustment = penyesuaian stock
    type = db.Column(
        db.String(20),
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        nullable=False
    )

    stock_before = db.Column(
        db.Integer,
        nullable=False
    )

    stock_after = db.Column(
        db.Integer,
        nullable=False
    )

    note = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )

    # Relationship ke Product
    product = db.relationship(
        "Product",
        back_populates="stock_movements"
    )

    # Relationship ke Supplier
    supplier = db.relationship(
        "Supplier",
        back_populates="stock_movements"
    )


# ------------------------------------------------------------
# SALE
# ------------------------------------------------------------

class Sale(db.Model):
    __tablename__ = "sales"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    invoice_number = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    customer_name = db.Column(
        db.String(100),
        nullable=True
    )

    payment_method = db.Column(
        db.String(30),
        nullable=False,
        default="cash"
    )

    paid_amount = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    change_amount = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    total = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    # Gunakan waktu komputer/server lokal, bukan SQLite UTC
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now
    )

    # Satu penjualan memiliki banyak item
    items = db.relationship(
        "SaleItem",
        backref="sale",
        cascade="all, delete-orphan"
    )

    # Relasi ke user
    user = db.relationship(
        "User",
        backref="sales"
    )

# ------------------------------------------------------------
# SALE ITEM
# ------------------------------------------------------------

class SaleItem(db.Model):
    __tablename__ = "sale_items"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    sale_id = db.Column(
        db.Integer,
        db.ForeignKey("sales.id"),
        nullable=False
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        nullable=False
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    subtotal = db.Column(
        db.Float,
        nullable=False
    )

    product = db.relationship(
        "Product",
        backref="sale_items"
    )

# ------------------------------------------------------------
# USER
# ------------------------------------------------------------

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        default="staff"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )


# ============================================================
# 3. AUTHORIZATION DECORATORS
# ============================================================


# ------------------------------------------------------------
# LOGIN REQUIRED
# ------------------------------------------------------------


@app.template_filter("rupiah")
def rupiah(value):
    try:
        value = float(value or 0)
        if value.is_integer():
            value = int(value)
        return "Rp {:,.0f}".format(value).replace(",", ".")
    except (TypeError, ValueError):
        return "Rp 0"

@app.template_filter("datetime_id")
def datetime_id(value):
    if not value:
        return "-"
    return value.strftime("%d/%m/%Y %H:%M")

def login_required(view):
    """
    Memastikan user sudah login sebelum
    mengakses halaman tertentu.
    """

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:
            flash(
                "Silakan login terlebih dahulu.",
                "warning"
            )

            return redirect("/login")

        return view(*args, **kwargs)

    return wrapped_view


# ------------------------------------------------------------
# ADMIN REQUIRED
# ------------------------------------------------------------

def admin_required(redirect_to="/"):
    """
    Membatasi route agar hanya dapat diakses oleh admin.

    redirect_to:
    halaman tujuan jika user bukan admin.
    """

    def decorator(view):

        @wraps(view)
        def wrapped_view(*args, **kwargs):

            # Belum login
            if "user_id" not in session:
                flash(
                    "Silakan login terlebih dahulu.",
                    "warning"
                )

                return redirect("/login")

            # Sudah login tetapi bukan admin
            if session.get("role") != "admin":
                flash(
                    "Anda tidak memiliki akses ke halaman ini.",
                    "danger"
                )

                return redirect(redirect_to)

            return view(*args, **kwargs)

        return wrapped_view

    return decorator


# ============================================================
# 4. AUTHENTICATION
# ============================================================


# ------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            username=username
        ).first()

        # Login berhasil
        if user and user.password == password:

            session["user_id"] = user.id
            session["username"] = user.username
            session["name"] = user.name
            session["role"] = user.role

            flash(
                "Login berhasil.",
                "success"
            )

            return redirect("/")

        # Login gagal
        flash(
            "Username atau password salah.",
            "danger"
        )

    return render_template("login.html")


# ------------------------------------------------------------
# LOGOUT
# ------------------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Anda telah logout.",
        "success"
    )

    return redirect("/login")


# ============================================================
# 5. DASHBOARD
# ============================================================

@app.route("/")
@login_required
def dashboard():
    # ========================================================
    # PRODUCT STATISTICS
    # ========================================================

    products = Product.query.all()

    total_products = len(products)

    total_stock = sum(
        product.stock
        for product in products
    )

    low_stock_products = [
        product
        for product in products
        if product.stock <= product.minimum_stock
    ]

    low_stock = sum(
        1
        for product in products
        if product.stock <= product.minimum_stock
        and product.stock > 0
    )

    out_of_stock = sum(
        1
        for product in products
        if product.stock == 0
    )

    # ========================================================
    # SALES STATISTICS
    # ========================================================

    sales = Sale.query.all()

    # Total nominal semua penjualan
    total_sales = sum(
        sale.total
        for sale in sales
    )

    # Total seluruh transaksi
    total_transactions = len(sales)

    # ========================================================
    # TODAY SALES
    # ========================================================

    today = datetime.now().date()

    today_sales = [
        sale
        for sale in sales
        if sale.created_at
        and sale.created_at.date() == today
    ]

    today_total = sum(
        sale.total
        for sale in today_sales
    )

    today_transactions = len(today_sales)

    # ========================================================
    # RECENT SALES
    # ========================================================

    recent_sales = (
        Sale.query
        .order_by(Sale.id.desc())
        .limit(5)
        .all()
    )

    # ========================================================
    # DASHBOARD
    # ========================================================

    return render_template(
        "dashboard.html",

        total_products=total_products,
        total_stock=total_stock,

        low_stock=low_stock,
        out_of_stock=out_of_stock,
        low_stock_products=low_stock_products,

        today_total=today_total,
        today_transactions=today_transactions,

        total_sales=total_sales,
        total_transactions=total_transactions,

        recent_sales=recent_sales
    )


# ============================================================
# 6. PRODUCT MANAGEMENT
# ============================================================


# ------------------------------------------------------------
# PRODUCT LIST
# ------------------------------------------------------------

@app.route("/products")
@login_required
def products():

    products = Product.query.order_by(
        Product.id.desc()
    ).all()

    return render_template(
        "products.html",
        products=products
    )


# ------------------------------------------------------------
# ADD PRODUCT
# ------------------------------------------------------------

@app.route("/products/add", methods=["GET", "POST"])
@admin_required()
def add_product():

    categories = Category.query.order_by(
        Category.name
    ).all()

    if request.method == "POST":

        sku = request.form.get(
            "sku",
            ""
        ).strip()

        barcode = request.form.get(
            "barcode",
            ""
        ).strip()

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        category_id = request.form.get(
            "category_id"
        )

        purchase_price = request.form.get(
            "purchase_price",
            0
        )

        selling_price = request.form.get(
            "selling_price",
            0
        )

        stock = request.form.get(
            "stock",
            0
        )

        minimum_stock = request.form.get(
            "minimum_stock",
            0
        )

        unit = request.form.get(
            "unit",
            "pcs"
        ).strip()

        # Validasi dasar
        if not sku or not name or not category_id:

            flash(
                "SKU, nama produk, dan kategori wajib diisi.",
                "danger"
            )

            return redirect("/products/add")

        # Cek SKU
        if Product.query.filter_by(
            sku=sku
        ).first():

            flash(
                "SKU sudah digunakan.",
                "danger"
            )

            return redirect("/products/add")

        # Cek barcode jika diisi
        if barcode and Product.query.filter_by(
            barcode=barcode
        ).first():

            flash(
                "Barcode sudah digunakan.",
                "danger"
            )

            return redirect("/products/add")

        try:

            product = Product(
                sku=sku,
                barcode=barcode or None,
                name=name,
                description=description,
                category_id=int(category_id),
                purchase_price=int(purchase_price),
                selling_price=int(selling_price),
                stock=int(stock),
                minimum_stock=int(minimum_stock),
                unit=unit
            )

            db.session.add(product)
            db.session.commit()

            flash(
                "Produk berhasil ditambahkan.",
                "success"
            )

            return redirect("/products")

        except ValueError:

            db.session.rollback()

            flash(
                "Data angka tidak valid.",
                "danger"
            )

            return redirect("/products/add")

    return render_template(
        "product-form.html",
        title="Tambah Produk",
        categories=categories
    )


# ------------------------------------------------------------
# EDIT PRODUCT
# ------------------------------------------------------------

@app.route("/products/edit/<int:id>", methods=["GET", "POST"])
@admin_required()
def edit_product(id):

    product = Product.query.get_or_404(id)

    categories = Category.query.order_by(
        Category.name
    ).all()

    if request.method == "POST":

        product.sku = request.form.get(
            "sku",
            ""
        ).strip()

        product.barcode = request.form.get(
            "barcode",
            ""
        ).strip() or None

        product.name = request.form.get(
            "name",
            ""
        ).strip()

        product.description = request.form.get(
            "description",
            ""
        ).strip()

        product.category_id = int(
            request.form.get("category_id")
        )

        product.purchase_price = int(
            request.form.get(
                "purchase_price",
                0
            )
        )

        product.selling_price = int(
            request.form.get(
                "selling_price",
                0
            )
        )

        product.stock = int(
            request.form.get(
                "stock",
                0
            )
        )

        product.minimum_stock = int(
            request.form.get(
                "minimum_stock",
                0
            )
        )

        product.unit = request.form.get(
            "unit",
            "pcs"
        ).strip()

        db.session.commit()

        flash(
            "Produk berhasil diperbarui.",
            "success"
        )

        return redirect("/products")

    return render_template(
        "product-form.html",
        title="Edit Produk",
        product=product,
        categories=categories
    )


# ------------------------------------------------------------
# DELETE PRODUCT
# ------------------------------------------------------------

@app.route("/products/delete/<int:id>", methods=["POST"])
@admin_required()
def delete_product(id):

    product = Product.query.get_or_404(id)

    # Jangan hapus produk jika memiliki riwayat stok
    movement = StockMovement.query.filter_by(
        product_id=product.id
    ).first()

    if movement:

        flash(
            "Produk tidak dapat dihapus karena sudah memiliki riwayat stok.",
            "danger"
        )

        return redirect("/products")

    db.session.delete(product)
    db.session.commit()

    flash(
        "Produk berhasil dihapus.",
        "success"
    )

    return redirect("/products")


# ============================================================
# 7. CATEGORY MANAGEMENT
# ============================================================


# ------------------------------------------------------------
# CATEGORY LIST
# ------------------------------------------------------------

@app.route("/categories")
@login_required
def categories():

    categories = Category.query.order_by(
        Category.id.desc()
    ).all()

    return render_template(
        "categories.html",
        categories=categories
    )


# ------------------------------------------------------------
# ADD CATEGORY
# ------------------------------------------------------------

@app.route("/categories/add", methods=["GET", "POST"])
@admin_required()
def add_category():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        if not name:

            flash(
                "Nama kategori wajib diisi.",
                "danger"
            )

            return redirect("/categories/add")

        if Category.query.filter_by(
            name=name
        ).first():

            flash(
                "Kategori sudah ada.",
                "danger"
            )

            return redirect("/categories/add")

        category = Category(
            name=name,
            description=description
        )

        db.session.add(category)
        db.session.commit()

        flash(
            "Kategori berhasil ditambahkan.",
            "success"
        )

        return redirect("/categories")

    return render_template(
        "category-form.html",
        title="Tambah Kategori"
    )


# ------------------------------------------------------------
# EDIT CATEGORY
# ------------------------------------------------------------

@app.route("/categories/edit/<int:id>", methods=["GET", "POST"])
@admin_required()
def edit_category(id):

    category = Category.query.get_or_404(id)

    if request.method == "POST":

        category.name = request.form.get(
            "name",
            ""
        ).strip()

        category.description = request.form.get(
            "description",
            ""
        ).strip()

        db.session.commit()

        flash(
            "Kategori berhasil diperbarui.",
            "success"
        )

        return redirect("/categories")

    return render_template(
        "category-form.html",
        title="Edit Kategori",
        category=category
    )


# ------------------------------------------------------------
# DELETE CATEGORY
# ------------------------------------------------------------

@app.route("/categories/delete/<int:id>", methods=["POST"])
@admin_required()
def delete_category(id):

    category = Category.query.get_or_404(id)

    # Jangan hapus kategori jika masih digunakan produk
    if category.products:

        flash(
            "Kategori tidak dapat dihapus karena masih digunakan produk.",
            "danger"
        )

        return redirect("/categories")

    db.session.delete(category)
    db.session.commit()

    flash(
        "Kategori berhasil dihapus.",
        "success"
    )

    return redirect("/categories")


# ============================================================
# 8. INVENTORY MANAGEMENT
# ============================================================


# ------------------------------------------------------------
# INVENTORY LIST
# ------------------------------------------------------------

@app.route("/inventory")
@login_required
def inventory():

    products = Product.query.order_by(
        Product.name
    ).all()

    movements = StockMovement.query.order_by(
        StockMovement.id.desc()
    ).all()

    total_products = len(products)

    total_stock = sum(
        product.stock
        for product in products
    )

    normal_stock = sum(
        1
        for product in products
        if product.stock > product.minimum_stock
    )

    low_stock = sum(
        1
        for product in products
        if product.stock <= product.minimum_stock
        and product.stock > 0
    )

    out_of_stock = sum(
        1
        for product in products
        if product.stock == 0
    )

    return render_template(
        "inventory.html",
        products=products,
        movements=movements,

        total_products=total_products,
        total_stock=total_stock,
        normal_stock=normal_stock,
        low_stock=low_stock,
        out_of_stock=out_of_stock
    )

@app.route("/inventory/product/<int:id>")
@login_required
def inventory_product_detail(id):
    product = Product.query.get_or_404(id)

    movements = (
        StockMovement.query
        .filter_by(product_id=product.id)
        .order_by(StockMovement.id.desc())
        .all()
    )

    return render_template(
        "inventory-detail.html",
        product=product,
        movements=movements
    )

# =========================
# STOCK IN
# =========================

@app.route("/inventory/in", methods=["GET", "POST"])
@admin_required("/inventory")
def stock_in():

    # Ambil semua produk
    products = Product.query.order_by(
        Product.name.asc()
    ).all()

    # Ambil semua supplier
    suppliers = Supplier.query.order_by(
        Supplier.name.asc()
    ).all()

    # =========================
    # POST
    # =========================

    if request.method == "POST":

        product_id = request.form.get(
            "product_id"
        )

        supplier_id = request.form.get(
            "supplier_id"
        )

        quantity = request.form.get(
            "quantity"
        )

        note = request.form.get(
            "note",
            ""
        ).strip()

        # =========================
        # VALIDATION
        # =========================

        if (
            not product_id
            or not supplier_id
            or not quantity
        ):
            flash(
                "Supplier, produk, dan jumlah wajib diisi.",
                "danger"
            )

            return redirect(
                "/inventory/in"
            )

        if not note:
            note = "Stok masuk"

        try:

            # Ambil product
            product = Product.query.get_or_404(
                int(product_id)
            )

            # Ambil supplier
            supplier = Supplier.query.get_or_404(
                int(supplier_id)
            )

            # Konversi quantity
            quantity = int(quantity)

            # Quantity harus > 0
            if quantity <= 0:

                flash(
                    "Jumlah stok harus lebih dari 0.",
                    "danger"
                )

                return redirect(
                    "/inventory/in"
                )

            # =========================
            # STOCK CALCULATION
            # =========================

            stock_before = product.stock

            product.stock += quantity

            stock_after = product.stock

            # =========================
            # STOCK MOVEMENT
            # =========================

            movement = StockMovement(

                product_id=product.id,

                supplier_id=supplier.id,

                type="in",

                quantity=quantity,

                stock_before=stock_before,

                stock_after=stock_after,

                note=note

            )

            db.session.add(
                movement
            )

            db.session.commit()

            flash(
                f"Stok {product.name} berhasil ditambahkan.",
                "success"
            )

            return redirect(
                "/inventory"
            )

        except ValueError:

            db.session.rollback()

            flash(
                "Data stok tidak valid.",
                "danger"
            )

            return redirect(
                "/inventory/in"
            )

    # =========================
    # GET
    # =========================

    return render_template(
        "inventory-in.html",
        products=products,
        suppliers=suppliers
    )

# ------------------------------------------------------------
# STOCK OUT
# ------------------------------------------------------------

@app.route("/inventory/out", methods=["GET", "POST"])
@admin_required("/inventory")
def stock_out():

    products = Product.query.order_by(
        Product.name
    ).all()

    if request.method == "POST":

        product_id = request.form.get(
            "product_id"
        )

        quantity = request.form.get(
            "quantity"
        )

        note = request.form.get(
            "note",
            ""
        ).strip()

        if not note:
            note = "Stok keluar"

        try:

            product = Product.query.get_or_404(
                int(product_id)
            )

            quantity = int(quantity)

            if quantity <= 0:

                flash(
                    "Jumlah stok harus lebih dari 0.",
                    "danger"
                )

                return redirect("/inventory/out")

            # Pastikan stok cukup
            if quantity > product.stock:

                flash(
                    "Stok tidak mencukupi.",
                    "danger"
                )

                return redirect("/inventory/out")

            stock_before = product.stock

            # Kurangi stok
            product.stock -= quantity

            movement = StockMovement(
                product_id=product.id,
                type="out",
                quantity=quantity,
                stock_before=stock_before,
                stock_after=product.stock,
                note=note
            )

            db.session.add(movement)
            db.session.commit()

            flash(
                "Stok berhasil dikurangi.",
                "success"
            )

            return redirect("/inventory")

        except ValueError:

            flash(
                "Data stok tidak valid.",
                "danger"
            )

            return redirect("/inventory/out")

    return render_template(
        "inventory-out.html",
        products=products
    )

@app.route("/inventory/adjustment", methods=["GET", "POST"])
@admin_required("/inventory")
def inventory_adjustment():
    products = Product.query.order_by(Product.name).all()

    if request.method == "POST":
        product_id = request.form.get("product_id", type=int)
        actual_stock = request.form.get("actual_stock", type=int)
        note = request.form.get("note", "").strip()

        if not product_id or actual_stock is None:
            flash("Produk dan stok aktual wajib diisi.", "danger")
            return redirect("/inventory/adjustment")

        if actual_stock < 0:
            flash("Stok aktual tidak boleh kurang dari 0.", "danger")
            return redirect("/inventory/adjustment")

        product = Product.query.get_or_404(product_id)

        stock_before = product.stock
        difference = actual_stock - stock_before

        if difference == 0:
            flash("Tidak ada perubahan stok.", "warning")
            return redirect("/inventory/adjustment")

        product.stock = actual_stock

        movement = StockMovement(
            product_id=product.id,
            type="adjustment",
            quantity=abs(difference),
            stock_before=stock_before,
            stock_after=actual_stock,
            note=note or f"Penyesuaian stok ({difference:+d})"
        )

        db.session.add(movement)
        db.session.commit()

        flash("Stok berhasil disesuaikan.", "success")
        return redirect(
            url_for("inventory_product_detail", id=product.id)
        )

    return render_template(
        "inventory-adjustment.html",
        products=products
    )

@app.route("/inventory/low-stock")
@login_required
def low_stock():
    products = (
        Product.query
        .filter(Product.stock <= Product.minimum_stock)
        .order_by(Product.stock.asc(), Product.name.asc())
        .all()
    )

    low_stock_products = [
        product for product in products
        if product.stock > 0
    ]

    out_of_stock_products = [
        product for product in products
        if product.stock == 0
    ]

    return render_template(
        "low-stock.html",
        products=products,
        low_stock_products=low_stock_products,
        out_of_stock_products=out_of_stock_products
    )

# ============================================================
# 9. SALES MANAGEMENT
# ============================================================


# ------------------------------------------------------------
# SALES LIST
# ------------------------------------------------------------

@app.route("/sales")
@login_required
def sales():
    products = Product.query.order_by(
        Product.name.asc()
    ).all()

    sales = Sale.query.order_by(
        Sale.id.desc()
    ).all()

    return render_template(
        "sales.html",
        products=products,
        sales=sales
    )

# ------------------------------------------------------------
# CREATE SALE
# ------------------------------------------------------------

@app.route("/sales/create", methods=["GET", "POST"])
@login_required
def create_sale():

    products = Product.query.order_by(
        Product.name.asc()
    ).all()

    if request.method == "POST":

        product_ids = request.form.getlist("product_id[]")
        quantities = request.form.getlist("quantity[]")

        # --------------------------------------------------------
        # VALIDASI DATA DASAR
        # --------------------------------------------------------

        if not product_ids or not quantities:
            flash(
                "Minimal harus memilih satu produk.",
                "danger"
            )
            return redirect("/sales")

        if len(product_ids) != len(quantities):
            flash(
                "Data produk dan jumlah tidak valid.",
                "danger"
            )
            return redirect("/sales")

        try:

            # ----------------------------------------------------
            # GABUNGKAN PRODUK YANG SAMA
            # ----------------------------------------------------

            product_quantities = {}

            for product_id, quantity in zip(
                product_ids,
                quantities
            ):

                product_id = int(product_id)
                quantity = int(quantity)

                if quantity <= 0:
                    flash(
                        "Jumlah produk harus lebih dari 0.",
                        "danger"
                    )
                    return redirect("/sales")

                product_quantities[product_id] = (
                    product_quantities.get(product_id, 0)
                    + quantity
                )

            # ----------------------------------------------------
            # VALIDASI STOK + HITUNG TOTAL
            # ----------------------------------------------------

            sale_items_data = []
            total = 0

            for product_id, quantity in product_quantities.items():

                product = Product.query.get_or_404(product_id)

                # Pastikan stok cukup
                if product.stock < quantity:

                    flash(
                        f"Stok {product.name} tidak mencukupi. "
                        f"Stok tersedia: {product.stock}.",
                        "danger"
                    )

                    return redirect("/sales")

                price = product.selling_price
                subtotal = price * quantity

                total += subtotal

                sale_items_data.append({
                    "product": product,
                    "quantity": quantity,
                    "price": price,
                    "subtotal": subtotal
                })

            # ----------------------------------------------------
            # DATA CUSTOMER & PEMBAYARAN
            # ----------------------------------------------------

            customer_name = (
                request.form.get(
                    "customer_name",
                    ""
                ).strip()
                or None
            )

            payment_method = (
                request.form.get(
                    "payment_method",
                    "cash"
                ).strip()
            )

            try:
                paid_amount = int(
                    request.form.get(
                        "paid_amount",
                        0
                    ) or 0
                )

            except ValueError:

                flash(
                    "Nominal pembayaran tidak valid.",
                    "danger"
                )

                return redirect("/sales")

            # Uang harus mencukupi total
            if paid_amount < total:

                flash(
                    f"Uang pembayaran kurang. "
                    f"Total transaksi: "
                    f"Rp {total:,.0f}".replace(",", "."),
                    "danger"
                )

                return redirect("/sales")

            change_amount = paid_amount - total

            # ----------------------------------------------------
            # BUAT SALE
            # ----------------------------------------------------

            sale = Sale(
                invoice_number="TEMP",
                total=total,
                user_id=session.get("user_id"),
                customer_name=customer_name,
                payment_method=payment_method,
                paid_amount=paid_amount,
                change_amount=change_amount
            )

            db.session.add(sale)

            # Flush agar sale.id langsung tersedia
            db.session.flush()

            # ----------------------------------------------------
            # GENERATE INVOICE
            # ----------------------------------------------------

            invoice_number = (
                f"INV-{datetime.now().strftime('%Y%m%d')}-"
                f"{sale.id:05d}"
            )

            sale.invoice_number = invoice_number

            # ----------------------------------------------------
            # SALE ITEMS + STOCK MOVEMENT
            # ----------------------------------------------------

            for item in sale_items_data:

                product = item["product"]
                quantity = item["quantity"]
                price = item["price"]
                subtotal = item["subtotal"]

                stock_before = product.stock

                # Kurangi stok
                product.stock -= quantity

                # Sale Item
                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=price,
                    subtotal=subtotal
                )

                db.session.add(sale_item)

                # Stock Movement
                movement = StockMovement(
                    product_id=product.id,
                    type="out",
                    quantity=quantity,
                    stock_before=stock_before,
                    stock_after=product.stock,
                    note=f"Penjualan {invoice_number}"
                )

                db.session.add(movement)

            # ----------------------------------------------------
            # SIMPAN TRANSAKSI
            # ----------------------------------------------------

            db.session.commit()

            flash(
                f"Penjualan {invoice_number} berhasil dibuat.",
                "success"
            )

            return redirect(
                url_for(
                    "sale_detail",
                    sale_id=sale.id
                )
            )

        except (ValueError, TypeError):

            db.session.rollback()

            flash(
                "Data transaksi tidak valid.",
                "danger"
            )

            return redirect("/sales")

        except Exception:

            db.session.rollback()

            flash(
                "Terjadi kesalahan saat menyimpan transaksi.",
                "danger"
            )

            return redirect("/sales")

    return render_template(
        "sales.html",
        products=products
    )

# ------------------------------------------------------------
# SALES HISTORY
# ------------------------------------------------------------

@app.route("/sales-history")
@login_required
def sales_history():

    sales = Sale.query.order_by(
        Sale.id.desc()
    ).all()

    return render_template(
        "sales-history.html",
        sales=sales
    )


# ------------------------------------------------------------
# SALES DETAIL
# ------------------------------------------------------------

@app.route("/sales-history/<int:sale_id>")
@login_required
def sale_detail(sale_id):
    sale = Sale.query.get_or_404(sale_id)

    return render_template(
        "sales-detail.html",
        sale=sale
    )


# Alias endpoint agar template lama dengan nama
# "sales_detail" tetap dapat digunakan.
app.add_url_rule(
    "/sales-history/<int:sale_id>",
    endpoint="sales_detail",
    view_func=sale_detail
)


# ============================================================
# 10. PROFILE
# ============================================================


# ------------------------------------------------------------
# PROFILE
# ------------------------------------------------------------

@app.route("/profile")
@login_required
def profile():

    user = User.query.get_or_404(
        session["user_id"]
    )

    return render_template(
        "profile.html",
        user=user
    )


# ------------------------------------------------------------
# CHANGE PASSWORD
# ------------------------------------------------------------

@app.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():

    user = User.query.get_or_404(
        session["user_id"]
    )

    old_password = request.form.get(
        "old_password",
        ""
    )

    new_password = request.form.get(
        "new_password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )

    if user.password != old_password:

        flash(
            "Password lama salah.",
            "danger"
        )

        return redirect("/profile")

    if new_password != confirm_password:

        flash(
            "Konfirmasi password tidak cocok.",
            "danger"
        )

        return redirect("/profile")

    if not new_password:

        flash(
            "Password baru tidak boleh kosong.",
            "danger"
        )

        return redirect("/profile")

    user.password = new_password

    db.session.commit()

    flash(
        "Password berhasil diubah.",
        "success"
    )

    return redirect("/profile")


# ============================================================
# 11. USER MANAGEMENT
# ============================================================


# ------------------------------------------------------------
# USER LIST
# ------------------------------------------------------------

@app.route("/users")
@admin_required()
def users():

    users = User.query.order_by(
        User.id.desc()
    ).all()

    return render_template(
        "users.html",
        users=users
    )


# ------------------------------------------------------------
# ADD USER
# ------------------------------------------------------------

@app.route("/users/add", methods=["GET", "POST"])
@admin_required()
def add_user():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        name = request.form.get(
            "name",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        role = request.form.get(
            "role",
            "staff"
        )

        if not username or not name or not password:

            flash(
                "Semua field wajib diisi.",
                "danger"
            )

            return redirect("/users/add")

        if User.query.filter_by(
            username=username
        ).first():

            flash(
                "Username sudah digunakan.",
                "danger"
            )

            return redirect("/users/add")

        user = User(
            username=username,
            name=name,
            password=password,
            role=role
        )

        db.session.add(user)
        db.session.commit()

        flash(
            "User berhasil ditambahkan.",
            "success"
        )

        return redirect("/users")

    return render_template(
        "user-form.html",
        title="Tambah User"
    )


# ------------------------------------------------------------
# EDIT USER
# ------------------------------------------------------------

@app.route("/users/edit/<int:id>", methods=["GET", "POST"])
@admin_required()
def edit_user(id):

    user = User.query.get_or_404(id)

    if request.method == "POST":

        user.username = request.form.get(
            "username",
            ""
        ).strip()

        user.name = request.form.get(
            "name",
            ""
        ).strip()

        user.role = request.form.get(
            "role",
            "staff"
        )

        db.session.commit()

        flash(
            "User berhasil diperbarui.",
            "success"
        )

        return redirect("/users")

    return render_template(
        "user-form.html",
        title="Edit User",
        user=user
    )


# ------------------------------------------------------------
# RESET PASSWORD USER
# ------------------------------------------------------------

@app.route("/users/reset-password/<int:id>", methods=["POST"])
@admin_required()
def reset_password(id):

    user = User.query.get_or_404(id)

    new_password = request.form.get(
        "password",
        ""
    )

    if not new_password:

        flash(
            "Password baru wajib diisi.",
            "danger"
        )

        return redirect("/users")

    user.password = new_password

    db.session.commit()

    flash(
        "Password user berhasil direset.",
        "success"
    )

    return redirect("/users")


# ------------------------------------------------------------
# DELETE USER
# ------------------------------------------------------------

@app.route("/users/delete/<int:id>", methods=["POST"])
@admin_required()
def delete_user(id):

    user = User.query.get_or_404(id)

    # Jangan menghapus akun yang sedang digunakan
    if user.id == session.get("user_id"):

        flash(
            "Anda tidak dapat menghapus akun sendiri.",
            "danger"
        )

        return redirect("/users")

    db.session.delete(user)
    db.session.commit()

    flash(
        "User berhasil dihapus.",
        "success"
    )

    return redirect("/users")


# ============================================================
# 12. SUPPLIER MANAGEMENT
# ============================================================


# ------------------------------------------------------------
# SUPPLIER LIST
# ------------------------------------------------------------

@app.route("/suppliers")
@login_required
def suppliers():

    suppliers = Supplier.query.order_by(
        Supplier.id.desc()
    ).all()

    return render_template(
        "suppliers.html",
        suppliers=suppliers
    )


# ------------------------------------------------------------
# SUPPLIER DETAIL
# ------------------------------------------------------------

@app.route("/suppliers/<int:id>")
@login_required
def supplier_detail(id):

    supplier = Supplier.query.get_or_404(
        id
    )

    movements = (
        StockMovement.query
        .filter_by(
            supplier_id=supplier.id
        )
        .order_by(
            StockMovement.id.desc()
        )
        .all()
    )

    return render_template(
        "supplier-detail.html",
        supplier=supplier,
        movements=movements
    )


# ------------------------------------------------------------
# ADD SUPPLIER
# ------------------------------------------------------------

@app.route("/suppliers/add", methods=["GET", "POST"])
@admin_required("/suppliers")
def add_supplier():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        if not name:

            flash(
                "Nama supplier wajib diisi.",
                "danger"
            )

            return redirect("/suppliers/add")

        supplier = Supplier(
            name=name,
            phone=phone,
            email=email,
            address=address,
            notes=notes
        )

        db.session.add(supplier)
        db.session.commit()

        flash(
            "Supplier berhasil ditambahkan.",
            "success"
        )

        return redirect("/suppliers")

    return render_template(
        "supplier-form.html",
        title="Tambah Supplier"
    )


# ------------------------------------------------------------
# EDIT SUPPLIER
# ------------------------------------------------------------

@app.route("/suppliers/edit/<int:id>", methods=["GET", "POST"])
@admin_required("/suppliers")
def edit_supplier(id):

    supplier = Supplier.query.get_or_404(
        id
    )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        if not name:

            flash(
                "Nama supplier wajib diisi.",
                "danger"
            )

            return redirect(
                f"/suppliers/edit/{id}"
            )

        supplier.name = name
        supplier.phone = phone
        supplier.email = email
        supplier.address = address
        supplier.notes = notes

        db.session.commit()

        flash(
            "Supplier berhasil diperbarui.",
            "success"
        )

        return redirect("/suppliers")

    return render_template(
        "supplier-form.html",
        title="Edit Supplier",
        supplier=supplier
    )


# ------------------------------------------------------------
# DELETE SUPPLIER
# ------------------------------------------------------------

@app.route("/suppliers/delete/<int:id>", methods=["POST"])
@admin_required("/suppliers")
def delete_supplier(id):

    supplier = Supplier.query.get_or_404(
        id
    )

    # Supplier tidak boleh dihapus jika
    # sudah memiliki riwayat stock movement.
    movement = StockMovement.query.filter_by(
        supplier_id=supplier.id
    ).first()

    if movement:

        flash(
            "Supplier tidak dapat dihapus karena sudah memiliki riwayat transaksi.",
            "danger"
        )

        return redirect("/suppliers")

    db.session.delete(supplier)
    db.session.commit()

    flash(
        "Supplier berhasil dihapus.",
        "success"
    )

    return redirect("/suppliers")


# ============================================================
# 13. DATABASE INITIALIZATION
# ============================================================

with app.app_context():

    # Membuat tabel yang belum ada.
    #
    # Catatan:
    # db.create_all() TIDAK melakukan migration
    # terhadap tabel lama.
    #
    # Jika struktur tabel berubah, gunakan migration
    # seperti Flask-Migrate/Alembic.
    db.create_all()

    # --------------------------------------------------------
    # Membuat akun admin default jika belum ada
    # --------------------------------------------------------

    admin = User.query.filter_by(
        username="admin"
    ).first()

    if not admin:

        admin = User(
            username="admin",
            password="admin123",
            name="Administrator",
            role="admin"
        )

        db.session.add(admin)
        db.session.commit()

        print(
            "Akun admin default berhasil dibuat:"
        )

        print(
            "Username : admin"
        )

        print(
            "Password : admin123"
        )


# ============================================================
# 14. DEBUG / ROUTE INFORMATION
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("INVENTORY SYSTEM")
    print("=" * 60)

    print(
        "FILE YANG DIJALANKAN:"
    )

    print(
        __file__
    )

    print()
    print("REGISTERED ROUTES:")

    for rule in app.url_map.iter_rules():

        print(
            f"{rule.methods} -> {rule}"
        )

    print()
    print(
        "Server berjalan di:"
    )

    print(
        "http://127.0.0.1:5000"
    )

    print("=" * 60)
    print()

    app.run(
        debug=True,
        use_reloader=False
    )