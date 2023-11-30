# Import necessary modules and classes from Django and other dependencies
from decimal import Decimal
import json
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.core.serializers.json import DjangoJSONEncoder
from login.forms import AddMoneyForm, LoginForm, PurchaseForm, RegisterForm, UserProfileForm, sellform
from login.models import Purchase, Transaction, UserDetails, CryptoCurrency, Wallet
from django.contrib.auth.hashers import check_password, make_password


# Define Django views for the application

# View for user login
def login(request):
    # Check if the user is already authenticated
    if request.session.get('_user_id'):
        return HttpResponseRedirect(reverse('index'))

    # Process POST request for user login
    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                user = UserDetails.objects.get(username=username)
                # Check if the entered password matches the stored password
                if password == user.password:
                    # Manually set the user's ID in the session to log them in
                    request.session['_user_id'] = user.id
                    return redirect('index')  # Redirect to the user's profile page

                else:
                    # If the password is incorrect, add an error to the form
                    form.add_error(None, 'Invalid login credentials')
                    return render(request, 'login.html', {'form': form})
            except UserDetails.DoesNotExist:
                # If the user does not exist, add an error to the form
                form.add_error(None, 'User does not exist')
                return render(request, 'login.html', {'form': form})
    else:
        # Render the login form for GET requests
        form = LoginForm()
        return render(request, 'login.html', {'form': form})


# View for user registration
def signup(request):
    if request.method == 'POST':
        # Process POST request for user registration
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            # Create a new user and save the registration form data
            user = form.save(commit=False)
            user.password = form.cleaned_data['password']
            user.save()
            return redirect('/login/login')  # Redirect to the login page after successful registration
        else:
            print("wrong")  # Handle the case where registration fails
    else:
        # Render the registration form for GET requests
        form = RegisterForm()
        return render(request, 'signup.html', {'form': form})


# View for user logout
def user_logout(request):
    # Clear user session data on logout
    request.session.delete()
    request.session.flush()
    return redirect('index')  # Redirect to the home page


# View for user wallet
def wallet(request):
    # Check if the user is authenticated
    user_id = request.session.get('_user_id')
    if not user_id:
        return redirect('/login/login')  # Redirect to login if the user is not authenticated

    # Retrieve or create the user's wallet
    user_wallet, created = Wallet.objects.get_or_create(user_id=user_id)

    if request.method == "POST":
        # Process POST request to add money to the wallet
        form = AddMoneyForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            # Update the user's wallet balance
            user_wallet.balance += amount
            user_wallet.save()

            # Log the transaction
            Transaction.objects.create(user_id=user_id, amount=amount)

            msg = "Money added successfully."
            form = AddMoneyForm()
            return render(request, 'wallet.html',
                          {'form': form, 'balance': user_wallet.balance, 'UserDetails': user_wallet.user, "msg": msg})
        else:
            # Render the HTML with an error message if form is invalid
            msg = "Error adding money in wallet."
            form = AddMoneyForm()
            return render(request, 'wallet.html',
                          {'form': form, 'balance': user_wallet.balance, 'UserDetails': user_wallet.user, "msg": msg})
    else:
        # Render the wallet page for GET requests
        form = AddMoneyForm()
        return render(request, 'wallet.html',
                      {'form': form, 'UserDetails': user_wallet.user, 'balance': user_wallet.balance})


# View for purchasing cryptocurrency
def buy(request):
    user_id = request.session.get('_user_id')
    if not user_id:
        return redirect('/login/login')  # Redirect to login if the user is not authenticated

    user_wallet, created = Wallet.objects.get_or_create(user_id=user_id)

    if request.method == 'POST':
        # Process POST request for purchasing cryptocurrency
        form = PurchaseForm(user_id, request.POST)
        if form.is_valid():
            cryptocurrency = form.cleaned_data['cryptocurrency']
            quantity = form.cleaned_data['quantity']
            total_amount = cryptocurrency.current_price_cad * quantity

            if user_wallet.balance >= total_amount:
                user_wallet.balance -= total_amount

                # Log the purchase transaction
                Purchase.objects.create(user_id=user_id, cryptocurrency=cryptocurrency, quantity=quantity,
                                        total_amount=total_amount, type="buy")

                user = UserDetails.objects.get(id=user_id)

                # Update the user's cryptocurrency holdings
                cryptocurrencies = user.cryptocurrencies

                if cryptocurrency.name in cryptocurrencies:
                    cryptocurrencies[cryptocurrency.name] += int(quantity)
                else:
                    cryptocurrencies[cryptocurrency.name] = int(quantity)

                user.cryptocurrencies = cryptocurrencies
                user_wallet.save()
                user.save()
                msg = "Coin Bought!"
                return render(request, 'buy.html',
                              {'form': form, 'balance': user_wallet.balance, 'id': "purchase-currency", "user": user,
                               'UserDetails': user_wallet.user, 'total_amount': total_amount, 'msg': msg})
            else:
                return JsonResponse({'success': False, 'error': 'Insufficient balance'})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid form data'})
    else:
        # Render the purchase form for GET requests
        form = PurchaseForm(user_id)
        crypto_choices = [{'id': crypto.id, 'name': crypto.name, 'price': str(crypto.current_price_cad)} for crypto in
                          CryptoCurrency.objects.all()]
        crypto_choices_json = json.dumps(crypto_choices, cls=DjangoJSONEncoder)
        user = UserDetails.objects.get(pk=user_id)
        return render(request, 'buy.html',
                      {'form': form, 'balance': user_wallet.balance, 'crypto_choices_json': crypto_choices_json,
                       'id': "purchase-currency", "user": user, 'UserDetails': user_wallet.user})


# View for selling cryptocurrency
def sell(request):
    user_id = request.session.get('_user_id')
    if not user_id:
        return redirect('/login/login')  # Redirect to login if the user is not authenticated

    user_wallet, created = Wallet.objects.get_or_create(user_id=user_id)

    if request.method == "POST":
        # Process POST request for selling cryptocurrency
        form = sellform(user_id, request.POST)
        if form.is_valid():
            cryptocurrency = request.POST['cryptocurrencies']
            quantity = request.POST['sell_quantity']
            cryptmod = CryptoCurrency.objects.get(name=cryptocurrency)
            total_amount = cryptmod.current_price_cad * Decimal(quantity)
            user = UserDetails.objects.get(id=user_id)

            cryptocurrencies = user.cryptocurrencies

            if int(quantity) <= int(cryptocurrencies[cryptocurrency]):
                user_wallet.balance += total_amount
                cryptocurrencies[cryptocurrency] = int(cryptocurrencies[cryptocurrency]) - int(quantity)
                if int(cryptocurrencies[cryptocurrency]) <= 0:
                    del cryptocurrencies[cryptocurrency]

                user.cryptocurrencies = cryptocurrencies
                user_wallet.save()
                user.save()

                return JsonResponse({'success': True})
            else:
                msg = "Enter Proper Quantity"
                return render(request, 'sell.html', {'msg_fail': msg, "user": user, 'form': form, 'id': "sell"})
        else:
            return redirect('index')
    else:
        # Render the sell form for GET requests
        form = sellform(user_id)
        user = UserDetails.objects.get(pk=user_id)
        crypto_choices = [{'id': crypto.id, 'name': crypto.name, 'price': str(crypto.current_price_cad)} for crypto in
                          CryptoCurrency.objects.all()]
        crypto_choices_json = json.dumps(crypto_choices, cls=DjangoJSONEncoder)

        return render(request, 'sell.html',
                      {'UserDetails': user_wallet.user, 'crypto_choices_json': crypto_choices_json, "user": user,
                       'form': form, 'id': "sell"})


# View for transaction history
def history(request):
    user_id = request.session.get('_user_id')
    if user_id:
        user = UserDetails.objects.get(pk=user_id)
        history = Purchase.objects.filter(user=user).order_by('-timestamp')
        return render(request, 'payment_history.html', {'history': history, "id": "purchase-history"})
    else:
        msg = "Please Login in First!"
        return render(request, 'login.html', {'msg': msg})


# View for displaying user's cryptocurrency holdings
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
        coins_list = user.cryptocurrencies.items()

        return render(request, 'mycoins.html',
                      {'crypto_choices_json': crypto_choices_json, 'coins_list': coins_list, "user": user, 'id': "sell",
                       'UserDetails': user_wallet.user})


# View for user profile
def user_profile(request):
    user_id = request.session.get('_user_id')
    user = UserDetails.objects.get(id=user_id)

    if request.method == 'POST':
        # Process POST request for updating user profile
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            # Update user profile with the form data
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.username = form.cleaned_data['username']

            if 'id_image' in request.FILES:
                user.id_image = request.FILES['id_image']

            user.save()

            return redirect('/login/userprofile/')  # Redirect to the user's profile page
    else:
        # Render user profile form for GET requests
        form = UserProfileForm(instance=user)

    return render(request, 'profile.html', {'form': form, 'id': "profile-details", 'user': user})
