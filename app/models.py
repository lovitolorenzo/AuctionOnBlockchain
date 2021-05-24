from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
# Create your models here.

def one_day_hence():
    return timezone.now() + timezone.timedelta(days=1)


class Product(models.Model):
    name = models.CharField(max_length=200, null=True)
    base_price = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    digital = models.BooleanField(default=False, null=True, blank=True)
    start_date = models.DateTimeField(default=timezone.now(), blank=True, null=True)
    end_date = models.DateTimeField(default=one_day_hence(), blank=True, null=True)
    bidding_finished = models.BooleanField(default=False)
    image = models.ImageField(null=True, blank=True, upload_to="postpics/", default="/default.png")

    def __str__(self):
        return self.name

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url

class ClosedAuction(models.Model):
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    winner_price = models.FloatField(null=True)
    total_bidders = models.IntegerField(null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True)
    hash = models.CharField(max_length=200, null=True, unique=True)

    def __str__(self):
        return str(self.hash)

'''    @property
    def shipping(self):
        shipping = False
        orderitems = self.orderitem_set.all()
        for i in orderitems:
            if i.product.digital == False:
                shipping = True
        return shipping

    @property
    def get_cart_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total for item in orderitems])
        return total

    @property
    def get_cart_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total

class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True)
    order = models.ForeignKey(ClosedAuction, on_delete=models.SET_NULL, blank=True, null=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    @property
    def get_total(self):
        total = self.product.price * self.quantity
        return total

class ShippingAddress(models.Model):
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    order = models.ForeignKey(ClosedAuction, on_delete=models.SET_NULL, blank=True, null=True)
    address = models.CharField(max_length=200, null=True)
    city = models.CharField(max_length=200, null=True)
    state = models.CharField(max_length=200, null=True)
    zipcode = models.CharField(max_length=200, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address'''