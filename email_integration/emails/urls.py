from django.urls import path
from .views import EmailListView, EmailAccountCreateView

urlpatterns = [
    path('', EmailListView.as_view(), name='email_list'),
    path('account/create/', EmailAccountCreateView.as_view(), name='account_create'),
] 