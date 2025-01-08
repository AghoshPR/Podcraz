from django.db import models
from django.contrib.auth.models import *


    
class User(AbstractUser):
    phone = models.CharField(max_length=15, null=True, blank=True)
    


# ProductCategory Model
class ProductCategory(models.Model):
    name = models.CharField(max_length=255)

# Brand Model
class Brand(models.Model):
    name = models.CharField(max_length=255)

# Product Model
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    product_category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE,related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE,related_name='products')

# ProductVariant Model
class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    color = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()

class ProductImage(models.Model):
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    image_path = models.ImageField(upload_to='product_images/')
    is_deleted = models.BooleanField(default=False)


# Cart Model
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True)

# CartItems Model
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

# Wishlist Model
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='wishlists')
    created_at = models.DateTimeField(auto_now_add=True)
    product_variants = models.ManyToManyField(ProductVariant, related_name='wishlists')


    

# Order Model
class Order(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    address = models.ForeignKey('Address', on_delete=models.CASCADE) #on_delete=models.PROTECT
    payment_method = models.ForeignKey('PaymentMethod', on_delete=models.SET_NULL, null=True)

# OrderItem Model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)

# PaymentMethod Model
class PaymentMethod(models.Model):
    name = models.CharField(max_length=255)

# Coupon Model
class Coupon(models.Model):

    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=50, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

# AppliedCoupon Model
class AppliedCoupon(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='coupon_applications')
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='applications')
    applied_at = models.DateTimeField(auto_now_add=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)

# Wallet Model
class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2)

# WalletTransaction Model
class WalletTransaction(models.Model):

    TRANSACTION_TYPES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=50, choices=TRANSACTION_TYPES)
    amount = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)

# Address Model
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    city = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    state = models.CharField(max_length=255)
    pin_code = models.CharField(max_length=10)
    address = models.TextField()
    is_default = models.BooleanField(default=False)
    order_address = models.BooleanField(default=False)




class Rating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ratings")
    rating = models.PositiveIntegerField()

class Offer(models.Model):
    DISCOUNT_TYPES = [
        ("percentage", "Percentage"),
        ("fixed", "Fixed Amount"),
    ]

    name = models.CharField(max_length=255)
    discount_type = models.CharField(max_length=50, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    max_uses = models.PositiveIntegerField()
    last_updated = models.DateTimeField(auto_now=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    product_category = models.ForeignKey(
        ProductCategory, on_delete=models.SET_NULL, null=True, blank=True
    )


