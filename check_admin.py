import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.admin.sites import site
from store.models import Product

admin_class = site._registry[Product]
print("Fields on Product edit form:")
print(admin_class.get_fields(None))
