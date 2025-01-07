from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from user.models import *

# Create your views here.



def adminlogin(request):
    if request.POST:

        admuser=request.POST['admin']
        admpass=request.POST['adminpass']

        user=authenticate(request,username=admuser,password=admpass)
        if user is not None and user.is_superuser:
            login(request,user)
            return redirect('adminproducts')
        else:
            messages.error(request,"invalid Credentials!")
    return render(request,'admin/adminlogin.html')

def adminlogout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('adminlogin')



def adminproducts(request):
    return render(request,'admin/adminproducts.html')

def adminaddproducts(request):
    return render(request,'admin/adminaddproduct.html')

def editproducts(request):
    return render(request,'admin/editproducts.html')

def productvarient(request):
    return render(request,'admin/productvarient.html')

def viewvarient(request):
    return render(request,'admin/viewvarients.html')



def admincustomers(request):
    return render(request,'admin/admincustomers.html')

def admincategory(request):

    categories=ProductCategory.objects.all()
    return render(request,'admin/admincategories.html',{'categories':categories})

def adminaddcategory(request):

    if request.POST:
        name=request.POST.get('categoryName')
        if name:
            ProductCategory.objects.create(name=name)
            return redirect('admincategory')
        
    return render(request,'admin/addcategories.html')

def admineditcategory(request):
    return render(request,'admin/editcategories.html')

def admindeletecategory(request,id):
    category=ProductCategory.objects.get(id=id)
    if category:
        category.delete()
        return redirect('admincategory')






