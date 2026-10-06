from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/<uuid:token>/', views.register_view, name='register'),
    path('invite/', views.invite_view, name='invite'),
]
