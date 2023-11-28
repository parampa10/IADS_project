from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse

from login.forms import LoginForm, RegisterForm, UserProfileForm
from login.models import UserDetails, CryptoCurrency
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
    else:
        form = RegisterForm()
        return render(request,'signup.html',{'form':form})

def user_logout(request):
    request.session.delete()
    # messages.success(request,("You Were Logged Out Successfully!"))
    return redirect('index')

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

            return redirect('/userprofile/')  # Redirect to the user's profile page
    else:
        # Populate the form with the user's current profile information
        form = UserProfileForm(instance=user)

    return render(request, 'profile', {'form': form, 'id': "profile-details", 'user': user})