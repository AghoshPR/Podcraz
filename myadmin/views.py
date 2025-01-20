from django.shortcuts import *
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from user.models import *
from django.db.models import *
from django.core.exceptions import *
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
import imghdr,re

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

@login_required(login_url='adminlogin')
@never_cache
def admindashboard(request):
    return render(request,'admin/admindashboard.html')

@login_required(login_url='adminlogin')
@never_cache
def adminproducts(request):

    # if not request.user.is_superuser:
    #     return HttpResponse("You are restricted to enter this page")

    products = Product.objects.prefetch_related('productvariant_set').select_related('brand', 'product_category').annotate(variant_count=Count('productvariant'))

    products_list={
        'products':products,
    }

    return render(request,'admin/adminproducts.html',products_list)

def adminaddproducts(request):

    if request.POST:
        name=request.POST.get('prd_name','').strip()
        brand_id=request.POST.get('prd_brand','').strip()
        category_id=request.POST.get('prd_category','').strip()
        description=request.POST.get('description','').strip()

        errors=[]

        if not name or len(name) < 3:
            errors.append("Product name must be at least 3 characters long.")

        if not re.match(r'^[A-Za-z0-9\s]+$', name):  
            errors.append("Product name can only contain letters, numbers.")

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
        name=request.POST.get('prd_name','').strip()
        brand_id=request.POST.get('prd_brand','').strip()
        category_id = request.POST.get('prd_category','').strip()
        description = request.POST.get('description','').strip()


        errors = []
        if not name or len(name) < 3:
            errors.append("Product name must be at least 3 characters long.")

        if not re.match(r'^[A-Za-z0-9\s]+$', name):  
            errors.append("Product name can only contain letters, numbers.")
        
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
        variant_color=request.POST.get('color','').strip()
        variant_price=request.POST.get('price','').strip()
        variant_stock=request.POST.get('stock','').strip()

        errors = []

        if not variant_color or len(variant_color) < 3:
            errors.append("Color must be at least 3 characters long.")

        if not re.match(r'^[A-Za-z\s]+$', variant_color):  
            errors.append("Color name can only contain letters.")

        if not variant_price or not variant_price.isdigit():
            errors.append("Price must be a valid number.")

        if not variant_stock or int(variant_stock) <= 0:
            errors.append("Stock must be a number.")


        img = [
            request.FILES.get('productImage1'),
            request.FILES.get('productImage2'),
            request.FILES.get('productImage3'),
            request.FILES.get('productImage4')
        ]

        uploaded_images = [image for image in img if image]
        if len(uploaded_images) != 4:
            errors.append("Exactly 4 product images are required.")
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
        variant_color = request.POST.get('color', '').strip()
        variant_price = request.POST.get('price', '').strip()
        variant_stock = request.POST.get('stock', '').strip()

        errors = []

        if not variant_color or len(variant_color) < 3:
            errors.append("Color must be at least 3 characters long.")
        
        elif not re.match(r'^[A-Za-z\s]+$', variant_color):  
            errors.append("Color name can only contain letters.")
        
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

        

        #  new images if any are uploaded
        for image in new_images:
            if image:
                image_type = imghdr.what(image)
                if image_type not in ['jpeg', 'png', 'jpg']:
                    errors.append(f"Invalid image file type for {image.name}. Only JPEG, PNG, and JPG files are allowed.")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('editvarients', variant_id=variant_id)
        
        # Update variant 
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

        name = request.POST.get('brand_name', '').strip()

        errors = []

        
        if not name:
            errors.append("Brand name is required.")

        elif not re.match(r'^[A-Za-z\s]+$', name):  
            errors.append("Brand name can only contain letters and spaces.")

        elif len(name) < 3:
            errors.append("Brand name must be at least 3 characters long.")

        elif Brand.objects.filter(name__iexact=name).exists():
            errors.append("Brand name already exists.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
                Brand.objects.create(name=name)
                messages.success(request, "Brand added successfully.")
                return redirect('brands')
    return render(request,'admin/addbrands.html')

def editbrands(request, brand_id):

    brand= get_object_or_404(Brand,id=brand_id)
    if request.POST:
        name = request.POST.get('brand_name', '').strip()
        errors = []

        if not name:
            errors.append("Brand name is required.")
        elif not re.match(r'^[A-Za-z\s]+$', name):  
            errors.append("Brand name can only contain letters.")
        elif len(name) < 3:
            errors.append("Brand name must be at least 3 characters long.")
        elif Brand.objects.filter(name__iexact=name).exclude(id=brand_id).exists():
            errors.append("Brand name already exists.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
                brand.name=name
                brand.save()
                messages.success(request, "Brand updated successfully.")
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
        messages.success(request, f' {user.username} has been deleted successfully.')
    else:
        messages.error(request,"You do not have permission to delete this user.")
    
    return redirect('admincustomers')
    


def admincategory(request):

    categories=ProductCategory.objects.all()
    return render(request,'admin/admincategories.html',{'categories':categories})

def adminaddcategory(request):

    if request.POST:
        name = request.POST.get('categoryName', '').strip()
        errors = []

        if not name:
            errors.append("Category name is required.")
        elif not re.match(r'^[A-Za-z\s]+$', name):  
            errors.append("Category name can only contain letters and spaces.")
        elif len(name) < 3:
            errors.append("Category name must be at least 3 characters long.")
        elif ProductCategory.objects.filter(name__iexact=name).exists():
            errors.append("Category name already exists.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            ProductCategory.objects.create(name=name)
            messages.success(request, "Category added successfully.")
            return redirect('admincategory')
        
    return render(request,'admin/addcategories.html')

def admineditcategory(request,category_id):
    category=get_object_or_404(ProductCategory, id=category_id)
    if request.POST:

        category_name = request.POST.get('categoryName', '').strip()
        errors = []

        if not category_name:
            errors.append("Category name is required.")
        elif not re.match(r'^[A-Za-z\s]+$', category_name):  # Only alphabets and spaces allowed
            errors.append("Category name can only contain letters and spaces.")
        elif len(category_name) < 3:
            errors.append("Category name must be at least 3 characters long.")
        elif ProductCategory.objects.filter(name__iexact=category_name).exclude(id=category_id).exists():
            errors.append("Category name already exists.")

        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            category.name=category_name
            category.save()
            messages.success(request, "Category updated successfully.")
            return redirect('admincategory')       

    return render(request,'admin/editcategories.html',{'category':category})

def adminblockcategory(request,category_id):
    category=get_object_or_404(ProductCategory,id=category_id)

    if category.status == 'Active':
        category.status = 'Blocked'
        messages.success(request, f"Category '{category.name}' has been successfully blocked.")
    else:
        category.status ='Active'
        messages.success(request, f"Category '{category.name}' has been successfully unblocked.")
    category.save()
    return redirect('admincategory')





def admindeletecategory(request,id):
    category=ProductCategory.objects.get(id=id)
    if request.POST:
        category.delete()
        return redirect('admincategory')
    


def adminorders(request):

    orders = (
        Order.objects.all()
        .prefetch_related('items__product_variant__product', 'items__product_variant__productimage_set')
        .order_by('-created_at')
    )

    context = {
        'orders': orders
    }

    return render(request,'admin/adminorder.html',context)



def adminorders_details(request,order_id):

    
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.all()
    user = order.user
    

    if request.POST:
        new_status = request.POST.get('status')

        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f"Order status updated to {new_status}.")
        
        else:
            messages.error(request, "Invalid status selected.")

    context = { 
        "order": order,
        "order_items": order_items,
        "user": user,
    }
    
    return render(request,'admin/adminorder_details.html', context)



def adminorders_delete(request,prd_id):
    prd_order=get_object_or_404(Order,id=prd_id)
    prd_order.delete()
    return redirect('adminorders')



    


def orderrequests(request):

    cancel_requests = Order.objects.filter(

        status__in = ['pending','processing','shipped'], cancellation_reason__isnull = False
    ).select_related('user').prefetch_related('items__product_variant__product__productimage_set')


    return_requests = Order.objects.filter(
        return_reason__isnull=False
    ).select_related(
        'user'
    ).prefetch_related(
        'items__product_variant__productimage_set', 
        'items__product_variant__product'
    ).order_by('-created_at')


    context = {
        'cancel_requests': cancel_requests,
        'return_requests':return_requests
    }

    return render(request,'admin/order_requests.html',context)


def request_handle(request, order_id):

    if request.POST:
        order = get_object_or_404(Order,id=order_id)

        action = request.POST.get('action')

        if action == 'approve':
            order.status = 'return_approved'
            messages.success(request, 'Return request approved successfully')
        elif action == 'reject':
            order.status = 'return_rejected'
            messages.success(request, 'Return request Rejected successfully')
        
        order.save()
        return redirect('orderrequests')


    return redirect('orderrequests')






