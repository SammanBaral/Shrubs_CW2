from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .decorators import allowed_users
from .forms import NewItemForm, EditItemForm, BillForm
from .models import Category, Item, review,ItemImage, Bill
from .models import ItemImageGallery, ItemImage
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
    category_id= request.GET.get('category', 0)
    categories=Category.objects.all()
    items = Item.objects.filter(is_sold=False)
    price_min=request.GET.get('input-min',0)
    price_max=request.GET.get('input-max',0)
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
   
    
    if category_id:
        items=items.filter(category_id=category_id)

        for item in items:
            if(item.discount > 0):
                discounted_price = Decimal(product.price) * (1 - Decimal(product.discount) / 100)
                item.discounted_price=discounted_price

       
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
        items = Item.objects.filter(price__range=(float(price_min),float(price_max)))
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

            form.save()

            # Clear existing images from the gallery
            item_image_gallery.images.clear()

            # Add new images to the gallery
            for image_file in image_files:
                item_image = ItemImage.objects.create(item=item, image=image_file)
                item_image_gallery.images.add(item_image)

            messages.success(request, "Item updated successfully")
            return redirect('item:detail', pk=item.id)
    else:
        form = EditItemForm(instance=item)

    return render(request, 'item/form.html', {
        'form': form,
        'title': 'Edit item',
    })





def Category_view(request,pro):
    category=Category.objects.get(name=pro)
    products=Item.objects.filter(category=category)

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
        # Send email to the seller
        template = get_template('item/bill_template.html')
        html = template.render({'bill': bill})
        
        pdf_content = ContentFile(pisa.pisaDocument(BytesIO(html.encode('UTF-8'))).dest.getvalue())
        bill.pdf.save(f'bill_{generated_bill_no}.pdf', pdf_content)

        # Send email to the seller with the attached PDF
        seller_email = item.created_by.email
        subject = f'New Bill for Item: {item.name}'
        message = 'Please deliver the Item as soon as possible'  # You can customize this message
        email = EmailMessage(subject, message, 'meroherbs0@gmail.com', [seller_email])
        email.attach_file(bill.pdf.path)  # Attach the generated PDF
        email.send()

        return render(request, 'item/buy_item.html', {'item': item, 'bill': bill, 'generated_bill_no': generated_bill_no})

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
