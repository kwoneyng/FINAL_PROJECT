from django.db import models
from django.conf import settings


class Genre(models.Model):
    name = models.CharField(max_length=20, unique=True)


class Movie(models.Model):
    title = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)
    genres = models.ManyToManyField(Genre, related_name='movies')
    prdtyear = models.CharField(max_length=10)
    openyear = models.CharField(max_length=10)
    showtime = models.CharField(max_length=10)
    watchgrade = models.CharField(max_length=30)
    company = models.CharField(max_length=20)
    audience = models.IntegerField()
    discription = models.TextField()
    poster_url = models.CharField(max_length=150)
    liked_user = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_movies')


class Director(models.Model):
    name = models.CharField(max_length=20)
    code = models.CharField(max_length=10, unique=True)
    movies = models.ManyToManyField(Movie, related_name='directors')


class Actor(models.Model):
    name = models.CharField(max_length=20)
    code = models.CharField(max_length=10, unique=True)
    movies = models.ManyToManyField(Movie, related_name='actors')


class Review(models.Model):
    content = models.CharField(max_length=200)
    score = models.IntegerField()
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
