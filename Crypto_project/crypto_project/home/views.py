from django.shortcuts import render, redirect, get_object_or_404
from login.models import UserDetails, CryptoCurrency
from django.db.models import F, Func
# Create your views here.
def index(request):
    coin_list = CryptoCurrency.objects.all().order_by('market_cap_rank')[:20]
    # print("user details are: ", user)
    top_list = CryptoCurrency.objects.all().order_by('-current_price')[:3]
    
    top_change_list = CryptoCurrency.objects.annotate(abs_price_change=Func(F('price_change_percentage_24h'), function='ABS')).order_by('-abs_price_change')[:3]


    top_market_cap_list=CryptoCurrency.objects.all().order_by('market_cap_rank')[:3]
    a = False
    value = request.session.get('_user_id')
    wish_list = []
    user = None
    user_log = False
    my_var = request.session.get('_user_id')
    if "_user_id" in request.session :
        user_log = True
        id_value=request.session['_user_id']
        user = UserDetails.objects.get(id=id_value)
        wish_list = user.wishlist
    else:
        user_log = False
    return render(request,'index.html',{'user':user,'coins':coin_list,'top_list':top_list,"top_change_list":top_change_list,"top_market_cap_list":top_market_cap_list,'wish_list': wish_list,'user_log': user_log})