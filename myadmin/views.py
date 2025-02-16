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
from django.db.models import Sum, Count, F
from django.db.models.functions import ExtractMonth, ExtractYear, TruncDate, TruncWeek, TruncMonth, ExtractHour
from decimal import Decimal
import xlsxwriter
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import json
from django.http import JsonResponse, HttpResponse
import calendar
from django.db.models import Min
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch


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



@login_required(login_url='adminlogin')
def block_user(request,user_id):

    try:

        user=User.objects.get(id=user_id)
        user.status='Blocked'
        user.save()
        messages.success(request,f'User {user.username} has been blocked successfully.')

    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    
    return redirect('admincustomers')

@login_required(login_url='adminlogin')
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
def admindashboard(request):
    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")
    
   
    date_filter = request.GET.get('date_filter', 'weekly') 

    
    end_date = timezone.now()
    labels = []
    sales_amounts = []
    
    if date_filter == 'today':
        start_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_filter == 'monthly':
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif date_filter == 'yearly':
        start_date = end_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:  
        start_date = end_date - timedelta(days=7)

   
    orders = Order.objects.filter(
        created_at__range=(start_date, end_date)
    )
    
    
    for order in orders:
        print(f"Order ID: {order.id}, Date: {order.created_at}, Amount: {order.total_price}")

    if date_filter == 'yearly':
       
        monthly_totals = {}
        
        
        for order in orders:
            order_month = order.created_at.month
            if order_month in monthly_totals:
                monthly_totals[order_month] += float(order.total_price)
            else:
                monthly_totals[order_month] = float(order.total_price)
        
       
        for month in range(1, 13):
            month_name = datetime(2000, month, 1).strftime('%b')
            labels.append(month_name)
            sales_amounts.append(monthly_totals.get(month, 0))

        print("Monthly Totals:", monthly_totals)

    elif date_filter == 'monthly':
      
        daily_totals = {}
        
       
        for order in orders:
            order_date = order.created_at.date()
            if order_date in daily_totals:
                daily_totals[order_date] += float(order.total_price)
            else:
                daily_totals[order_date] = float(order.total_price)
        
       
        current_date = start_date.date()
        end_date = end_date.date()
        
        while current_date <= end_date:
            labels.append(current_date.strftime('%d %b'))
            sales_amounts.append(daily_totals.get(current_date, 0))
            current_date += timedelta(days=1)

        print("Daily Totals for Month:", daily_totals)

    elif date_filter == 'today':
        
        hourly_totals = {}
        
      
        for order in orders:
            order_hour = order.created_at.hour
            if order_hour in hourly_totals:
                hourly_totals[order_hour] += float(order.total_price)
            else:
                hourly_totals[order_hour] = float(order.total_price)
        
       
        for hour in range(24):
            time_label = f"{hour:02d}:00"
            labels.append(time_label)
            sales_amounts.append(hourly_totals.get(hour, 0))

        print("Hourly Totals:", hourly_totals)

    else:  
       
        daily_totals = {}
        
       
        for order in orders:
            order_date = order.created_at.date()
            if order_date in daily_totals:
                daily_totals[order_date] += float(order.total_price)
            else:
                daily_totals[order_date] = float(order.total_price)
        
       
        current_date = start_date.date()
        end_date = end_date.date()
        
        while current_date <= end_date:
            labels.append(current_date.strftime('%d %b'))
            sales_amounts.append(daily_totals.get(current_date, 0))
            current_date += timedelta(days=1)


    total_orders = Order.objects.filter(
        status__in=['Delivered', 'Processing', 'Shipped', 'Pending']
    ).count()
    
    total_customers = User.objects.filter(
        is_superuser=False, 
        is_active=True
    ).count()

    current_orders = Order.objects.filter(
        status__in=['Processing', 'Shipped', 'Pending']
    )

    # top selling products 
    top_products = OrderItem.objects.filter(
        order__in=current_orders
    ).values(
        'product_variant__product__name'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]

    # top categories f
    top_categories = OrderItem.objects.filter(
        order__in=current_orders
    ).values(
        'product_variant__product__product_category__name'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]

    # top brands
    top_brands = OrderItem.objects.filter(
        order__in=current_orders
    ).values(
        'product_variant__product__brand__name'
    ).annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]

    context = {
        'total_orders': total_orders,
        'total_customers': total_customers,
        'top_products': top_products,
        'top_categories': top_categories,
        'top_brands': top_brands,
        'date_filter': date_filter,
        'labels': json.dumps(labels),
        'sales_amounts': json.dumps(sales_amounts)
    }

    return render(request, 'admin/admindashboard.html', context)



@login_required(login_url='adminlogin')
def salesreport(request):
    
    search_query = request.GET.get('search', '')
    date_filter = request.GET.get('date_filter', 'all')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Initial queryset
    filtered_orders = Order.objects.select_related(
        'user', 
        'payment_method'
    ).prefetch_related(
        'items',
        'items__product_variant',
        'items__product_variant__product'
    )

    
    today = timezone.localtime(timezone.now()).date()
    
    if date_filter == 'daily':
        today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        filtered_orders = filtered_orders.filter(created_at__range=(today_start, today_end))
    elif date_filter == 'weekly':
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        start_of_week = timezone.make_aware(datetime.combine(start_of_week, datetime.min.time()))
        filtered_orders = filtered_orders.filter(created_at__range=(start_of_week, end_of_week))
    elif date_filter == 'monthly':
        start_of_month = today.replace(day=1)
        if today.month == 12:
            end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        start_datetime = timezone.make_aware(datetime.combine(start_of_month, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_of_month, datetime.max.time()))
        filtered_orders = filtered_orders.filter(created_at__range=(start_datetime, end_datetime))
    elif date_filter == 'custom' and start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            start_datetime = timezone.make_aware(datetime.combine(start, datetime.min.time()))
            end_datetime = timezone.make_aware(datetime.combine(end, datetime.max.time()))
            filtered_orders = filtered_orders.filter(created_at__range=(start_datetime, end_datetime))
        except ValueError:
            messages.error(request, "Invalid date format")

    
    if search_query:
        filtered_orders = filtered_orders.filter(
            Q(id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(status__icontains=search_query)
        )

    # Apply status filter
    filtered_orders = filtered_orders.filter(
        status__in=['Delivered', 'Processing', 'Shipped', 'Pending']
    ).order_by('-created_at')

    # Calculate totals from filtered orders
    total_original_price = sum(order.get_total_original_price() for order in filtered_orders)
    total_product_discount = sum(order.get_total_product_discount() for order in filtered_orders)
    total_final_price = sum(order.total_price for order in filtered_orders)
    total_coupon_discount = sum(order.discount or 0 for order in filtered_orders)

    total_sales = {
        'total_orders': filtered_orders.count(),
        'total_original_price': total_original_price,
        'total_discount': total_product_discount
    }

    # Handle export requests
    if request.GET.get('export') == 'excel':
        orders_list = list(filtered_orders)  
        return export_to_excel(
            orders_list,
            total_sales,
            total_product_discount,
            total_coupon_discount,
            total_final_price
        )

    if request.GET.get('export') == 'pdf':
        orders_list = list(filtered_orders)  
        return export_to_pdf(
            orders_list,
            total_sales,
            total_product_discount,
            total_coupon_discount,
            total_final_price
        )

    # Apply pagination for display
    paginator = Paginator(filtered_orders, 10)
    page = request.GET.get('page', 1)
    
    try:
        orders_page = paginator.page(page)
    except PageNotAnInteger:
        orders_page = paginator.page(1)
    except EmptyPage:
        orders_page = paginator.page(paginator.num_pages)

    context = {
        'orders': orders_page,
        'search_query': search_query,
        'date_filter': date_filter,
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
        'total_coupon_discount': total_coupon_discount,
        'net_total': total_final_price,
        'total_original_price': total_original_price,
        'total_product_discount': total_product_discount,
        'total_final_price': total_final_price,
    }

    return render(request, 'admin/salesreport.html', context)

def export_to_excel(filtered_orders, total_sales, product_discounts, coupon_discounts, final_price):
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    company_name = "PODCRAZE"
    billing_date = timezone.localtime(timezone.now()).date()

    # Add company name and billing date
    bold_format = workbook.add_format({'bold': True})
    worksheet.write(0, 0, company_name, bold_format)
    worksheet.write(1, 0, f"Billing Date: {billing_date}", bold_format)

    # Add headers (now starting from row 3)
    headers = ['Date', 'Order ID', 'Customer', 'Product', 'Original Price', 
               'Product Discount', 'Coupon Discount', 'Final Price']
    for col, header in enumerate(headers):
        worksheet.write(3, col, header)

    # Add data from filtered orders (starting from row 4)
    for row, order in enumerate(filtered_orders, 4):
        first_item = order.items.first()
        product_name = first_item.product_variant.product.name if first_item else "N/A"
        
        worksheet.write(row, 0, order.created_at.strftime('%Y-%m-%d'))
        worksheet.write(row, 1, f"#{order.id}")
        worksheet.write(row, 2, order.user.first_name)
        worksheet.write(row, 3, product_name)
        worksheet.write(row, 4, float(order.get_total_original_price()))
        worksheet.write(row, 5, float(order.get_total_product_discount()))
        worksheet.write(row, 6, float(order.discount or 0))
        worksheet.write(row, 7, float(order.total_price))

    # Add totals row
    row = len(filtered_orders) + 4
    worksheet.write(row, 0, "Totals")
    worksheet.write(row, 4, float(total_sales['total_original_price']))
    worksheet.write(row, 5, float(product_discounts))
    worksheet.write(row, 6, float(coupon_discounts))
    worksheet.write(row, 7, float(final_price))

    workbook.close()
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=sales_report.xlsx'
    return response

def export_to_pdf(filtered_orders, total_sales, product_discounts, coupon_discounts, final_price):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=sales_report.pdf'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []

    # Add company name and billing date
    styles = getSampleStyleSheet()
    elements.append(Paragraph("PODCRAZE - Sales Report", styles['Heading1']))
    elements.append(Paragraph(f"Billing Date: {timezone.localtime(timezone.now()).date()}", styles['Normal']))
    elements.append(Spacer(1, 12))  # Add some space
    
    data = [['Date', 'Order ID', 'Customer', 'Product', 'Original Price', 
             'Product Discount', 'Coupon Discount', 'Final Price']]
    
    for order in filtered_orders:
        first_item = order.items.first()
        product_name = first_item.product_variant.product.name if first_item else "N/A"
        
        data.append([
            order.created_at.strftime('%Y-%m-%d'),
            f"#{order.id}",
            order.user.first_name,
            product_name,
            f"Rs{order.get_total_original_price()}",
            f"Rs{order.get_total_product_discount()}",
            f"Rs{order.discount or 0}",
            f"Rs{order.total_price}"
        ])

    data.append([
        "Totals", "", "", "",
        f"Rs{total_sales['total_original_price']}",
        f"Rs{product_discounts}",
        f"Rs{coupon_discounts}",
        f"Rs{final_price}"
    ])

    col_widths = [60, 80, 100, 100, 100, 100, 100, 100]  
    table = Table(data, colWidths=col_widths)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    doc.build(elements)
    return response


    


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
                
                if i < len(existing_images):
                    existing_images[i].image_path = new_image
                    existing_images[i].save()
                else:
                   
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

User = get_user_model()
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

    
    order_items = OrderItem.objects.select_related(
        'order',
        'order__user',
        'order__payment_method',
        'product_variant',
        'product_variant__product'
    ).all().order_by('-order__created_at')

    
    if search_query:
        order_items = order_items.filter(
            Q(product_variant__product__name__icontains=search_query) |
            Q(order__user__first_name__icontains=search_query) |
            Q(status__icontains=search_query) |
            Q(order__payment_method__name__icontains=search_query)
        )

    
    paginator = Paginator(order_items, 10)  
    page = request.GET.get('page')
    try:
        order_items = paginator.page(page)
    except PageNotAnInteger:
        order_items = paginator.page(1)
    except EmptyPage:
        order_items = paginator.page(paginator.num_pages)

    context = {
        'order_items': order_items,
        'search_query': search_query
    }

    return render(request, 'admin/adminorder.html', context)



def adminorders_details(request, order_item_id):
    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")
    
    order_item = get_object_or_404(OrderItem, id=order_item_id)

    ALLOWED_STATUSES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('return_pending', 'Return Pending'),
        ('return_approved', 'Return Approved'),
        ('return_rejected', 'Return Rejected'),
    ]    

    if request.POST:
        new_status = request.POST.get('status')

        if new_status in dict(ALLOWED_STATUSES):
            order_item.status = new_status
            order_item.save()
            messages.success(request, f"Order item status updated to {new_status}.")
        else:
            messages.error(request, "Invalid status selected.")

    context = { 
        "order_item": order_item,
        "status_choices": ALLOWED_STATUSES
    }
    
    return render(request, 'admin/adminorder_details.html', context)



def adminorders_delete(request,prd_id):
    prd_order=get_object_or_404(Order,id=prd_id)
    prd_order.delete()
    return redirect('adminorders')



    


def orderrequests(request):
    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")
    
    # Query order items with return requests
    order_items = OrderItem.objects.select_related(
        'order',
        'order__user',
        'product_variant',
        'product_variant__product'
    ).prefetch_related(
        'product_variant__productimage_set'
    ).filter(
        status__in=['return_pending', 'return_approved', 'return_rejected']
    ).order_by('-order__created_at')

    context = {
        'order_items': order_items,
    }

    return render(request, 'admin/order_requests.html', context)



def request_handle(request, order_item_id):
    if not request.user.is_superuser:
        return HttpResponse("You are restricted to enter this page")

    if request.method == 'POST':
        order_item = get_object_or_404(OrderItem, id=order_item_id)
        
        if order_item.status == 'return_pending':
            action = request.POST.get('action')

            if action == 'approve':
                order_item.status = 'return_approved'
                order_item.save()

                
                product_variant = order_item.product_variant
                product_variant.stock += order_item.quantity
                product_variant.save()

               
                
                order = order_item.order
                total_items = order.items.count()

                
                per_item_discount = Decimal(str(order.discount)) / Decimal(str(total_items))

                
                item_total = Decimal(str(order_item.price)) * Decimal(str(order_item.quantity))
                
                refund_amount = item_total - per_item_discount

                
                wallet, created = Wallet.objects.get_or_create(
                    user=order_item.order.user,
                    defaults={'balance': Decimal('0.00')}
                )

                wallet.balance += refund_amount
                wallet.save()

               
                WalletTransaction.objects.create(
                    wallet=wallet,
                    type='credit',
                    amount=refund_amount,
                    product=order_item.product_variant.product,
                    order=order_item.order
                )

                messages.success(request, f'Return request approved for {order_item.product_variant.product.name}')

            elif action == 'reject':
                order_item.status = 'return_rejected'
                order_item.save()
                messages.success(request, f'Return request rejected for {order_item.product_variant.product.name}')
            
        return redirect('orderrequests')

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
            product_id = request.POST.get('product')
            valid_from = make_aware(
                datetime.strptime(request.POST.get('valid_from'), '%Y-%m-%dT%H:%M')
            )
            valid_until = make_aware(
                datetime.strptime(request.POST.get('valid_until'), '%Y-%m-%dT%H:%M')
            )

           
            if not name or len(name.strip()) < 3:
                messages.error(request, "Offer name must be at least 3 characters long")
                return redirect('productoffer')
            if len(name) > 20:
                messages.error(request, "Offer name cannot exceed 20 characters")
                return redirect('productoffer')
            
            if valid_until <= valid_from:
                messages.error(request, "Valid Until date must be after Valid From date")
                return redirect('productoffer')

           
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
            product_id = request.POST.get('product')
            
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
            
            if offer.valid_until <= offer.valid_from:
                messages.error(request, "Valid Until date must be after Valid From date")
                return redirect('productoffer')
            
            
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
            category_id = request.POST.get('category') 
            
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

