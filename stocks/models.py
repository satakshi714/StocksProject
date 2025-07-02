from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Stocks(models.Model):
    ticker   =  models.CharField(max_length=10)
    name =  models.CharField(max_length=300)
    description  =  models.CharField(max_length =5000)
    curr_price =  models.FloatField()

    def __str__(self):
        return  self.name

class UserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length = 15)
    address = models.CharField(max_length = 500)
    pancard_number = models.CharField(max_length = 30)
    user_image = models.ImageField()
    pancard_image = models.ImageField()

