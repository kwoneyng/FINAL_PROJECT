from django.urls import path
from . import views

app_name = 'movies'

urlpatterns = [
    path('', views.index, name='index'),
    path('push/', views.push, name='push'),
    path('<int:movie_pk>/', views.detail, name='detail'),
    path('<int:movie_pk>/review/', views.review_create, name='review_create'),
    path('<int:movie_pk>/review/<int:review_pk>/delete/', views.review_delete, name='review_delete'),
    path('<int:movie_pk>/like/', views.like, name='like'),
    path('mylist/', views.mylist, name='mylist'),
    path('recommend_list/', views.recommend_list, name='recommend_list'),
    path('actor_detail/<int:actor_id>/', views.actor_detail, name='actor_detail'),
    path('director_detail/<int:director_id>/', views.director_detail, name='director_detail'),
    path('manager_only/', views.manager_only, name='manager_only'),
    path('movie_create/', views.movie_create, name='movie_create'),
    path('<int:movie_pk>/delete/', views.movie_delete, name='movie_delete'),    
    path('<int:movie_pk>/update/', views.movie_update, name='movie_update'),
]