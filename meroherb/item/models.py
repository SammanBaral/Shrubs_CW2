from django.contrib.auth.models import User
from django.db import models
from django.db.models import Avg


class Category(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        ordering =('name',)
        verbose_name_plural='Categories'

    def __str__(self):
        return self.name

class Item(models.Model):
    category = models.ForeignKey(Category, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    scientific_name = models.CharField(max_length=255, default='')
    description = models.TextField(blank=True, null=True)
    usage_and_benefits = models.TextField(default='', blank=False, null=False)
    price = models.FloatField(max_length=255)
    quantity_available = models.CharField(max_length=255)
    image = models.ImageField(upload_to='item_images', blank=True, null=True)
    is_sold = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='items', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # New field for discount
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)





    def calculate_discounted_price(self):
        try:
            price = float(self.price)
            discount = float(self.discount)
            discounted_price = round(price - (price * (discount / 100)), 2)
            self.discounted_price = discounted_price
            self.save()  # Save the discounted price to the database
        except (ValueError, TypeError):
            self.discounted_price = None  # Handle cases where price or discount is not a valid number
            self.save()
        
    def average_rating(self):
        avg_rating = review.objects.filter(item=self).aggregate(avg_rating=Avg('rating'))
        return avg_rating['avg_rating'] if avg_rating['avg_rating'] else 0
    def __str__(self):
        return self.name
    

class ItemImage(models.Model):
    item=models.ForeignKey(Item, on_delete=models.CASCADE)
    image=models.ImageField(upload_to='item_images/' , null=True,blank=True)

    def __str__(self):
        return self.item.name

class ItemImageGallery(models.Model):
    item = models.OneToOneField(Item, on_delete=models.CASCADE)
    images = models.ManyToManyField(ItemImage)

    def __str__(self):
        return f"{self.item.name} - Image Gallery"

class  review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    rating = models.IntegerField()


class Bill(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True)
    quantity = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    bill_no = models.AutoField(primary_key=True)  # Add bill_no field
    seller = models.CharField(max_length=100, null=True)  # Add seller field
    issued_date_time = models.DateTimeField(auto_now=True)  # Add issued_date_time field
    discount_per = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # New field for discount
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    delivery=models.CharField(max_length=100, null=True)
    contact_info = models.CharField(max_length=15, null= True, blank=True)
    pdf = models.FileField(upload_to='bill_pdfs/', blank=True, null=True)


    def __str__(self):
        return f'{self.customer.username} - {self.item.name}'