from django.shortcuts import render
from login.models import UserDetails, CryptoCurrency
from django.db.models import F, Func
# Create your views here.
def index(request):
    coin_list = CryptoCurrency.objects.all().order_by('market_cap_rank')[:20]
    # print("user details are: ", user)
    top_list = CryptoCurrency.objects.all().order_by('-current_price')[:3]
    
    top_change_list = CryptoCurrency.objects.annotate(abs_price_change=Func(F('price_change_percentage_24h'), function='ABS')).order_by('-abs_price_change')[:3]


    top_market_cap_list=CryptoCurrency.objects.all().order_by('market_cap_rank')[:3]

    return render(request,'index.html',{'coins':coin_list,'top_list':top_list,"top_change_list":top_change_list,"top_market_cap_list":top_market_cap_list})