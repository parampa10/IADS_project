from decimal import Decimal
import json
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from login.forms import AddMoneyForm, LoginForm, PurchaseForm, RegisterForm, UserProfileForm, sellform
from login.models import Purchase, Transaction, UserDetails, CryptoCurrency, Wallet
from django.contrib.auth.hashers import check_password,make_password

# Create your views here.
def login(request):
    if request.session.get('_user_id'):
        return HttpResponseRedirect(reverse('index'))
    if request.method == 'POST':
        
        form = LoginForm(request.POST)
        
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            try:
                user = UserDetails.objects.get(username=username)
                print("user details are:", user.password)
                if password == user.password:
                    # Manually set the user's ID in the session to log them in
                    request.session['_user_id'] = user.id
                    print("#######################")
                    print(request.session['_user_id'])
                    return redirect('index')
                    # # Redirect to the user's profile page
                    # return HttpResponseRedirect(reverse('CryptoCrackers:profile'))
                else:
                    form.add_error(None, 'Invalid login credentials')
                    return render(request,'login.html',{'form':form})
            except UserDetails.DoesNotExist:
                form.add_error(None, 'User does not exist')
                return render(request, 'login.html', {'form': form})
    else:
        # print(user.username)
        form = LoginForm()
        return render(request,'login.html',{'form':form})

def signup(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = form.cleaned_data['password']
            user.save()
            return redirect('/login/login')
        else:
            print("wrong")
    else:#get request
        form = RegisterForm()
        return render(request,'signup.html',{'form':form})

def user_logout(request):
    request.session.delete()
    request.session.flush()
    # messages.success(request,("You Were Logged Out Successfully!"))
    return redirect('index')


def wallet(request):

    user_id = request.session.get('_user_id')
    if not user_id:
        # Redirect to login or handle the case where the user is not authenticated
        return redirect('/login/login')

    user_wallet, created = Wallet.objects.get_or_create(user_id=user_id)
    

    if request.method == "POST":
        
        form = AddMoneyForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            

            user_wallet.balance += amount
            user_wallet.save()

            Transaction.objects.create(
                user_id=user_id,
                amount=amount,
            )
            msg="Money added successfully."
            
            form = AddMoneyForm()
            return render(request, 'wallet.html',{'form': form, 'balance': user_wallet.balance,'UserDetails':user_wallet.user, "msg":msg})

        else:
            # Render the HTML with an error message
            msg="Error adding money in wallet."
            
            form = AddMoneyForm()
            return render(request, 'wallet.html',
                          {'form': form, 'balance': user_wallet.balance,'UserDetails':user_wallet.user, "msg":msg})
    else:
        
        form = AddMoneyForm()
    
        return render(request, 'wallet.html',{'form': form,'UserDetails':user_wallet.user,'balance':user_wallet.balance})

def buy(request):
    user_id = request.session.get('_user_id')
    if not user_id:
        # Redirect to login or handle the case where the user is not authenticated
        return redirect('/login/login')

    user_wallet, created = Wallet.objects.get_or_create(user_id=user_id)

    if request.method == 'POST':
        form = PurchaseForm(user_id, request.POST)

        if form.is_valid():
            cryptocurrency = form.cleaned_data['cryptocurrency']
            quantity = form.cleaned_data['quantity']
            total_amount = cryptocurrency.current_price_cad * quantity

            if user_wallet.balance >= total_amount:
                user_wallet.balance -= total_amount

                Purchase.objects.create(
                    user_id=user_id,
                    cryptocurrency=cryptocurrency,
                    quantity=quantity,
                    total_amount=total_amount,
                    type="buy"
                )
                user = UserDetails.objects.get(id=user_id)

                # Get the current cryptocurrencies of the user
                cryptocurrencies = user.cryptocurrencies

                # If the user has already bought this cryptocurrency, add the quantity to the existing quantity
                if cryptocurrency.name in cryptocurrencies:
                    cryptocurrencies[cryptocurrency.name] += int(quantity)
                else:
                    # If the user has not bought this cryptocurrency before, add it to the dictionary
                    cryptocurrencies[cryptocurrency.name] = int(quantity)

                # Save the updated cryptocurrencies dictionary
                user.cryptocurrencies = cryptocurrencies
                user_wallet.save()
                user.save()
                msg="Coin Bought!"
                return render(request, 'buy.html',
                      {'form': form, 'balance': user_wallet.balance,'id': "purchase-currency", "user": user,
                       'UserDetails':user_wallet.user,'total_amount': total_amount,'msg':msg})
                
            else:
                return JsonResponse({'success': False, 'error': 'Insufficient balance'})
        else:
            # Form is not valid, return JsonResponse with error details
            return JsonResponse({'success': False, 'error': 'Invalid form data'})

    else:
        form = PurchaseForm(user_id)

        # Fetch the cryptocurrency choices and pass them to the template as a JSON string
        crypto_choices = [{'id': crypto.id, 'name': crypto.name, 'price': str(crypto.current_price_cad)} for crypto in
                        CryptoCurrency.objects.all()]
        crypto_choices_json = json.dumps(crypto_choices, cls=DjangoJSONEncoder)

        user = UserDetails.objects.get(pk=user_id)
        return render(request, 'buy.html',
                      {'form': form, 'balance': user_wallet.balance, 'crypto_choices_json': crypto_choices_json,
                       'id': "purchase-currency", "user": user,'UserDetails':user_wallet.user})
    

def sell(request):
    user_id = request.session.get('_user_id')
    if not user_id:
        return redirect('/login/login')

    user_wallet, created = Wallet.objects.get_or_create(user_id=user_id)

    if request.method == "POST":
        form = sellform(user_id, request.POST)
        if form.is_valid():
            cryptocurrency = request.POST['cryptocurrencies']
            quantity = request.POST['sell_quantity']
            cryptmod = CryptoCurrency.objects.get(name=cryptocurrency)
            total_amount = cryptmod.current_price_cad * Decimal(quantity)
            user = UserDetails.objects.get(id=user_id)

            # Get the current cryptocurrencies of the user
            cryptocurrencies = user.cryptocurrencies
            print(type(cryptocurrencies[cryptocurrency]))

            if int(quantity) <= int(cryptocurrencies[cryptocurrency]):
                user_wallet.balance += total_amount
                # print(user_wallet.balance)
                cryptocurrencies[cryptocurrency] = int(cryptocurrencies[cryptocurrency]) - int(quantity)
                if int(cryptocurrencies[cryptocurrency]) <= 0:
                    del cryptocurrencies[cryptocurrency]

                user.cryptocurrencies = cryptocurrencies
                
                # print(user.cryptocurrencies)
                user_wallet.save()
                user.save()

                Purchase.objects.create(
                    user_id=user_id,
                    cryptocurrency=cryptmod,
                    quantity=quantity,
                    total_amount=total_amount,
                    type="sell"
                )

                msg="Coin Sold"
                return render(request, 'sell.html', {'msg_success':msg,"user": user, 'form':form ,  'id': "sell"})
            else:
                msg="Enter Proper Quantity"
                return render(request, 'sell.html', {'msg_fail':msg,"user": user, 'form':form ,  'id': "sell"})

        else:
            return redirect('index')
    else:
        form = sellform(user_id)
        user = UserDetails.objects.get(pk=user_id)
        crypto_choices = [{'id': crypto.id, 'name': crypto.name, 'price': str(crypto.current_price_cad)} for crypto in
                          CryptoCurrency.objects.all()]
        crypto_choices_json = json.dumps(crypto_choices, cls=DjangoJSONEncoder)




        return render(request, 'sell.html', {'UserDetails':user_wallet.user,'crypto_choices_json': crypto_choices_json,"user": user, 'form':form ,  'id': "sell"})


def history(request):
    
    user_id = request.session.get('_user_id')
    # Check if the user ID is present in the session
    if user_id:
        # Retrieve the user based on the user ID
        user = UserDetails.objects.get(pk=user_id)

        # Filter transactions for the current user
        history = Purchase.objects.filter(user=user).order_by('-timestamp')
    
        return render(request, 'payment_history.html', {'history': history, "id": "purchase-history"})
    else:
        msg="Please Login in First!"
        # Handle the case when the user ID is not present in the session (you can redirect to a login page or display an error message)
        return render(request, 'login.html',{'msg':msg})

def mycoins(request):

    user_id = request.session.get('_user_id')
    if not user_id:
        return redirect('/login/')

    user_wallet, created = Wallet.objects.get_or_create(user_id=user_id)

    if request.method == "POST":
        pass
    else:
        user = UserDetails.objects.get(pk=user_id)
        crypto_choices = [{'id': crypto.id, 'name': crypto.name, 'price': str(crypto.current_price_cad)} for crypto in
                          CryptoCurrency.objects.all()]
        crypto_choices_json = json.dumps(crypto_choices, cls=DjangoJSONEncoder)

        coins_list=user.cryptocurrencies.items()

        

        return render(request, 'mycoins.html', {'crypto_choices_json': crypto_choices_json,'coins_list':coins_list,"user": user,'id': "sell",'UserDetails':user_wallet.user})

        

def user_profile(request):
    user_id = request.session.get('_user_id')
    # Get user details from the retrieved user id
    user = UserDetails.objects.get(id=user_id)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            # Process the form data
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.username = form.cleaned_data['username']


            if 'id_image' in request.FILES:
                user.id_image = request.FILES['id_image']
            # if len(request.FILES) != 0:
            #     user.id_image = request.FILES['id_image']

            user.save()

            return redirect('/login/userprofile/')  # Redirect to the user's profile page
    else:
        # Populate the form with the user's current profile information
        form = UserProfileForm(instance=user)

    return render(request, 'profile.html', {'form': form, 'id': "profile-details", 'user': user})