from django.contrib import admin
from .models import User, Protector, Address

admin.site.register(User)
admin.site.register(Protector)
admin.site.register(Address)
