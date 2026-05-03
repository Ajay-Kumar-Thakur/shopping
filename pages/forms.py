"""
REPLACE your existing forms.py with this file.
Fix: city and street_address are required=False at field level.
     Cross-field validation in clean() handles the home-delivery requirement.
     This prevents Django from rejecting the form before clean() even runs.
"""
from django import forms
from .models import Order, Review, ContactMessage, Testimonial

PROVINCE_CHOICES = [
    ('', 'Select Province'),
    ('koshi',         'Koshi Province'),
    ('madhesh',       'Madhesh Province'),
    ('bagmati',       'Bagmati Province'),
    ('gandaki',       'Gandaki Province'),
    ('lumbini',       'Lumbini Province'),
    ('karnali',       'Karnali Province'),
    ('sudurpashchim', 'Sudurpashchim Province'),
]

INPUT = 'form-input'


# forms.py - Updated EnhancedOrderForm

class EnhancedOrderForm(forms.Form):
    DELIVERY_CHOICES = [
        ('home', 'Home Delivery'),
        ('pickup', 'Pickup'),
    ]
    
    delivery_type = forms.ChoiceField(
        choices=DELIVERY_CHOICES,
        initial='home',
        required=False,  # Change to False to prevent validation error
        widget=forms.HiddenInput(),
    )
    
    # Customer fields
    guest_name = forms.CharField(
        max_length=200,
        required=True,  # Explicitly required
        label='Full Name',
        widget=forms.TextInput(attrs={
            'placeholder': 'Your full name',
            'class': INPUT,
            'autocomplete': 'name',
        })
    )
    
    guest_phone = forms.CharField(
        max_length=20,
        required=True,
        label='Phone Number',
        widget=forms.TextInput(attrs={
            'placeholder': '98XXXXXXXX',
            'class': INPUT,
            'autocomplete': 'tel',
        })
    )
    
    guest_email = forms.EmailField(
        required=False,
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'placeholder': 'your@email.com',
            'class': INPUT,
            'autocomplete': 'email',
        })
    )
    
    # Address fields
    city = forms.CharField(
        max_length=100,
        required=False,
        label='City / District',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Kathmandu',
            'class': INPUT,
            'autocomplete': 'address-level2',
        })
    )
    
    province = forms.ChoiceField(
        choices=PROVINCE_CHOICES,
        required=False,
        label='Province',
        widget=forms.Select(attrs={
            'class': INPUT,
        })
    )
    
    street_address = forms.CharField(
        max_length=300,
        required=False,
        label='Street Address',
        widget=forms.TextInput(attrs={
            'placeholder': 'Tole, Ward No., Landmark',
            'class': INPUT,
            'autocomplete': 'street-address',
        })
    )
    
    # Order fields
    note = forms.CharField(
        required=False,
        label='Order Note (Optional)',
        widget=forms.Textarea(attrs={
            'placeholder': 'Any special instructions...',
            'class': INPUT,
            'rows': '3',
        })
    )
    
    quantity = forms.IntegerField(
        min_value=1,
        max_value=99,
        initial=1,
        required=True,
        label='Quantity',
        widget=forms.NumberInput(attrs={
            'placeholder': '1',
            'class': INPUT,
            'min': '1',
            'max': '99',
            'value': '1',
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Get delivery_type, default to 'home' if not provided
        delivery_type = cleaned_data.get('delivery_type')
        if not delivery_type:
            delivery_type = 'home'
            cleaned_data['delivery_type'] = 'home'
        
        # Fix province value - convert display value to stored value
        province = cleaned_data.get('province')
        if province:
            # Map display names to stored values
            province_mapping = {
                'Koshi Province': 'koshi',
                'Madhesh Province': 'madhesh',
                'Bagmati Province': 'bagmati',
                'Gandaki Province': 'gandaki',
                'Lumbini Province': 'lumbini',
                'Karnali Province': 'karnali',
                'Sudurpashchim Province': 'sudurpashchim',
            }
            # If province is the display name, convert it to the stored value
            if province in province_mapping:
                cleaned_data['province'] = province_mapping[province]
        
        # Validate for home delivery
        if delivery_type == 'home':
            city = cleaned_data.get('city', '').strip()
            street = cleaned_data.get('street_address', '').strip()
            
            if not city:
                self.add_error('city', 'City/District is required for home delivery.')
            
            if not street:
                self.add_error('street_address', 'Street address is required for home delivery.')
        
        return cleaned_data

# Legacy alias — keeps any existing references working
GuestOrderForm = EnhancedOrderForm


# ── Unchanged forms ───────────────────────────────────────────────────────────

class ReviewForm(forms.ModelForm):
    RATING_CHOICES = [(i, f'{i} Star{"s" if i > 1 else ""}') for i in range(1, 6)]
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'star-radio'})
    )

    class Meta:
        model  = Review
        fields = ['reviewer', 'email', 'rating', 'title', 'body']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'reviewer': 'Your name',
            'email':    'your@email.com',
            'title':    'Review title (optional)',
        }
        for name, field in self.fields.items():
            if name != 'rating':
                field.widget.attrs.update({
                    'placeholder': placeholders.get(name, ''),
                    'class': INPUT,
                })
        self.fields['body'].widget = forms.Textarea(attrs={
            'class': INPUT,
            'rows': '4',
            'placeholder': 'Share your experience...',
        })
        self.fields['title'].required = False


class ContactForm(forms.ModelForm):
    class Meta:
        model  = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'name':    'Your full name',
            'email':   'your@email.com',
            'phone':   '+977 98XXXXXXXX',
            'subject': 'How can we help?',
            'message': 'Your message...',
        }
        for name, field in self.fields.items():
            field.widget.attrs.update({
                'placeholder': placeholders.get(name, ''),
                'class': INPUT,
            })
        self.fields['message'].widget = forms.Textarea(attrs={
            'class': INPUT,
            'rows': '5',
            'placeholder': 'Your message...',
        })
        self.fields['phone'].required = False


class TestimonialForm(forms.ModelForm):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.HiddenInput(attrs={'id': 'id_rating'})
    )

    class Meta:
        model  = Testimonial
        fields = ['name', 'role', 'message', 'rating']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({
            'placeholder': 'Full name',
            'class': INPUT,
        })
        self.fields['role'].widget.attrs.update({
            'placeholder': 'e.g. Verified Buyer',
            'class': INPUT,
        })
        self.fields['message'].widget = forms.Textarea(attrs={
            'placeholder': 'Tell us what you loved...',
            'class': INPUT,
            'rows': '4',
        })
        self.fields['role'].required = False