from venv import logger
from django.shortcuts import *
from django.contrib.auth.hashers import *
from django.contrib.auth import authenticate,login,logout,get_user_model
from django.http import HttpResponse
from django.contrib import messages
from django.http import *
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import random,smtplib
from datetime import  timedelta,datetime
from django.utils.timezone import now
from django.utils import timezone
from django.db.models import *
from django.utils.dateparse import parse_datetime
from .models import *
from django.contrib.auth.hashers import make_password
from email.message import EmailMessage
from decouple import config
import re,json
from django.urls import reverse
import razorpay
from django.conf.urls import handler404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from num2words import num2words
from decimal import Decimal

User = get_user_model()




########### user login and signup ###############


@never_cache

def userlogin(request):
    if request.user.is_authenticated:
        return redirect('userhome')
    
    if request.POST:


        email = request.POST.get('usr')
        password = request.POST.get('password')


        if not email or not password:
            messages.error(request,"Email and Password are Required")

        user=authenticate(request,username=email,password=password)
        
        
        
        if user:
            if user.status == 'Blocked':
                messages.error(request,"Your account has been blocked. Please contact support.")
                return redirect('userlogin')
            
            login(request,user)
            return redirect('userhome')
        else:
            messages.error(request, "Invalid email or password!")


    return render(request,'user/login.html')




def signup(request):
    if request.POST:


        if request.POST:
            fname = request.POST.get('usr_fname', '').strip()
            lname = request.POST.get('usr_lname', '').strip()
            usrPhone = request.POST.get('usr_phone', '').strip()
            usrEmail = request.POST.get('usr_email', '').strip()
            usrPassword = request.POST.get('usr_password', '').strip()
            usrConfirmPassword = request.POST.get('usr_cpassword', '').strip()

            if not all([fname,lname,usrPhone,usrEmail,usrPassword,usrConfirmPassword]):
                messages.error(request,"all fileds are Required!")
                return render(request,'user/signup.html')
            
            if not fname.isalpha():
                messages.error(request,"First name must only contain alphabets.")
                return render(request,'user/signup.html')
            
            if not lname.isalpha():
                messages.error(request,"Last name must only contain alphabets.")
                return render(request,'user/signup.html')
            
            email_validate=r'^[\w\.-]+@[\w\.-]+\.\w+$'
            if not re.match(email_validate,usrEmail):
                messages.error(request,"Invalid Email format.")
                return render(request,'user/signup.html')

            if User.objects.filter(email=usrEmail).exists():
                messages.error(request, "User with this email already exists.")
                return render(request,'user/signup.html')
            
            phone_validate = r'^[1-9]\d{9}$'
            if not re.match(phone_validate, usrPhone):
                messages.error(request, "Invalid phone number. Must be 10 digits and cannot start with 0.")
                return render(request, 'user/signup.html')

            if usrPassword != usrConfirmPassword:
                messages.error(request,'Enter password correctly')
                return render(request,'user/signup.html')
            
            if len(usrPassword) < 8:
                messages.error(request, "Password must be at least 8 characters long.")
                return render(request, 'user/signup.html')
            
            if not re.search(r'[A-Za-z]', usrPassword):
                messages.error(request, "Password must contain at least one letter.")
                return render(request, 'user/signup.html')
            
            if not re.search(r'[0-9]', usrPassword):
                messages.error(request, "Password must contain at least one number.")
                return render(request, 'user/signup.html')
            
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', usrPassword):
                messages.error(request, "Password must contain at least one special character.")
                return render(request, 'user/signup.html')
            
            
            
            
            otp = ''.join(str(random.randint(0, 9)) for _ in range(4))
            request.session['reg_firstname'] = fname
            request.session['reg_lastname'] = lname
            request.session['reg_email'] = usrEmail
            request.session['reg_password'] = usrPassword
            request.session['reg_phone'] = usrPhone
            request.session['reg_otp'] = otp
            request.session['reg_otp_time']=str(now())

            # Send OTP
            server = smtplib.SMTP(
                config('EMAIL_HOST'),
                config('EMAIL_PORT', cast=int)
            )
            server.starttls()
            server.login(config('EMAIL_HOST_USER'), config('EMAIL_HOST_PASSWORD'))

            msg = EmailMessage()
            msg['Subject'] = 'Signup OTP Verification'
            msg['From'] = config('EMAIL_HOST_USER')
            msg['To'] = usrEmail  
            msg.set_content(f'Your OTP is: {otp}')

            server.send_message(msg)
            server.quit()

            
            return redirect('signup_otp')

        
    return render(request,'user/signup.html')


def signup_otp(request):

    if request.POST:

        action=request.POST.get('action')
        if action=='submit':
            entered_otp=request.POST.get('signup-otp')
            original_otp=request.session.get('reg_otp')
            otp_time=request.session.get('reg_otp_time')

            if not entered_otp:
                messages.error(request, 'OTP field is required.')
                return render(request, 'user/otp-signup.html')
            
            if not entered_otp.isdigit():
                messages.error(request, 'OTP must contain only numbers.')
                return render(request, 'user/otp-signup.html')
            
            if len(entered_otp) != 4:
                messages.error(request, 'OTP must be exactly 4 digits.')
                return render(request, 'user/otp-signup.html')

            otp_time_parsed = parse_datetime(otp_time)
            if not otp_time_parsed or now() > otp_time_parsed + timedelta(minutes=1):
                messages.error(request, 'OTP has expired. Please resend OTP.')
                return render(request, 'user/otp-signup.html', {'remaining_time': 0})

            if entered_otp==original_otp:
                uname = request.session.get('reg_firstname')
                ulastname = request.session.get('reg_lastname')
                uemail = request.session.get('reg_email')
                phone = request.session.get('reg_phone')
                upassword = request.session.get('reg_password')
                
                hashed_password = make_password(upassword)
                usr=User.objects.create(
                    username=uemail,
                    first_name=uname,
                    last_name=ulastname,
                    email=uemail,
                    password=hashed_password,
                    phone=phone
                )            
                usr.save()
                messages.error(request,'User Registered Successfully')
                return redirect('userlogin')
                
            else:
                messages.error(request,'Ivalid OTP. Please Try Again')
                return render(request, 'user/otp-signup.html')
            
        elif action == 'resend':
            otp = ''.join(str(random.randint(0, 9)) for _ in range(4))
            request.session['reg_otp'] = otp
            request.session['reg_otp_time'] = str(now())

            # Resend OTP via email
            server = smtplib.SMTP(
                config('EMAIL_HOST'),
                config('EMAIL_PORT', cast=int)
            )
            server.starttls()
            server.login(config('EMAIL_HOST_USER'), config('EMAIL_HOST_PASSWORD'))

            msg = EmailMessage()
            msg['Subject'] = 'New Signup OTP'
            msg['From'] = config('EMAIL_HOST_USER')
            msg['To'] = request.session.get('reg_email')
            msg.set_content(f'Your new OTP is: {otp}')

            server.send_message(msg)
            server.quit()

            messages.success(request, 'A new OTP has been sent to your email.')
            return redirect('signup_otp')
        
    otp_time = request.session.get('reg_otp_time')
    otp_time_parsed = parse_datetime(otp_time)
    if otp_time_parsed:
        elapsed = (now() - otp_time_parsed).seconds
        remaining_time = max(60 - elapsed, 0)
    else:
        remaining_time = 0


    return render(request,'user/otp-signup.html',{'remaining_time': remaining_time})

########### user login and signup ###############


#################Search##############


#################Search##############




########### user password and user new password ###############

def forgot_pass(request):
    return render(request,'user/forgot_password.html')

def reset_password(request):

    if request.POST:
        new_pass=request.POST['new_pass']
        confirm_pass=request.POST['confirm_pass']

        if not new_pass or not confirm_pass:
            messages.error(request,"Both fileds are required")
            return render(request,'user/new_password.html')
        
        if new_pass != confirm_pass:
            messages.error(request,"Password do not match.")
        
        if len(new_pass) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'user/new_password.html')
        if not re.search(r'[A-Za-z]', new_pass):
            messages.error(request, "Password must contain at least one letter.")
            return render(request, 'user/new_password.html')
        if not re.search(r'[0-9]', new_pass):
            messages.error(request, "Password must contain at least one number.")
            return render(request, 'user/new_password.html')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_pass):
            messages.error(request, "Password must contain at least one special character.")
            return render(request, 'user/new_password.html')

        if new_pass==confirm_pass:
            email = request.session.get('forgotpass_otpmail')
            user=User.objects.get(email=email)
            user.set_password(new_pass)
            user.save()
            return redirect('userlogin')

    return render(request,'user/new_password.html')



########### user password and user new password ###############
@never_cache
def userhome(request):

    new_launches = ProductVariant.objects.filter(
        product__product_category__status='Active'
    ).prefetch_related(
        'productimage_set',
        'wishlists'
    ).order_by(
        '-product__created_at'
    )[:4] 


    # Get best sellers base
    best_sellers = ProductVariant.objects.filter(
        product__product_category__status='Active'
    ).prefetch_related(
        'productimage_set',
        'wishlists'
    ).annotate(
        order_count=Count('orderitem')
    ).order_by(
        '-order_count'
    )[:4]

    
    user_wishlist = []
    if request.user.is_authenticated:
        user_wishlist = Wishlist.objects.filter(
            user=request.user
        ).values_list('product_variants', flat=True)

    context = {
        'new_launches': new_launches,
        'best_sellers': best_sellers,
        'user_wishlist': user_wishlist,
    }
    

    return render(request,'user/homepage.html',context)


def userlogout(request):
    logout(request)
    return redirect('userlogin')

def about(request):
    return render(request,'user/about.html')

@login_required
def user_changepass(request):
    
    if request.POST:
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user


        if not check_password(current_password,user.password):
            messages.error(request, 'Current password is incorrect')
            return render(request,'user/changepass.html')
        
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long')
            return render(request, 'user/changepass.html')
        
        if not re.search(r'[A-Z]', new_password):  
            messages.error(request, 'Password must contain at least one uppercase letter')
            return render(request, 'user/changepass.html')
        
        if not re.search(r'[a-z]', new_password):  
            messages.error(request, 'Password must contain at least one lowercase letter')
            return render(request, 'user/changepass.html')
        
        if not re.search(r'[0-9]', new_password):  
            messages.error(request, 'Password must contain at least one digit')
            return render(request, 'user/changepass.html')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):  # At least one special character
            messages.error(request, 'Password must contain at least one special character')
            return render(request, 'user/changepass.html')
        
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match')
            return render(request,'user/changepass.html')
        
        user.set_password(new_password)
        user.save()

        messages.success(request, 'Password changed successfully. Please login again.')
        return redirect('userlogin')
        

        

    return render(request,'user/changepass.html')



def userproducts(request):

    

    product_variants = ProductVariant.objects.filter(
        product__product_category__status='Active'
    ).prefetch_related('productimage_set','wishlists')


    search_query = request.GET.get('q','')

    if search_query:

        product_variants = product_variants.filter(
            product__name__icontains=search_query
        )
    else:
        product_variants = ProductVariant.objects.filter(
            product__product_category__status='Active'
        ).prefetch_related('productimage_set', 'wishlists')


    #soring

    selected_categories = request.GET.getlist('category')
    selected_brands = request.GET.getlist('brand')
    price_range = request.GET.get('price_range')
    sort = request.GET.get('sort')

    if selected_categories:
        product_variants = product_variants.filter(product__product_category__id__in=selected_categories)

    
    if selected_brands:
        product_variants = product_variants.filter(product__brand__id__in=selected_brands)


    if price_range:
        if price_range == '0-1000':
            product_variants = product_variants.filter(price__lte=1000)
        elif price_range == '1000-5000':
            product_variants = product_variants.filter(price__gt=1000, price__lte=5000)
        elif price_range == '5000-10000':
            product_variants = product_variants.filter(price__gt=5000, price__lte=10000)
        elif price_range == '10000+':
            product_variants = product_variants.filter(price__gt=10000)



    if sort:
        if sort == 'price_low':
            product_variants = product_variants.order_by('price')
        elif sort == 'price_high':
            product_variants = product_variants.order_by('-price')
        elif sort == 'newest':
            product_variants = product_variants.order_by('-product__created_at')
        elif sort == 'name_asc':
            product_variants = product_variants.order_by('product__name')
        elif sort == 'name_desc':
            product_variants = product_variants.order_by('-product__name')


    #sorting end


    user_wishlist = []
    if request.user.is_authenticated:
        user_wishlist = Wishlist.objects.filter(user=request.user).values_list('product_variants', flat=True)

    categories=ProductCategory.objects.filter(status='Active')

    brands=Brand.objects.all()

    context={
        'categories':categories,
        'brands':brands,
        'product_variants':product_variants,
        'user_wishlist': user_wishlist,

        'selected_categories': selected_categories,
        'selected_brands': selected_brands,
        'price_range': price_range,
        'sort': sort,
        'search_query': search_query,
    }

    return render(request,'user/products.html',context)

def userproductview(request, variant_id):
    product_variants = get_object_or_404(ProductVariant, id=variant_id)
    product_images = ProductImage.objects.filter(product_variant=product_variants)

    
    similar_products = ProductVariant.objects.filter(
        product__name__icontains=product_variants.product.name.split()[0] 
    ).exclude(id=variant_id)[:4]  

    

    related_variants = ProductVariant.objects.filter(product=product_variants.product)

    cart_quantity = 0
    if request.user.is_authenticated:
        cart_item = CartItem.objects.filter(
            cart__user=request.user,
            product_variant=product_variants
        ).first()
        if cart_item:
            cart_quantity = cart_item.quantity

    context = {
        'product_variants': product_variants,
        'product_images': product_images,
        'related_variants': related_variants,
        'similar_products': similar_products,  
        'cart_quantity': cart_quantity
    }

    return render(request, 'user/productview.html', context)

def userwishlist(request):

    if not request.user.is_authenticated: 
        return redirect('userlogin')
    
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    products =  wishlist.product_variants.all()
    
    for product in products:
        product.offer_price = product.get_offer_price()

    context = {
        'products': products
    }

    return render(request,'user/wishlist.html',context)


def toggle_wishlist(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'User not authenticated'}, status=403)

    if request.method == 'POST':
        data = json.loads(request.body)
        variant_id = data.get('variant_id')
        action = data.get('action')

        try:
            wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
            product_variant = ProductVariant.objects.get(id=variant_id)

            if action == 'add':
                wishlist.product_variants.add(product_variant)
                message = 'Added to wishlist'

            elif action == 'remove':
                wishlist.product_variants.remove(product_variant)
                message = 'Removed from wishlist'

            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)

            return JsonResponse({'status': 'success', 'message': message})

        except ProductVariant.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Product not found'}, status=404)

    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)







def usercart(request):

    

    cart,created=Cart.objects.get_or_create(user=request.user)
    cart_items=CartItem.objects.filter(cart=cart)

    for item in cart_items:
        
        offer_price = item.product_variant.get_offer_price()
        if offer_price:
            item.price = offer_price
        else:
            item.price = item.product_variant.price
        item.save()
    


        if item.product_variant.stock == 0:
            messages.warning(request, f"{item.product_variant.product.name} is out of stock")
        elif item.quantity > item.product_variant.stock:
            messages.warning(request, f"Only {item.product_variant.stock} units available for {item.product_variant.product.name}")

    total_price = sum(item.get_total_price() for item in cart_items)

    context={
        'cart_items':cart_items,
        'total_price':total_price,
    }


    return render(request,'user/cart.html',context)


def add_to_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Please login to add items to cart'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_variant_id = data.get('product_variant_id')
            quantity = int(data.get('quantity', 1))

            product_variant = get_object_or_404(ProductVariant, id=product_variant_id)
            
            if product_variant.stock == 0:
                return JsonResponse({'status': 'error', 'message': 'Product is out of stock'})

            cart = Cart.objects.get_or_create(user=request.user)[0]
            
            # Use get_or_create with defaults
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product_variant=product_variant,
                defaults={
                    'quantity': 0,
                    'price': product_variant.get_offer_price() or product_variant.price
                }
            )

            # Update quantity
            new_quantity = cart_item.quantity + quantity
            if new_quantity > 4:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Cannot add more than 4 items of this product'
                })
            
            if new_quantity < 1:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Quantity must be greater than 0'
                })

            cart_item.quantity = new_quantity
            cart_item.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Item added to cart successfully'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

    
def update_cart_item(request):
    if request.POST:
        item_id=request.POST.get('item_id')
        action=request.POST.get('action')


        cart_item=get_object_or_404(CartItem, id=item_id, cart__user=request.user)

        if action == 'increase':
            
            if cart_item.quantity + 1 > 4:
                messages.error(request, 'cant add more than 4 product')
                return JsonResponse({'status': 'error', 'message': 'You cannot add more than 4 of this product to the cart'}, status=400)
            cart_item.quantity += 1

        elif action == 'decrease' and cart_item.quantity > 1:
            cart_item.quantity -= 1

        

        offer_price = cart_item.product_variant.get_offer_price()

        if offer_price:
            cart_item.price = offer_price
        else:
            cart_item.price = cart_item.product_variant.price
        
        cart_item.save()

        item_total = cart_item.get_total_price()
        cart_items = CartItem.objects.filter(cart__user=request.user)
        cart_total = sum(item.get_total_price() for item in cart_items)

        return JsonResponse({
            'status': 'success',
            'quantity': cart_item.quantity,
            'item_total': item_total,
            'cart_total': cart_total,
        })
    return JsonResponse({
        'error':'Invalid request'
    },status=400)




    

def remove_cart_item(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')

        try:
            with transaction.atomic():
                
                cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
                cart_item.delete()

                
                remaining_cart_items = CartItem.objects.filter(cart__user=request.user)
                cart_total = sum(item.get_total_price() for item in remaining_cart_items)

                return JsonResponse({
                    'status': 'success',
                    'cart_total': cart_total,
                    'item_count': remaining_cart_items.count()
                })
                
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request'
    }, status=400)





@login_required
@never_cache
def myprofile(request):
    user = request.user
    default_address = Address.objects.filter(user=user, is_default=True).first()
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        city = request.POST.get('city', '').strip()

        
        if not first_name or not last_name:
            messages.error(request, 'First Name and Last Name cannot be empty.')
            return redirect('myprofile')
        
        if not re.match(r'^[A-Za-z ]+$', first_name) or not re.match(r'^[A-Za-z ]+$', last_name):
            messages.error(request, 'First Name and Last Name should only contain letters and spaces.')
            return redirect('myprofile')

        if city and not re.match(r'^[A-Za-z ]+$', city):
            messages.error(request, 'City should only contain letters and spaces.')
            return redirect('myprofile')

        try:
            
            user.first_name = first_name
            user.last_name = last_name
            user.save()

            
            if default_address:
                default_address.city = city
                default_address.save()
            elif city:
                Address.objects.create(
                    user=user,
                    city=city,
                    is_default=True
                )

            messages.success(request, 'Profile updated successfully!')
        except Exception as e:
            messages.error(request, 'An error occurred while updating your profile.')
            
        return redirect('myprofile')

    context = {
        'user': user,
        'default_address': default_address
    }
    return render(request, 'user/myprofile.html', context)


@login_required
def address(request):
    user = request.user
   
    addresses = Address.objects.filter(user=user, is_delete=False)
    default_address = addresses.filter(is_default=True).first()
    other_addresses = addresses.filter(is_default=False)

    context = {
        'default_address': default_address,
        'other_addresses': other_addresses,
        'user': user,
    }

    return render(request, 'user/address.html', context)

@login_required
def add_address(request):
    if request.method == 'POST':
        usr_address = request.POST.get('address','').strip()
        phone = request.POST.get('phone','').strip()
        city = request.POST.get('city','').strip()
        state = request.POST.get('state','').strip()
        pin_code = request.POST.get('pin_code','').strip()
        is_default = request.POST.get('is_default') == 'on'

        if not all([usr_address, phone, city, state, pin_code]):
            messages.error(request, 'All fields are required.')
            return redirect('add_address')

        if len(usr_address) < 10:
                messages.error(request, 'Address should be at least 10 characters long.')
                return redirect('add_address')

        
        if not phone.isdigit():
            messages.error(request, 'Phone number should contain only digits.')
            return redirect('add_address')
        
        if len(phone) != 10:
            messages.error(request, 'Phone number must be exactly 10 digits.')
            return redirect('add_address')
        
        if phone == "0" * 10 or all(digit == phone[0] for digit in phone):
            messages.error(request, 'Invalid phone number. Cannot use repeated digits or all zeros.')
            return redirect('add_address')
        
        if not city.replace(' ', '').isalpha():
            messages.error(request, 'City name should contain only letters.')
            return redirect('add_address')
        
        if len(city) < 3:
            messages.error(request, 'City name should be at least 3 characters long.')
            return redirect('add_address')
        
        if not state.replace(' ', '').isalpha():
            messages.error(request, 'State name should contain only letters.')
            return redirect('add_address')
        
        if len(state) < 3:
            messages.error(request, 'State name should be at least 3 characters long.')
            return redirect('add_address')
        
        if not pin_code.isdigit():
            messages.error(request, 'PIN code should contain only digits.')
            return redirect('add_address')
        
        if len(pin_code) != 6:
            messages.error(request, 'PIN code must be exactly 6 digits.')
            return redirect('add_address')
        
        if pin_code == "0" * 6 or all(digit == pin_code[0] for digit in pin_code):
            messages.error(request, 'Invalid PIN code. Cannot use repeated digits or all zeros.')
            return redirect('add_address')


        if is_default:
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)

        Address.objects.create(
            user=request.user,
            address=usr_address,
            phone=phone,
            city=city,
            state=state,
            pin_code=pin_code,
            is_default=is_default
        )
        messages.success(request, 'Address added successfully.')
        return redirect('address')

    return render(request, 'user/add_address.html')



   

def editaddress(request,address_id):

    user_address=get_object_or_404(Address,id=address_id,user=request.user)

    if request.POST:
        address_data=request.POST.get('edit_address')
        phone = request.POST.get('edit_phone')
        city = request.POST.get('edit_city')
        state = request.POST.get('edit_state')
        pin_code = request.POST.get('edit_pin_code')
        is_default = request.POST.get('edit_is_default') == 'on'



        if not all([address_data, phone, city, state, pin_code]):
            messages.error(request, 'All fields are required.')
            return redirect('add_address',id=address_id)

        if len(address_data) < 10:
                messages.error(request, 'Address should be at least 10 characters long.')
                return redirect('add_address')

        
        if not phone.isdigit():
            messages.error(request, 'Phone number should contain only digits.')
            return redirect('add_address')
        
        if len(phone) != 10:
            messages.error(request, 'Phone number must be exactly 10 digits.')
            return redirect('add_address')
        
        if phone == "0" * 10 or all(digit == phone[0] for digit in phone):
            messages.error(request, 'Invalid phone number. Cannot use repeated digits or all zeros.')
            return redirect('add_address')
        
        if not city.replace(' ', '').isalpha():
            messages.error(request, 'City name should contain only letters.')
            return redirect('add_address')
        
        if len(city) < 3:
            messages.error(request, 'City name should be at least 3 characters long.')
            return redirect('add_address')
        
        if not state.replace(' ', '').isalpha():
            messages.error(request, 'State name should contain only letters.')
            return redirect('add_address')
        
        if len(state) < 3:
            messages.error(request, 'State name should be at least 3 characters long.')
            return redirect('add_address')
        
        if not pin_code.isdigit():
            messages.error(request, 'PIN code should contain only digits.')
            return redirect('add_address')
        
        if len(pin_code) != 6:
            messages.error(request, 'PIN code must be exactly 6 digits.')
            return redirect('add_address')
        
        if pin_code == "0" * 6 or all(digit == pin_code[0] for digit in pin_code):
            messages.error(request, 'Invalid PIN code. Cannot use repeated digits or all zeros.')
            return redirect('add_address')

        
        
        if is_default:
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
        

        user_address.address = address_data
        user_address.phone = phone
        user_address.city = city
        user_address.state = state
        user_address.pin_code = pin_code
        user_address.is_default = is_default
        user_address.save()

        messages.success(request, 'Address updated successfully.')
        return redirect('address')
    context = {
        'user_address': user_address
        }

    return render(request,'user/edit_address.html',context)

@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == 'POST':
        address.soft_delete() 
        messages.success(request, "Address deleted successfully!")
        return redirect('address') 

    messages.error(request, "Invalid request.")
    return redirect('address')

@login_required
def set_default(request,address_id):
    user_address=get_object_or_404(Address,id=address_id,user=request.user)
    Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
    user_address.is_default=True
    user_address.save()
    messages.success(request,'Default address updated')
    return redirect('address')


def usercheckout(request):

    if not request.user.is_authenticated:
        return redirect('userlogin')

    cart = Cart.objects.get(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty. Please add items before checkout.")
        return redirect('usercart')
    
    out_of_stock_items = []
    for item in cart_items:
        if item.product_variant.stock == 0:
            out_of_stock_items.append(item.product_variant.product.name)

        elif item.quantity > item.product_variant.stock:
            out_of_stock_items.append(f"{item.product_variant.product.name} (Only {item.product_variant.stock} available)")


    if out_of_stock_items:
        messages.error(request, f"The following items are out of stock: {', '.join(out_of_stock_items)}")
        return redirect('usercart')


    total_price = sum(item.get_total_price() for item in cart_items)

    current_time = datetime.now()

    available_coupons = Coupon.objects.filter(
        is_active=True,
        valid_from__lte=current_time,
        valid_until__gte=current_time,
        min_purchase_amount__lte=total_price
    )
    
        
    addresses=Address.objects.filter(user=request.user)
    default_address=addresses.filter(is_default=True,is_delete=False).first()
    other_addresses = addresses.filter(is_default=False,is_delete=False)

    if request.method == 'POST':

        if 'apply_coupon' in request.POST:
            coupon_id = request.POST.get('coupon')

            if coupon_id:
                try:
                    coupon = Coupon.objects.get(id=coupon_id)

                    if coupon.discount_type == 'percentage':
                        discount = (coupon.discount_value / 100) * total_price
                    else:
                        discount = coupon.discount_value

                    if discount > total_price:
                        messages.error(request, 'Coupon discount amount exceeds the total price!')
                        return redirect('usercheckout')
                    
                    if total_price < coupon.min_purchase_amount:
                        messages.error(request, f'Minimum purchase amount of ₹{coupon.min_purchase_amount} required for this coupon!')
                        return redirect('usercheckout')


                    cart.coupon = coupon
                    cart.discount = discount
                    cart.save()
                    messages.success(request, 'Coupon applied successfully!')

                except Coupon.DoesNotExist:
                    messages.error(request, 'Invalid coupon')
            else:
                messages.error(request, 'Please select a valid coupon.')
            return redirect('usercheckout')


        elif 'remove_coupon' in request.POST: 
            cart.coupon = None
            cart.discount = 0
            cart.save()
            messages.success(request, 'Coupon removed successfully!')
            return redirect('usercheckout')
        

        elif 'place_order' in request.POST: 
            address_id = request.POST.get('address_id')
            if not address_id:
                return JsonResponse({'status': 'error', 'message': 'No address selected'})

            request.session['selected_address_id'] = address_id  
            return JsonResponse({'status': 'success', 'redirect_url': reverse('payment')})
        
    
    subtotal = total_price - cart.discount  

    context={

        'subtotal': subtotal,
        'cart_items': cart_items,
        'total_price': total_price,
        'default_address': default_address,
        'other_addresses': other_addresses,
        'applied_coupon': cart.coupon,
        'available_coupons': available_coupons
    }

    return render(request,'user/checkout.html',context)


@login_required
def checkout_address(request):
    if request.method == 'POST':
        address = request.POST.get('address','').strip()
        phone = request.POST.get('phone','').strip()
        city = request.POST.get('city','').strip()
        state = request.POST.get('state','').strip()
        pin_code = request.POST.get('pin_code','').strip()
        is_default = request.POST.get('is_default') == 'on'

        if not all([address, phone, city, state, pin_code]):
            messages.error(request, 'All fields are required.')
            return redirect('add_address')

        if len(address) < 10:
                messages.error(request, 'Address should be at least 10 characters long.')
                return redirect('add_address')

        
        if not phone.isdigit():
            messages.error(request, 'Phone number should contain only digits.')
            return redirect('add_address')
        
        if len(phone) != 10:
            messages.error(request, 'Phone number must be exactly 10 digits.')
            return redirect('add_address')
        
        if phone == "0" * 10 or all(digit == phone[0] for digit in phone):
            messages.error(request, 'Invalid phone number. Cannot use repeated digits or all zeros.')
            return redirect('add_address')
        
        if not city.replace(' ', '').isalpha():
            messages.error(request, 'City name should contain only letters.')
            return redirect('add_address')
        
        if len(city) < 3:
            messages.error(request, 'City name should be at least 3 characters long.')
            return redirect('add_address')
        
        if not state.replace(' ', '').isalpha():
            messages.error(request, 'State name should contain only letters.')
            return redirect('add_address')
        
        if len(state) < 3:
            messages.error(request, 'State name should be at least 3 characters long.')
            return redirect('add_address')
        
        if not pin_code.isdigit():
            messages.error(request, 'PIN code should contain only digits.')
            return redirect('add_address')
        
        if len(pin_code) != 6:
            messages.error(request, 'PIN code must be exactly 6 digits.')
            return redirect('add_address')
        
        if pin_code == "0" * 6 or all(digit == pin_code[0] for digit in pin_code):
            messages.error(request, 'Invalid PIN code. Cannot use repeated digits or all zeros.')
            return redirect('add_address')


        if is_default:
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)

        Address.objects.create(
            user=request.user,
            address=address,
            phone=phone,
            city=city,
            state=state,
            pin_code=pin_code,
            is_default=is_default
        )
        messages.success(request, 'Address added successfully.')
        return redirect('usercheckout')

    return render(request, 'user/checkout_address.html')

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
# Razorpay Callback View


@csrf_exempt
def razorpay_callback(request):
    if request.method == "POST":
        try:
            payment_id = request.POST.get('razorpay_payment_id')
            order_id = request.POST.get('razorpay_order_id')
            signature = request.POST.get('razorpay_signature')

            
            order = Order.objects.select_related('user').get(razorpay_order_id=order_id)
            
           
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            try:
                razorpay_client.utility.verify_payment_signature(params_dict)
                
                with transaction.atomic():
                    
                    order.razorpay_payment_id = payment_id
                    order.razorpay_signature = signature
                    order.status = 'processing'
                    order.is_paid = True
                    order.save()

                    
                    cart = Cart.objects.get(user=order.user)
                    cart_items = CartItem.objects.filter(cart=cart)
                    
                   
                    for item in cart_items:
                        variant = item.product_variant
                        variant.stock -= item.quantity
                        variant.save()
                        
                        
                        OrderItem.objects.create(
                            order=order,
                            product_variant=variant,
                            quantity=item.quantity,
                            price=item.product_variant.get_offer_price() if item.product_variant.get_offer_price() else item.product_variant.price
                        )
                    
                    cart_items.delete()
                    cart.coupon = None
                    cart.discount = 0
                    cart.save()

               
                if not request.user.is_authenticated:
                    from django.contrib.auth import login
                    from django.contrib.auth import get_user_model
                    User = get_user_model()
                    login(request, order.user, backend='django.contrib.auth.backends.ModelBackend')
                    request.session.save()

                
                request.session['last_order_id'] = order.id

                messages.success(request, 'Payment successful!')
                return redirect('order_success')

            except razorpay.errors.SignatureVerificationError:
                order.status = 'payment_failed'
                order.save()
                messages.error(request, 'Payment verification failed. Please try again.')
                return redirect('orderview', order_id=order.id)

            except Exception as e:
                order.status = 'payment_failed'
                order.save()
                messages.error(request, f'Payment verification error: {str(e)}')
                return redirect('orderview', order_id=order.id)

        except Order.DoesNotExist:
            messages.error(request, 'Order not found')
            return redirect('userhome')
        except Exception as e:
            messages.error(request, f'Payment processing error: {str(e)}')
            return redirect('userhome')

    return redirect('userhome')

@csrf_exempt
def retry_payment(request, order_id):
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        
        if order.is_paid:
            messages.error(request, 'This order has already been paid.')
            return redirect('orderview', order_id=order.id)

        
        amount_in_paise = int(float(order.total_price) * 100)

        
        razorpay_order = razorpay_client.order.create({
            'amount': amount_in_paise,
            'currency': 'INR',
            'payment_capture': '1'
        })

        
        order.razorpay_order_id = razorpay_order['id']
        order.status = 'payment_pending'
        order.save()

        
        payment_data = {
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
            'razorpay_amount': amount_in_paise,
            'currency': 'INR',
            'callback_url': request.build_absolute_uri(reverse('razorpay_callback')),
            'customer_name': request.user.get_full_name() or request.user.username,
            'customer_email': request.user.email,
            'customer_phone': request.user.phone,
            'order_id': order.id,
           
        }

        context = {
        'order': order,
        'payment_data': payment_data,
    }

        

        return render(request, 'user/retry_payment.html',context)

    except Exception as e:
        messages.error(request, f'Error initiating payment: {str(e)}')
        return redirect('orderview', order_id=order_id)


User = get_user_model()
def payment(request):
    if not request.user.is_authenticated:
        return redirect('userlogin')

    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        
        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('usercart')

        wallet, created = Wallet.objects.get_or_create(user=request.user, defaults={'balance': 0})

        
        out_of_stock_items = []
        for item in cart_items:
            if item.product_variant.stock == 0:
                out_of_stock_items.append(item.product_variant.product.name)
            elif item.quantity > item.product_variant.stock:
                out_of_stock_items.append(f"{item.product_variant.product.name} (Only {item.product_variant.stock} available)")

        if out_of_stock_items:
            messages.error(request, f"The following items are out of stock: {', '.join(out_of_stock_items)}")
            return redirect('usercart')

        total_price = sum(item.get_total_price() for item in cart_items)
        subtotal = total_price - cart.discount

        selected_address_id = request.session.get('selected_address_id')
        if not selected_address_id:
            messages.error(request, 'Please select a delivery address.')
            return redirect('usercheckout')

        try:
            selected_address = Address.objects.get(id=selected_address_id, user=request.user)
        except Address.DoesNotExist:
            messages.error(request, 'Invalid address selected.')
            return redirect('usercheckout')

        if request.method == 'POST':
            payment_method = request.POST.get('payment_method')
            
            if not payment_method:
                messages.error(request, 'Please select a payment method')
                return redirect('payment')

            if payment_method == 'cod':
                if subtotal > 1000:
                    messages.error(request, 'Cash on Delivery is available only for orders up to ₹1000')
                    return redirect('payment')
                
                payment_method_obj, _ = PaymentMethod.objects.get_or_create(name='cod')
                order = Order.objects.create(
                    user=request.user,
                    total_price=subtotal,
                    status='pending',
                    address=selected_address,
                    payment_method=payment_method_obj,
                    discount=cart.discount
                )
                
                
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product_variant=item.product_variant,
                        quantity=item.quantity,
                        price=item.product_variant.get_offer_price() if item.product_variant.get_offer_price() else item.product_variant.price
                    )
                    
                    item.product_variant.stock -= item.quantity
                    item.product_variant.save()
                
                
                cart_items.delete()
                cart.coupon = None
                cart.discount = 0
                cart.save()
                
                request.session['last_order_id'] = order.id
                return render(request, 'user/order_success.html', {'order': order})

            elif payment_method == 'wallet':
                if wallet.balance < subtotal:
                    messages.error(request, 'Insufficient wallet balance')
                    return redirect('payment')
                
                try:
                    with transaction.atomic():  # Add transaction management
                        # Create order first
                        payment_method_obj, _ = PaymentMethod.objects.get_or_create(name='wallet')
                        order = Order.objects.create(
                            user=request.user,
                            total_price=subtotal,
                            status='processing',
                            address=selected_address,
                            payment_method=payment_method_obj,
                            discount=cart.discount
                        )
                        
                        # Process order items and update stock
                        for item in cart_items:
                            OrderItem.objects.create(
                                order=order,
                                product_variant=item.product_variant,
                                quantity=item.quantity,
                                price=item.product_variant.get_offer_price() if item.product_variant.get_offer_price() else item.product_variant.price
                            )
                            item.product_variant.stock -= item.quantity
                            item.product_variant.save()
                        
                        # Update wallet balance
                        wallet.balance -= subtotal
                        wallet.save()
                        
                        # Create wallet transaction
                        WalletTransaction.objects.create(
                            wallet=wallet,
                            type='debit',
                            amount=subtotal,
                            order=order
                        )
                        
                        # Clear cart
                        cart_items.delete()
                        cart.coupon = None
                        cart.discount = 0
                        cart.save()
                        
                        # Store order ID in session
                        request.session['last_order_id'] = order.id
                        
                        # Redirect to success page with order details
                        return render(request, 'user/order_success.html', {'order': order})

                except Exception as e:
                    messages.error(request, f'Error processing payment: {str(e)}')
                    return redirect('payment')

            elif payment_method == 'razorpay':
                # Create Razorpay order
                razorpay_order = razorpay_client.order.create({
                    'amount': int(subtotal * 100),
                    'currency': 'INR',
                })
                
                # Create order in database
                payment_method_obj, _ = PaymentMethod.objects.get_or_create(name='razorpay')
                order = Order.objects.create(
                    user=request.user,
                    total_price=subtotal,
                    status='pending',
                    address=selected_address,
                    payment_method=payment_method_obj,
                    discount=cart.discount,
                    razorpay_order_id=razorpay_order['id']
                )
                
                context = {
                    'razorpay_order_id': razorpay_order['id'],
                    'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
                    'razorpay_amount': int(subtotal * 100),
                    'currency': 'INR',
                    'callback_url': request.build_absolute_uri(reverse('razorpay_callback')),
                    'order': order,
                }
                
                return render(request, 'user/razorpay.html', context)

        # GET request - show payment page
        context = {
            'cart_items': cart_items,
            'total_price': total_price,
            'subtotal': subtotal,
            'discount': cart.discount,
            'wallet_balance': wallet.balance
        }
        
        return render(request, 'user/payment.html', context)

    except Cart.DoesNotExist:
        messages.error(request, "Cart not found.")
        return redirect('usercart')




def order_success(request):
    try:
        order_id = request.session.get('last_order_id')
        if not order_id:
            messages.error(request, 'No order found.')
            return redirect('userhome')

        order = Order.objects.get(id=order_id, user=request.user)
        
        # Ensure user stays logged in
        request.session.modified = True
        
        context = {
            'order': order,
            'user': request.user
        }
        
        return render(request, 'user/order_success.html', context)
    
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('userhome')



def myorder(request):
    try:
        status_filter = request.GET.get('status')

        if not status_filter or status_filter == 'All':
            # Keep existing order-based display for 'All'
            orders = (
                Order.objects.filter(user=request.user)
                .prefetch_related('items__product_variant__product',
                               'items__product_variant__productimage_set')
                .order_by('-created_at')
            )
        else:
            # For specific status, get individual order items
            order_items = OrderItem.objects.filter(
                order__user=request.user,
                status=status_filter
            ).select_related(
                'order',
                'product_variant__product'
            ).prefetch_related(
                'product_variant__productimage_set'
            ).order_by('-order__created_at')

        context = {
            'orders': orders if not status_filter or status_filter == 'All' else None,
            'order_items': order_items if status_filter and status_filter != 'All' else None,
            'current_status': status_filter or 'All',
            'user': request.user
        }

        return render(request, 'user/order.html', context)
    except Exception as e:
        messages.error(request, f'Error retrieving orders: {str(e)}')
        return redirect('userhome')

def generate_invoice(request, order_id):
    
    order = get_object_or_404(Order.objects.prefetch_related(
        'items__product_variant__product',
        'items__product_variant__productimage_set'
    ).select_related('user', 'address'), id=order_id, user=request.user)
    
    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()
    
   
    p = canvas.Canvas(buffer, pagesize=A4)
    
    
    y = 800  
    
    
    p.setFont("Helvetica-Bold", 24)
    p.drawString(50, y, "PODCRAZE")
    
    
    p.setFont("Helvetica-Bold", 16)
    y -= 30
    p.drawString(50, y, f"Invoice #{order.id}")
    
    
    p.setFont("Helvetica", 12)
    y -= 20
    p.drawString(50, y, f"Date: {order.created_at.strftime('%d/%m/%Y')}")
    
    
    y -= 40
    p.drawString(50, y, "Bill To:")
    y -= 20
    p.drawString(50, y, f"Name: {order.user.first_name} {order.user.last_name}")
    y -= 20
    p.drawString(50, y, f"Email: {order.user.email}")
    
   
    if order.address:
        y -= 20
        p.drawString(50, y, "Shipping Address:")
        y -= 20
        p.drawString(50, y, f"{order.address.address}")
        y -= 20
        p.drawString(50, y, f"{order.address.city}, {order.address.state}")
        y -= 20
        p.drawString(50, y, f"PIN: {order.address.pin_code}")
        y -= 20
        p.drawString(50, y, f"Phone: {order.address.phone}")
    
    
    data = [['Product', 'Quantity', 'Price', 'Total']]
    
    # Calculate totals
    subtotal = 0
    
    # Add order items to table
    for item in order.items.all():
        item_total = item.quantity * item.price
        subtotal += item_total
        
        data.append([
            item.product_variant.product.name,
            str(item.quantity),
            f"Rs {item.price}",
            f"Rs {item_total}"
        ])
    
    # Draw table
    table = Table(data, colWidths=[200, 100, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),  
    ]))
    
    
    y -= 40
    table.wrapOn(p, 400, 200)
    table.drawOn(p, 50, y - 100)
    
   
    y -= 150 
    p.drawString(350, y, f"Subtotal: Rs {subtotal}")
    y -= 20
    if order.discount:
        p.drawString(350, y, f"Discount: Rs {order.discount}")
        y -= 20
    p.setFont("Helvetica-Bold", 14)
    p.drawString(350, y, f"Total Amount: Rs {order.total_price}")
    
    # Add footer
    p.setFont("Helvetica", 10)
    y = 50  # Set to bottom of page
    p.drawString(50, y, "Thank you for shopping with PODCRAZE!")
    y -= 20
   
    
    # Close the PDF object cleanly
    p.showPage()
    p.save()
    
    # Get the value of the BytesIO buffer and write it to the response
    buffer.seek(0)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'
    response.write(buffer.getvalue())
    buffer.close()
    
    return response



def orderview(request,order_id):

    if not request.user.is_authenticated:
        return redirect('userlogin')

    order = get_object_or_404(
        Order.objects.prefetch_related(
            'items__product_variant__product',
            'items__product_variant__productimage_set'
        ),
        id=order_id,
        user=request.user
    )

    status_updates = [
        {'status':'Order Placed','date':order.created_at},
        
    ]

    if order.status in ['processing','shipped','delivered','cancelled']:

        if order.status in ['shipped', 'delivered']:
            status_updates.append({'status': 'Shipped', 'date': order.created_at + timedelta(days=2)})

        if order.status == 'delivered':
            status_updates.append({'status': 'Delivered', 'date': now()})

        if order.status == 'cancelled':
            status_updates.append({'status': 'Cancelled', 'date': now()})


    possible_statuses = {
        'processing': ['processing', 'shipped', 'delivered'],
        'shipped': ['shipped', 'delivered'],
        'delivered': ['delivered'],
        'cancelled': ['cancelled']
    }


    order.subtotal = order.total_price + order.discount


    context = {
        'order': order,
        'status_updates': status_updates,
        'possible_statuses': possible_statuses

    }

    return render(request,'user/orderview.html',context)


def cancel_order(request,order_id):

    if not request.user.is_authenticated:
        return redirect('userlogin')

    if request.POST:

        cancellation_reason = request.POST.get('cancellation_reason','')
        order = get_object_or_404(Order, id=order_id, user=request.user)

        if order.status in ['pending','processing','shipped','delivered']:
            order.status = 'cancelled'
            order.cancellation_reason =cancellation_reason
            order.save()

            for item in order.items.all():  
                product_variant = item.product_variant 
                product_variant.stock += item.quantity 
                product_variant.save()



            # Handle paymentof return products amount to wallet

            if order.payment_method.name == 'wallet':  
                wallet = Wallet.objects.get(user=request.user)

                wallet.balance += order.total_price
                wallet.save()

                # Create transaction record
                WalletTransaction.objects.create(
                    wallet=wallet,
                    type='credit',
                    amount=order.total_price,
                    order=order
                )
                messages.success(request, 'Order cancelled and amount refunded to wallet successfully.')
            
            elif order.payment_method.name == 'razorpay':  
                try:
                    # Process Razorpay refund
                    razorpay_client.payment.refund(order.razorpay_payment_id, {
                        'amount': int(order.total_price * 100)
                    })

                    # Credit to wallet after refund
                    wallet, created = Wallet.objects.get_or_create(
                        user=request.user,
                        defaults={'balance': 0}
                    )
                    wallet.balance += order.total_price
                    wallet.save()

                    WalletTransaction.objects.create(
                        wallet=wallet,
                        type='credit',
                        amount=order.total_price,
                        order=order
                    )
                    messages.success(request, 'Order cancelled and amount refunded to wallet successfully.')
                except Exception as e:
                    messages.error(request, f"Failed to process refund: {str(e)}")
            else:
                messages.success(request, 'Order cancelled successfully.')

        else:
            messages.error(request, "This order cannot be cancelled.")

    return redirect('myorder')





def order_return(request, order_id):

    if not request.user.is_authenticated:
        return redirect('userlogin')

    order = get_object_or_404(Order, id=order_id,user=request.user)

    if request.POST:
        reason = request.POST.get('return_reason', '').strip()

        if reason and order.status == 'delivered':
            order.return_reason = reason
            order.status = 'return_pending'
            order.save()
            messages.success(request, 'Return request submitted successfully')
        else:
            if not reason:
                messages.error(request, 'Please provide a valid return reason.')
            else:
                messages.error(request, 'Only delivered orders can be returned.')
        
        return redirect('myorder')
    
    messages.error(request, 'Invalid request.')
    return redirect('myorder')



def wallet(request):

    if not request.user.is_authenticated:
        return redirect('userlogin')

    wallet,created = Wallet.objects.get_or_create(
        user = request.user,
        defaults={'balance':0}
    )

    #get all transaction

    transactions = WalletTransaction.objects.filter(
        wallet = wallet
    ).order_by('-date')

    context = {

        'wallet':wallet,
        'transactions':transactions
    }

    return render(request,'user/wallet.html',context)

def coupon(request):

    if not request.user.is_authenticated:
        return redirect('userlogin')
    
    active_coupons = Coupon.objects.filter(
        is_active=True,
        
    ).order_by('-valid_from')

    context = {
        'coupons': active_coupons
    }

    return render(request, 'user/coupon.html', context)

from django.utils import timezone  # Ensure this import is present

def cancel_order_item(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)

    if request.method == 'POST':
        cancellation_reason = request.POST.get('cancellation_reason', '').strip()

        if cancellation_reason:
            if order_item.status in ['pending', 'processing', 'shipped']:
                order_item.status = 'cancelled'
                order_item.cancellation_reason = cancellation_reason
                order_item.cancelled_at = timezone.now()
                order_item.save()

                # Update product variant stock
                product_variant = order_item.product_variant
                product_variant.stock += order_item.quantity
                product_variant.save()

                # Calculate refund amount
                refund_amount = order_item.quantity * order_item.price

                # Handle refund through wallet
                try:
                    wallet, created = Wallet.objects.get_or_create(
                        user=request.user,
                        defaults={'balance': Decimal('0')}
                    )
                    
                    # Update wallet balance
                    wallet.balance += refund_amount
                    wallet.save()

                    # Create wallet transaction
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        type='credit',
                        amount=refund_amount,
                        product=order_item.product_variant.product,
                        order=order_item.order
                    )

                    messages.success(
                        request, 
                        f'Item cancelled successfully. Rs {refund_amount:.2f} refunded to wallet.'
                    )
                except Exception as e:
                    messages.error(
                        request, 
                        f'Item cancelled but refund failed. Please contact support. Error: {str(e)}'
                    )
            else:
                messages.error(request, 'This item cannot be cancelled.')
        else:
            messages.error(request, 'Please provide a cancellation reason.')

    return redirect('orderview', order_id=order_item.order.id)

def return_order_item(request, item_id):
    if not request.user.is_authenticated:
        return redirect('userlogin')

    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user)
    
    if request.method == 'POST':
        if order_item.status == 'delivered':
            return_reason = request.POST.get('return_reason', '').strip()
            if return_reason:
                order_item.status = 'return_pending'
                order_item.return_reason = return_reason
                order_item.save()
                messages.success(request, 'Return request submitted successfully.')
            else:
                messages.error(request, 'Please provide a return reason.')
        else:
            messages.error(request, 'Only delivered items can be returned.')
    
    return redirect('orderview', order_id=order_item.order.id)







