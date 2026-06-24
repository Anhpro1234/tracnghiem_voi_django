from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # 1. Allauth lo hết phần Account (Login, Signup, Logout, Password)
    path('accounts/', include('allauth.urls')),

    # 2. Các chức năng của app1
    path('', include('app1.urls')),
]