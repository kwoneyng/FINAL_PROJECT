from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from .models import Movie, Genre, Review
from .forms import ReviewForm


movie_list = [
    {
        'title': '엑시트',
        'movie_pk': 1,
        'movieCd': 101,
        'post_url':'https://picsum.photos/id/599/200/300',
        'genre': '코미디',
        'openingDt': '2019-07-31',
    },
    {
        'title': '마이펫의 이중생활2',
        'movie_pk': 2,
        'movieCd': 102,
        'post_url': 'https://picsum.photos/id/399/200/300',
        'genre': '애니메이션',
        'openingDt': '2019-07-31',
    },
]


def index(request):
    if request.user.is_authenticated:
        context = { 'movie_list': movie_list }
        return render(request, 'movies/index.html', context)
    return redirect('accounts:login')


@login_required
def detail(request, movie_pk):
    movie = get_object_or_404(Movie, pk=movie_pk)
    review_form = ReviewForm()
    reviews = movie.reviews.all()
    context = {
        ''
        'movie': movie,
        'review_form': review_form,
        'reviews': reviews,
    }
    return render(request, 'movies/detail.html', context)


@require_POST
def review_create(request, movie_pk):
    if request.user.is_authenticated:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.movie_id = movie_pk
            review.user = request.user
            review.save()
    return redirect('movies:detail', movie_pk)


@require_POST
def review_delete(request, movie_pk, review_pk):
    if request.user.is_authenticated:
        review = get_object_or_404(Review, pk=review_pk)
        if review.user == request.user:
            review.delete()
        return redirect('movies:detail', movie_pk)
    return HttpResponse('You are Unauthorized', status=401)

