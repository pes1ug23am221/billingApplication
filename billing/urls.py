from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('history/', views.history_view, name='history'),
    path('new/', views.new_bill_view, name='new_bill'),
    path('<int:pk>/review/', views.review_view, name='review'),
    path('<int:pk>/confirm/', views.confirm_view, name='confirm'),
    path('<int:pk>/receipt/', views.receipt_view, name='receipt'),
    path('<int:pk>/delete/', views.delete_view, name='delete'),
]
