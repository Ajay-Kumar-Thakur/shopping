"""
Complete E-Commerce Models — CLEAN SINGLE FILE
No duplicate classes. Invoice included. DeliverySettings defined once.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


# ╔══════════════════════════════════════════════════════╗
# ║  1. PRODUCT MANAGEMENT                               ║
# ╚══════════════════════════════════════════════════════╝

class Category(models.Model):
    name       = models.CharField(max_length=100)
    slug       = models.SlugField(unique=True)
    parent     = models.ForeignKey('self', null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Brand(models.Model):
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(unique=True)
    logo_url    = models.URLField(blank=True)
    description = models.TextField(blank=True)
    website     = models.URLField(blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10)

    def __str__(self):
        return f'{self.name} ({self.code})'


class Color(models.Model):
    name     = models.CharField(max_length=50)
    hex_code = models.CharField(max_length=7, blank=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    category    = models.ForeignKey(Category, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='products')
    brand       = models.ForeignKey(Brand, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='products')
    name        = models.CharField(max_length=200)
    slug        = models.SlugField(unique=True)
    description = models.TextField()
    price       = models.DecimalField(max_digits=10, decimal_places=2)
    image       = models.ImageField(upload_to='products/', blank=True, null=True)
    image_url   = models.URLField(blank=True)
    stock       = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return 0

    def review_count(self):
        return self.reviews.filter(is_approved=True).count()

    def get_display_image(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        primary = self.images.filter(is_primary=True).first()
        if primary:
            url = primary.get_url()
            if url:
                return url
        first = self.images.first()
        if first:
            url = first.get_url()
            if url:
                return url
        return ''


class ProductImage(models.Model):
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image      = models.ImageField(upload_to='product_images/', blank=True, null=True)
    image_url  = models.URLField(blank=True)
    alt_text   = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order      = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'Image — {self.product.name}'

    def get_url(self):
        if self.image:
            return self.image.url
        if self.image_url:
            return self.image_url
        return ''


class ProductVariant(models.Model):
    product          = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size             = models.ForeignKey(Size, null=True, blank=True, on_delete=models.SET_NULL)
    color            = models.ForeignKey(Color, null=True, blank=True, on_delete=models.SET_NULL)
    sku              = models.CharField(max_length=100, unique=True)
    price_adjustment = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    stock            = models.IntegerField(default=0)
    is_active        = models.BooleanField(default=True)

    class Meta:
        unique_together = ['product', 'size', 'color']

    def __str__(self):
        parts = [self.product.name]
        if self.size:  parts.append(self.size.code)
        if self.color: parts.append(self.color.name)
        return ' — '.join(parts)

    def final_price(self):
        return self.product.price + self.price_adjustment


class Review(models.Model):
    product     = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    reviewer    = models.CharField(max_length=100)
    email       = models.EmailField()
    rating      = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title       = models.CharField(max_length=200, blank=True)
    body        = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'email']

    def __str__(self):
        return f'{self.reviewer} — {self.product.name} ({self.rating}★)'


# ╔══════════════════════════════════════════════════════╗
# ║  2. CUSTOMER MANAGEMENT                              ║
# ╚══════════════════════════════════════════════════════╝

class Customer(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE,
                                      related_name='customer', null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)
    email      = models.EmailField(unique=True)
    phone      = models.CharField(max_length=20, blank=True)
    avatar_url = models.URLField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def full_name(self):
        return f'{self.first_name} {self.last_name}'


class CustomerAddress(models.Model):
    ADDRESS_TYPES = [('billing','Billing'),('shipping','Shipping'),('both','Both')]
    customer      = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='addresses')
    address_type  = models.CharField(max_length=10, choices=ADDRESS_TYPES, default='shipping')
    full_name     = models.CharField(max_length=200)
    phone         = models.CharField(max_length=20, blank=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city          = models.CharField(max_length=100)
    state         = models.CharField(max_length=100)
    postal_code   = models.CharField(max_length=20)
    country       = models.CharField(max_length=100, default='Nepal')
    is_default    = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Customer Addresses'

    def __str__(self):
        return f'{self.full_name} — {self.city}, {self.country}'


class CustomerWishlist(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='wishlist')
    product  = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Customer Wishlists'
        unique_together = ['customer', 'product']
        ordering = ['-added_at']

    def __str__(self):
        return f'{self.customer} ♥ {self.product.name}'


# ╔══════════════════════════════════════════════════════╗
# ║  3. ORDER MANAGEMENT                                 ║
# ╚══════════════════════════════════════════════════════╝

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending','Pending'),('confirmed','Confirmed'),('processing','Processing'),
        ('packed','Packed'),('shipped','Shipped'),('delivered','Delivered'),
        ('cancelled','Cancelled'),('refunded','Refunded'),
    ]
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    customer     = models.ForeignKey(Customer, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='orders')
    guest_name   = models.CharField(max_length=200, blank=True)
    guest_email  = models.EmailField(blank=True)
    guest_phone  = models.CharField(max_length=20, blank=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    subtotal     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_fee = models.DecimalField(max_digits=8,  decimal_places=2, default=0)
    tax          = models.DecimalField(max_digits=8,  decimal_places=2, default=0)
    total        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    note         = models.TextField(blank=True)
    coupon       = models.ForeignKey('Coupon', null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name='orders')
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.order_number or self.id}'

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f'ORD-{uuid.uuid4().hex[:8].upper()}'
        super().save(*args, **kwargs)

    def buyer_name(self):
        if self.customer:
            return self.customer.full_name()
        return self.guest_name


class OrderItem(models.Model):
    order       = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product     = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant     = models.ForeignKey('ProductVariant', null=True, blank=True,
                                    on_delete=models.SET_NULL)
    quantity    = models.PositiveIntegerField(default=1)
    unit_price  = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.quantity}x {self.product.name}'

    def save(self, *args, **kwargs):
        self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status     = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    note       = models.TextField(blank=True)
    changed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Order Status Histories'
        ordering = ['-changed_at']

    def __str__(self):
        return f'Order #{self.order.order_number} → {self.status}'

class ShippingDetail(models.Model):
    DELIVERY_TYPES   = [('home','Home Delivery'),('pickup','Pickup')]
    PROVINCE_CHOICES = [
        ('koshi','Koshi Province'),('madhesh','Madhesh Province'),
        ('bagmati','Bagmati Province'),('gandaki','Gandaki Province'),
        ('lumbini','Lumbini Province'),('karnali','Karnali Province'),
        ('sudurpashchim','Sudurpashchim Province'),
    ]
    order          = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='shipping')
    delivery_type  = models.CharField(max_length=10, choices=DELIVERY_TYPES, default='home')
    full_name      = models.CharField(max_length=200, blank=True)
    phone          = models.CharField(max_length=20, blank=True)
    email          = models.EmailField(blank=True)
    city           = models.CharField(max_length=100, blank=True)
    province       = models.CharField(max_length=20, choices=PROVINCE_CHOICES, blank=True)
    street_address = models.CharField(max_length=300, blank=True)
    address_line1  = models.CharField(max_length=255, blank=True)
    address_line2  = models.CharField(max_length=255, blank=True)
    state          = models.CharField(max_length=100, blank=True)
    postal_code    = models.CharField(max_length=20, blank=True)
    country        = models.CharField(max_length=100, default='Nepal')
    tracking_number    = models.CharField(max_length=100, blank=True)
    carrier            = models.CharField(max_length=100, blank=True)
    shipped_at         = models.DateTimeField(null=True, blank=True)
    delivered_at       = models.DateTimeField(null=True, blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'Shipping ({self.get_delivery_type_display()}) — Order #{self.order.order_number}'


class Invoice(models.Model):
    order          = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=20, unique=True, blank=True)
    issued_at      = models.DateTimeField(auto_now_add=True)
    due_date       = models.DateField(null=True, blank=True)
    is_paid        = models.BooleanField(default=False)
    notes          = models.TextField(blank=True)

    def __str__(self):
        return f'Invoice #{self.invoice_number}'

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f'INV-{uuid.uuid4().hex[:8].upper()}'
        super().save(*args, **kwargs)


# ╔══════════════════════════════════════════════════════╗
# ║  4. PAYMENT MANAGEMENT                               ║
# ╚══════════════════════════════════════════════════════╝

class PaymentMethod(models.Model):
    METHOD_TYPES = [
        ('credit_card','Credit Card'),('debit_card','Debit Card'),
        ('paypal','PayPal'),('stripe','Stripe'),('esewa','eSewa'),
        ('khalti','Khalti'),('bank_transfer','Bank Transfer'),
        ('cash_on_delivery','Cash on Delivery'),
    ]
    name        = models.CharField(max_length=100)
    method_type = models.CharField(max_length=20, choices=METHOD_TYPES)
    is_active   = models.BooleanField(default=True)
    icon_url    = models.URLField(blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending','Pending'),('completed','Completed'),
        ('failed','Failed'),('refunded','Refunded'),
    ]
    order          = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.ForeignKey(PaymentMethod, null=True, blank=True,
                                       on_delete=models.SET_NULL)
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=200, blank=True)
    paid_at        = models.DateTimeField(null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Payment ${self.amount} — Order #{self.order.order_number}'


class Transaction(models.Model):
    TYPES = [('charge','Charge'),('refund','Refund'),('partial_refund','Partial Refund')]
    payment          = models.ForeignKey(Payment, on_delete=models.CASCADE,
                                         related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TYPES)
    amount           = models.DecimalField(max_digits=10, decimal_places=2)
    reference_id     = models.CharField(max_length=200, blank=True)
    gateway_response = models.TextField(blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.transaction_type} — ${self.amount}'


class Refund(models.Model):
    STATUS_CHOICES = [
        ('requested','Requested'),('approved','Approved'),
        ('rejected','Rejected'),('processed','Processed'),
    ]
    order        = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refunds')
    payment      = models.ForeignKey(Payment, null=True, blank=True, on_delete=models.SET_NULL)
    amount       = models.DecimalField(max_digits=10, decimal_places=2)
    reason       = models.TextField()
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Refund ${self.amount} — Order #{self.order.order_number}'


# ╔══════════════════════════════════════════════════════╗
# ║  5. INVENTORY / STOCK MANAGEMENT                     ║
# ╚══════════════════════════════════════════════════════╝

class Inventory(models.Model):
    product             = models.OneToOneField(Product, on_delete=models.CASCADE,
                                               related_name='inventory')
    quantity            = models.IntegerField(default=0)
    reserved            = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(default=10)
    last_restocked      = models.DateTimeField(null=True, blank=True)
    updated_at          = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Inventories'

    def __str__(self):
        return f'Inventory — {self.product.name}'

    def available_stock(self):
        return self.quantity - self.reserved

    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold


class StockHistory(models.Model):
    ACTION_TYPES = [
        ('restock','Restock'),('sale','Sale'),('return','Return'),
        ('adjustment','Adjustment'),('damage','Damage'),
    ]
    inventory    = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='history')
    action       = models.CharField(max_length=20, choices=ACTION_TYPES)
    quantity     = models.IntegerField()
    note         = models.TextField(blank=True)
    performed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Stock Histories'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} ({self.quantity}) — {self.inventory.product.name}'


class LowStockAlert(models.Model):
    inventory   = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name='alerts')
    message     = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Alert — {self.inventory.product.name}'


# ╔══════════════════════════════════════════════════════╗
# ║  6. MARKETING                                        ║
# ╚══════════════════════════════════════════════════════╝

class Coupon(models.Model):
    DISCOUNT_TYPES = [('percent','Percentage'),('fixed','Fixed Amount')]
    code             = models.CharField(max_length=50, unique=True)
    discount_type    = models.CharField(max_length=10, choices=DISCOUNT_TYPES)
    discount_value   = models.DecimalField(max_digits=8, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_uses         = models.IntegerField(null=True, blank=True)
    used_count       = models.IntegerField(default=0)
    valid_from       = models.DateTimeField()
    valid_until      = models.DateTimeField()
    is_active        = models.BooleanField(default=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True


class Discount(models.Model):
    DISCOUNT_TYPES = [('percent','Percentage'),('fixed','Fixed Amount')]
    name           = models.CharField(max_length=100)
    discount_type  = models.CharField(max_length=10, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=8, decimal_places=2)
    products       = models.ManyToManyField(Product, blank=True, related_name='discounts')
    categories     = models.ManyToManyField(Category, blank=True, related_name='discounts')
    valid_from     = models.DateTimeField()
    valid_until    = models.DateTimeField()
    is_active      = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PromoCode(models.Model):
    code        = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount    = models.ForeignKey(Discount, on_delete=models.CASCADE, related_name='promo_codes')
    max_uses    = models.IntegerField(null=True, blank=True)
    used_count  = models.IntegerField(default=0)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code


class Offer(models.Model):
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image_url   = models.URLField(blank=True)
    link        = models.URLField(blank=True)
    valid_from  = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active   = models.BooleanField(default=True)

    def __str__(self):
        return self.title


# ╔══════════════════════════════════════════════════════╗
# ║  7. WEBSITE CONTENT MANAGEMENT                       ║
# ╚══════════════════════════════════════════════════════╝

class Page(models.Model):
    title      = models.CharField(max_length=200)
    slug       = models.SlugField(unique=True)
    content    = models.TextField()
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Banner(models.Model):
    POSITIONS = [('hero','Hero'),('top','Top Bar'),('sidebar','Sidebar'),('popup','Popup')]
    title       = models.CharField(max_length=200)
    subtitle    = models.CharField(max_length=300, blank=True)
    image_url   = models.URLField()
    link        = models.URLField(blank=True)
    position    = models.CharField(max_length=20, choices=POSITIONS, default='hero')
    order       = models.PositiveIntegerField(default=0)
    is_active   = models.BooleanField(default=True)
    valid_from  = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Slider(models.Model):
    title     = models.CharField(max_length=200)
    subtitle  = models.CharField(max_length=300, blank=True)
    image_url = models.URLField()
    link      = models.URLField(blank=True)
    btn_text  = models.CharField(max_length=50, blank=True)
    order     = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    name       = models.CharField(max_length=100)
    role       = models.CharField(max_length=100, blank=True)
    message    = models.TextField()
    avatar_url = models.URLField(blank=True)
    rating     = models.IntegerField(default=5,
                     validators=[MinValueValidator(1), MaxValueValidator(5)])
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} — Testimonial'


class FAQ(models.Model):
    question  = models.CharField(max_length=300)
    answer    = models.TextField()
    category  = models.CharField(max_length=100, blank=True)
    order     = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['order']

    def __str__(self):
        return self.question


class ContactMessage(models.Model):
    STATUS_CHOICES = [
        ('new','New'),('read','Read'),('replied','Replied'),('archived','Archived'),
    ]
    name       = models.CharField(max_length=100)
    email      = models.EmailField()
    phone      = models.CharField(max_length=20, blank=True)
    subject    = models.CharField(max_length=200)
    message    = models.TextField()
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} — {self.subject}'


# ╔══════════════════════════════════════════════════════╗
# ║  8. SETTINGS                                         ║
# ╚══════════════════════════════════════════════════════╝

class SiteSetting(models.Model):
    key        = models.CharField(max_length=100, unique=True)
    value      = models.TextField()
    label      = models.CharField(max_length=200, blank=True)
    group      = models.CharField(max_length=50, default='general')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Site Setting'
        verbose_name_plural = 'Site Settings'
        ordering = ['group', 'key']

    def __str__(self):
        return f'[{self.group}] {self.key}'


class ShippingSetting(models.Model):
    name       = models.CharField(max_length=100)
    rate       = models.DecimalField(max_digits=8, decimal_places=2)
    min_days   = models.IntegerField(default=1)
    max_days   = models.IntegerField(default=7)
    is_active  = models.BooleanField(default=True)
    free_above = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.name


class TaxSetting(models.Model):
    name      = models.CharField(max_length=100)
    rate      = models.DecimalField(max_digits=5, decimal_places=2)
    country   = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name} ({self.rate}%)'


class EmailSetting(models.Model):
    smtp_host     = models.CharField(max_length=200, default='smtp.gmail.com')
    smtp_port     = models.IntegerField(default=587)
    smtp_user     = models.CharField(max_length=200)
    smtp_password = models.CharField(max_length=200)
    use_tls       = models.BooleanField(default=True)
    from_email    = models.EmailField()
    from_name     = models.CharField(max_length=100, default='MyShop')
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Email Setting'
        verbose_name_plural = 'Email Settings'

    def __str__(self):
        return f'Email Config — {self.smtp_host}'


class PaymentSetting(models.Model):
    provider     = models.CharField(max_length=100)
    api_key      = models.CharField(max_length=300, blank=True)
    secret_key   = models.CharField(max_length=300, blank=True)
    is_test_mode = models.BooleanField(default=True)
    is_active    = models.BooleanField(default=False)
    updated_at   = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.provider} ({"Test" if self.is_test_mode else "Live"})'


# ╔══════════════════════════════════════════════════════╗
# ║  9. DELIVERY SETTINGS  (defined ONCE here only)     ║
# ╚══════════════════════════════════════════════════════╝

class DeliverySettings(models.Model):
    standard_label       = models.CharField(max_length=100, default='Standard Delivery')
    standard_description = models.CharField(max_length=200,
                               default='3–5 business days across Nepal')
    standard_free_above  = models.DecimalField(max_digits=10, decimal_places=2, default=2000)
    standard_badge_text  = models.CharField(max_length=100, blank=True)

    express_label        = models.CharField(max_length=100, default='Express Delivery')
    express_description  = models.CharField(max_length=200,
                               default='Next-day delivery within Kathmandu Valley')
    express_surcharge    = models.DecimalField(max_digits=8, decimal_places=2, default=150)
    express_badge_text   = models.CharField(max_length=100, blank=True)

    pickup_enabled       = models.BooleanField(default=True)
    pickup_address       = models.CharField(max_length=300, blank=True,
                               default='New Road, Kathmandu')
    pickup_hours         = models.CharField(max_length=200, blank=True,
                               default='Sun–Fri, 10 AM – 6 PM')

    is_active  = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'Delivery Settings'
        verbose_name_plural = 'Delivery Settings'

    def __str__(self):
        return f'Delivery Settings (updated {self.updated_at.strftime("%Y-%m-%d")})'

    def get_standard_badge(self):
        return self.standard_badge_text or \
               f'FREE on orders over NPR {int(self.standard_free_above):,}'

    def get_express_badge(self):
        return self.express_badge_text or \
               f'NPR {int(self.express_surcharge)} surcharge'

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True).first()