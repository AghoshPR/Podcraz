
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
from datetime import datetime
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
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from num2words import num2words

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

    # Get wishlist items if user is authenticated
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
   
   
    product_variants=get_object_or_404(ProductVariant,id=variant_id)
    product_images=ProductImage.objects.filter(product_variant=product_variants)

    related_variants=ProductVariant.objects.filter(product=product_variants.product)
    
    cart_quantity = 0
    if request.user.is_authenticated:
        cart_item = CartItem.objects.filter(
            cart__user=request.user,
            product_variant=product_variants
        ).first()
        if cart_item:
            cart_quantity = cart_item.quantity


    context={
        
        'product_variants':product_variants,
        'product_images':product_images,
        'related_variants':related_variants,
        'cart_quantity': cart_quantity
    }
    
    return render(request,'user/productview.html',context)

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
        # Get offer price if available
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

            data=json.loads(request.body)
            product_variant_id=data.get('product_variant_id')
            quantity=int(data.get('quantity',1))


            product_variant=ProductVariant.objects.get(id=product_variant_id)

            if product_variant.stock == 0:
                return JsonResponse({'status': 'error', 'message': 'Product is out of stock'})

            cart,created=Cart.objects.get_or_create(user=request.user)

            cart_item, item_created=CartItem.objects.get_or_create(
                cart=cart,
                product_variant=product_variant,
                defaults={
                    'price':product_variant.price,
                    'quantity':quantity
                }
            )

            if not item_created:
               
                if cart_item.quantity + quantity > 4:
                    return JsonResponse({'status': 'error', 'message': 'You cannot add more than 4 of this product to the cart'}, status=400)
                
                cart_item.quantity += quantity
                cart_item.save()

            return JsonResponse({'status': 'success', 'message': 'Item added to cart successfully'})
        
        except ProductVariant.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid product'})
        
    return JsonResponse({'status': 'error', 'message': 'Unauthorized or bad request'})

    
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

        if cart_item.product_variant.discounted_price:
            cart_item.price = cart_item.product_variant.discounted_price
        else:
            cart_item.price = cart_item.product_variant.price
        
        cart_item.save()

        item_total = cart_item.total_price
        cart_items = CartItem.objects.filter(cart__user=request.user)
        cart_total = sum(item.total_price for item in cart_items)

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
        item_id=request.POST.get('item_id')

        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()

        
        cart_total = sum(item.total_price for item in CartItem.objects.filter(cart__user=request.user))

        return JsonResponse({
                'status': 'success',
                'cart_total': cart_total,
            })
    return JsonResponse({
        'error':'Invalid request'
    },status=400)





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

    user=request.user
    addresses=Address.objects.filter(user=request.user)
    default_address=addresses.filter(is_default=True).first()
    other_addresses=addresses.filter(is_default=False)

    context={
        'default_address':default_address,
        'other_addresses':other_addresses,
        'user':user,
    }

    return render(request,'user/address.html',context)

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

def delete_address(request,address_id):
    address=get_object_or_404(Address,id=address_id,user=request.user)

    if request.POST:
        address.delete()
        messages.error(request,"Address deleted Successfully!")
        return redirect('address')
    messages.error(request,"Invalid Request.")
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
    default_address=addresses.filter(is_default=True).first()
    other_addresses = addresses.filter(is_default=False)

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

def payment(request):
   
    if not request.user.is_authenticated:
        return redirect('userlogin')

    try:
        # Fetch the user's cart and cart items
        cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)

        # Fetch or create the user's wallet
        wallet, created = Wallet.objects.get_or_create(user=request.user, defaults={'balance': 0})

        # Stock verification
        out_of_stock_items = []
        for item in cart_items:
            if item.product_variant.stock == 0:
                out_of_stock_items.append(item.product_variant.product.name)
            elif item.quantity > item.product_variant.stock:
                out_of_stock_items.append(f"{item.product_variant.product.name} (Only {item.product_variant.stock} available)")

        # If any items are out of stock, show an error message
        if out_of_stock_items:
            messages.error(request, f"The following items are out of stock: {', '.join(out_of_stock_items)}")
            return redirect('usercart')

        # Calculate total price and subtotal
        total_price = sum(
            item.product_variant.get_offer_price() if item.product_variant.get_offer_price() else item.get_total_price()
            for item in cart_items
        )
        subtotal = total_price - cart.discount

    except Cart.DoesNotExist:
        messages.error(request, "Cart not found.")
        return redirect('usercart')

    # Check if a delivery address is selected
    selected_address_id = request.session.get('selected_address_id')
    if not selected_address_id:
        messages.error(request, 'No delivery address selected.')
        return redirect('usercheckout')

    try:
        selected_address = Address.objects.get(id=selected_address_id, user=request.user)
    except Address.DoesNotExist:
        messages.error(request, 'Invalid address selected.')
        return redirect('usercheckout')

    # Handle POST request (payment submission)
    if request.method == 'POST':
        method = request.POST.get('payment_method')
        valid_methods = ['wallet', 'razorpay', 'cod']

        # Validate payment method
        if not method:
            messages.error(request, 'Please select a payment method.')
            return redirect('payment')

        if method not in valid_methods:
            messages.error(request, 'Invalid payment method selected.')
            return redirect('payment')

        # Validate Cash on Delivery (COD) conditions
        if method == 'cod' and subtotal > 1000:
            messages.error(request, 'Cash on Delivery is not available for orders above ₹1000.')
            return redirect('payment')

        # Validate wallet balance for wallet payments
        if method == 'wallet':
            if wallet.balance < subtotal:
                messages.error(request, f'Insufficient wallet balance. Required: ₹{subtotal}, Available: ₹{wallet.balance}')
                return redirect('payment')

        # Fetch or create the payment method
        payment_method, _ = PaymentMethod.objects.get_or_create(name=method)

        try:
            # Create the order
            order = Order.objects.create(
                user=request.user,
                total_price=subtotal,
                status='pending',
                address=selected_address,
                payment_method=payment_method,
                discount=cart.discount
            )

            # Handle Razorpay payment
            if method == 'razorpay':
                # Create a Razorpay order
                razorpay_order = razorpay_client.order.create({
                    'amount': int(subtotal * 100),  # Amount in paise
                    'currency': 'INR',
                    'receipt': f'order_{order.id}',
                    'payment_capture': 1  # Auto-capture payment
                })

                # Save Razorpay order ID in the order
                order.razorpay_order_id = razorpay_order['id']
                order.save()

                # Prepare context for the Razorpay payment page
                context = {
                    'razorpay_order_id': razorpay_order['id'],
                    'razorpay_merchant_key': settings.RAZORPAY_KEY_ID,
                    'razorpay_amount': int(subtotal * 100),
                    'currency': 'INR',
                    'callback_url': request.build_absolute_uri(reverse('razorpay_callback')),
                    'order': order,
                }

                # Store the pending order ID in the session
                request.session['pending_order_id'] = order.id

                # Render the Razorpay payment page
                return render(request, 'user/razorpay.html', context)

            # Handle non-Razorpay payments (COD and Wallet)
            if method == 'wallet':
                # Deduct the amount from the wallet
                wallet.balance -= subtotal
                wallet.save()

                # Create a wallet transaction record
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=subtotal,
                    type='debit',
                    order=order
                )

            # Process order items
            for cart_item in cart_items:
                variant = cart_item.product_variant
                variant.stock -= cart_item.quantity
                variant.save()

                item_unit_price = (
                    variant.get_offer_price()
                    if variant.get_offer_price()
                    else variant.price
                )

                OrderItem.objects.create(
                    order=order,
                    product_variant=cart_item.product_variant,
                    quantity=cart_item.quantity,
                    price=item_unit_price
                )

            # Clear the cart
            cart_items.delete()
            cart.coupon = None
            cart.discount = 0
            cart.save()

            # Clear the selected address from the session
            if 'selected_address_id' in request.session:
                del request.session['selected_address_id']

            # Store the order ID in the session for the order success page
            request.session['last_order_id'] = order.id

            # Show success message and redirect to the order success page
            messages.success(request, 'Order placed successfully!')
            return redirect('order_success')

        except Exception as e:
            # If an error occurs, delete the order and show an error message
            if 'order' in locals():
                order.delete()
            messages.error(request, f"Error processing order: {str(e)}")
            return redirect('payment')

    # Prepare context for the payment page
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'subtotal': subtotal,
        'discount': cart.discount,
        'wallet_balance': wallet.balance
    }

    return render(request, 'user/payment.html', context)




#razor pay
@csrf_exempt
def razorpay_callback(request):
    if request.method == "POST":
        try:
            # Get payment details from POST data
            payment_id = request.POST.get('razorpay_payment_id')
            order_id = request.POST.get('razorpay_order_id')
            signature = request.POST.get('razorpay_signature')

            # Verify payment signature
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            try:
                razorpay_client.utility.verify_payment_signature(params_dict)
            except Exception as e:
                # Payment verification failed
                logger.error(f"Payment verification failed: {str(e)}")
                return JsonResponse({'status': 'error', 'message': 'Payment verification failed'}, status=400)

            # Get the order
            order = Order.objects.get(razorpay_order_id=order_id)
            
            # Update order with payment details
            order.razorpay_payment_id = payment_id
            order.razorpay_signature = signature
            order.status = 'processing'
            order.save()

            # Process cart items
            try:
                cart = Cart.objects.get(user=order.user)
                cart_items = CartItem.objects.filter(cart=cart)

                # Create order items and update stock
                for cart_item in cart_items:
                    variant = cart_item.product_variant
                    
                    # Check stock availability again
                    if variant.stock >= cart_item.quantity:
                        variant.stock -= cart_item.quantity
                        variant.save()

                        OrderItem.objects.create(
                            order=order,
                            product_variant=variant,
                            quantity=cart_item.quantity,
                            price=variant.get_offer_price() or variant.price,
                            status='processing'
                        )
                    else:
                        raise Exception(f"Insufficient stock for {variant.product.name}")

                # Clear cart
                cart_items.delete()
                cart.coupon = None
                cart.discount = 0
                cart.save()

                # Store order ID in session
                request.session['last_order_id'] = order.id

                # Return success response with redirect URL
                success_url = request.build_absolute_uri(reverse('order_success'))
                return JsonResponse({
                    'status': 'success',
                    'redirect_url': success_url
                })

            except Cart.DoesNotExist:
                logger.error(f"Cart not found for user {order.user.id}")
                return JsonResponse({'status': 'error', 'message': 'Cart not found'}, status=400)

        except Order.DoesNotExist:
            logger.error(f"Order not found for Razorpay order ID {order_id}")
            return JsonResponse({'status': 'error', 'message': 'Order not found'}, status=400)
        
        except Exception as e:
            logger.error(f"Payment processing failed: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    # Handle GET request (redirect after payment)
    elif request.method == "GET":
        payment_id = request.GET.get('razorpay_payment_id')
        order_id = request.GET.get('razorpay_order_id')
        
        try:
            order = Order.objects.get(
                razorpay_order_id=order_id,
                razorpay_payment_id=payment_id
            )
            request.session['last_order_id'] = order.id
            return redirect('order_success')
            
        except Order.DoesNotExist:
            messages.error(request, 'Order not found')
            return redirect('payment')

    return HttpResponse(status=400)



def ordersuccess(request):
    if not request.user.is_authenticated:
        return redirect('userlogin')

    order_id = request.session.get('last_order_id')
    if not order_id:
        messages.error(request, 'No order found')
        return redirect('myorder')

    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Verify order status
        if order.status not in ['processing', 'pending']:
            messages.error(request, 'Invalid order status')
            return redirect('myorder')

        order_items = OrderItem.objects.filter(order=order)

        # Clear session data
        request.session.pop('last_order_id', None)
        request.session.pop('pending_order_id', None)

        context = {
            'order': order,
            'order_items': order_items
        }
        return render(request, 'user/order_success.html', context)

    except Order.DoesNotExist:
        messages.error(request, 'Order not found')
        return redirect('myorder')
    except Exception as e:
        logger.error(f"Error in order success page: {str(e)}")
        messages.error(request, 'Error retrieving order details')
        return redirect('myorder')



def myorder(request):

    if not request.user.is_authenticated:
        return redirect('userlogin')

    user = request.user
    orders = (
        Order.objects.filter(user=user)
        .prefetch_related('items__product_variant__product',
                          'items__product_variant__productimage_set')
        .order_by('-created_at')
    )
    
    status_filter = request.GET.get('status')

    if status_filter and status_filter != 'All':
        orders = orders.filter(status__iexact=status_filter)

    orders = orders.order_by('-created_at')


    for order in orders:
        order.subtotal = order.total_price + order.discount



    

    context = {
        'orders':orders,
        'current_status': status_filter or 'All'
    }

    return render(request,'user/order.html',context)

def generate_invoice(request, order_id):
    if not request.user.is_authenticated:
        return redirect('userlogin')
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status != 'delivered':
        messages.error(request, 'Invoice is only available for delivered orders.')
        return redirect('myorder')

    # Initialize document
    buffer = BytesIO()
    width, height = A4
    p = canvas.Canvas(buffer, pagesize=A4)

    # Colors
    PURPLE_COLOR = colors.HexColor('#4B0082')
    LIGHT_PURPLE = colors.HexColor('#E6E6FA')
    
    def draw_header():
        # Main Invoice Header
        p.setFillColor(PURPLE_COLOR)
        p.rect(30, height-80, width-60, 50, fill=1)
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 30)
        p.drawString(50, height-55, "INVOICE")
        
        # Logo placeholder (right side of header)
        p.setFillColor(colors.white)
        p.rect(width-150, height-70, 70, 30, fill=0)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(width-140, height-55, "PodCraze")

    def draw_business_info():
        # Left side
        p.setFillColor(colors.black)
        p.setFont("Helvetica-Bold", 10)
        left_info = [
            ("Business Name:", "PodCraze"),
            ("Address:", "123 Business Street"),
            ("Phone Number:", "+91 9876543210")
        ]
        
        y_pos = height-110
        for label, value in left_info:
            p.drawString(40, y_pos, label)
            p.setFont("Helvetica", 10)
            p.drawString(120, y_pos, value)
            p.setFont("Helvetica-Bold", 10)
            y_pos -= 15

        # Right side
        right_info = [
            ("GSTIN No:", "29ABCDE1234F1Z5"),
            ("Invoice No:", f"INV-{order.id}"),
            ("Date:", datetime.now().strftime("%d-%m-%Y")),
            ("State:", "Kerala")
        ]
        
        y_pos = height-110
        for label, value in right_info:
            p.drawString(350, y_pos, label)
            p.setFont("Helvetica", 10)
            p.drawString(420, y_pos, value)
            p.setFont("Helvetica-Bold", 10)
            y_pos -= 15

    def draw_address_sections():
        # Address Headers
        p.setFillColor(PURPLE_COLOR)
        # Bill To header
        p.rect(30, height-200, (width-70)/2, 25, fill=1)
        # Ship To header
        p.rect((width/2)+10, height-200, (width-70)/2, 25, fill=1)
        
        p.setFillColor(colors.white)
        p.setFont("Helvetica-Bold", 12)
        p.drawString(45, height-190, "BILL TO")
        p.drawString((width/2)+25, height-190, "SHIP TO")

        # Address Content
        p.setFillColor(colors.black)
        p.setFont("Helvetica", 10)
        
        # Function to draw address
        def draw_address(x, address_data):
            y = height-220
            for label, value in address_data:
                p.setFont("Helvetica-Bold", 10)
                p.drawString(x, y, f"{label}:")
                p.setFont("Helvetica", 10)
                p.drawString(x+60, y, str(value))
                y -= 15

        # Bill To Address
        bill_address = [
            ("Name", f"{order.user.first_name} {order.user.last_name}"),
            ("Address", order.address.address),
            ("Phone", order.address.phone),
            ("GSTIN", "N/A"),
            ("State", order.address.state)
        ]
        draw_address(40, bill_address)

        # Ship To Address
        ship_address = [
            ("Name", f"{order.user.first_name} {order.user.last_name}"),
            ("Address", order.address.address),
            ("Phone", order.address.phone),
            ("GSTIN", "N/A"),
            ("State", order.address.state)
        ]
        draw_address((width/2)+20, ship_address)

    def draw_items_table():
        # Table Header and Data
        table_data = [['S.No', 'Goods Description', 'HSN', 'QTY', 'MRP', 'Amount']]
        
        for idx, item in enumerate(order.items.all(), 1):
            table_data.append([
                str(idx),
                item.product_variant.product.name,
                "N/A",
                str(item.quantity),
                f"Rs.{item.price:,.2f}",
                f"Rs.{item.price * item.quantity:,.2f}"
            ])

        # Create table
        table = Table(table_data, colWidths=[40, 200, 60, 60, 80, 80])
        table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), PURPLE_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            # Content style
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),  # S.No center
            ('ALIGN', (-2, 0), (-1, -1), 'RIGHT'),  # Price columns right
            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        table.wrapOn(p, width-60, height)
        table.drawOn(p, 30, height-450)

    def draw_footer():
        # Amount in words
        p.setFont("Helvetica-Bold", 10)
        p.drawString(40, height-480, "Amount in Words:")
        p.setFont("Helvetica", 10)
        amount_words = num2words(order.total_price, lang='en_IN').title()
        p.drawString(130, height-480, f"{amount_words} Rupees Only")

        # Calculations
        calculations = [
            ("Sub Total:", f"Rs.{order.total_price + order.discount:,.2f}"),
            ("Discount:", f"Rs.{order.discount:,.2f}"),
            ("SGST (9%):", f"Rs.{0:,.2f}"),
            ("CGST (9%):", f"Rs.{0:,.2f}"),
            ("Total:", f"Rs.{order.total_price:,.2f}")
        ]

        y_pos = height-680
        for label, value in calculations:
            p.setFont("Helvetica-Bold", 10)
            p.drawString(350, y_pos, label)
            p.setFont("Helvetica", 10)
            p.drawString(450, y_pos, value)
            y_pos -= 20

        # Bank Details
        p.setFont("Helvetica-Bold", 10)
        p.drawString(40, height-580, "Bank Details:")
        
        bank_details = [
            ("Bank Name", "ABCXXXX"),
            ("Account Name", "PODCRAZE"),
            ("Account Number", "9876578765"),
            ("IFSC Code", "SIH87667"),
            ("Branch", "ABC")
        ]

        y_pos = height-600
        for label, value in bank_details:
            p.setFont("Helvetica-Bold", 10)
            p.drawString(40, y_pos, f"{label}:")
            p.setFont("Helvetica", 10)
            p.drawString(130, y_pos, value)
            y_pos -= 15

        # Terms and Conditions
        p.setFont("Helvetica-Bold", 8)
        p.drawString(40, 50, "Terms & Conditions:")
        p.setFont("Helvetica", 8)
        terms = [
            "1. Goods once sold will not be taken back or exchanged.",
            "2. All disputes are subject to local jurisdiction only.",
            "3. E.& O.E."
        ]
        y_pos = 40
        for term in terms:
            p.drawString(40, y_pos, term)
            y_pos -= 10

    # Draw all components
    draw_header()
    draw_business_info()
    draw_address_sections()
    draw_items_table()
    draw_footer()

    # Finish and return PDF
    p.showPage()
    p.save()
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="PodCraze_Invoice_{order.id}.pdf"'
    response.write(pdf)
    
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


