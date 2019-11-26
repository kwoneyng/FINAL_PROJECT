from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    path('', views.index, name='index'),
<<<<<<< HEAD
        path('push/', views.push, name='push'),
=======
    path('push/', views.push, name='push'),
>>>>>>> 93d513fea96965d37ab694535e16c95d49a14034
    path('<int:movie_pk>/', views.detail, name='detail'),
    path('<int:movie_pk>/review/', views.review_create, name='review_create'),
    path('<int:movie_pk>/review/<int:review_pk>/delete/', views.review_delete, name='review_delete'),
    path('<int:movie_pk>/like/', views.like, name='like'),
    path('mylist/', views.mylist, name='mylist'),
]