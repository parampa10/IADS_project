from django.contrib import admin

from login.models import UserDetails,CryptoCurrency

# Register your models here.
admin.site.register(UserDetails)
admin.site.register(CryptoCurrency)