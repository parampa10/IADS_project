from django.contrib import admin

from login.models import Purchase, Transaction, UserDetails,CryptoCurrency, Wallet

# Register your models here.
admin.site.register(UserDetails)
admin.site.register(CryptoCurrency)
admin.site.register(Wallet)
admin.site.register(Transaction)
admin.site.register(Purchase)
