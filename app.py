# app.py - Simple In-Memory Flask Product API

from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid # To generate unique IDs for products

# Initialize Flask app
app = Flask(__name__)
# Enable CORS for all routes.
CORS(app)

# --- In-Memory Data Store ---
# This list will hold our product data.
# Data will be lost when the server restarts.
products = [
    {
        "id": "prod1",
        "name": "Laptop Pro X",
        "category": "Electronics",
        "price": 1200.00,
        "stock": 50,
        "description": "High-performance laptop for professionals."
    },
    {
        "id": "prod2",
        "name": "Mechanical Keyboard",
        "category": "Electronics",
        "price": 95.50,
        "stock": 200,
        "description": "Tactile and clicky mechanical keyboard."
    },
    {
        "id": "prod3",
        "name": "Ergonomic Office Chair",
        "category": "Furniture",
        "price": 350.00,
        "stock": 30,
        "description": "Comfortable chair for long working hours."
    },
    {
        "id": "prod4",
        "name": "Wireless Mouse",
        "category": "Electronics",
        "price": 25.00,
        "stock": 500,
        "description": "Compact and precise wireless mouse."
    },
    {
        "id": "prod5",
        "name": "Desk Lamp LED",
        "category": "Lighting",
        "price": 40.00,
        "stock": 120,
        "description": "Adjustable LED desk lamp with multiple brightness levels."
    }
]

# --- API Endpoints ---

@app.route('/products', methods=['GET'])
def get_products():
    """
    GET /products
    Retrieves products with optional filtering by category and search term.
    Query Parameters:
        category (string, optional): Filter products by category.
        search (string, optional): Search product names or descriptions.
    Returns: JSON array of product objects.
    """
    print("GET /products request received.")
    
    # Get query parameters
    category_filter = request.args.get('category')
    search_term = request.args.get('search')

    filtered_products = products

    # Apply category filter if provided
    if category_filter:
        filtered_products = [
            p for p in filtered_products if p['category'].lower() == category_filter.lower()
        ]

    # Apply search term filter if provided (case-insensitive search in name or description)
    if search_term:
        search_term_lower = search_term.lower()
        filtered_products = [
            p for p in filtered_products
            if search_term_lower in p['name'].lower() or search_term_lower in p['description'].lower()
        ]
            
    return jsonify(filtered_products), 200

@app.route('/products/<string:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    """
    GET /products/<id>
    Retrieves a single product by its ID.
    Returns: JSON product object or 404 if not found.
    """
    print(f"GET /products/{product_id} request received.")
    for product in products:
        if product['id'] == product_id:
            return jsonify(product), 200
    return jsonify({"message": "Product not found"}), 404

@app.route('/products', methods=['POST'])
def add_product():
    """
    POST /products
    Adds a new product to the in-memory store.
    Request Body: JSON object with 'name', 'category', 'price', 'stock', 'description'.
    Returns: JSON of the newly added product or 400 if data is missing.
    """
    print("POST /products request received.")
    data = request.get_json() # Get JSON data from request body

    # Basic input validation
    required_fields = ['name', 'category', 'price', 'stock', 'description']
    if not data or not all(k in data for k in required_fields):
        return jsonify({"message": f"Missing required product data. Required: {', '.join(required_fields)}"}), 400
    
    # Validate price and stock are numbers
    try:
        data['price'] = float(data['price'])
        data['stock'] = int(data['stock'])
    except (ValueError, TypeError):
        return jsonify({"message": "Price must be a number and Stock must be an integer"}), 400

    new_product = {
        "id": str(uuid.uuid4()), # Generate a unique ID
        "name": data['name'],
        "category": data['category'],
        "price": data['price'],
        "stock": data['stock'],
        "description": data['description']
    }
    products.append(new_product)
    print(f"Added new product: {new_product['name']}")
    return jsonify(new_product), 201 # 201 Created status

@app.route('/products/<string:product_id>', methods=['PUT'])
def update_product(product_id):
    """
    PUT /products/<id>
    Updates an existing product by its ID.
    Request Body: JSON object with fields to update.
    Returns: JSON of the updated product or 404/400.
    """
    print(f"PUT /products/{product_id} request received.")
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required for update"}), 400

    for i, product in enumerate(products):
        if product['id'] == product_id:
            # Update only the fields provided in the request body
            # Basic type validation for price/stock if they are updated
            if 'price' in data:
                try:
                    data['price'] = float(data['price'])
                except (ValueError, TypeError):
                    return jsonify({"message": "Price must be a number"}), 400
            if 'stock' in data:
                try:
                    data['stock'] = int(data['stock'])
                except (ValueError, TypeError):
                    return jsonify({"message": "Stock must be an integer"}), 400

            product.update(data)
            print(f"Updated product: {product['name']}")
            return jsonify(product), 200
    return jsonify({"message": "Product not found"}), 404

@app.route('/products/<string:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """
    DELETE /products/<id>
    Deletes a product by its ID.
    Returns: Success message or 404.
    """
    print(f"DELETE /products/{product_id} request received.")
    global products # Needed to modify the global 'products' list
    initial_len = len(products)
    products = [p for p in products if p['id'] != product_id]
    if len(products) < initial_len:
        print(f"Deleted product with ID: {product_id}")
        return jsonify({"message": "Product deleted successfully"}), 200
    return jsonify({"message": "Product not found"}), 404

# --- Run the Flask App ---
if __name__ == '__main__':
    # Run in debug mode, accessible from any IP on port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)

