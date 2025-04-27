import os
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import render_template, redirect, url_for, flash, request, jsonify, abort, session
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func, extract, desc
from werkzeug.security import generate_password_hash

from app import app, db
from models import User, Category, Product, Sale, SaleItem, Expense
from forms import (
    LoginForm, RegisterUserForm, ChangePasswordForm, CategoryForm, ProductForm,
    SaleForm, SaleItemForm, ExpenseForm, ReportFilterForm
)
from helpers import generate_invoice_number


# Role-based access control decorator
def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Auth routes
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')
    
    return render_template('login.html', form=form, title='Login')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Current password is incorrect.', 'danger')
    
    return render_template('change_password.html', form=form, title='Change Password')


# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    # Get sales data for the current month
    today = datetime.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get total sales amount for the current month
    monthly_sales = db.session.query(func.sum(Sale.total_amount)).filter(
        Sale.sale_date >= start_of_month
    ).scalar() or 0

    # Get total expenses for the current month
    monthly_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.expense_date >= start_of_month
    ).scalar() or 0

    # Get cost of goods sold for the current month
    monthly_cogs = db.session.query(
        func.sum(SaleItem.quantity * Product.purchase_price)
    ).join(Product, SaleItem.product_id == Product.id).join(
        Sale, SaleItem.sale_id == Sale.id
    ).filter(
        Sale.sale_date >= start_of_month
    ).scalar() or 0

    # Calculate profit
    monthly_profit = monthly_sales - monthly_expenses - monthly_cogs

    # Get low stock products (less than 10 items)
    low_stock_count = Product.query.filter(Product.quantity < 10).count()

    # Get recent sales (last 5)
    recent_sales = Sale.query.order_by(Sale.sale_date.desc()).limit(5).all()

    # Get recent expenses (last 5)
    recent_expenses = Expense.query.order_by(Expense.expense_date.desc()).limit(5).all()

    # Get sales data for the last 7 days for chart
    seven_days_ago = today - timedelta(days=7)
    daily_sales = db.session.query(
        func.date(Sale.sale_date).label('date'),
        func.sum(Sale.total_amount).label('total')
    ).filter(
        Sale.sale_date >= seven_days_ago
    ).group_by(
        func.date(Sale.sale_date)
    ).all()

    daily_sales_data = {str(day.date): float(day.total) for day in daily_sales}

    # Get category sales distribution for pie chart
    category_sales = db.session.query(
        Category.name,
        func.sum(SaleItem.total_price).label('total')
    ).join(
        Product, Product.id == SaleItem.product_id
    ).join(
        Category, Category.id == Product.category_id
    ).join(
        Sale, Sale.id == SaleItem.sale_id
    ).filter(
        Sale.sale_date >= start_of_month
    ).group_by(
        Category.name
    ).all()

    category_sales_data = {cat.name: float(cat.total) for cat in category_sales}

    return render_template(
        'dashboard.html',
        title='Dashboard',
        monthly_sales=monthly_sales,
        monthly_expenses=monthly_expenses,
        monthly_profit=monthly_profit,
        low_stock_count=low_stock_count,
        recent_sales=recent_sales,
        recent_expenses=recent_expenses,
        daily_sales_data=json.dumps(daily_sales_data),
        category_sales_data=json.dumps(category_sales_data)
    )


# User management routes
@app.route('/users')
@login_required
@role_required('admin')
def user_list():
    users = User.query.all()
    return render_template('users.html', users=users, title='User Management')


@app.route('/users/add', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_user():
    form = RegisterUserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data,
            created_at=datetime.now()
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User has been created successfully!', 'success')
        return redirect(url_for('user_list'))
    
    return render_template('register.html', form=form, title='Add User')


@app.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot edit your own user account from this page.', 'danger')
        return redirect(url_for('user_list'))
        
    form = RegisterUserForm(obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('User has been updated successfully!', 'success')
        return redirect(url_for('user_list'))
        
    # For GET request, don't fill password fields
    form.password.data = ''
    form.confirm_password.data = ''
    return render_template('register.html', form=form, title='Edit User', edit_mode=True)


@app.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own user account.', 'danger')
        return redirect(url_for('user_list'))
        
    db.session.delete(user)
    db.session.commit()
    flash('User has been deleted successfully!', 'success')
    return redirect(url_for('user_list'))


# Category routes
@app.route('/categories')
@login_required
def category_list():
    categories = Category.query.order_by(Category.name).all()
    return render_template('categories.html', categories=categories, title='Categories')


@app.route('/categories/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(category)
        db.session.commit()
        flash('Category has been added successfully!', 'success')
        return redirect(url_for('category_list'))
    
    return render_template('categories.html', form=form, title='Add Category')


@app.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    form = CategoryForm(obj=category)
    
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        db.session.commit()
        flash('Category has been updated successfully!', 'success')
        return redirect(url_for('category_list'))
    
    return render_template('categories.html', form=form, category=category, edit_mode=True, title='Edit Category')


@app.route('/categories/delete/<int:category_id>', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    
    # Check if there are products associated with this category
    if category.products:
        flash('Cannot delete this category because it has products associated with it.', 'danger')
        return redirect(url_for('category_list'))
    
    db.session.delete(category)
    db.session.commit()
    flash('Category has been deleted successfully!', 'success')
    return redirect(url_for('category_list'))


# Product routes
@app.route('/products')
@login_required
def product_list():
    products = Product.query.join(Category).order_by(Product.name).all()
    return render_template('products.html', products=products, title='Products')


@app.route('/products/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            category_id=form.category_id.data,
            size=form.size.data,
            quantity=form.quantity.data,
            purchase_price=form.purchase_price.data,
            selling_price=form.selling_price.data,
            description=form.description.data
        )
        db.session.add(product)
        db.session.commit()
        flash('Product has been added successfully!', 'success')
        return redirect(url_for('product_list'))
    
    return render_template('products.html', form=form, title='Add Product')


@app.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.category_id = form.category_id.data
        product.size = form.size.data
        product.quantity = form.quantity.data
        product.purchase_price = form.purchase_price.data
        product.selling_price = form.selling_price.data
        product.description = form.description.data
        db.session.commit()
        flash('Product has been updated successfully!', 'success')
        return redirect(url_for('product_list'))
    
    return render_template('products.html', form=form, product=product, edit_mode=True, title='Edit Product')


@app.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if there are sales associated with this product
    if product.sale_items:
        flash('Cannot delete this product because it has sales associated with it.', 'danger')
        return redirect(url_for('product_list'))
    
    db.session.delete(product)
    db.session.commit()
    flash('Product has been deleted successfully!', 'success')
    return redirect(url_for('product_list'))


# Sale routes
@app.route('/sales')
@login_required
def sale_list():
    sales = Sale.query.order_by(Sale.sale_date.desc()).all()
    return render_template('sales.html', sales=sales, title='Sales')


@app.route('/sales/add', methods=['GET', 'POST'])
@login_required
def add_sale():
    form = SaleForm()
    
    # Auto-generate invoice number if not provided
    if not form.invoice_number.data:
        form.invoice_number.data = generate_invoice_number()
    
    # Handle form submission
    if form.validate_on_submit():
        total_amount = 0
        sale_items = []
        
        # Process selected products from dropdowns
        row_index = 1
        product_key = f'product_id_{row_index}'
        
        while product_key in request.form:
            product_id = request.form.get(product_key)
            quantity_key = f'quantity_{row_index}'
            quantity = int(request.form.get(quantity_key, 0))
            
            if product_id and quantity > 0:
                product_id = int(product_id)
                # Get product details
                product = Product.query.get(product_id)
                if not product:
                    row_index += 1
                    product_key = f'product_id_{row_index}'
                    continue
                
                # Validate quantity
                if quantity > product.quantity:
                    flash(f'Cannot add {quantity} of {product.name}. Only {product.quantity} available.', 'danger')
                    return redirect(url_for('add_sale'))
                
                # Calculate total price
                unit_price = product.selling_price
                item_total = unit_price * quantity
                total_amount += item_total
                
                # Add to sale items list
                sale_items.append({
                    'product_id': product_id,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': item_total,
                    'product': product
                })
            
            # Move to next row
            row_index += 1
            product_key = f'product_id_{row_index}'
        
        # Verify items were selected
        if not sale_items:
            flash('Please select at least one product for the sale.', 'danger')
            return redirect(url_for('add_sale'))
        
        # Create new sale
        sale = Sale(
            invoice_number=form.invoice_number.data,
            customer_name=form.customer_name.data,
            customer_mobile=form.customer_mobile.data,
            total_amount=total_amount,
            created_by=current_user.id,
            sale_date=form.sale_date.data
        )
        db.session.add(sale)
        db.session.flush()  # Get sale ID without committing
        
        # Add sale items and reduce inventory
        for item in sale_items:
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                total_price=item['total_price']
            )
            db.session.add(sale_item)
            
            # Reduce product inventory
            product = item['product']
            product.quantity -= item['quantity']
        
        db.session.commit()
        flash('Sale has been recorded successfully!', 'success')
        return redirect(url_for('sale_list'))
    
    # Get all products for the form
    products = Product.query.filter(Product.quantity > 0).all()
    
    return render_template(
        'sales.html', 
        form=form,
        products=products, 
        title='New Sale'
    )


# Cart functionality removed as per client request


@app.route('/sales/view/<int:sale_id>')
@login_required
def view_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('sales.html', sale=sale, view_mode=True, title='View Sale')


@app.route('/sales/delete/<int:sale_id>', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    
    # Return products to inventory
    for item in sale.items:
        product = Product.query.get(item.product_id)
        if product:
            product.quantity += item.quantity
    
    # Delete the sale
    db.session.delete(sale)
    db.session.commit()
    flash('Sale has been deleted and products returned to inventory.', 'success')
    return redirect(url_for('sale_list'))


# Expense routes
@app.route('/expenses')
@login_required
def expense_list():
    expenses = Expense.query.order_by(Expense.expense_date.desc()).all()
    return render_template('expenses.html', expenses=expenses, title='Expenses')


@app.route('/expenses/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def add_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = Expense(
            category=form.category.data,
            amount=form.amount.data,
            description=form.description.data,
            expense_date=form.expense_date.data,
            created_by=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        flash('Expense has been added successfully!', 'success')
        return redirect(url_for('expense_list'))
    
    return render_template('expenses.html', form=form, title='Add Expense')


@app.route('/expenses/edit/<int:expense_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    form = ExpenseForm(obj=expense)
    
    if form.validate_on_submit():
        expense.category = form.category.data
        expense.amount = form.amount.data
        expense.description = form.description.data
        expense.expense_date = form.expense_date.data
        db.session.commit()
        flash('Expense has been updated successfully!', 'success')
        return redirect(url_for('expense_list'))
    
    return render_template('expenses.html', form=form, expense=expense, edit_mode=True, title='Edit Expense')


@app.route('/expenses/delete/<int:expense_id>', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense has been deleted successfully!', 'success')
    return redirect(url_for('expense_list'))


# Report routes
@app.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
    form = ReportFilterForm()
    
    if form.validate_on_submit():
        start_date = form.start_date.data
        end_date = form.end_date.data
    else:
        # Default to current month
        today = datetime.now()
        start_date = today.replace(day=1)
        end_date = today
    
    # Get data for reports
    sales_data = get_sales_report(start_date, end_date)
    expense_data = get_expense_report(start_date, end_date)
    profit_data = get_profit_report(start_date, end_date)
    
    return render_template(
        'reports.html',
        form=form,
        sales_data=sales_data,
        expense_data=expense_data,
        profit_data=profit_data,
        start_date=start_date,
        end_date=end_date,
        title='Reports'
    )


def get_sales_report(start_date, end_date):
    # Get all sales for the period
    sales = Sale.query.filter(
        Sale.sale_date >= start_date,
        Sale.sale_date <= end_date
    ).order_by(Sale.sale_date).all()
    
    # Get totals by day
    daily_sales = db.session.query(
        func.date(Sale.sale_date).label('date'),
        func.sum(Sale.total_amount).label('total')
    ).filter(
        Sale.sale_date >= start_date,
        Sale.sale_date <= end_date
    ).group_by(
        func.date(Sale.sale_date)
    ).all()
    
    # Get top selling products
    top_products = db.session.query(
        Product.name,
        Product.size,
        func.sum(SaleItem.quantity).label('quantity'),
        func.sum(SaleItem.total_price).label('total')
    ).join(
        SaleItem, SaleItem.product_id == Product.id
    ).join(
        Sale, Sale.id == SaleItem.sale_id
    ).filter(
        Sale.sale_date >= start_date,
        Sale.sale_date <= end_date
    ).group_by(
        Product.id
    ).order_by(
        desc('total')
    ).limit(5).all()
    
    # Get sales by category
    category_sales = db.session.query(
        Category.name,
        func.sum(SaleItem.total_price).label('total')
    ).join(
        Product, Product.id == SaleItem.product_id
    ).join(
        Category, Category.id == Product.category_id
    ).join(
        Sale, Sale.id == SaleItem.sale_id
    ).filter(
        Sale.sale_date >= start_date,
        Sale.sale_date <= end_date
    ).group_by(
        Category.name
    ).all()
    
    # Calculate total sales amount
    total_sales_amount = sum(sale.total_amount for sale in sales)
    
    # Prepare data for charts
    daily_sales_data = {str(day.date): float(day.total) for day in daily_sales}
    category_data = {cat.name: float(cat.total) for cat in category_sales}
    
    return {
        'sales': sales,
        'total_sales_amount': total_sales_amount,
        'top_products': top_products,
        'daily_sales_data': json.dumps(daily_sales_data),
        'category_data': json.dumps(category_data)
    }


def get_expense_report(start_date, end_date):
    # Get all expenses for the period
    expenses = Expense.query.filter(
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).order_by(Expense.expense_date).all()
    
    # Get totals by day
    daily_expenses = db.session.query(
        func.date(Expense.expense_date).label('date'),
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).group_by(
        func.date(Expense.expense_date)
    ).all()
    
    # Get expenses by category
    category_expenses = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).group_by(
        Expense.category
    ).all()
    
    # Calculate total expense amount
    total_expense_amount = sum(expense.amount for expense in expenses)
    
    # Prepare data for charts
    daily_expense_data = {str(day.date): float(day.total) for day in daily_expenses}
    category_data = {cat.category: float(cat.total) for cat in category_expenses}
    
    return {
        'expenses': expenses,
        'total_expense_amount': total_expense_amount,
        'daily_expense_data': json.dumps(daily_expense_data),
        'category_data': json.dumps(category_data)
    }


def get_profit_report(start_date, end_date):
    # Get total sales amount
    total_sales = db.session.query(func.sum(Sale.total_amount)).filter(
        Sale.sale_date >= start_date,
        Sale.sale_date <= end_date
    ).scalar() or 0
    
    # Get total expenses
    total_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).scalar() or 0
    
    # Get cost of goods sold
    cogs = db.session.query(
        func.sum(SaleItem.quantity * Product.purchase_price)
    ).join(
        Product, SaleItem.product_id == Product.id
    ).join(
        Sale, SaleItem.sale_id == Sale.id
    ).filter(
        Sale.sale_date >= start_date,
        Sale.sale_date <= end_date
    ).scalar() or 0
    
    # Calculate gross profit and net profit
    gross_profit = total_sales - cogs
    net_profit = gross_profit - total_expenses
    
    # Get daily profit data
    daily_sales = db.session.query(
        func.date(Sale.sale_date).label('date'),
        func.sum(Sale.total_amount).label('sales'),
        func.sum(SaleItem.quantity * Product.purchase_price).label('cogs')
    ).join(
        SaleItem, SaleItem.sale_id == Sale.id
    ).join(
        Product, SaleItem.product_id == Product.id
    ).filter(
        Sale.sale_date >= start_date,
        Sale.sale_date <= end_date
    ).group_by(
        func.date(Sale.sale_date)
    ).all()
    
    daily_expenses = db.session.query(
        func.date(Expense.expense_date).label('date'),
        func.sum(Expense.amount).label('expenses')
    ).filter(
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).group_by(
        func.date(Expense.expense_date)
    ).all()
    
    # Create a dictionary to easily access expense data by date
    expense_by_date = {str(e.date): float(e.expenses) for e in daily_expenses}
    
    # Calculate daily profit
    daily_profit_data = {}
    for day in daily_sales:
        date_str = str(day.date)
        sales_amount = float(day.sales)
        cogs_amount = float(day.cogs)
        expense_amount = expense_by_date.get(date_str, 0)
        
        gross_profit = sales_amount - cogs_amount
        net_profit = gross_profit - expense_amount
        
        daily_profit_data[date_str] = {
            'sales': sales_amount,
            'cogs': cogs_amount,
            'expenses': expense_amount,
            'gross_profit': gross_profit,
            'net_profit': net_profit
        }
    
    return {
        'total_sales': total_sales,
        'total_expenses': total_expenses,
        'cogs': cogs,
        'gross_profit': gross_profit,
        'net_profit': net_profit,
        'daily_profit_data': json.dumps({
            date: data['net_profit'] for date, data in daily_profit_data.items()
        })
    }


@app.route('/low-stock')
@login_required
def low_stock():
    # Get products with low stock (less than 10 items)
    low_stock_products = Product.query.filter(Product.quantity < 10).order_by(Product.quantity).all()
    return render_template('low_stock.html', products=low_stock_products, title='Low Stock Report')


# Get product info for sale
@app.route('/api/product/<int:product_id>')
@login_required
def get_product_info(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'size': product.size,
        'quantity': product.quantity,
        'selling_price': float(product.selling_price)
    })
