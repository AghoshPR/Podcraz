from django.shortcuts import *
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from user.models import *
from django.db.models import *
from django.core.exceptions import *
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
import imghdr

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


################# user block and unblock ####################




def block_user(request,user_id):

    try:

        user=User.objects.get(id=user_id)
        user.status='Blocked'
        user.save()
        messages.success(request,f'User {user.username} has been blocked successfully.')

    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    
    return redirect('admincustomers')

def unblock_user(request, user_id):

    try:

        user=User.objects.get(id=user_id)
        user.status='Active'
        user.save()
        messages.success(request,f'User {user.username} has been unblocked successfully.')

    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    
    return redirect('admincustomers')



    






################# user block and unblock ####################




################## product ######################


def adminproducts(request):

    products = Product.objects.prefetch_related('productvariant_set').select_related('brand', 'product_category').annotate(variant_count=Count('productvariant'))

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

        errors=[]

        if not name or len(name) < 3:
            errors.append("Product name must be at least 3 characters long.")
        if not brand_id or not Brand.objects.filter(id=brand_id).exists():
            errors.append("Please select a valid brand.")
        if not category_id or not ProductCategory.objects.filter(id=category_id).exists():
            errors.append("Please select a valid category.")
        if not description or len(description) < 10:
            errors.append("Description must be at least 10 characters long.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:

            if brand_id and category_id:
                brand=Brand.objects.get(id=brand_id)
                category=ProductCategory.objects.get(id=category_id)
                Product.objects.create(name=name, description=description, brand=brand, product_category=category)

                messages.success(request, "Product added successfully.")
                return redirect('adminproducts')
    
    brands= Brand.objects.all()
    categories=ProductCategory.objects.all()

    product_addlist={
        'brands': brands,
        'categories': categories
    }


    return render(request,'admin/adminaddproduct.html',product_addlist)

def editproducts(request,product_id):

    product=Product.objects.get(id=product_id)
    
    if request.POST:
        name=request.POST.get('prd_name')
        brand_id=request.POST.get('prd_brand')
        category_id = request.POST.get('prd_category')
        description = request.POST.get('description')


        errors = []
        if not name or len(name) < 3:
            errors.append("Product name must be at least 3 characters long.")
        if not brand_id or not Brand.objects.filter(id=brand_id).exists():
            errors.append("Please select a valid brand.")
        if not category_id or not ProductCategory.objects.filter(id=category_id).exists():
            errors.append("Please select a valid category.")
        if not description or len(description) < 10:
            errors.append("Description must be at least 10 characters long.")

        if errors:
            
            for error in errors:
                messages.error(request, error)
        else:

            if brand_id and category_id:
                brand=Brand.objects.get(id=brand_id)
                category=ProductCategory.objects.get(id=category_id)

                product.name=name
                product.description=description
                product.brand=brand
                product.product_category=category
                product.save()

                return redirect('adminproducts')
    
    brands=Brand.objects.all()
    categories=ProductCategory.objects.all()

    edit_list={
        'brands':brands,
        'categories':categories,
        'product':product
    }



    return render(request,'admin/editproducts.html',edit_list)


def deleteproducts(request,product_id):
    product=get_object_or_404(Product,id=product_id)
    product.delete()
    return redirect('adminproducts')



def productvarient(request,product_id):
    if request.POST:
        variant_color=request.POST.get('color')
        variant_price=request.POST.get('price')
        variant_stock=request.POST.get('stock')

        errors = []

        if not variant_color or len(variant_color) < 3:
            errors.append("Color must be at least 3 characters long.")
        if not variant_price or not variant_price.isdigit():
            errors.append("Price must be a valid number.")
        if not variant_stock or int(variant_stock) <= 0:
            errors.append("Stock must be a positive number.")


        img = [
            request.FILES.get('productImage1'),
            request.FILES.get('productImage2'),
            request.FILES.get('productImage3'),
            request.FILES.get('productImage4')
        ]

        if not any(img): 
            errors.append("At least one product image is required.")
        else:
            for image in img:
                if image:

                    image_type = imghdr.what(image)
                    if image_type not in ['jpeg', 'png', 'jpg']:
                        errors.append(f"Invalid image file type for {image.name}. Only JPEG, PNG, and JPG files are allowed.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:

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


            for images in img:
                if images:
                    ProductImage.objects.create(
                        product_variant=variant,
                        image_path=images
                    )
            messages.success(request, "Product variant added successfully.")
            return redirect('adminproducts')

    
    return render(request,'admin/productvarient.html')

def viewvarient(request,product_id):

    prd_id=get_object_or_404(Product, id=product_id)

    product_variants=ProductVariant.objects.filter(product=prd_id)
    
    context = {
        'product': prd_id,
        'product_variants': product_variants,
    }

    return render(request,'admin/viewvarients.html',context)

def editvarient(request, variant_id):
    try:
        variants = ProductVariant.objects.get(id=variant_id)
        product_images = ProductImage.objects.filter(product_variant=variants)
    except ProductVariant.DoesNotExist:
        messages.error(request, "Variant does not exist")
        return redirect('viewvarients', product_id=variant_id)

    if request.POST:
        variant_color = request.POST.get('color')
        variant_price = request.POST.get('price')
        variant_stock = request.POST.get('stock')

        errors = []

        if not variant_color or len(variant_color) < 3:
            errors.append("Color must be at least 3 characters long.")
        
        try:
            variant_price = float(variant_price)
            if variant_price <= 0:
                errors.append("price must be positive number!")
        except ValueError:
            errors.append("Price must be a valid number.")

        if not variant_stock or int(variant_stock) <= 0:
            errors.append("Stock must be a positive number.")

        # Handle image uploads
        new_images = [
            request.FILES.get('productImage1'),
            request.FILES.get('productImage2'),
            request.FILES.get('productImage3'),
            request.FILES.get('productImage4')
        ]

        # Validate new images if any are uploaded
        for image in new_images:
            if image:
                image_type = imghdr.what(image)
                if image_type not in ['jpeg', 'png', 'jpg']:
                    errors.append(f"Invalid image file type for {image.name}. Only JPEG, PNG, and JPG files are allowed.")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('editvarients', variant_id=variant_id)
        
        # Update variant details
        variants.color = variant_color
        variants.price = variant_price
        variants.stock = variant_stock
        variants.save()

        # Handle image updates
        existing_images = list(product_images)
        for i, new_image in enumerate(new_images):
            if new_image:
                # If there's an existing image at this position, update it
                if i < len(existing_images):
                    existing_images[i].image_path = new_image
                    existing_images[i].save()
                else:
                    # Create new image if we don't have one at this position
                    ProductImage.objects.create(
                        product_variant=variants,
                        image_path=new_image
                    )

        messages.success(request, "Product Variant updated successfully.")
        return redirect('viewvarients', product_id=variants.product.id)

    context = {
        'variant': variants,
        'product': variants.product,
        'product_images': product_images,
        'remaining_image_slots': range(product_images.count(), 4) 
    }

    return render(request, 'admin/editvarients.html', context)


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

    return render(request,'admin/admincustomers.html',{'users':user})

def deletecustomers(request,user_id):
    user=get_object_or_404(User,id=user_id)

    if user:
        user.delete()
        messages.success(request, "f'User {user.first_name} has been deleted successfully.")
    else:
        messages.error(request,"You do not have permission to delete this user.")
    
    return redirect('admincustomers')
    


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

def admineditcategory(request,category_id):
    category=get_object_or_404(ProductCategory, id=category_id)
    if request.POST:
        category_name=request.POST.get('categoryName')
        if category_name:
            category.name=category_name
            category.save()
            return redirect('admincategory')       

    return render(request,'admin/editcategories.html',{'category':category})


def admindeletecategory(request,id):
    category=ProductCategory.objects.get(id=id)
    if request.POST:
        category.delete()
        return redirect('admincategory')






