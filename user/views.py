
from django.shortcuts import *
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate,login,logout,get_user_model
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import *
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import random,smtplib
from datetime import  timedelta
from django.utils.timezone import now
from django.utils.dateparse import parse_datetime
from .models import *
from django.contrib.auth.hashers import make_password
from email.message import EmailMessage
from decouple import config
import re,json
UserModel = get_user_model()


########### user login and signup ###############

def userlogin(request):

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

    return render(request,'user/homepage.html')


def userlogout(request):
    logout(request)
    return redirect('userlogin')

def about(request):
    return render(request,'user/about.html')



def userproducts(request):

    categories=ProductCategory.objects.filter(status='Active')

    brands=Brand.objects.all()

    product_variants = ProductVariant.objects.filter(
        product__product_category__status='Active'
    ).prefetch_related('productimage_set','wishlists')


    user_wishlist = []
    if request.user.is_authenticated:
        user_wishlist = Wishlist.objects.filter(user=request.user).values_list('product_variants', flat=True)


    context={
        'categories':categories,
        'brands':brands,
        'product_variants':product_variants,
        'user_wishlist': user_wishlist,
    }

    return render(request,'user/products.html',context)

def userproductview(request, variant_id):
   
   
    product_variants=get_object_or_404(ProductVariant,id=variant_id)
    product_images=ProductImage.objects.filter(product_variant=product_variants)

    related_variants=ProductVariant.objects.filter(product=product_variants.product)
    

    context={
        
        'product_variants':product_variants,
        'product_images':product_images,
        'related_variants':related_variants
    }
    
    return render(request,'user/productview.html',context)

def userwishlist(request):
    if not request.user.is_authenticated: 
        return redirect('userlogin')
    
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    products =  wishlist.product_variants.all()
    

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

    total_price = sum(item.total_price for item in cart_items)

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
                # Check if adding the new quantity will exceed the limit
                if cart_item.quantity + quantity > 4:
                    return JsonResponse({'status': 'error', 'message': 'You cannot add more than 4 of this product to the cart'}, status=400)
                # Update the quantity if under the limit
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
            # Check if adding will exceed the quantity limit of 4
            if cart_item.quantity + 1 > 4:
                return JsonResponse({'status': 'error', 'message': 'You cannot add more than 4 of this product to the cart'}, status=400)
            cart_item.quantity += 1

        elif action == 'decrease' and cart_item.quantity > 1:
            cart_item.quantity -= 1
        
        cart_item.save()

        item_total = cart_item.product_variant.price * cart_item.quantity
        cart_items = CartItem.objects.filter(cart__user=request.user)
        cart_total = sum(item.product_variant.price * item.quantity for item in cart_items)

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

        #for calculate new total after removing 
        cart_total = sum(item.total_price for item in CartItem.objects.filter(cart__user=request.user))

        return JsonResponse({
                'status': 'success',
                'cart_total': cart_total,
            })
    return JsonResponse({
        'error':'Invalid request'
    },status=400)


def usercheckout(request):
    return render(request,'user/checkout.html')


@login_required
def myprofile(request):

    user=request.user
    default_address=Address.objects.filter(user=user, is_default=True).first()
    
    context={
        'user':user,
        'default_address':default_address
    }

    return render(request,'user/myprofile.html',context)


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
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pin_code = request.POST.get('pin_code')
        is_default = request.POST.get('is_default') == 'on'

        if not all([address, phone, city, state, pin_code]):
            messages.error(request, 'All fields are required.')
            return redirect('add_address')

        if not phone.isdigit() or len(phone) < 10:
            messages.error(request, 'Invalid phone number.')
            return redirect('add_address')

        if not pin_code.isdigit() or len(pin_code) != 6:
            messages.error(request, 'Invalid PIN code.')
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
            return redirect('edit_address', id=address_id)

        if not phone.isdigit() or len(phone) < 10:
            messages.error(request, 'Invalid phone number.')
            return redirect('edit_address', id=address_id)

        if not pin_code.isdigit() or len(pin_code) != 6:
            messages.error(request, 'Invalid PIN code.')
            return redirect('edit_address', id=address_id)
        
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






def order(request):
    return render(request,'user/order.html')

def order_return(request):
    return render(request,'user/order_return.html')

def orderview(request):
    return render(request,'user/orderview.html')

def wallet(request):
    return render(request,'user/wallet.html')

def coupon(request):
    return render(request,'user/coupon.html')

def changepass(request):
    return render(request,'user/changepass.html')