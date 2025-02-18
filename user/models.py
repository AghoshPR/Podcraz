from django.db import models
from django.contrib.auth.models import *
import decimal
from datetime import timezone
from django.utils.timezone import now
from decimal import Decimal
from cloudinary.models import CloudinaryField


    
class User(AbstractUser):
    phone = models.CharField(max_length=15, null=True, blank=True)
    status = models.CharField(
        max_length=10,
        choices=[('Active', 'Active'), ('Blocked', 'Blocked')],
        default='Active'
    )

    def __str__(self):
        return self.username
    


# ProductCategory Model
class ProductCategory(models.Model):
    name = models.CharField(max_length=255)
    status = models.CharField(
        max_length=10,
        choices=[('Active', 'Active'), ('Blocked', 'Blocked')],
        default='Active' 
    )

    def __str__(self):
        return self.name

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

    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def apply_discount(self, discount_value, discount_type):
        
        if discount_type == 'percentage':
            self.discounted_price = self.price - (self.price * Decimal(str(discount_value)) / 100)
        else:  # fixed amount
            self.discounted_price = self.price - Decimal(str(discount_value))
        
        self.save()

    def remove_discount(self):
        self.discounted_price = None
        self.save()

    def get_active_offer(self):
        current_time = now()
        
        product_offer = Offer.objects.filter(
            product=self.product,
            is_active=True,
            valid_from__lte=current_time,
            valid_until__gte=current_time
        ).first()
        
        if product_offer:
            return product_offer
            
        
        category_offer = Offer.objects.filter(
            product_category=self.product.product_category,
            is_active=True,
            valid_from__lte=current_time,
            valid_until__gte=current_time
        ).first()
        
        return category_offer

    def get_offer_price(self):
        offer = self.get_active_offer()
        if not offer:
            return None
            
        if offer.discount_type == 'percentage':
            discount = self.price * Decimal(str(offer.discount_value)) / 100
            return self.price - discount
        else:  # fixed amount
            return self.price - Decimal(str(offer.discount_value))
        

class ProductImage(models.Model):
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    image_path = CloudinaryField('image')
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


    def get_total_price(self):
        offer_price = self.product_variant.get_offer_price()
        if offer_price:
            return offer_price * self.quantity
        return self.product_variant.price * self.quantity

    @property
    def total_price(self):
        if self.product_variant.discounted_price:
            return self.quantity * self.product_variant.discounted_price
        return self.quantity * self.price
    
    def save(self, *args ,**kwargs):

        self.price = (

            self.product_variant.discounted_price
            if self.product_variant.discounted_price
            else self.product_variant.price
        )
        super().save(*args, **kwargs)


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
        ('delivered', 'Delivered'),
        ('payment_failed', 'Payment Failed'),
        ('payment_pending', 'Payment Pending'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    address = models.ForeignKey('Address', on_delete=models.CASCADE)
    payment_method = models.ForeignKey('PaymentMethod', on_delete=models.SET_NULL, null=True)
    cancellation_reason = models.TextField(null=True, blank=True)
    return_reason = models.TextField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)

    def get_total_original_price(self):
        return sum(item.product_variant.price * item.quantity for item in self.items.all())

    def get_total_product_discount(self):
        return sum((item.product_variant.price * item.quantity) - (item.price * item.quantity) 
                  for item in self.items.all())

# OrderItem Model
class OrderItem(models.Model):
    ITEM_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('payment_failed', 'Payment Failed'),
        ('return_pending', 'Return Pending'),
        ('return_approved', 'Return Approved'),
        ('return_rejected', 'Return Rejected'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=ITEM_STATUS_CHOICES, default='pending')
    cancellation_reason = models.TextField(null=True, blank=True)
    return_reason = models.TextField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)

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
    description = models.TextField(null=True, blank=True)

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
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)

# Address Model
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    city = models.CharField(max_length=255)
    phone = models.CharField(max_length=15)
    state = models.CharField(max_length=255)
    pin_code = models.CharField(max_length=10)
    address = models.TextField()
    is_delete =  models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    order_address = models.BooleanField(default=False)

    def soft_delete(self):
             self.is_delete = True
             self.save()
 




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
    last_updated = models.DateTimeField(auto_now=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='offer')
    product_category = models.ForeignKey(
        ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='offer'
    )


