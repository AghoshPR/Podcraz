from django.shortcuts import *
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from user.models import *
from django.db.models import *
from django.core.exceptions import *

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




################## product ######################

def adminproducts(request):

    products=Product.objects.select_related('brand','product_category').annotate(varient_count=Count('productvariant'))

    products_list={
        'products':products,
    }

    return render(request,'admin/adminproducts.html',products_list)

def adminaddproducts(request):

    if request.POST:
        name=request.POST.get('prd_name')
        brand_id=request.POST.get('prd_brand')
        category_id=request.POST.get('prd_category')
        description=request.POST.get('description')

        if brand_id and category_id:
            brand=Brand.objects.get(id=brand_id)
            category=ProductCategory.objects.get(id=category_id)

            Product.objects.create(name=name, description=description, brand=brand, product_category=category)
            return redirect('adminproducts')
    
    brands= Brand.objects.all()
    categories=ProductCategory.objects.all()

    product_addlist={
        'brands': brands,
        'categories': categories
    }


    return render(request,'admin/adminaddproduct.html',product_addlist)

def editproducts(request):
    return render(request,'admin/editproducts.html')


def deleteproducts(request,product_id):
    product=get_object_or_404(Product,id=product_id)
    product.delete()
    return redirect('adminproducts')



def productvarient(request,product_id):
    if request.POST:
        variant_color=request.POST.get('color')
        variant_price=request.POST.get('price')
        variant_stock=request.POST.get('stock')

        try:
            product = Product.objects.get(id=product_id)  
        except Product.DoesNotExist:
            return redirect('adminproducts')
        
        variant=ProductVariant.objects.create(
            product=product,
            color=variant_color,
            price=variant_price,
            stock=variant_stock
        )

        img=[
            request.FILES.get('productImage1'),
            request.FILES.get('productImage2'),
            request.FILES.get('productImage3'),
            request.FILES.get('productImage4')
            
        ]

        for images in img:
            if images:
                ProductImage.objects.create(
                    product_variant=variant,
                    image_path=images
                )
        return redirect('adminproducts')


    return render(request,'admin/productvarient.html')

def viewvarient(request,product_id):

    prd_id=get_object_or_404(Product, id=product_id)

    product_variants=ProductVariant.objects.filter(product=prd_id)
    

    product_variants=ProductVariant.objects.filter(product=prd_id)

    context = {
        'product': prd_id,
        'product_variants': product_variants,
    }

    return render(request,'admin/viewvarients.html',context)

def editvarient(request):
    return render(request,'admin/editvarients.html')

def deletevarient(request,variant_id):
    delete_variant=get_object_or_404(ProductVariant, id=variant_id)
    product_id=delete_variant.product.id
    delete_variant.delete()
     
    return redirect('viewvarients', product_id=product_id)
    



def adminbrands(request):
    brands=Brand.objects.all()
    return render(request,'admin/adminbrands.html',{'brands':brands})

def addbrands(request):

    if request.POST:

        name=request.POST.get('brand_name')
        if name:
            Brand.objects.create(name=name)
            return redirect('brands')
    return render(request,'admin/addbrands.html')

def editbrands(request, brand_id):

    brand= get_object_or_404(Brand,id=brand_id)
    if request.POST:
        name=request.POST.get('brand_name')
        if name:
            brand.name=name
            brand.save()
            return redirect('brands')
    return render(request,'admin/editbrands.html',{'brand':brand})

def deletebrand(request, brand_id):
    brand=get_object_or_404(Brand, id=brand_id)
    if request.POST:
        brand.delete()
        return redirect('brands')


def admincustomers(request):

    user=User.objects.all()

    return render(request,'admin/admincustomers.html',{'user':user})

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
    if request.POST:
        category.delete()
        return redirect('admincategory')






