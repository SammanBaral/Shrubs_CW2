from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .decorators import allowed_users
from .forms import NewItemForm, EditItemForm, BillForm
from .models import Category, Item, review,ItemImage, Bill
from .models import ItemImageGallery, ItemImage
from core.models import AuditLog
from django.db import IntegrityError
from decimal import Decimal
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa  
from django.views import View
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from io import BytesIO

def is_valid_queryparam(param):
    return param != '' and param is not None and param !=0.0   #for price

def browse(request): 
   
    query = request.GET.get('query', '')
    error_message = None
    # XSS protection for query
    try:
        from userprofile.views import validate_backend_input, sanitize_backend_input
        if query:
            validate_backend_input(query)
            query = sanitize_backend_input(query)
    except Exception as e:
        error_message = 'Invalid or potentially dangerous search input. Please use safe characters.'
        query = ''
    category_id = request.GET.get('category', 0)
    categories = Category.objects.all()
    items = Item.objects.filter(is_sold=False)
    price_min = request.GET.get('input-min', 0)
    price_max = request.GET.get('input-max', 0)

    # error_message is now set above for XSS or below for invalid filters
    # Validate category_id is an integer
    invalid_sql_input = False
    try:
        category_id = int(category_id)
    except (ValueError, TypeError):
        category_id = 0
        error_message = "Invalid or potentially dangerous category filter. Please use a valid category."
        invalid_sql_input = True

    # Validate price_min and price_max are floats
    try:
        price_min = float(price_min)
    except (ValueError, TypeError):
        price_min = 0.0
        error_message = "Invalid or potentially dangerous minimum price filter. Please use a valid number."
        invalid_sql_input = True
    try:
        price_max = float(price_max)
    except (ValueError, TypeError):
        price_max = 0.0
        error_message = "Invalid or potentially dangerous maximum price filter. Please use a valid number."
        invalid_sql_input = True
    for product in items:
            if product.discount > 0:
                print("discount")
                discounted_price = Decimal(product.price) * (1 - Decimal(product.discount) / 100)
                product.discounted_price = discounted_price
                print(discounted_price)
    
    
    items_with_images = []
    for product in items:
        item_image_gallery = ItemImageGallery.objects.filter(item=product).first()
        product_data = {
            'product': product,
            'image_url': item_image_gallery.images.first().image.url if item_image_gallery and item_image_gallery.images.exists() else None,
        }
        items_with_images.append(product_data)
   
    

    if invalid_sql_input:
        items_with_images = []
    elif category_id:
        items = items.filter(category_id=category_id)
        for item in items:
            if item.discount > 0:
                discounted_price = Decimal(item.price) * (1 - Decimal(item.discount) / 100)
                item.discounted_price = discounted_price
        items_with_images = []
        for product in items:
            item_image_gallery = ItemImageGallery.objects.filter(item=product).first()
            product_data = {
                'product': product,
                'image_url': item_image_gallery.images.first().image.url if item_image_gallery and item_image_gallery.images.exists() else None,
            }
            items_with_images.append(product_data)
    elif query:
        items = items.filter(name__icontains=query)
        items_with_images = []
        for product in items:
            item_image_gallery = ItemImageGallery.objects.filter(item=product).first()
            product_data = {
                'product': product,
                'image_url': item_image_gallery.images.first().image.url if item_image_gallery and item_image_gallery.images.exists() else None,
            }
            items_with_images.append(product_data)
    elif is_valid_queryparam(price_min) and is_valid_queryparam(price_max):
        items = Item.objects.filter(price__range=(price_min, price_max))
        items_with_images = []
        for product in items:
            item_image_gallery = ItemImageGallery.objects.filter(item=product).first()
            product_data = {
                'product': product,
                'image_url': item_image_gallery.images.first().image.url if item_image_gallery and item_image_gallery.images.exists() else None,
            }
            items_with_images.append(product_data)

    return render(request,'item/browse.html',{
        'items_with_images': items_with_images,
        'query': query,
        'categories': categories,
        'error_message': error_message,
    })

from django.shortcuts import redirect

def detail(request, pk):
    item = get_object_or_404(Item, pk=pk)
    
    if(item.discount > 0):
                discounted_price = Decimal(item.price) * (1 - Decimal(item.discount) / 100)
                item.discounted_price=discounted_price
                print(discounted_price)
    reviews = review.objects.filter(item=item)
    item_image_gallery = ItemImageGallery.objects.filter(item=item).first()

    if request.method == 'POST':
        star_rating = request.POST.get('rating')
        try:
            review.objects.create(user=request.user, item=item, rating=star_rating)
        except IntegrityError:
            messages.error(request, "Please fill all the fields")
        else:
            # Redirect to the same detail page after successful review submission so that the user should not resubmit data on reload
            return redirect('item:detail', pk=pk)

    return render(request, 'item/detail.html', {
        'item': item,
        'reviews': reviews,
        'item_image_gallery': item_image_gallery,
    })


@login_required
@allowed_users(allowed_roles=['seller'])
def new(request):
    if request.method == 'POST':
        form = NewItemForm(request.POST)
        image_files = request.FILES.getlist("images")

        if form.is_valid():
            if len(image_files) > 3:
                messages.error(request, "You can upload a maximum of 3 images.")
                return render(request, 'item/form.html', {
                'form': form,
                'title': 'New item',}
                )
            
            item = form.save(commit=False)
            item.created_by = request.user
            item.save()

            # Create an ItemImageGallery instance and associate it with the Item
            item_image_gallery = ItemImageGallery.objects.create(item=item)

            # Add each image to the ItemImageGallery
            for image_file in image_files:
                item_image = ItemImage.objects.create(item=item, image=image_file)
                item_image_gallery.images.add(item_image)

            # Audit log for product creation
            AuditLog.objects.create(
                user=request.user,
                user_role=getattr(request.user, 'role', 'seller'),
                action='CREATE_PRODUCT',
                entity='Product',
                entity_id=str(item.id),
                old_value=None,
                new_value={
                    'name': item.name,
                    'price': str(item.price),
                    'category': str(item.category),
                    'created_by': str(item.created_by)
                },
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )

            messages.success(request, "New item created")
            return redirect('item:detail', pk=item.id)
    else:
        form = NewItemForm()

    return render(request, 'item/form.html', {
        'form': form,
        'title': 'New item',
    })


@login_required
def delete(request, pk):
    item = get_object_or_404(Item, pk= pk, created_by=request.user)
    # Audit log for product delete
    AuditLog.objects.create(
        user=request.user,
        user_role=getattr(request.user, 'role', 'seller'),
        action='DELETE_PRODUCT',
        entity='Product',
        entity_id=str(item.id),
        old_value={
            'name': item.name,
            'price': str(item.price),
            'category': str(item.category),
            'created_by': str(item.created_by)
        },
        new_value=None,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    item.delete()
    return redirect('item:browse')


@login_required
def edit(request, pk):
    item = get_object_or_404(Item, pk=pk, created_by=request.user)
    item_image_gallery, created = ItemImageGallery.objects.get_or_create(item=item)

    if request.method == 'POST':
        form = EditItemForm(request.POST, instance=item)
        image_files = request.FILES.getlist("images")

        if form.is_valid():
            if len(image_files) > 3:
                messages.error(request, "You can upload a maximum of 3 images.")
                return render(request, 'item/form.html', {
                'form': form,
                'title': 'New item',}
                )

            old_item = {
                'name': item.name,
                'price': str(item.price),
                'category': str(item.category),
                'created_by': str(item.created_by)
            }
            form.save()

            # Clear existing images from the gallery
            item_image_gallery.images.clear()

            # Add new images to the gallery
            for image_file in image_files:
                item_image = ItemImage.objects.create(item=item, image=image_file)
                item_image_gallery.images.add(item_image)

            # Audit log for product update
            AuditLog.objects.create(
                user=request.user,
                user_role=getattr(request.user, 'role', 'seller'),
                action='UPDATE_PRODUCT',
                entity='Product',
                entity_id=str(item.id),
                old_value=old_item,
                new_value={
                    'name': item.name,
                    'price': str(item.price),
                    'category': str(item.category),
                    'created_by': str(item.created_by)
                },
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )

            messages.success(request, "Item updated successfully")
            return redirect('item:detail', pk=item.id)
    else:
        form = EditItemForm(instance=item)

    return render(request, 'item/form.html', {
        'form': form,
        'title': 'Edit item',
    })





def Category_view(request,pro):
    from django.shortcuts import get_object_or_404
    category = get_object_or_404(Category, name=pro)
    products = Item.objects.filter(category=category)

    items_with_images = []
    for product in products:
        item_image_gallery = ItemImageGallery.objects.filter(item=product).first()
        product_data = {
            'product': product,
            'image_url': item_image_gallery.images.first().image.url if item_image_gallery and item_image_gallery.images.exists() else None,
        }
        items_with_images.append(product_data)

    return render(request,'item/browse.html',{'items_with_images':items_with_images,'category':category})


# def buy_item(request, pk):
#     item = get_object_or_404(Item, pk=pk)
    
#     if request.method == 'POST':
#         # Assuming you have a button in your buy_item.html that posts to generate_pdf
#         form = BillForm(request.POST)
#         if form.is_valid():
#             # Create a Bill instance based on the data from Item and the form
#             bill = Bill.objects.create(
#                 customer_name=form.cleaned_data['customer_name'],
#                 item_name=item.name,
#                 quantity=form.cleaned_data['quantity'],
#                 total_amount=form.cleaned_data['total_amount'],
#             )

#             return render(request, 'buy_item.html', {'item': item, 'bill': bill})

#     # Render the buy_item template initially
#     form = BillForm()
#     return render(request, 'buy_item.html', {'form': form, 'item': item})
# def generate_unique_bill_no():
#     timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")  # Use the current timestamp
#     last_serial_number = Bill.objects.latest('id').id if Bill.objects.exists() else 0
#     serial_number = last_serial_number + 1
#     return f"BILL{serial_number}_{timestamp}"


def buy_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    discounted_price = 0
    if item.discount > 0:
        discounted_price = Decimal(item.price) * (1 - Decimal(item.discount) / 100)
        item.discounted_price = discounted_price
        print(discounted_price)

    if request.method == 'POST':
        bill = Bill.objects.create(
            customer=request.user,
            item=item,
            quantity=item.quantity_available,
            total_amount=item.price,
            seller=item.created_by.username,
            discount_per=item.discount,
            discount_price=discounted_price,
            delivery=request.user.userprofile.location,
            contact_info = request.user.userprofile.contact_number
        )

        generated_bill_no = bill.bill_no
        bill.save()
        # Audit log for order placement
        from core.models import AuditLog
        AuditLog.objects.create(
            user=request.user,
            user_role='admin' if request.user.is_superuser else 'customer',
            action='PLACE_ORDER',
            entity='Bill',
            entity_id=str(bill.bill_no),
            old_value=None,
            new_value={
                'item': str(item),
                'quantity': item.quantity_available,
                'total_amount': str(item.price),
                'seller': item.created_by.username,
                'discount_per': str(item.discount),
                'discount_price': str(discounted_price),
                'delivery': request.user.userprofile.location,
                'contact_info': request.user.userprofile.contact_number
            },
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )
        # Do NOT generate PDF or send email yet. Show Khalti payment option.
        # Render buy_item.html with bill info and Khalti payment button
        return render(request, 'item/buy_item.html', {'item': item, 'bill': bill, 'generated_bill_no': generated_bill_no, 'show_khalti': True})

    # Render the buy_item template initially
    return render(request, 'item/buy_item.html', {'item': item})



class GeneratePDF(View):
    def get(self, request, bill_no, *args, **kwargs):
        bill = get_object_or_404(Bill, bill_no=bill_no)
        template = get_template('item/bill_template.html')
        html = template.render({'bill': bill})
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'filename=bill_{bill.bill_no}.pdf'
        
        pisa_status = pisa.CreatePDF(html, dest=response)
        
        if pisa_status.err:
            return HttpResponse('Error while generating PDF', status=500)
        
        return response

    def post(self, request, bill_no, *args, **kwargs):
        # Retrieve the bill object
        bill = get_object_or_404(Bill,  bill_no=bill_no)

        # Handle POST request logic here
        # You can access form data using `request.POST`
        # Generate PDF or perform any other necessary actions

        # Example: Generating a PDF response
        template = get_template('item/bill_template.html')
        html = template.render({'bill': bill})

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'filename=bill_{bill.bill_no}.pdf'

        pisa_status = pisa.CreatePDF(html, dest=response)

        if pisa_status.err:
            return HttpResponse('Error while generating PDF', status=500)

        return response
