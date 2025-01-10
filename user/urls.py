from django.urls import path
from . import views
from .otp_validate import *
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    
    path('',views.userhome,name='userhome'),
    path('user/login/',views.userlogin,name='userlogin'),
    path('user/signup/',views.signup,name='register'),
    path('user/signup-otp/',views.signup_otp,name='signup_otp'),
    path('user/forgot-password/',views.forgot_pass,name='forgot-pass'),
    path('user/OTP/',send_otp,name='send_otp'),
    path('user/OTP-verification/',otp_verify,name='verify_otp'),
    path('user/new-password/',views.reset_password,name='reset_password'),
    path('logout/',views.userlogout,name='userlogout'),

    
    path('products/',views.userproducts,name='userproducts'),
    path('productview/<int:product_id>/',views.userproductview,name='userproductview'),
    path('wishlist/',views.userwishlist,name='userwishlist'),
    path('cart/',views.usercart,name='usercart'),
    path('checkout/',views.usercheckout,name='usercheckout'),
    


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
