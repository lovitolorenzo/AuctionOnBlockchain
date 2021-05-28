from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from rest_framework.urlpatterns import format_suffix_patterns
from . import views


urlpatterns = [
    path('', views.store, name="store"),
    path('cart/', views.bids_summary, name="cart"),
    path('cart/delete', views.delete, name="cart_delete"),
    path('product/auction/', views.manage_bids, name="product_auction"),
    path('logout/', views.logout_user, name='logout'),
    path('login/', views.login_page, name="login_page"),
    path('register/', views.register_page, name="register"),
    path('show/closed/', views.show_closed, name="show_closed"),
    path('transaction/verification', views.transaction_verification, name='transaction_verification'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
