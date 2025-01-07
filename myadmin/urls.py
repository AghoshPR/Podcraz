from django.urls import path,include
from . import views
urlpatterns = [
    

    path('login/',views.adminlogin,name='adminlogin'),
    
    path('logout/',views.adminlogout,name='adminlogout'),

    path('products/',views.adminproducts,name='adminproducts'),
    path('addproducts/',views.adminaddproducts,name='adminaddproducts'),
    path('editproducts/',views.editproducts,name='editproducts'),
    path('productsvarient/',views.productvarient,name='productvarient'),
    
    path('viewvarient/',views.viewvarient,name='viewvarients'),

    path('customers/',views.admincustomers,name='admincustomers'),

    path('category/',views.admincategory,name='admincategory'),
    path('addcategory/',views.adminaddcategory,name='adminaddcategory'),
    path('editcategory/<int:id>/',views.admineditcategory,name='admineditcategory'),
   
    

   
    
]
