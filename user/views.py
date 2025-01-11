
from django.shortcuts import *
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate,login,logout,get_user_model
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
import random,smtplib
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.utils.dateparse import parse_datetime
from .models import *
from django.contrib.auth.hashers import make_password
from email.message import EmailMessage
from decouple import config
import re
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




def userproducts(request):

    categories=ProductCategory.objects.filter(status='Active')
    brands=Brand.objects.all()
    product_variants = ProductVariant.objects.filter(
        product__product_category__status='Active'
    )


    context={
        'categories':categories,
        'brands':brands,
        'product_variants':product_variants
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
    return render(request,'user/wishlist.html')


def usercart(request):
    return render(request,'user/cart.html')

def usercheckout(request):
    return render(request,'user/checkout.html')
