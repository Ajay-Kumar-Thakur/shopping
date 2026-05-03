"""
Complete Admin Configuration — CLEAN VERSION
No nested classes. Invoice imported from models. DeliverySettings registered at module level.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import (
    Category, Brand, Product, ProductImage,
    Size, Color, ProductVariant, Review,
    Customer, CustomerAddress, CustomerWishlist,
    Order, OrderItem, OrderStatusHistory, ShippingDetail, Invoice,
    PaymentMethod, Payment, Transaction, Refund,
    Inventory, StockHistory, LowStockAlert,
    Coupon, Discount, PromoCode, Offer,
    Page, Banner, Slider, Testimonial, FAQ, ContactMessage,
    SiteSetting, ShippingSetting, TaxSetting, EmailSetting, PaymentSetting,
    DeliverySettings,
)

admin.site.site_header = '✦ MyShop Administration'
admin.site.site_title  = 'MyShop Admin'
admin.site.index_title = 'Dashboard'


# ╔══════════════════════════════════════════════════════╗
# ║  1. PRODUCT MANAGEMENT                               ║
# ╚══════════════════════════════════════════════════════╝

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display        = ['name', 'slug', 'parent', 'product_count']
    prepopulated_fields = {'slug': ('name',)}
    search_fields       = ['name']

    def product_count(self, obj):
        return format_html('<b style="color:#2e8b62">{}</b>', obj.products.count())
    product_count.short_description = 'Products'


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display        = ['name', 'slug', 'website', 'is_active', 'product_count', 'created_at']
    list_filter         = ['is_active']
    list_editable       = ['is_active']
    search_fields       = ['name']
    prepopulated_fields = {'slug': ('name',)}

    def product_count(self, obj):
        return format_html('<b style="color:#2e8b62">{}</b>', obj.products.count())
    product_count.short_description = 'Products'


class ProductImageInline(admin.TabularInline):
    model           = ProductImage
    extra           = 2
    fields          = ['image_url', 'alt_text', 'is_primary', 'order', 'preview']
    readonly_fields = ['preview']

    def preview(self, obj):
        if obj.pk and obj.image_url:
            return format_html(
                '<img src="{}" style="height:70px;width:100px;object-fit:cover;'
                'border-radius:4px;border:1px solid #ddd;" '
                'onerror="this.style.display=\'none\'" />',
                obj.image_url,
            )
        return mark_safe('<span style="color:#bbb;font-size:11px;">save to preview</span>')
    preview.short_description = 'Preview'


class ProductVariantInline(admin.TabularInline):
    model  = ProductVariant
    extra  = 1
    fields = ['size', 'color', 'sku', 'price_adjustment', 'stock', 'is_active']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display        = ['name', 'brand', 'category', 'price', 'stock',
                           'is_featured', 'is_active', 'rating_col', 'created_at']
    list_filter         = ['category', 'brand', 'is_featured', 'is_active']
    list_editable       = ['price', 'stock', 'is_featured', 'is_active']
    search_fields       = ['name', 'description', 'brand__name']
    prepopulated_fields = {'slug': ('name',)}
    inlines             = [ProductImageInline, ProductVariantInline]
    readonly_fields     = ['main_image_preview', 'live_preview_script']
    fieldsets = (
        ('Basic Info',      {'fields': ('name', 'slug', 'category', 'brand', 'description')}),
        ('Pricing & Stock', {'fields': ('price', 'stock', 'image_url', 'main_image_preview')}),
        ('Visibility',      {'fields': ('is_featured', 'is_active')}),
        ('',                {'fields': ('live_preview_script',), 'classes': ('collapse',)}),
    )

    def main_image_preview(self, obj):
        url = ''
        if obj is not None and obj.pk and obj.image_url:
            url = obj.image_url
        if url:
            return format_html(
                '<img id="main-img-preview" src="{}" '
                'style="margin-top:6px;height:120px;width:180px;object-fit:cover;'
                'border-radius:6px;border:1px solid #ddd;" '
                'onerror="this.style.display=\'none\'" />',
                url,
            )
        return mark_safe(
            '<img id="main-img-preview" src="" '
            'style="display:none;margin-top:6px;height:120px;width:180px;'
            'object-fit:cover;border-radius:6px;border:1px solid #ddd;" />'
            '<span id="main-img-placeholder" '
            'style="display:block;margin-top:6px;color:#aaa;font-size:12px;">'
            'Enter an image URL above to see a live preview.</span>'
        )
    main_image_preview.short_description = 'Image preview'

    def live_preview_script(self, obj):
        return mark_safe("""
<script>
(function () {
  'use strict';
  function attachMainPreview() {
    var inp = document.querySelector('#id_image_url');
    var img = document.getElementById('main-img-preview');
    var ph  = document.getElementById('main-img-placeholder');
    if (!inp || !img) return;
    function update() {
      var url = inp.value.trim();
      if (url) { img.src = url; img.style.display = 'block'; if (ph) ph.style.display = 'none'; }
      else { img.style.display = 'none'; if (ph) ph.style.display = 'block'; }
    }
    inp.addEventListener('input', update);
    inp.addEventListener('change', update);
    update();
  }
  function wireRow(input) {
    var tr = input.closest('tr'); if (!tr) return;
    var previewTd = tr.querySelector('td.field-preview'); if (!previewTd) return;
    var img = previewTd.querySelector('img.inline-preview');
    if (!img) {
      img = document.createElement('img');
      img.className = 'inline-preview';
      img.style.cssText = 'height:70px;width:100px;object-fit:cover;border-radius:4px;border:1px solid #ddd;display:none;';
      img.onerror = function () { this.style.display = 'none'; };
      previewTd.innerHTML = ''; previewTd.appendChild(img);
    }
    function update() {
      var url = input.value.trim();
      if (url) { img.src = url; img.style.display = 'block'; } else { img.style.display = 'none'; }
    }
    input.addEventListener('input', update); input.addEventListener('change', update); update();
  }
  function attachInlinePreviews() {
    document.querySelectorAll('[id$="-image_url"]').forEach(function (inp) {
      if (inp.id.indexOf('images-') !== -1) wireRow(inp);
    });
  }
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (t && (t.classList.contains('add-row') || (t.closest && t.closest('.add-row')))) {
      setTimeout(attachInlinePreviews, 80);
    }
  });
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { attachMainPreview(); attachInlinePreviews(); });
  } else { attachMainPreview(); attachInlinePreviews(); }
}());
</script>
""")
    live_preview_script.short_description = ''

    def rating_col(self, obj):
        avg = obj.average_rating()
        if avg:
            stars = '★' * int(avg) + '☆' * (5 - int(avg))
            return format_html('<span style="color:#c9a84c">{}</span> ({})', stars, avg)
        return '—'
    rating_col.short_description = 'Rating'


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display  = ['name', 'code']
    search_fields = ['name', 'code']


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display  = ['name', 'hex_code', 'swatch']
    search_fields = ['name']

    def swatch(self, obj):
        if obj.hex_code:
            return format_html(
                '<div style="width:26px;height:26px;background:{};'
                'border-radius:4px;border:1px solid #ccc;display:inline-block;"></div>',
                obj.hex_code)
        return '—'
    swatch.short_description = 'Color'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display  = ['product', 'size', 'color', 'sku', 'price_adjustment', 'stock', 'is_active']
    list_filter   = ['is_active', 'size', 'color']
    list_editable = ['stock', 'is_active']
    search_fields = ['sku', 'product__name']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ['reviewer', 'product', 'stars_col', 'title', 'is_approved', 'created_at']
    list_filter   = ['is_approved', 'rating']
    list_editable = ['is_approved']
    search_fields = ['reviewer', 'email', 'product__name']
    actions       = ['approve', 'reject']

    def stars_col(self, obj):
        return format_html(
            '<span style="color:#c9a84c">{}</span><span style="color:#ccc">{}</span>',
            '★' * obj.rating, '☆' * (5 - obj.rating))
    stars_col.short_description = 'Rating'

    def approve(self, request, qs):
        qs.update(is_approved=True)
    approve.short_description = '✓ Approve selected reviews'

    def reject(self, request, qs):
        qs.update(is_approved=False)
    reject.short_description = '✗ Reject selected reviews'


# ╔══════════════════════════════════════════════════════╗
# ║  2. CUSTOMER MANAGEMENT                              ║
# ╚══════════════════════════════════════════════════════╝

class CustomerAddressInline(admin.TabularInline):
    model  = CustomerAddress
    extra  = 1
    fields = ['address_type', 'full_name', 'city', 'country', 'is_default']


class CustomerWishlistInline(admin.TabularInline):
    model           = CustomerWishlist
    extra           = 0
    fields          = ['product', 'added_at']
    readonly_fields = ['added_at']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display    = ['full_name', 'email', 'phone', 'is_active', 'order_count', 'created_at']
    list_filter     = ['is_active', 'created_at']
    list_editable   = ['is_active']
    search_fields   = ['first_name', 'last_name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    inlines         = [CustomerAddressInline, CustomerWishlistInline]

    def order_count(self, obj):
        return format_html('<b style="color:#2e8b62">{} orders</b>', obj.orders.count())
    order_count.short_description = 'Orders'


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display  = ['full_name', 'customer', 'address_type', 'city', 'country', 'is_default']
    list_filter   = ['address_type', 'country', 'is_default']
    search_fields = ['full_name', 'customer__email', 'city']


@admin.register(CustomerWishlist)
class CustomerWishlistAdmin(admin.ModelAdmin):
    list_display  = ['customer', 'product', 'added_at']
    list_filter   = ['added_at']
    search_fields = ['customer__email', 'product__name']


# ╔══════════════════════════════════════════════════════╗
# ║  3. ORDER MANAGEMENT                                 ║
# ╚══════════════════════════════════════════════════════╝

class OrderItemInline(admin.TabularInline):
    model           = OrderItem
    extra           = 0
    fields          = ['product', 'variant', 'quantity', 'unit_price', 'total_price']
    readonly_fields = ['total_price']


class OrderStatusHistoryInline(admin.TabularInline):
    model           = OrderStatusHistory
    extra           = 0
    fields          = ['status', 'note', 'changed_by', 'changed_at']
    readonly_fields = ['changed_at']


class ShippingDetailInline(admin.StackedInline):
    model  = ShippingDetail
    extra  = 0
    fields = [
        'delivery_type', 'full_name', 'phone', 'email',
        'city', 'province', 'street_address', 'country',
        'tracking_number', 'carrier', 'estimated_delivery',
    ]


class InvoiceInline(admin.TabularInline):
    model           = Invoice
    extra           = 0
    fields          = ['invoice_number', 'issued_at', 'due_date', 'is_paid']
    readonly_fields = ['invoice_number', 'issued_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display    = ['order_number', 'buyer_col', 'status',
                       'status_badge', 'total_col', 'items_count', 'created_at']
    list_filter     = ['status', 'created_at']
    list_editable   = ['status']
    search_fields   = ['order_number', 'guest_name', 'guest_email', 'customer__email']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines         = [OrderItemInline, ShippingDetailInline,
                       OrderStatusHistoryInline, InvoiceInline]
    fieldsets = (
        ('Order Info',  {'fields': ('order_number', 'status', 'note', 'coupon')}),
        ('Customer',    {'fields': ('customer', 'guest_name', 'guest_email', 'guest_phone')}),
        ('Financials',  {'fields': ('subtotal', 'discount', 'shipping_fee', 'tax', 'total')}),
        ('Timestamps',  {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def buyer_col(self, obj):
        return obj.buyer_name() or '—'
    buyer_col.short_description = 'Customer'

    def status_badge(self, obj):
        colors = {
            'pending': '#e2a800', 'confirmed': '#3dab78', 'processing': '#2e8b62',
            'packed': '#1a6040',  'shipped': '#185fa5',   'delivered': '#27500a',
            'cancelled': '#e05252', 'refunded': '#8b3a8b',
        }
        color = colors.get(obj.status, '#888')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;'
            'border-radius:12px;font-size:11px;font-weight:500">{}</span>',
            color, obj.get_status_display())
    status_badge.short_description = 'Badge'

    def total_col(self, obj):
        return format_html('<b style="color:#c9a84c">NPR {}</b>', obj.total)
    total_col.short_description = 'Total'

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Items'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display  = ['order', 'product', 'variant', 'quantity', 'unit_price', 'total_price']
    list_filter   = ['order__status']
    search_fields = ['order__order_number', 'product__name']


@admin.register(ShippingDetail)
class ShippingDetailAdmin(admin.ModelAdmin):
    list_display    = ['order', 'delivery_type_badge', 'full_name', 'phone', 'city', 'country']
    list_filter     = ['delivery_type']
    search_fields   = ['order__order_number', 'full_name', 'phone', 'city']
    readonly_fields = ['order']
    fieldsets = (
        ('Order',            {'fields': ('order', 'delivery_type')}),
        ('Customer Contact', {'fields': ('full_name', 'phone', 'email')}),
        ('Delivery Address', {'fields': ('city', 'province', 'street_address', 'country')}),
        ('Logistics',        {'classes': ('collapse',),
                              'fields': ('tracking_number', 'carrier',
                                         'shipped_at', 'delivered_at', 'estimated_delivery')}),
    )

    def delivery_type_badge(self, obj):
        colors = {'home': '#185fa5', 'pickup': '#2e8b62'}
        color  = colors.get(obj.delivery_type, '#888')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;'
            'border-radius:12px;font-size:11px;font-weight:500">{}</span>',
            color, obj.get_delivery_type_display())
    delivery_type_badge.short_description = 'Delivery Type'


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display  = ['invoice_number', 'order', 'issued_at', 'due_date', 'is_paid']
    list_filter   = ['is_paid']
    list_editable = ['is_paid']
    search_fields = ['invoice_number', 'order__order_number']


# ╔══════════════════════════════════════════════════════╗
# ║  4. PAYMENT MANAGEMENT                               ║
# ╚══════════════════════════════════════════════════════╝

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display  = ['name', 'method_type', 'is_active']
    list_editable = ['is_active']
    list_filter   = ['is_active', 'method_type']


class TransactionInline(admin.TabularInline):
    model           = Transaction
    extra           = 0
    fields          = ['transaction_type', 'amount', 'reference_id', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ['order', 'payment_method', 'amount_col',
                     'status', 'status_badge', 'transaction_id', 'created_at']
    list_filter   = ['status', 'payment_method']
    list_editable = ['status']
    search_fields = ['order__order_number', 'transaction_id']
    inlines       = [TransactionInline]

    def amount_col(self, obj):
        return format_html('<b style="color:#c9a84c">NPR {}</b>', obj.amount)
    amount_col.short_description = 'Amount'

    def status_badge(self, obj):
        colors = {'pending': '#e2a800', 'completed': '#2e8b62',
                  'failed': '#e05252',  'refunded': '#8b3a8b'}
        color = colors.get(obj.status, '#888')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;'
            'border-radius:12px;font-size:11px">{}</span>',
            color, obj.get_status_display())
    status_badge.short_description = 'Badge'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display  = ['payment', 'transaction_type', 'amount', 'reference_id', 'created_at']
    list_filter   = ['transaction_type']
    search_fields = ['reference_id', 'payment__order__order_number']


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display  = ['order', 'amount', 'status', 'created_at']
    list_filter   = ['status']
    list_editable = ['status']
    search_fields = ['order__order_number']
    actions       = ['approve_refunds']

    def approve_refunds(self, request, qs):
        qs.update(status='approved')
    approve_refunds.short_description = '✓ Approve selected refunds'


# ╔══════════════════════════════════════════════════════╗
# ║  5. INVENTORY / STOCK MANAGEMENT                     ║
# ╚══════════════════════════════════════════════════════╝

class StockHistoryInline(admin.TabularInline):
    model           = StockHistory
    extra           = 0
    fields          = ['action', 'quantity', 'note', 'performed_by', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display  = ['product', 'quantity', 'reserved', 'available_col',
                     'low_stock_threshold', 'stock_status', 'last_restocked']
    list_filter   = ['last_restocked']
    search_fields = ['product__name']
    inlines       = [StockHistoryInline]

    def available_col(self, obj):
        return format_html('<b>{}</b>', obj.available_stock())
    available_col.short_description = 'Available'

    def stock_status(self, obj):
        if obj.is_low_stock():
            return mark_safe('<span style="background:#e05252;color:#fff;padding:3px 10px;border-radius:12px;font-size:11px">⚠ Low Stock</span>')
        return mark_safe('<span style="background:#2e8b62;color:#fff;padding:3px 10px;border-radius:12px;font-size:11px">✓ OK</span>')
    stock_status.short_description = 'Status'


@admin.register(StockHistory)
class StockHistoryAdmin(admin.ModelAdmin):
    list_display  = ['inventory', 'action', 'quantity', 'performed_by', 'created_at']
    list_filter   = ['action', 'created_at']
    search_fields = ['inventory__product__name']


@admin.register(LowStockAlert)
class LowStockAlertAdmin(admin.ModelAdmin):
    list_display  = ['inventory', 'message', 'is_resolved', 'created_at']
    list_filter   = ['is_resolved']
    list_editable = ['is_resolved']
    actions       = ['mark_resolved']

    def mark_resolved(self, request, qs):
        qs.update(is_resolved=True, resolved_at=timezone.now())
    mark_resolved.short_description = '✓ Mark as Resolved'


# ╔══════════════════════════════════════════════════════╗
# ║  6. MARKETING                                        ║
# ╚══════════════════════════════════════════════════════╝

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display  = ['code', 'discount_type', 'discount_value',
                     'used_count', 'max_uses', 'valid_status', 'is_active']
    list_filter   = ['discount_type', 'is_active']
    list_editable = ['is_active']
    search_fields = ['code']

    def valid_status(self, obj):
        if obj.is_valid():
            return mark_safe('<span style="background:#2e8b62;color:#fff;padding:3px 10px;border-radius:12px;font-size:11px">✓ Valid</span>')
        return mark_safe('<span style="background:#e05252;color:#fff;padding:3px 10px;border-radius:12px;font-size:11px">✗ Expired</span>')
    valid_status.short_description = 'Validity'


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display      = ['name', 'discount_type', 'discount_value', 'valid_from', 'valid_until', 'is_active']
    list_filter       = ['discount_type', 'is_active']
    list_editable     = ['is_active']
    filter_horizontal = ['products', 'categories']


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display  = ['code', 'discount', 'used_count', 'max_uses', 'is_active']
    list_editable = ['is_active']
    search_fields = ['code']


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display  = ['title', 'valid_from', 'valid_until', 'is_active']
    list_editable = ['is_active']
    search_fields = ['title']


# ╔══════════════════════════════════════════════════════╗
# ║  7. CONTENT MANAGEMENT                               ║
# ╚══════════════════════════════════════════════════════╝

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display        = ['title', 'slug', 'is_active', 'updated_at']
    list_editable       = ['is_active']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display  = ['title', 'position', 'order', 'is_active', 'valid_from', 'valid_until']
    list_editable = ['order', 'is_active']
    list_filter   = ['position', 'is_active']


@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display  = ['title', 'order', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display  = ['name', 'role', 'rating_col', 'is_active', 'created_at']
    list_editable = ['is_active']

    def rating_col(self, obj):
        return format_html('<span style="color:#c9a84c">{}</span>', '★' * obj.rating)
    rating_col.short_description = 'Rating'


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display  = ['question', 'category', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter   = ['category', 'is_active']
    search_fields = ['question', 'answer']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display    = ['name', 'email', 'subject', 'status', 'status_badge', 'created_at']
    list_filter     = ['status']
    list_editable   = ['status']
    search_fields   = ['name', 'email', 'subject']
    readonly_fields = ['created_at']

    def status_badge(self, obj):
        colors = {'new': '#e2a800', 'read': '#185fa5',
                  'replied': '#2e8b62', 'archived': '#888'}
        color = colors.get(obj.status, '#888')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;'
            'border-radius:12px;font-size:11px">{}</span>',
            color, obj.get_status_display())
    status_badge.short_description = 'Badge'


# ╔══════════════════════════════════════════════════════╗
# ║  8. SETTINGS                                         ║
# ╚══════════════════════════════════════════════════════╝

@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display  = ['key', 'label', 'group', 'value_preview', 'updated_at']
    list_filter   = ['group']
    search_fields = ['key', 'label']

    def value_preview(self, obj):
        v = obj.value
        return v[:60] + '...' if len(v) > 60 else v
    value_preview.short_description = 'Value'


@admin.register(ShippingSetting)
class ShippingSettingAdmin(admin.ModelAdmin):
    list_display  = ['name', 'rate', 'min_days', 'max_days', 'free_above', 'is_active']
    list_editable = ['is_active']


@admin.register(TaxSetting)
class TaxSettingAdmin(admin.ModelAdmin):
    list_display  = ['name', 'rate', 'country', 'is_active']
    list_editable = ['is_active']


@admin.register(EmailSetting)
class EmailSettingAdmin(admin.ModelAdmin):
    list_display = ['smtp_host', 'smtp_port', 'from_email', 'from_name', 'use_tls']


@admin.register(PaymentSetting)
class PaymentSettingAdmin(admin.ModelAdmin):
    list_display  = ['provider', 'is_test_mode', 'is_active', 'updated_at']
    list_editable = ['is_active']


# ╔══════════════════════════════════════════════════════╗
# ║  9. DELIVERY SETTINGS                                ║
# ╚══════════════════════════════════════════════════════╝

@admin.register(DeliverySettings)
class DeliverySettingsAdmin(admin.ModelAdmin):
    list_display  = ['standard_label', 'standard_free_above',
                     'express_label',  'express_surcharge',
                     'pickup_enabled', 'is_active', 'updated_at']
    list_editable = ['is_active']
    fieldsets = (
        ('Standard Delivery', {
            'fields': ('standard_label', 'standard_description',
                       'standard_free_above', 'standard_badge_text'),
        }),
        ('Express Delivery', {
            'fields': ('express_label', 'express_description',
                       'express_surcharge', 'express_badge_text'),
        }),
        ('Pickup', {
            'fields': ('pickup_enabled', 'pickup_address', 'pickup_hours'),
        }),
        ('Status', {
            'fields': ('is_active',),
        }),
    )

    def has_add_permission(self, request):
        return not DeliverySettings.objects.exists()