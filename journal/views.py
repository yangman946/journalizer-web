from django.shortcuts import render

# Create your views here.
def home(request):
    context = {
        'title': 'Secure Journal',
        'message': 'Welcome to your journal.',
    }

    return render(request, 'journal/home.html', context)