from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    

    path('login/',views.adminlogin,name='adminlogin'),
    path('logout/',views.adminlogout,name='adminlogout'),




    path('dashboard/',views.admindashboard,name='admindashboard'),
    
    

#admin product
    path('products/',views.adminproducts,name='adminproducts'),
    path('addproducts/',views.adminaddproducts,name='adminaddproducts'),
    path('editproducts/<int:product_id>/',views.editproducts,name='editproducts'),
    path('deleteproducts/<int:product_id>/',views.deleteproducts,name='deleteproducts'),




    path('productsvarient/<int:product_id>/',views.productvarient,name='productvarient'),
    path('viewvarient/<int:product_id>/',views.viewvarient,name='viewvarients'),
    path('editvarient/<int:variant_id>',views.editvarient,name='editvarients'),
    path('deletevarient/<int:variant_id>/',views.deletevarient,name='deletevarient'),




    path('brands/',views.adminbrands,name='brands'),
    path('addbrands/',views.addbrands,name='addbrands'),
    path('editbrands/<int:brand_id>/',views.editbrands,name='editbrands'),
    path('deletebrand/<int:brand_id>/',views.deletebrand,name='deletebrand'),




    path('customers/',views.admincustomers,name='admincustomers'),
    path('block_user/<int:user_id>/', views.block_user, name='block_user'),
    path('unblock_user/<int:user_id>/', views.unblock_user, name='unblock_user'),
    path('deleteuser/<int:user_id>/', views.deletecustomers, name='delete_user'),



    path('category/',views.admincategory,name='admincategory'),
    path('addcategory/',views.adminaddcategory,name='adminaddcategory'),
    path('editcategory/<int:category_id>/',views.admineditcategory,name='admineditcategory'),
    path('status/<int:category_id>/',views.adminblockcategory,name='adminblockcategory'),
    path('deletecategory/<int:id>/',views.admindeletecategory,name='admindeletecategory'),




    path('orders/',views.adminorders,name='adminorders'),
    path('ordersdetails/<int:order_id>',views.adminorders_details,name='adminorders_details'),



    path('deleteorder/<int:prd_id>/',views.adminorders_delete,name='prd_order_delete'),
    path('orderrequests/',views.orderrequests,name='orderrequests'),
    path('handle-return/<int:order_id>/', views.request_handle, name='request_handle'),



    path('offer/', views.offer, name='offer'),
    path('productoffer/', views.productoffer, name='productoffer'),
    path('edit_offer/<int:offer_id>/', views.edit_offer, name='edit_offer'),


    path('categoryoffer/', views.categoryoffer, name='categoryoffer'),
    path('edit_categoryoffer/<int:offer_id>/', views.edit_categoryoffer, name='edit_categoryoffer'),
    path('delete-offer/<int:offer_id>/', views.delete_offer, name='delete_offer'),


    
   
    path('admincoupon/', views.admincoupon, name='admincoupon'),
    path('addcoupon/', views.addcoupon, name='addcoupon'),
    path('edit_coupon/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('deletecoupon/<int:coupon_id>', views.deletecoupon, name='deletecoupon'),
    

    path('dashboard/sales-data/', views.get_sales_data_api, name='sales_data_api'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
