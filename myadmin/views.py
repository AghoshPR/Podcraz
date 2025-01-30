from django.shortcuts import *
from django.contrib.auth import authenticate, login,logout, get_user_model
from django.contrib import messages
from user.models import *
from django.db.models import *
from django.utils import timezone
from datetime import  timedelta
from datetime import datetime
from django.db.models import *
from django.utils.timezone import *
from django.core.exceptions import *
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import imghdr,re

from django.db.models.functions import ExtractMonth

from decimal import Decimal


# Create your views here.

User = get_user_model

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

@login_required(login_url='adminlogin')
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

def admindashboard(request):

    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")

    
    User = get_user_model()
    
    
    current_date = datetime.now()
    current_year = current_date.year
    
    
    orders = Order.objects.filter(
        created_at__year=current_year,
        status__in=['delivered', 'shipped']  
    )

    total_revenue = orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_orders = orders.count()

    total_offer_discount = 0
    for order in orders:
        for item in order.items.all():
            variant = item.product_variant
            original_price = variant.price * item.quantity
            final_price = item.price * item.quantity
            total_offer_discount += (original_price - final_price)


    
    total_coupon_discount = orders.aggregate(Sum('discount'))['discount__sum'] or 0

    
    total_discounts = total_offer_discount + total_coupon_discount


    
    def calculate_trend(current, previous):
        if previous == 0:
            return 0
        return ((current - previous) / previous) * 100
    


    # Monthly data for charts
    monthly_data = orders.annotate(
        month=ExtractMonth('created_at')
    ).values('month').annotate(
        revenue=Sum('total_price'),
        order_count=Count('id')
    ).order_by('month')

    # Calculate totals
    total_revenue = orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_orders = orders.count()
    total_products = ProductVariant.objects.count()
    # Update the customer count query
    total_customers = User.objects.filter(is_superuser=False, is_staff=False).count()

    # Previous year data for trends
    prev_year_orders = Order.objects.filter(
        created_at__year=current_year-1,
        status__in=['delivered', 'shipped']
    )
    prev_year_revenue = prev_year_orders.aggregate(Sum('total_price'))['total_price__sum'] or 0
    prev_year_orders_count = prev_year_orders.count()

    # Calculate trends
    revenue_trend = calculate_trend(total_revenue, prev_year_revenue)
    orders_trend = calculate_trend(total_orders, prev_year_orders_count)
    
    # Calculate product trend (based on last month vs current month)
    current_month = current_date.month
    last_month = (current_date - timedelta(days=30)).month
    
    current_month_products = ProductVariant.objects.filter(
        product__created_at__month=current_month,
        product__created_at__year=current_year
    ).count()
    last_month_products = ProductVariant.objects.filter(
        product__created_at__month=last_month,
        product__created_at__year=current_year
    ).count()
    products_trend = calculate_trend(current_month_products, last_month_products)

    # Calculate customer trend using the User model
    current_month_customers = User.objects.filter(
        date_joined__month=current_month,
        date_joined__year=current_year,
        is_superuser=False,
        is_staff=False
    ).count()
    last_month_customers = User.objects.filter(
        date_joined__month=last_month,
        date_joined__year=current_year,
        is_superuser=False,
        is_staff=False
    ).count()
    customers_trend = calculate_trend(current_month_customers, last_month_customers)

    # Calculate period sales
    today = current_date.date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Today's sales
    today_orders = orders.filter(created_at__date=today)
    today_sales = today_orders.aggregate(
        sales=Sum('total_price'),
        discounts=Sum('discount')
    )

    # Week's sales
    week_orders = orders.filter(created_at__date__gte=week_start)
    week_sales = week_orders.aggregate(
        sales=Sum('total_price'),
        discounts=Sum('discount')
    )

    # Month's sales
    month_orders = orders.filter(created_at__date__gte=month_start)
    month_sales = month_orders.aggregate(
        sales=Sum('total_price'),
        discounts=Sum('discount')
    )

    sales_report = Order.objects.filter(
        status__in=['delivered', 'shipped']
    ).select_related('user').prefetch_related('items', 'items__product_variant').order_by('-created_at')[:15]
    
    # sales report data
    report_data = []
    for order in sales_report:
        original_price = order.total_price + order.discount
        
        
        order_items = order.items.all()
        total_offer_discount = 0
        offer_applied = "No Offer"
        
        for item in order_items:
            variant = item.product_variant
            original_item_price = variant.price * item.quantity
            actual_item_price = item.price * item.quantity
            item_discount = original_item_price - actual_item_price
            total_offer_discount += item_discount

        # Fetch applied offer details
            offer = variant.get_active_offer()
            if offer:
                if offer.discount_type == "percentage":
                    offer_applied = f"{offer.discount_value}%"
                else:
                    offer_applied = f"₹{offer.discount_value}"
        
        # Calculate coupon discount (remaining discount after offer)
        coupon_amount = order.discount - total_offer_discount if order.discount > total_offer_discount else 0
        
        if total_offer_discount > 0:
            offer_percentage = (total_offer_discount / original_price) * 100
            offer_applied = f"{offer_percentage:.0f}%"
        else:
            offer_applied = "0%"
        
        report_data.append({
            'date': order.created_at.strftime('%d/%m/%Y'),
            'order_id': order.id,
            'customer': order.user.username,
            'original_price': original_price,
            'offer_applied': offer_applied,
            'coupon': coupon_amount,
            'net_amount': order.total_price
        })
    
   


    context = {
        'current_year': current_year,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_products': total_products,
        'total_customers': total_customers,
        'revenue_trend': revenue_trend,
        'orders_trend': orders_trend,
        'total_discounts': total_discounts,
        'products_trend': products_trend,
        'customers_trend': customers_trend,
        'monthly_data': list(monthly_data),
        'today_sales': today_sales['sales'] or 0,
        'today_discounts': today_sales['discounts'] or 0,
        'week_sales': week_sales['sales'] or 0,
        'week_discounts': week_sales['discounts'] or 0,
        'month_sales': month_sales['sales'] or 0,
        'month_discounts': month_sales['discounts'] or 0,
        'sales_report': report_data,
    }
    
    return render(request, 'admin/admindashboard.html', context)







@login_required(login_url='adminlogin')
@never_cache
def adminproducts(request):

    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")

    search_query = request.GET.get('search','')
    page = request.GET.get('page', 1)

    products = Product.objects.prefetch_related('productvariant_set').select_related('brand', 'product_category').annotate(variant_count=Count('productvariant'))

    if search_query:
        products = products.filter(
            Q(name__icontains = search_query)|
            Q(brand__name__icontains = search_query) |
            Q(product_category__name__icontains = search_query)

        )

    paginator = Paginator(products, 5)

    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)


    products_list={
        'products':products_page,
        'search_query':search_query
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


@login_required(login_url='adminlogin')
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

        try:
            price = float(variant_price)
            if price <= 0:
                errors.append("Price must be greater than 0.")
            elif price >= 100000:
                errors.append("Price must not exceed ₹10,00,000.")
            elif not re.match(r'^\d+(\.\d{1,2})?$', variant_price):
                errors.append("Price can have up to two decimal places only.")
        except ValueError:
            errors.append("Price must be a valid number.")

        if not variant_stock or int(variant_stock) <= 0:
            errors.append("Stock must be a number.")

        try:
            stock = int(variant_stock)
            if stock <= 0:
                errors.append("Stock cannot be negative.")
            elif stock >= 10000:
                errors.append("Stock must not exceed 10,000.")
        except ValueError:
            errors.append("Stock must be a valid integer.")


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

    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")

    prd_id=get_object_or_404(Product, id=product_id)

    product_variants=ProductVariant.objects.filter(product=prd_id)
    
    context = {
        'product': prd_id,
        'product_variants': product_variants,
    }

    return render(request,'admin/viewvarients.html',context)

def editvarient(request, variant_id):

    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")
    
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

        if not variant_stock or int(variant_stock) < 0:
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
    


@login_required(login_url='adminlogin')
def adminbrands(request):

    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")
    
    search_query = request.GET.get('search','')

    brands=Brand.objects.all()

    if search_query:
        
        brands = brands.filter(
            Q(name__icontains=search_query) |  
            Q(products__name__icontains=search_query) | 
            Q(products__product_category__name__icontains=search_query)
        ).distinct() 
         
    context = {
        'brands':brands,
        'search_query':search_query

    }

    return render(request,'admin/adminbrands.html',context)



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


@login_required(login_url='adminlogin')
def admincustomers(request):

    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")
    
    search_query = request.GET.get('search', '')

    users = User.objects.filter(is_superuser=False)

    if search_query:
        
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )

    context = {
        'users':users,
        'search_query':search_query
    }

    return render(request,'admin/admincustomers.html',context)

def deletecustomers(request,user_id):
    user=get_object_or_404(User,id=user_id)

    if user:
        user.delete()
        messages.success(request, f' {user.username} has been deleted successfully.')
    else:
        messages.error(request,"You do not have permission to delete this user.")
    
    return redirect('admincustomers')
    

@login_required(login_url='adminlogin')
def admincategory(request):

    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")

    search_query = request.GET.get('search', '')

    categories=ProductCategory.objects.all()

    if search_query:
        categories = ProductCategory.objects.filter(
            Q(name__icontains=search_query) |
            Q(status__icontains=search_query)
        )
    else:
        categories = ProductCategory.objects.all()


    context = {
        'categories':categories,
        'search_query': search_query,

    }

    return render(request,'admin/admincategories.html',context)

def adminaddcategory(request):

    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")

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

    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")

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
    

@login_required(login_url='adminlogin')
def adminorders(request):

    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")
    
    search_query = request.GET.get('search', '')

    orders = (
        Order.objects.all()
        .prefetch_related('items__product_variant__product', 'items__product_variant__productimage_set')
        .order_by('-created_at')
    )

    
    if search_query:
        orders = orders.filter(
            Q(user__first_name__icontains=search_query) |  
            Q(payment_method__name__icontains=search_query) |
            Q(status__icontains=search_query)
        )

    context = {
        'orders': orders,
        'search_query': search_query 
    }

    return render(request,'admin/adminorder.html',context)



def adminorders_details(request,order_id):

    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")
    

    
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.all()
    user = order.user

    ALLOWED_STATUSES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered')
    ]    

    if request.POST:
        new_status = request.POST.get('status')

        if new_status in dict(ALLOWED_STATUSES):
            order.status = new_status
            order.save()
            messages.success(request, f"Order status updated to {new_status}.")
        
        else:
            messages.error(request, "Invalid status selected.")

    context = { 
        "order": order,
        "order_items": order_items,
        "user": user,
        "status_choices": ALLOWED_STATUSES
    }
    
    return render(request,'admin/adminorder_details.html', context)



def adminorders_delete(request,prd_id):
    prd_order=get_object_or_404(Order,id=prd_id)
    prd_order.delete()
    return redirect('adminorders')



    


def orderrequests(request):

    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")
    

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

    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        
        
        if order.status == 'return_pending':
            action = request.POST.get('action')

            if action == 'approve':
                order.status = 'return_approved'
                order.save()

                for item in order.items.all():
                    product_variant = item.product_variant  
                    product_variant.stock += item.quantity  
                    product_variant.save()

#credit to account

                wallet, created = Wallet.objects.get_or_create(
                    user=order.user,
                    defaults={'balance': 0}
                )

                wallet.balance += order.total_price
                wallet.save()


#add order amount to the wallet

                WalletTransaction.objects.create(
                    wallet = wallet,
                    type = 'credit',
                    amount = order.total_price,
                    product=order.items.first().product_variant.product,
                    order=order

                )

                messages.success(request, 'Return request approved successfully')

            elif action == 'reject':
                order.status = 'return_rejected'
                order.save()
                messages.success(request, 'Return request rejected successfully')
            
            
            return redirect('orderrequests')
    


#admin offers

def offer(request):

    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")

    return render(request,'admin/adminoffer.html')



def productoffer(request):
    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")

    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            discount_type = request.POST.get('discount_type')
            discount_value = request.POST.get('discount_value')
            valid_from = make_aware(
                datetime.strptime(request.POST.get('valid_from'), '%Y-%m-%dT%H:%M')
            )
            valid_until = make_aware(
                datetime.strptime(request.POST.get('valid_until'), '%Y-%m-%dT%H:%M')
            )
            product_id = request.POST.get('product')

            # Validate the offer name
            if not name or len(name.strip()) < 3:
                messages.error(request, "Offer name must be at least 3 characters long")
                return redirect('productoffer')
            if len(name) > 20:
                messages.error(request, "Offer name cannot exceed 20 characters")
                return redirect('productoffer')

            # Validate discount value
            try:
                discount_value = float(discount_value)
                if discount_type == 'percentage':
                    if not (1 <= discount_value <= 90):
                        messages.error(request, "Percentage discount must be between 1 and 90")
                        return redirect('productoffer')
                elif discount_type == 'fixed':
                    if not (1 <= discount_value <= 10000):
                        messages.error(request, "Fixed discount must be between 1 and 10000")
                        return redirect('productoffer')
            except (ValueError, TypeError):
                messages.error(request, "Invalid discount value")
                return redirect('productoffer')

            # Validate date ranges
            if valid_from >= valid_until:
                messages.error(request, "Valid from date must be before valid until date")
                return redirect('productoffer')
            if valid_from < now():
                messages.error(request, "Valid from date cannot be in the past")
                return redirect('productoffer')

            # Check for active offers on the selected product
            if Offer.objects.filter(
                product_id=product_id, is_active=True, valid_until__gt=now()
            ).exists():
                messages.error(request, "Selected product already has an active offer")
                return redirect('productoffer')

            # Create the offer
            Offer.objects.create(
                name=name,
                discount_type=discount_type,
                discount_value=discount_value,
                valid_from=valid_from,
                valid_until=valid_until,
                product_id=product_id,
                is_active=True
            )
            messages.success(request, 'Product offer added successfully')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('productoffer')

    offers = Offer.objects.filter(product__isnull=False)
    products = Product.objects.all()

    context = {
        'offers': offers,
        'products': products,
    }
    return render(request, 'admin/productoffer.html', context)



def edit_offer(request, offer_id):
    if request.method == 'POST':
        try:
            offer = get_object_or_404(Offer, id=offer_id)
            
            
            offer.name = request.POST.get('name')
            offer.discount_type = request.POST.get('discount_type')
            offer.discount_value = request.POST.get('discount_value')
            
            
            valid_from = timezone.make_aware(
                datetime.strptime(request.POST.get('valid_from'), '%Y-%m-%dT%H:%M')
            )
            valid_until = timezone.make_aware(
                datetime.strptime(request.POST.get('valid_until'), '%Y-%m-%dT%H:%M')
            )
            
            offer.valid_from = valid_from
            offer.valid_until = valid_until

            
            if not offer.name or len(offer.name.strip()) < 3:
                messages.error(request, "Offer name must be at least 3 characters long")
                return redirect('productoffer')
            if len(offer.name) > 20:
                messages.error(request, "Offer name cannot exceed 20 characters")
                return redirect('productoffer')
            
            try:
                discount_value = float(offer.discount_value)
                if offer.discount_type == 'percentage':
                    if discount_value < 1 or discount_value > 90:
                        messages.error(request, "Percentage discount must be between 1 and 90")
                        return redirect('productoffer')
                else:  # fixed amount
                    if discount_value < 1 or discount_value > 10000:
                        messages.error(request, "Fixed discount must be between 1 and 10000")
                        return redirect('productoffer')
            except (ValueError, TypeError):
                messages.error(request, "Invalid discount value")
                return redirect('productoffer')
            
            if valid_from >= valid_until:
                    messages.error(request, "Valid from date must be before valid until date")
                    return redirect('productoffer')

            if valid_from < timezone.now():
                messages.error(request, "Valid from date cannot be in the past")
                return redirect('productoffer')
            
            product_id = request.POST.get('product')
            if Offer.objects.filter(
                product_id=product_id,
                is_active=True,
                valid_until__gt=timezone.now()
            ).exclude(id=offer_id).exists():
                messages.error(request, "Selected product already has another active offer")
                return redirect('productoffer')
            
            
            offer.product_id = request.POST.get('product')
            offer.is_active = request.POST.get('is_active') == 'True'
            
            offer.save()
            messages.success(request, 'Offer updated successfully')
            
        except Exception as e:
            messages.error(request, f'Error updating offer: {str(e)}')
            
    return redirect('productoffer')




def categoryoffer(request):
    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")

    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            discount_type = request.POST.get('discount_type')
            discount_value = request.POST.get('discount_value')
            valid_from = make_aware(
                datetime.strptime(request.POST.get('valid_from'), '%Y-%m-%dT%H:%M')
            )
            valid_until = make_aware(
                datetime.strptime(request.POST.get('valid_until'), '%Y-%m-%dT%H:%M')
            )
            category_id = request.POST.get('category')

            if not name or len(name.strip()) < 3:
                messages.error(request, "Offer name must be at least 3 characters long")
                return redirect('categoryoffer')

            if len(name) > 20:
                messages.error(request, "Offer name cannot exceed 20 characters")
                return redirect('categoryoffer')

            try:
                discount_value = float(discount_value)

                if discount_type == 'percentage' and not (1 <= discount_value <= 90):
                    messages.error(request, "Percentage discount must be between 1 and 90")
                    return redirect('categoryoffer')
                
                elif discount_type == 'fixed':

                    if not (1 <= discount_value <= 10000):
                        messages.error(request, "Fixed discount must be between 1 and 10000")
                        return redirect('categoryoffer')

                    
                    min_price = ProductVariant.objects.filter(product__product_category_id=category_id).aggregate(
                        min_price=Min('price')
                    )['min_price']

                    if min_price is not None and discount_value > min_price:
                        messages.error(request, f"Fixed discount cannot be greater than the lowest product variant price ({min_price})")
                        return redirect('categoryoffer')
                
            except (ValueError, TypeError):
                messages.error(request, "Invalid discount value")
                return redirect('categoryoffer')

            
            
            if Offer.objects.filter(
                product_category_id=category_id,
                is_active=True,
                valid_until__gt=now()
            ).exists():
                messages.error(request, "Selected category already has an active offer")
                return redirect('categoryoffer')
            
            if valid_from >= valid_until:
                    messages.error(request, "Valid from date must be before valid until date")
                    return redirect('categoryoffer')

            Offer.objects.create(
                name=name,
                discount_type=discount_type,
                discount_value=discount_value,
                valid_from=valid_from,
                valid_until=valid_until,
                product_category_id=category_id,
                is_active=True
            )

            messages.success(request, 'Category offer added successfully')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
        return redirect('categoryoffer')

    offers = Offer.objects.filter(product_category__isnull=False)
    categories = ProductCategory.objects.filter(status='Active')

    context = {
        'offers': offers,
        'categories': categories,
    }
    return render(request, 'admin/categoryoffer.html', context)

def edit_categoryoffer(request, offer_id):
    if request.method == 'POST':
        try:
            offer = get_object_or_404(Offer, id=offer_id)
            
            
            offer.name = request.POST.get('name')
            offer.discount_type = request.POST.get('discount_type')
            offer.discount_value = request.POST.get('discount_value')
            
            
            valid_from = timezone.make_aware(
                datetime.strptime(request.POST.get('valid_from'), '%Y-%m-%dT%H:%M')
            )
            valid_until = timezone.make_aware(
                datetime.strptime(request.POST.get('valid_until'), '%Y-%m-%dT%H:%M')
            )
            
            offer.valid_from = valid_from
            offer.valid_until = valid_until

            if not offer.name or len(offer.name.strip()) < 3:
                messages.error(request, "Offer name must be at least 3 characters long")
                return redirect('categoryoffer')
            
            if len(offer.name) > 20:
                messages.error(request, "Offer name cannot exceed 20 characters")
                return redirect('categoryoffer')
            
            try:
                discount_value = float(offer.discount_value)
                if offer.discount_type == 'percentage':
                    if discount_value < 1 or discount_value > 90:
                        messages.error(request, "Percentage discount must be between 1 and 90")
                        return redirect('categoryoffer')
                    
                elif offer.discount_type == 'fixed':
                    
                    if not (1 <= discount_value <= 10000):
                        messages.error(request, "Fixed discount must be between 1 and 10000")
                        return redirect('categoryoffer')

                    
                    min_price = ProductVariant.objects.filter(product__product_category_id=category_id).aggregate(
                        min_price=Min('price')
                    )['min_price']

                    if min_price is not None and discount_value > min_price:
                        messages.error(request, f"Fixed discount cannot be greater than the lowest product variant price ({min_price})")
                        return redirect('categoryoffer')
                    
            except (ValueError, TypeError):
                messages.error(request, "Invalid discount value")
                return redirect('categoryoffer')
            
            if valid_from >= valid_until:
                    messages.error(request, "Valid from date must be before valid until date")
                    return redirect('categoryoffer')

            
            
            category_id = request.POST.get('category')
            if Offer.objects.filter(
                product_category_id=category_id,
                is_active=True,
                valid_until__gt=timezone.now()
            ).exclude(id=offer_id).exists():
                messages.error(request, "Selected category already has another active offer")
                return redirect('categoryoffer')
            
            
            offer.product_category_id = request.POST.get('category')
            offer.is_active = request.POST.get('is_active') == 'True'


            
            
            offer.save()
            messages.success(request, 'Category offer updated successfully')
            
        except Exception as e:
            messages.error(request, f'Error updating offer: {str(e)}')
            
    return redirect('categoryoffer')





def delete_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    try:
        offer.delete()

        messages.success(request, 'Offer deleted successfully')
    except Exception as e:
        messages.error(request, f'Error deleting offer: {str(e)}')
    
    if offer.product:

        return redirect('productoffer')
    else: 
        return redirect('categoryoffer')
   


def admincoupon(request):

    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")

    coupons = Coupon.objects.all().order_by('-valid_from')

    context ={
        'coupons':coupons
    }

    return render(request,'admin/admincoupon.html',context)


def addcoupon(request):

    if request.POST:
        try:
            code = request.POST.get('code')
            discount_type = request.POST.get('discount_type')
            discount_value = request.POST.get('discount_value')
            min_purchase_amount = request.POST.get('min_purchase_amount')
            description = request.POST.get('description')
            
            valid_from = timezone.make_aware(
                    datetime.strptime(request.POST.get('valid_from'), '%Y-%m-%dT%H:%M')
            )

            valid_until = timezone.make_aware(
                datetime.strptime(request.POST.get('valid_until'), '%Y-%m-%dT%H:%M')
            )



            if not code or len(code.strip()) < 3:
                messages.error(request, "Coupon code must be at least 3 characters long")
                return redirect('admincoupon')
            
            if len(code) > 20:
                messages.error(request, "Coupon code cannot exceed 20 characters")
                return redirect('admincoupon')

            
            if Coupon.objects.filter(code=code).exists():
                messages.error(request, 'Coupon Code Already Exists!')
                return redirect('admincoupon')

            
            if not description or len(description.strip()) < 3:
                messages.error(request, "Description must be at least 3 characters long")
                return redirect('admincoupon')
            
            if len(description) > 30:
                messages.error(request, "Description cannot exceed 30 characters")
                return redirect('admincoupon')
            
            try:
                discount_value = float(discount_value)
                min_purchase_amount = float(min_purchase_amount)

                if discount_type == 'percentage':
                    if discount_value < 1 or discount_value > 90:
                        messages.error(request, "Percentage discount must be between 1 and 90")
                        return redirect('admincoupon')
                else:  
                    if discount_value < 1 or discount_value > min_purchase_amount:
                        messages.error(request, f"Fixed discount cannot exceed minimum purchase amount (₹{min_purchase_amount})")
                        return redirect('admincoupon')

                if min_purchase_amount < 0 or min_purchase_amount > 99999:
                    messages.error(request, "Minimum purchase amount must be between 0 and 99999")
                    return redirect('admincoupon')

            except (ValueError, TypeError):
                messages.error(request, "Invalid discount value or minimum purchase amount")
                return redirect('admincoupon')
            
            if valid_from >= valid_until:
                messages.error(request, "End date must be after start date")
                return redirect('admincoupon')

            
            
            

            coupon = Coupon.objects.create(

            code = code,
            discount_type = discount_type,
            discount_value = discount_value,
            min_purchase_amount = min_purchase_amount,
            valid_from = valid_from,
            valid_until = valid_until,
            is_active = True,
            description=description

            )
            
            coupon.save()
            messages.success(request, 'Coupon added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding coupon: {str(e)}')

    return redirect('admincoupon')


def edit_coupon(request, coupon_id):
    if request.method == 'POST':
        try:
            coupon = get_object_or_404(Coupon, id=coupon_id)
            
            
            new_code = request.POST.get('code')
            coupon.code = new_code
            coupon.discount_type = request.POST.get('discount_type')
            coupon.discount_value = request.POST.get('discount_value')
            coupon.min_purchase_amount = request.POST.get('min_purchase_amount')
            coupon.description = request.POST.get('description')
            
            
            valid_from = timezone.make_aware(
                datetime.strptime(request.POST.get('valid_from'), '%Y-%m-%dT%H:%M')
            )
            valid_until = timezone.make_aware(
                datetime.strptime(request.POST.get('valid_until'), '%Y-%m-%dT%H:%M')
            )
            
            coupon.valid_from = valid_from
            coupon.valid_until = valid_until
            coupon.is_active = request.POST.get('is_active') == 'True'


            if not new_code or len(new_code.strip()) < 3:
                messages.error(request, "Coupon code must be at least 3 characters long")
                return redirect('admincoupon')
            
            if len(new_code) > 20:
                messages.error(request, "Coupon code cannot exceed 20 characters")
                return redirect('admincoupon')
            
            if Coupon.objects.filter(code=new_code).exclude(id=coupon_id).exists():
                messages.error(request, 'Coupon Code Already Exists!')
                return redirect('admincoupon')

            
            if not coupon.description or len(coupon.description.strip()) < 3:
                messages.error(request, "Description must be at least 3 characters long")
                return redirect('admincoupon')
            
            if len(coupon.description) > 30:
                messages.error(request, "Description cannot exceed 30 characters")
                return redirect('admincoupon')
            
            try:
                discount_value_float = float(coupon.discount_value)
                min_purchase_float = float(coupon.min_purchase_amount)

                if coupon.discount_type == 'percentage':
                    if discount_value_float < 1 or discount_value_float > 90:
                        messages.error(request, "Percentage discount must be between 1 and 90")
                        return redirect('admincoupon')
                    
                elif coupon.discount_type == 'fixed':
                    if discount_value_float < 1 or discount_value_float > min_purchase_float:
                        messages.error(request, f"Fixed discount cannot exceed minimum purchase amount (₹{min_purchase_float})")
                        return redirect('admincoupon')

                
                if min_purchase_float < 0 or min_purchase_float > 99999:
                    messages.error(request, "Minimum purchase amount must be between 0 and 99999")
                    return redirect('admincoupon')

            except (ValueError, TypeError):
                messages.error(request, "Invalid discount value or minimum purchase amount")
                return redirect('admincoupon')
            
            if valid_from >= valid_until:
                messages.error(request, "End date must be after start date")
                return redirect('admincoupon')

            
            
            
            

            
            coupon.save()
            messages.success(request, 'Coupon updated successfully!')
            
        except Exception as e:
            messages.error(request, f'Error updating coupon: {str(e)}')
            
    return redirect('admincoupon')


def deletecoupon(request,coupon_id):

    coupon = Coupon.objects.get(id=coupon_id)
    coupon.delete()
    messages.success(request, 'Coupon deleted successfully!')

    return redirect('admincoupon')