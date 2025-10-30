from django.contrib import admin
from .models import Material, Destination,SupportTicket, UserProfile

admin.site.register(Material)

admin.site.register(SupportTicket)
admin.site.register(Destination)
admin.site.register(UserProfile)