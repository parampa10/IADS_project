from django.shortcuts import render
from login.models import UserDetails, CryptoCurrency

# Create your views here.
def index(request):
    coin_list = CryptoCurrency.objects.all().order_by('market_cap_rank')[:20]
    # print("user details are: ", user)

    #print(coin_list)
    return render(request,'index.html',{'coins':coin_list})