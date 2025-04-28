from app import app
from models import User, Category, Product, Sale, SaleItem, Expense

def view_customers():
    print("\n=== Customer Data ===")
    sales = Sale.query.all()
    for sale in sales:
        print(f"Customer: {sale.customer_name}")
        print(f"Mobile: {sale.customer_mobile}")
        print(f"Invoice: {sale.invoice_number}")
        print(f"Total Amount: ₹{sale.total_amount}")
        print("Items:")
        for item in sale.items:
            product = Product.query.get(item.product_id)
            print(f"  - {product.name}: {item.quantity} x ₹{item.unit_price}")
        print("-" * 30)

def view_products():
    print("\n=== Product Inventory ===")
    products = Product.query.all()
    for product in products:
        print(f"Name: {product.name}")
        print(f"Category: {product.category.name}")
        print(f"Size: {product.size}")
        print(f"Quantity: {product.quantity}")
        print(f"Selling Price: ₹{product.selling_price}")
        print("-" * 30)

def view_categories():
    print("\n=== Categories ===")
    categories = Category.query.all()
    for category in categories:
        print(f"Name: {category.name}")
        print(f"Products Count: {len(category.products)}")
        print("-" * 30)

if __name__ == "__main__":
    with app.app_context():
        print("\nH&D Fashions Data View")
        print("=" * 50)
        view_customers()
        view_products()
        view_categories() 