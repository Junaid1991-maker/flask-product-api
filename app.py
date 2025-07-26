# app.py

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from datetime import datetime
from sqlalchemy import func, desc, or_
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- Database Configuration ---
# IMPORTANT: Replace 'YOUR_POSTGRES_PASSWORD_HERE' with the actual password
# for your 'postgres' user. If you created a 'junaid' user and know its password,
# you can change 'postgres' back to 'junaid' and use that password.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or \
                                      'postgresql://postgres:Data##1991@localhost/product_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- Models ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = db.relationship('Category', backref='products')

    def __repr__(self):
        return f'<Product {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'stock': self.stock,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Category {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }

# --- API Routes ---

@app.route('/products', methods=['POST'])
def add_product():
    data = request.json
    if not data or not all(key in data for key in ['name', 'price']):
        return jsonify({'message': 'Missing data (name, price required)'}), 400

    category_name = data.get('category')
    category_id = None
    if category_name:
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name)
            db.session.add(category)
            db.session.commit()
        category_id = category.id

    new_product = Product(
        name=data['name'],
        description=data.get('description'),
        price=data['price'],
        stock=data.get('stock', 0),
        category_id=category_id
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify(new_product.to_dict()), 201

@app.route('/products', methods=['GET'])
def get_products():
    category_filter = request.args.get('category')
    search_term = request.args.get('search')

    query = Product.query

    if category_filter:
        query = query.join(Category).filter(Category.name.ilike(f'%{category_filter}%'))

    if search_term:
        query = query.filter(or_(
            Product.name.ilike(f'%{search_term}%'),
            Product.description.ilike(f'%{search_term}%')
        ))
    
    products = query.all()
    return jsonify([p.to_dict() for p in products])

@app.route('/products/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify(product.to_dict()), 200
    return jsonify({"message": "Product not found"}), 404

@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "Request body is required for update"}), 400

    if 'name' in data:
        product.name = data['name']
    if 'description' in data:
        product.description = data['description']
    if 'price' in data:
        try:
            product.price = float(data['price'])
        except (ValueError, TypeError):
            return jsonify({"message": "Price must be a number"}), 400
    if 'stock' in data:
        try:
            product.stock = int(data['stock'])
        except (ValueError, TypeError):
            return jsonify({"message": "Stock must be an integer"}), 400
    if 'category' in data:
        category_name = data['category']
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name)
            db.session.add(category)
            db.session.commit()
        product.category_id = category.id

    db.session.commit()
    return jsonify(product.to_dict()), 200

@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"}), 200


@app.route('/categories', methods=['POST'])
def add_category():
    data = request.json
    if not data or 'name' not in data:
        return jsonify({'message': 'Category name required'}), 400
    
    existing_category = Category.query.filter_by(name=data['name']).first()
    if existing_category:
        return jsonify({"message": "Category already exists", "category": existing_category.to_dict()}), 409

    new_category = Category(name=data['name'])
    db.session.add(new_category)
    db.session.commit()
    return jsonify(new_category.to_dict()), 201

@app.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([c.to_dict() for c in categories])


# --- Complex Query Routes ---

@app.route('/products/category_summary', methods=['GET'])
def get_product_category_summary():
    category_summary = db.session.query(
        Category.name,
        func.count(Product.id).label('product_count')
    ).join(Product, Category.id == Product.category_id)\
     .group_by(Category.name)\
     .order_by(desc(func.count(Product.id)))\
     .all()

    results = [{'category_name': row.name, 'product_count': row.product_count} for row in category_summary]
    return jsonify(results)


@app.route('/products/high_stock/<int:min_stock>', methods=['GET'])
def get_products_with_high_stock(min_stock):
    high_stock_products = Product.query.filter(Product.stock > min_stock)\
                                       .order_by(desc(Product.stock))\
                                       .all()
    return jsonify([p.to_dict() for p in high_stock_products])

@app.route('/products/average_price_by_category', methods=['GET'])
def get_avg_price_by_category():
    avg_prices = db.session.query(
        Category.name,
        func.avg(Product.price).label('average_price')
    ).join(Product, Category.id == Product.category_id)\
     .group_by(Category.name)\
     .all()
    
    results = [{'category_name': row.name, 'average_price': round(row.average_price, 2)} for row in avg_prices]
    return jsonify(results)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)