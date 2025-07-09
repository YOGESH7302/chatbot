from django.contrib import admin
from django.urls import path
from chatbot.views import chat_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', chat_view),
]
