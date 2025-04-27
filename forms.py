from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SelectField, TextAreaField, 
    FloatField, IntegerField, DateField, SubmitField, HiddenField,
    BooleanField
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange, ValidationError
from datetime import datetime
from models import User, Category


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RegisterUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('manager', 'Manager'), ('staff', 'Staff')], validators=[DataRequired()])
    submit = SubmitField('Register User')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already exists. Please choose a different email.')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')


class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Submit')


class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    size = StringField('Size', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    purchase_price = FloatField('Purchase Price', validators=[DataRequired(), NumberRange(min=0)])
    selling_price = FloatField('Selling Price', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name')]


class SaleForm(FlaskForm):
    invoice_number = StringField('Invoice Number', validators=[DataRequired(), Length(max=3)])
    customer_name = StringField('Customer Name', validators=[Optional()])
    customer_mobile = StringField('Customer Mobile', validators=[Optional(), Length(max=15)])
    sale_date = DateField('Sale Date', validators=[DataRequired()], default=datetime.now)
    discount_type = SelectField('Discount Type', choices=[
        ('none', 'No Discount'),
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('special', 'Special Offer')
    ], default='none')
    discount_value = FloatField('Discount Value', validators=[Optional(), NumberRange(min=0)], default=0)
    submit = SubmitField('Complete Sale')


class SaleItemForm(FlaskForm):
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Add to Sale')

    def __init__(self, *args, **kwargs):
        super(SaleItemForm, self).__init__(*args, **kwargs)
        from models import Product
        self.product_id.choices = [(p.id, f"{p.name} - {p.size} (Stock: {p.quantity})") for p in Product.query.filter(Product.quantity > 0).order_by('name')]


class ExpenseForm(FlaskForm):
    category = StringField('Expense Category', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    description = TextAreaField('Description', validators=[Optional()])
    expense_date = DateField('Date', validators=[DataRequired()], default=datetime.now)
    submit = SubmitField('Submit')


class ReportFilterForm(FlaskForm):
    start_date = DateField('Start Date', validators=[DataRequired()], default=lambda: datetime.now().replace(day=1))
    end_date = DateField('End Date', validators=[DataRequired()], default=datetime.now)
    submit = SubmitField('Generate Report')
