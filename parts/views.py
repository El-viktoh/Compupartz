from django.shortcuts import render
from store.models import Product

def parts_home(request):
    parts = Product.objects.filter(category='part', available=True)
    return render(request, 'parts/parts_home.html', {'parts': parts})
