from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def home(request):
    my_dict = {'test_data':'This is the home page of the project'}
    html = "<html><body>This is the home page of the project</body></html>"
    return HttpResponse(html)
