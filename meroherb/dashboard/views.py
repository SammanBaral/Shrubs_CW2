from django.shortcuts import get_object_or_404, render
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib.auth.models import User,Group
from item.models import Item, ItemImageGallery
from .models import Comment
from django.db.models import Avg
from item.models import Item
from userprofile.models import UserProfile




# Create your views here.

    

def dashboardView(request):
    items=Item.objects.all()

    return render(request,'dashboard/dashboard.html',{'items':items})

def logout_view(request):
    logout(request)
    return redirect ("core:login")
def sellerprofile(request, pk):
    seller_info = get_object_or_404(User, pk=pk)
    comments = Comment.objects.filter(seller=seller_info)
    average_rating = comments.aggregate(Avg('rating'))['rating__avg'] or 0
    seller_items=Item.objects.filter(created_by=pk)

    items_with_images = []
    for product in seller_items:
        item_image_gallery = ItemImageGallery.objects.filter(item=product).first()
        product_data = {
            'product': product,
            'image_url': item_image_gallery.images.first().image.url if item_image_gallery and item_image_gallery.images.exists() else None,
        }
        items_with_images.append(product_data)


 
    if request.method == 'POST':
        star_rating = request.POST.get('rating')
        seller_review = request.POST.get('seller_review')
        Comment.objects.create(user=request.user, seller=seller_info, rating=star_rating, text=seller_review)
        return redirect('dashboard:sellerprofile', pk=pk)


    return render(request, 'dashboard/Profile.html', {
        'seller_info': seller_info,
        'comments':comments,
        'avg_rating':average_rating,
        'items_with_images':items_with_images,
    })
    


def home(request):
   
    return dashboardView(request)

def seller_verify(request):
    # group=None
    # seller_status=False
    # if request.user.groups.exists():
    #     group=request.users.groups.all()[0].name
    # print("hello")
    # if group=="seller":
    #     seller_status=True
    # is_seller=False

    # username = request.user.username
    # user = User.objects.get(username=username)
    # user_group=user.groups.all().name

    # seller_group, created = Group.objects.get_or_create(name='seller')

    # for group in user_group:
    #     if group==seller_group:
    #         is_seller=True

    # return render(request,'dashboard/navbar.html',{'is_seller':is_seller})
    username = request.user.username
    user = User.objects.get(username=username)
    is_seller = user.groups.filter(name='seller').exists()

    return render(request, 'dashboard/navbar.html', {'is_seller': is_seller})


