from django.contrib import admin
from .models import Chatting
from .models import ConversationMessage
# Register your models here.
admin.site.register(Chatting)
admin.site.register(ConversationMessage)