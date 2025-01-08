from django.urls import path,include
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    

    path('login/',views.adminlogin,name='adminlogin'),
    
    path('logout/',views.adminlogout,name='adminlogout'),

    path('products/',views.adminproducts,name='adminproducts'),
    path('addproducts/',views.adminaddproducts,name='adminaddproducts'),
    path('editproducts/',views.editproducts,name='editproducts'),
    path('deleteproducts/<int:product_id>/',views.deleteproducts,name='deleteproducts'),



    path('productsvarient/<int:product_id>/',views.productvarient,name='productvarient'),
    path('viewvarient/<int:product_id>/',views.viewvarient,name='viewvarients'),
    path('editvarient/',views.editvarient,name='editvarients'),
    path('deletevarient/<int:variant_id>/',views.deletevarient,name='deletevarient'),


    path('brands/',views.adminbrands,name='brands'),
    path('addbrands/',views.addbrands,name='addbrands'),
    path('editbrands/<int:brand_id>/',views.editbrands,name='editbrands'),
    path('deletebrand/<int:brand_id>/',views.deletebrand,name='deletebrand'),
    

    path('customers/',views.admincustomers,name='admincustomers'),

    path('category/',views.admincategory,name='admincategory'),
    path('addcategory/',views.adminaddcategory,name='adminaddcategory'),
    path('editcategory/<int:id>/',views.admineditcategory,name='admineditcategory'),
    path('deletecategory/<int:id>/',views.admindeletecategory,name='admindeletecategory'),
   
    

   
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
