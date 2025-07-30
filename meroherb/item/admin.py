from django.contrib import admin

from .models import Category, Item,review,ItemImage,ItemImageGallery, Bill

admin.site.register(Category)
admin.site.register(Item)
admin.site.register(review)
admin.site.register(ItemImage)
admin.site.register(ItemImageGallery)


admin.site.register(Bill)
