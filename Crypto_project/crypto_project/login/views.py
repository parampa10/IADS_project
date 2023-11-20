from django.shortcuts import redirect, render

from login.forms import LoginForm, RegisterForm
from login.models import UserDetails, CryptoCurrency
from django.contrib.auth.hashers import check_password,make_password

# Create your views here.
def login(request):
    
    if request.method == 'POST':
        
        form = LoginForm(request.POST)
        
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            try:
                user = UserDetails.objects.get(username=username)
                print("user details are:", user.password)
                if user:
                    if user.password is None:
                        form.add_error(None, 'Google Auth Sign In Required')
                    else:
                        if password == user.password:
                            # Manually set the user's ID in the session to log them in
                            request.session['_user_id'] = user.id

                            return redirect('index')
                            # # Redirect to the user's profile page
                            # return HttpResponseRedirect(reverse('CryptoCrackers:profile'))
                        else:
                            form.add_error(None, 'Invalid login credentials')

            except UserDetails.DoesNotExist:
                form.add_error(None, 'User does not exist')
    else:
        # print("1")
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