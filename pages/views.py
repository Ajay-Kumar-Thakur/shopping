from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
import json
import uuid
import hmac
import hashlib
import base64
import requests

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from .models import (
    Product, Category, Brand, Order, OrderItem,
    ShippingDetail, Payment, PaymentMethod,
    Inventory, LowStockAlert,
    Coupon, Slider, Banner, Testimonial, FAQ,
    ContactMessage, Page, DeliverySettings,
)
from .forms import EnhancedOrderForm, ReviewForm, ContactForm
import uuid


def get_delivery_settings():
    try:
        return DeliverySettings.objects.filter(is_active=True).order_by('-pk').first()
    except Exception:
        return None


# ── Homepage ──────────────────────────────────────────────────
def index(request):
    return render(request, 'pages/index.html', {
        'featured_products': Product.objects.filter(is_featured=True, is_active=True, stock__gt=0)[:6],
        'latest_products':   Product.objects.filter(is_active=True, stock__gt=0).order_by('-created_at')[:8],
        'categories':        Category.objects.all(),
        'brands':            Brand.objects.filter(is_active=True),
        'sliders':           Slider.objects.filter(is_active=True).order_by('order'),
        'banners':           Banner.objects.filter(is_active=True, position='hero').order_by('order'),
        'testimonials':      Testimonial.objects.filter(is_active=True)[:6],
        'total_products':    Product.objects.filter(is_active=True, stock__gt=0).count(),
    })


# ── Product List ──────────────────────────────────────────────
def product_list(request):
    products   = Product.objects.filter(is_active=True, stock__gt=0).select_related('brand', 'category')
    categories = Category.objects.all()
    brands     = Brand.objects.filter(is_active=True)

    category_slug   = request.GET.get('category', '').strip()
    active_category = None
    if category_slug:
        active_category = Category.objects.filter(slug=category_slug).first()
        if active_category:
            products = products.filter(category=active_category)

    brand_slug   = request.GET.get('brand', '').strip()
    active_brand = None
    if brand_slug:
        active_brand = Brand.objects.filter(slug=brand_slug).first()
        if active_brand:
            products = products.filter(brand=active_brand)

    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(name__icontains=query)

    return render(request, 'pages/product_list.html', {
        'products':        products,
        'categories':      categories,
        'brands':          brands,
        'active_category': active_category,
        'active_brand':    active_brand,
        'query':           query,
        'total':           products.count(),
    })


# views.py - Updated product_detail function

# views.py - Update the product_detail function

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    reviews = product.reviews.filter(is_approved=True)
    variants = product.variants.filter(is_active=True).select_related('size', 'color')
    images = product.images.all()
    related = Product.objects.filter(
        category=product.category, is_active=True, stock__gt=0
    ).exclude(pk=pk)[:4]

    delivery_settings = get_delivery_settings()
    
    # Initialize form with initial data if GET request
    if request.method == 'GET':
        order_form = EnhancedOrderForm(initial={
            'delivery_type': 'home',
            'quantity': 1,
        })
    else:
        order_form = EnhancedOrderForm(request.POST)
    
    review_form = ReviewForm()

    # Place Order
    if request.method == 'POST' and 'place_order' in request.POST:
        print("=" * 50)
        print("POST DATA RECEIVED:", request.POST)
        print("=" * 50)
        
        # Create a mutable copy of POST data to fix issues
        post_data = request.POST.copy()
        
        # Fix delivery_type if missing
        if 'delivery_type' not in post_data or not post_data['delivery_type']:
            post_data['delivery_type'] = 'home'
        
        # Fix province if it's the display name
        if 'province' in post_data and post_data['province']:
            province_mapping = {
                'Koshi Province': 'koshi',
                'Madhesh Province': 'madhesh',
                'Bagmati Province': 'bagmati',
                'Gandaki Province': 'gandaki',
                'Lumbini Province': 'lumbini',
                'Karnali Province': 'karnali',
                'Sudurpashchim Province': 'sudurpashchim',
            }
            province = post_data['province']
            if province in province_mapping:
                post_data['province'] = province_mapping[province]
        
        # Fix street address field name
        if 'street' in post_data and 'street_address' not in post_data:
            post_data['street_address'] = post_data['street']
        
        order_form = EnhancedOrderForm(post_data)
        
        if order_form.is_valid():
            print("Form is VALID")
            d = order_form.cleaned_data
            print("Cleaned data:", d)
            
            qty = d['quantity']
            delivery_type = d.get('delivery_type', 'home')
            
            # Calculate totals
            subtotal = product.price * qty
            shipping_fee = 0
            tax = 0
            discount = 0
            
            # Apply shipping fee based on delivery settings
            if delivery_settings and delivery_type == 'home':
                if subtotal < delivery_settings.standard_free_above:
                    shipping_fee = 100  # Add a default shipping fee if needed
            
            total = subtotal + shipping_fee + tax - discount
            
            try:
                # Create Order
                order = Order.objects.create(
                    guest_name=d['guest_name'],
                    guest_email=d.get('guest_email') or '',
                    guest_phone=d.get('guest_phone') or '',
                    note=d.get('note') or '',
                    subtotal=subtotal,
                    shipping_fee=shipping_fee,
                    tax=tax,
                    discount=discount,
                    total=total,
                    status='pending',
                )
                print(f"Order created: {order.order_number}")
                
                # Create OrderItem
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=qty,
                    unit_price=product.price,
                    total_price=product.price * qty,
                )
                print("OrderItem created")
                
                # Create ShippingDetail
                shipping_data = {
                    'order': order,
                    'delivery_type': delivery_type,
                    'full_name': d['guest_name'],
                    'phone': d.get('guest_phone') or '',
                    'email': d.get('guest_email') or '',
                    'country': 'Nepal',
                }
                
                if delivery_type == 'home':
                    shipping_data.update({
                        'city': d.get('city') or '',
                        'province': d.get('province') or '',
                        'street_address': d.get('street_address') or '',
                    })
                else:
                    shipping_data.update({
                        'city': '',
                        'province': '',
                        'street_address': '',
                    })
                
                ShippingDetail.objects.create(**shipping_data)
                print("ShippingDetail created")
                
                # Create Invoice
                from .models import Invoice
                Invoice.objects.create(
                    order=order,
                    is_paid=False
                )
                print("Invoice created")
                
                # Reduce stock
                product.stock -= qty
                product.save()
                
                if hasattr(product, 'inventory'):
                    inv = product.inventory
                    inv.quantity -= qty
                    inv.save()
                    if inv.is_low_stock():
                        LowStockAlert.objects.get_or_create(
                            inventory=inv,
                            is_resolved=False,
                            defaults={'message': f'{product.name} stock is low ({inv.quantity} left).'}
                        )
                
                messages.success(
                    request,
                    f'Order #{order.order_number} placed successfully! We will contact you soon.'
                )
                return redirect('order_success')
                
            except Exception as e:
                print(f"ERROR creating order: {str(e)}")
                messages.error(request, f'Error placing order: {str(e)}')
        else:
            # Form is invalid - show errors
            print("Form is INVALID")
            print("Form errors:", order_form.errors)
            messages.error(request, 'Please fix the errors in the form.')
    
    # Submit Review
    if request.method == 'POST' and 'submit_review' in request.POST:
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            rev = review_form.save(commit=False)
            rev.product = product
            rev.is_approved = False
            rev.save()
            messages.success(request, 'Review submitted! It will appear after approval.')
            return redirect('product_detail', pk=pk)

    return render(request, 'pages/product_detail.html', {
        'product': product,
        'order_form': order_form,
        'review_form': review_form,
        'reviews': reviews,
        'variants': variants,
        'images': images,
        'related_products': related,
        'delivery_settings': delivery_settings,
    })
# ── Order Success ─────────────────────────────────────────────
def order_success(request):
    return render(request, 'pages/order_success.html')


def esewa_signature(message: str) -> str:
    """Generate HMAC-SHA256 base64 signature for eSewa v2."""
    secret = settings.ESEWA_SECRET_KEY.encode('utf-8')
    sig = hmac.new(secret, message.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(sig).decode('utf-8')
 
 
# ─────────────────────────────────────────────────────────────
# MAIN INITIATE ENDPOINT  (POST /orders/initiate/)
# ─────────────────────────────────────────────────────────────
@require_POST
@csrf_protect
def initiate_payment(request):
    try:
        data       = json.loads(request.body)
        product_id = data.get('product_id')
        quantity   = int(data.get('quantity', 1))
        method     = data.get('payment_method', 'cod')
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid request data.'}, status=400)
 
    product = get_object_or_404(Product, pk=product_id)
 
    if product.stock < quantity:
        return JsonResponse({'success': False, 'error': 'Insufficient stock.'})
 
    amount = int(product.price * quantity)  # NPR, whole number
 
    # ── Create a pending Order ──────────────────────────────
    order = Order.objects.create(
        product        = product,
        quantity       = quantity,
        amount         = amount,
        payment_method = method,
        status         = 'pending',
        transaction_id = str(uuid.uuid4()).replace('-', '')[:20].upper(),
    )
 
    if method == 'esewa':
        return _esewa_response(order)
    elif method == 'khalti':
        return _khalti_response(order)
    elif method == 'cod':
        order.status = 'confirmed'
        order.save()
        return JsonResponse({'success': True, 'order_id': order.pk})
    else:
        return JsonResponse({'success': False, 'error': 'Unknown payment method.'})
 
 
# ─────────────────────────────────────────────────────────────
# eSewa  
# ─────────────────────────────────────────────────────────────
def _esewa_response(order):
    """Build params for eSewa v2 form POST."""
    base_url    = settings.ESEWA_BASE_URL
    return_url  = f"{settings.PAYMENT_RETURN_BASE}/orders/esewa/success/"
    failure_url = f"{settings.PAYMENT_RETURN_BASE}/orders/esewa/failure/"
 
    amount       = str(order.amount)
    tax_amount   = "0"
    total_amount = amount
    txn_uuid     = order.transaction_id
    product_code = settings.ESEWA_PRODUCT_CODE
 
    # Signature covers: total_amount,transaction_uuid,product_code
    message   = f"total_amount={total_amount},transaction_uuid={txn_uuid},product_code={product_code}"
    signature = esewa_signature(message)
 
    params = {
        "amount":           amount,
        "tax_amount":       tax_amount,
        "total_amount":     total_amount,
        "transaction_uuid": txn_uuid,
        "product_code":     product_code,
        "product_service_charge": "0",
        "product_delivery_charge": "0",
        "success_url":      return_url,
        "failure_url":      failure_url,
        "signed_field_names": "total_amount,transaction_uuid,product_code",
        "signature":        signature,
    }
 
    return JsonResponse({
        'success':       True,
        'esewa_url':     f"{base_url}/api/epay/main/v2/form",
        'esewa_params':  params,
    })
 
 
@require_POST
def esewa_success(request):
    """eSewa redirects here with ?data=<base64-encoded-json>"""
    encoded = request.GET.get('data', '')
    try:
        decoded = base64.b64decode(encoded).decode('utf-8')
        payload = json.loads(decoded)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Invalid eSewa response.'})
 
    # Verify signature
    status     = payload.get('status')
    txn_uuid   = payload.get('transaction_uuid')
    total_amt  = payload.get('total_amount')
    prod_code  = payload.get('product_code')
    recv_sig   = payload.get('signature')
 
    message  = f"transaction_uuid={txn_uuid},product_code={prod_code},total_amount={total_amt}"
    expected = esewa_signature(message)
 
    if status != 'COMPLETE' or recv_sig != expected:
        return JsonResponse({'success': False, 'error': 'Payment verification failed.'})
 
    # Mark order as paid
    try:
        order = Order.objects.get(transaction_id=txn_uuid)
        order.status = 'paid'
        order.save()
        # Deduct stock
        order.product.stock -= order.quantity
        order.product.save()
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found.'})
 
    # Redirect to order success page
    from django.shortcuts import redirect
    return redirect(f"/orders/success/{order.pk}/")
 
 
def esewa_failure(request):
    from django.shortcuts import redirect
    return redirect('/orders/failed/')
 
 
# ─────────────────────────────────────────────────────────────
# Khalti  
# ─────────────────────────────────────────────────────────────
def _khalti_response(order):
    """Initiate Khalti v2 payment — returns a payment URL."""
    headers = {
        'Authorization': f"Key {settings.KHALTI_SECRET_KEY}",
        'Content-Type':  'application/json',
    }
    payload = {
        "return_url":    f"{settings.PAYMENT_RETURN_BASE}/orders/khalti/verify/",
        "website_url":   settings.PAYMENT_RETURN_BASE,
        "amount":        order.amount * 100,  # Khalti uses paisa
        "purchase_order_id":   str(order.transaction_id),
        "purchase_order_name": f"Order #{order.pk}",
        "customer_info": {
            "name":  "Guest",
            "email": "guest@example.com",
            "phone": "9800000000",
        },
    }
 
    try:
        resp = requests.post(
            f"{settings.KHALTI_BASE_URL}/api/v2/epayment/initiate/",
            json=payload, headers=headers, timeout=15
        )
        resp_data = resp.json()
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Khalti initiation failed: {e}'})
 
    if resp.status_code == 200 and 'payment_url' in resp_data:
        # Save Khalti pidx for verification
        order.khalti_pidx = resp_data['pidx']
        order.save()
        return JsonResponse({
            'success':             True,
            'khalti_payment_url':  resp_data['payment_url'],
        })
    else:
        return JsonResponse({'success': False, 'error': resp_data.get('detail', 'Khalti error.')})
 
 
@require_POST
def khalti_verify(request):
    """Khalti redirects here with ?pidx=... after payment."""
    pidx = request.GET.get('pidx') or request.POST.get('pidx')
    if not pidx:
        return JsonResponse({'success': False, 'error': 'Missing pidx.'})
 
    headers = {
        'Authorization': f"Key {settings.KHALTI_SECRET_KEY}",
        'Content-Type':  'application/json',
    }
    resp = requests.post(
        f"{settings.KHALTI_BASE_URL}/api/v2/epayment/lookup/",
        json={"pidx": pidx}, headers=headers, timeout=15
    )
    data = resp.json()
 
    if data.get('status') == 'Completed':
        try:
            order = Order.objects.get(khalti_pidx=pidx)
            order.status = 'paid'
            order.save()
            order.product.stock -= order.quantity
            order.product.save()
        except Order.DoesNotExist:
            pass
        from django.shortcuts import redirect
        return redirect(f"/orders/success/{order.pk}/")
    else:
        from django.shortcuts import redirect
        return redirect('/orders/failed/')
 
 
# ─────────────────────────────────────────────────────────────
# Card Payment
# ─────────────────────────────────────────────────────────────
@require_POST
@csrf_protect
def card_payment(request):
    """
    IMPORTANT: In production, integrate a PCI-compliant gateway.
    Options for Nepal: NCHL ConnectIPS, NIC Asia Bank, Global IME, or Stripe.
    This view shows the integration pattern — replace the PROCESSOR_URL
    and payload structure with your actual gateway's API spec.
    """
    try:
        data      = json.loads(request.body)
        prod_id   = data['product_id']
        quantity  = int(data.get('quantity', 1))
        card_num  = data['card_number']
        expiry    = data['expiry']        # MM/YY
        cvv       = data['cvv']
        name      = data['cardholder_name']
    except (KeyError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid card data.'})
 
    product = get_object_or_404(Product, pk=prod_id)
    amount  = int(product.price * quantity)
 
    # Create order first
    order = Order.objects.create(
        product=product, quantity=quantity, amount=amount,
        payment_method='card', status='pending',
        transaction_id=str(uuid.uuid4()).replace('-','')[:20].upper(),
    )
 
    # ── Replace below with your actual card gateway API call ──
    # Example using a generic gateway (replace URL + payload per your provider):
    """
    exp_parts = expiry.split('/')
    gateway_resp = requests.post(
        'https://your-card-gateway.com/api/charge',
        json={
            'amount':          amount * 100,   # in paisa/cents
            'currency':        'NPR',
            'card_number':     card_num,
            'exp_month':       exp_parts[0],
            'exp_year':        '20' + exp_parts[1],
            'cvv':             cvv,
            'cardholder_name': name,
            'order_id':        order.transaction_id,
        },
        headers={'Authorization': f'Bearer {settings.CARD_GATEWAY_KEY}'},
        timeout=30
    )
    result = gateway_resp.json()
    if result.get('status') == 'success':
        order.status = 'paid'
        order.save()
        ...
    """
 
    # For demo, simulate success:
    order.status = 'paid'
    order.save()
    order.product.stock -= quantity
    order.product.save()
 
    return JsonResponse({'success': True, 'order_id': order.pk})
 
 
# ─────────────────────────────────────────────────────────────
# urls.py  — add to your orders/urls.py
# ─────────────────────────────────────────────────────────────
"""
from django.urls import path
from . import views
 
urlpatterns = [
    path('initiate/',          views.initiate_payment, name='initiate_payment'),
    path('card-payment/',      views.card_payment,     name='card_payment'),
    path('esewa/success/',     views.esewa_success,    name='esewa_success'),
    path('esewa/failure/',     views.esewa_failure,    name='esewa_failure'),
    path('khalti/verify/',     views.khalti_verify,    name='khalti_verify'),
]
"""
 
 
# ─────────────────────────────────────────────────────────────
# models.py  — add khalti_pidx field to your Order model
# ─────────────────────────────────────────────────────────────
"""
class Order(models.Model):
    PAYMENT_METHODS = [
        ('esewa',  'eSewa'),
        ('khalti', 'Khalti'),
        ('card',   'Card'),
        ('cod',    'Cash on Delivery'),
    ]
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('confirmed', 'Confirmed'),
        ('paid',      'Paid'),
        ('failed',    'Failed'),
    ]
    product        = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    quantity       = models.PositiveIntegerField(default=1)
    amount         = models.PositiveIntegerField()           # NPR
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=50, unique=True)
    khalti_pidx    = models.CharField(max_length=100, blank=True, null=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)
 
    def __str__(self):
        return f"Order #{self.pk} — {self.product.name} ({self.status})"
"""
 
 
 
 # ─────────────────────────────────────────────────────────────
# MAIN INITIATE ENDPOINT  (POST /orders/initiate/)
# ─────────────────────────────────────────────────────────────
@require_POST
@csrf_protect
def initiate_payment(request):
    try:
        data       = json.loads(request.body)
        product_id = data.get('product_id')
        quantity   = int(data.get('quantity', 1))
        method     = data.get('payment_method', 'cod')
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid request data.'}, status=400)

    product = get_object_or_404(Product, pk=product_id, is_active=True)

    if product.stock < quantity:
        return JsonResponse({'success': False, 'error': 'Insufficient stock.'})

    amount   = product.price * quantity
    txn_id   = str(uuid.uuid4()).replace('-', '')[:20].upper()

    # ── Create Order using your real model fields ──────────────
    order = Order.objects.create(
        guest_name   = 'Guest',
        guest_email  = '',
        guest_phone  = '',
        subtotal     = amount,
        shipping_fee = 0,
        tax          = 0,
        discount     = 0,
        total        = amount,
        status       = 'pending',
        note         = txn_id,   # store txn id in note for lookup later
    )

    # Create the order item
    OrderItem.objects.create(
        order       = order,
        product     = product,
        quantity    = quantity,
        unit_price  = product.price,
        total_price = amount,
    )

    if method == 'esewa':
        return _esewa_response(order, txn_id)
    elif method == 'khalti':
        return _khalti_response(order, txn_id)
    elif method == 'cod':
        order.status = 'confirmed'
        order.save()
        # Reduce stock
        product.stock -= quantity
        product.save()
        return JsonResponse({'success': True, 'order_id': order.pk})
    else:
        return JsonResponse({'success': False, 'error': 'Unknown payment method.'})


# ─────────────────────────────────────────────────────────────
# eSewa
# ─────────────────────────────────────────────────────────────
def _esewa_response(order, txn_id):
    """Build params for eSewa v2 form POST."""
    base_url    = settings.ESEWA_BASE_URL
    return_url  = f"{settings.PAYMENT_RETURN_BASE}/orders/esewa/success/"
    failure_url = f"{settings.PAYMENT_RETURN_BASE}/orders/esewa/failure/"

    total_amount = str(int(order.total))
    product_code = settings.ESEWA_PRODUCT_CODE

    message   = f"total_amount={total_amount},transaction_uuid={txn_id},product_code={product_code}"
    signature = esewa_signature(message)

    params = {
        "amount":                    total_amount,
        "tax_amount":                "0",
        "total_amount":              total_amount,
        "transaction_uuid":          txn_id,
        "product_code":              product_code,
        "product_service_charge":    "0",
        "product_delivery_charge":   "0",
        "success_url":               return_url,
        "failure_url":               failure_url,
        "signed_field_names":        "total_amount,transaction_uuid,product_code",
        "signature":                 signature,
    }

    return JsonResponse({
        'success':      True,
        'esewa_url':    f"{base_url}/api/epay/main/v2/form",
        'esewa_params': params,
    })


@require_POST
def esewa_success(request):
    """eSewa redirects here with ?data=<base64-encoded-json>"""
    encoded = request.GET.get('data', '')
    try:
        decoded = base64.b64decode(encoded).decode('utf-8')
        payload = json.loads(decoded)
    except Exception:
        return JsonResponse({'success': False, 'error': 'Invalid eSewa response.'})

    status    = payload.get('status')
    txn_uuid  = payload.get('transaction_uuid')
    total_amt = payload.get('total_amount')
    prod_code = payload.get('product_code')
    recv_sig  = payload.get('signature')

    message  = f"transaction_uuid={txn_uuid},product_code={prod_code},total_amount={total_amt}"
    expected = esewa_signature(message)

    if status != 'COMPLETE' or recv_sig != expected:
        return redirect('/orders/failed/')

    # Find order by txn_id stored in note field
    try:
        order = Order.objects.get(note=txn_uuid)
    except Order.DoesNotExist:
        return redirect('/orders/failed/')

    order.status = 'confirmed'
    order.save()

    # Reduce stock for all items
    for item in order.items.all():
        item.product.stock -= item.quantity
        item.product.save()

    return redirect('order_success')


def esewa_failure(request):
    return redirect('order_success')  # or a failure page if you have one


# ─────────────────────────────────────────────────────────────
# Khalti
# ─────────────────────────────────────────────────────────────
def _khalti_response(order, txn_id):
    """Initiate Khalti v2 payment."""
    headers = {
        'Authorization': f"Key {settings.KHALTI_SECRET_KEY}",
        'Content-Type':  'application/json',
    }
    payload = {
        "return_url":          f"{settings.PAYMENT_RETURN_BASE}/orders/khalti/verify/",
        "website_url":         settings.PAYMENT_RETURN_BASE,
        "amount":              int(order.total) * 100,   # paisa
        "purchase_order_id":   txn_id,
        "purchase_order_name": f"Order #{order.order_number}",
        "customer_info": {
            "name":  order.guest_name or "Guest",
            "email": order.guest_email or "guest@example.com",
            "phone": order.guest_phone or "9800000000",
        },
    }

    try:
        resp      = requests.post(
            f"{settings.KHALTI_BASE_URL}/api/v2/epayment/initiate/",
            json=payload, headers=headers, timeout=15
        )
        resp_data = resp.json()
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Khalti initiation failed: {e}'})

    if resp.status_code == 200 and 'payment_url' in resp_data:
        # Store khalti pidx in the order note (append after txn_id)
        order.note = f"{order.note}|khalti:{resp_data['pidx']}"
        order.save()
        return JsonResponse({
            'success':            True,
            'khalti_payment_url': resp_data['payment_url'],
        })
    else:
        return JsonResponse({'success': False, 'error': resp_data.get('detail', 'Khalti error.')})


@require_POST
def khalti_verify(request):
    """Khalti redirects here with ?pidx=... after payment."""
    pidx = request.GET.get('pidx') or request.POST.get('pidx')
    if not pidx:
        return JsonResponse({'success': False, 'error': 'Missing pidx.'})

    headers = {
        'Authorization': f"Key {settings.KHALTI_SECRET_KEY}",
        'Content-Type':  'application/json',
    }
    resp = requests.post(
        f"{settings.KHALTI_BASE_URL}/api/v2/epayment/lookup/",
        json={"pidx": pidx}, headers=headers, timeout=15
    )
    data = resp.json()

    if data.get('status') == 'Completed':
        # Find order by pidx stored in note
        try:
            order = Order.objects.get(note__contains=f"khalti:{pidx}")
        except Order.DoesNotExist:
            return redirect('order_success')

        order.status = 'confirmed'
        order.save()

        for item in order.items.all():
            item.product.stock -= item.quantity
            item.product.save()

        return redirect('order_success')
    else:
        return redirect('order_success')  # or a failure page


# ─────────────────────────────────────────────────────────────
# Card Payment
# ─────────────────────────────────────────────────────────────
@require_POST
@csrf_protect
def card_payment(request):
    try:
        data     = json.loads(request.body)
        prod_id  = data['product_id']
        quantity = int(data.get('quantity', 1))
        # card fields (pass to your real gateway in production)
        _card_num = data['card_number']
        _expiry   = data['expiry']
        _cvv      = data['cvv']
        _name     = data['cardholder_name']
    except (KeyError, ValueError):
        return JsonResponse({'success': False, 'error': 'Invalid card data.'})

    product = get_object_or_404(Product, pk=prod_id, is_active=True)

    if product.stock < quantity:
        return JsonResponse({'success': False, 'error': 'Insufficient stock.'})

    amount = product.price * quantity

    order = Order.objects.create(
        guest_name   = _name,
        guest_email  = '',
        guest_phone  = '',
        subtotal     = amount,
        shipping_fee = 0,
        tax          = 0,
        discount     = 0,
        total        = amount,
        status       = 'pending',
    )
    OrderItem.objects.create(
        order       = order,
        product     = product,
        quantity    = quantity,
        unit_price  = product.price,
        total_price = amount,
    )

    # ── Replace with your real card gateway call in production ──
    # For demo, simulate success:
    order.status = 'confirmed'
    order.save()
    product.stock -= quantity
    product.save()

    return JsonResponse({'success': True, 'order_id': order.pk})
 
 
 
 
def payments(request):
    """
    Payment page. Call with ?order=ORD-XXXXXXXX to pre-load
    a specific order, or without it to show the empty form.
    """
    order = None
    order_number = request.GET.get('order', '').strip()

    if order_number:
        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            messages.error(request, f'Order {order_number} not found.')

    payment_methods = PaymentMethod.objects.filter(is_active=True)

    return render(request, 'pages/payments.html', {
        'order':           order,
        'payment_methods': payment_methods,
        'subtotal':        order.subtotal        if order else None,
        'shipping_fee':    order.shipping_fee     if order else None,
        'tax':             order.tax              if order else None,
        'discount':        order.discount         if order else None,
        'total':           order.total            if order else None,
        'buyer_name':      order.buyer_name()     if order else '',
    })
 
 

# ── Contact ───────────────────────────────────────────────────
def contact(request):
    form = ContactForm()
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Message sent! We will get back to you soon.')
            return redirect('contact')
    return render(request, 'pages/contact.html', {'form': form})


# ── FAQ ───────────────────────────────────────────────────────
def faq(request):
    faqs = FAQ.objects.filter(is_active=True).order_by('order')
    return render(request, 'pages/faq.html', {'faqs': faqs})


# ── Static Page ───────────────────────────────────────────────
def static_page(request, slug):
    page = get_object_or_404(Page, slug=slug, is_active=True)
    return render(request, 'pages/static_page.html', {'page': page})


# ── Testimonials ──────────────────────────────────────────────
def testimonials(request):
    from .models import Testimonial
    from .forms import TestimonialForm

    testimonials_qs = Testimonial.objects.filter(is_active=True).order_by('-created_at')
    form = TestimonialForm()

    if request.method == 'POST':
        form = TestimonialForm(request.POST)
        if form.is_valid():
            t           = form.save(commit=False)
            t.is_active = True
            t.save()
            messages.success(request, 'Thank you! Your review is pending approval.')
            return redirect('testimonials')

    return render(request, 'pages/testimonials.html', {
        'testimonials': testimonials_qs,
        'form':         form,
    })
    
    