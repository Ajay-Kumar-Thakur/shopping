from django.urls import path
from . import views

urlpatterns = [
    path('',                    views.index,            name='index'),
    path('shop/',               views.product_list,     name='product_list'),
    path('product/<int:pk>/',   views.product_detail,   name='product_detail'),
    path('order/success/',      views.order_success,    name='order_success'),
    path('contact/',            views.contact,          name='contact'),
    path('faq/',                views.faq,              name='faq'),
    path('testimonials/',       views.testimonials,     name='testimonials'),
    path('payments/',           views.payments,         name='payments'),
    path('page/<slug:slug>/',   views.static_page,      name='static_page'),

    # Payment processing endpoints
    path('orders/initiate/',        views.initiate_payment, name='initiate_payment'),
    path('orders/card-payment/',    views.card_payment,     name='card_payment'),
    path('orders/esewa/success/',   views.esewa_success,    name='esewa_success'),
    path('orders/esewa/failure/',   views.esewa_failure,    name='esewa_failure'),
    path('orders/khalti/verify/',   views.khalti_verify,    name='khalti_verify'),
]