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
    path('productview/<int:variant_id>/',views.userproductview,name='userproductview'),


    path('wishlist/', views.userwishlist, name='userwishlist'),
    path('toggle-wishlist/', views.toggle_wishlist, name='toggle_wishlist'),

    path('about/',views.about,name='about'),
    path('cart/',views.usercart,name='usercart'),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('update-cart-item/', views.update_cart_item, name='update_cart_item'),
    path('remove-cart-item/', views.remove_cart_item, name='remove_cart_item'),


    
    path('checkout/',views.usercheckout,name='usercheckout'),
    path('checkout_address/',views.checkout_address,name='checkout_address'),


    path('profile/',views.myprofile,name='myprofile'),
    


    path('address/',views.address,name='address'),
    path('addaddress/',views.add_address,name='add_address'),
    path('editaddress/<int:address_id>',views.editaddress,name='edit_address'),
    path('deleteaddress/<int:address_id>',views.delete_address,name='delete_address'),
    path('defaultaddress/<int:address_id>',views.set_default,name='set_default'),

    
    path('payment/',views.payment,name='payment'),

    path('order/',views.myorder,name='myorder'),
    path('ordersuccess/', views.order_success, name='order_success'),
    path('ordercancel/<int:order_id>/',views.cancel_order,name='cancel_order'),
    path('orderreturn/<int:order_id>/',views.order_return,name='order_return'),
    
    path('generate-invoice/<int:order_id>/', views.generate_invoice, name='generate_invoice'),
    

    #Razorpay
    
    path('razorpay/callback/', views.razorpay_callback, name='razorpay_callback'),
    


    path('orderview/<int:order_id>/',views.orderview,name='orderview'),


    path('wallet/',views.wallet,name='wallet'),


    path('coupon/',views.coupon,name='coupon'),

    path('changepassword/',views.user_changepass,name='user_changepass'),

    path('order/item/cancel/<int:item_id>/', views.cancel_order_item, name='cancel_order_item'),
    path('order/item/return/<int:item_id>/', views.return_order_item, name='return_order_item'),

    path('retry-payment/<int:order_id>/', views.retry_payment, name='retry_payment'),




]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
