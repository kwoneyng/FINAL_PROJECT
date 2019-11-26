from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from .models import Movie, Genre, Review
from .forms import ReviewForm
from datetime import datetime, timedelta
from IPython import embed
from decouple import config
from .models import Movie, Genre, Actor, Director
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests

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

def push(request):
    key = config('KEY')
    # targetDt = '20191101'
    client_id =  config('CLIENT_ID')
    client_secret = config('CLIENT_SECRET')
    HEADERS = {
                'X-Naver-Client-Id' : client_id,
                'X-Naver-Client-Secret' : client_secret,
            }

    for i in range(52):
        targetDt = datetime(2019, 11, 23) - timedelta(weeks=i)
        targetDt = targetDt.strftime('%Y%m%d')
        DAILY_BOXOFFICE_API_URL = f'http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json?key={key}&targetDt={targetDt}'
        response = requests.get(DAILY_BOXOFFICE_API_URL).json()['boxOfficeResult']['dailyBoxOfficeList']
        movie_info_url = f"http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json?key={key}&movieCd="
        # 영화 진흥원 top 10 리스트 : response
        for each_movie in response:
            movieNm = each_movie['movieNm']
            movieCd = each_movie['movieCd']
            # temp_movies = Movie.objects.filter(code=f'{movieCd}')
            # if temp_movies:
            #     continue
            movie = Movie()
            movie.code = movieCd
            movie.title = movieNm
            movie.openyear = each_movie['openDt'][:4]
            movie.audience = each_movie['audiCnt']

            # response 초기화 : 영화진흥원 영화 상세 API
            response_movieCd = requests.get(movie_info_url+movieCd).json()['movieInfoResult']['movieInfo']
            movie.showtime = response_movieCd['showTm']
            genres = []
            if response_movieCd['genres']:
                genres = response_movieCd['genres']
                for i in genres:
                    genre = Genre()
                    genre.name = i['genreNm']
                    try:
                        genre.save()
                    except:
                        pass
            if response_movieCd['audits']:
                movie.watchgrade = response_movieCd['audits'][0]['watchGradeNm']
            else :
                movie.watchgrade = ''   
            if response_movieCd['companys']:
                movie.company = response_movieCd['companys'][0]['companyNm']
            else :
                movie.company = ''
            peopleCan = []
            for movie_detail in response_movieCd['actors']:
                peopleNm = movie_detail['peopleNm']
                movie_people_url = f"http://www.kobis.or.kr/kobisopenapi/webservice/rest/people/searchPeopleList.json?key={key}&peopleNm={peopleNm}"
                response_peopleNm = requests.get(movie_people_url).json()
                if response_peopleNm['peopleListResult']:
                    for namedata in response_peopleNm['peopleListResult']['peopleList']:
                        if movieNm in namedata['filmoNames'].split('|'):
                            peopleCd = namedata['peopleCd']
                            peopleCan.append([peopleNm, peopleCd])

            if response_movieCd['directors']:
                director = response_movieCd['directors'][0]['peopleNm']
                movie_director_url = f"http://www.kobis.or.kr/kobisopenapi/webservice/rest/people/searchPeopleList.json?key={key}&peopleNm={director}"
                response_director = requests.get(movie_director_url).json()
                if response_director['peopleListResult']['peopleList']:
                    directorCd = response_director['peopleListResult']['peopleList'][0]['peopleCd']
            else :
                continue

            dirlen = len(director)
            encText = movieNm
            base_url = "https://openapi.naver.com/v1/search/movie.json?query="
            url = base_url + encText
            response_naver = requests.get(url,headers=HEADERS).json()
            if response_naver['display'] > 1:
                for i in response_naver['items']:
                    if i['director'][:dirlen] == director:
                        movieImg = i['image']
                        link = i['link']
                        movie.poster_url = i['image']
                        html = urlopen(link)
                        source = html.read()
                        html.close()
                        soup = BeautifulSoup(source, 'html.parser')
                        if soup.select_one('p.con_tx').text:
                            discrip = soup.select_one('p.con_tx').text
                        else:
                            discrip = ''
                        movie.discription = discrip   
                        div = soup.find('div', 'people')
                        img_tag = div.find_all('img')
                        for img in img_tag:
                            if 'alt' in img.attrs and 'src' in img.attrs:
                                for peopleNm, peopleCd in peopleCan:
                                    if peopleNm == img.attrs['alt']:
                                        actor = Actor()
                                        actor.code = peopleCd
                                        actor.img = img.attrs['src']
                                        actor.name = peopleNm                                        
                                        try:
                                            actor.save()
                                        except:
                                            pass
                                if director == img.attrs['alt']:
                                    drt = Director()
                                    drt.name = director
                                    drt.img = img.attrs['src']
                                    drt.code = directorCd
                                    try :
                                        drt.save()
                                    except:
                                        pass
 
                        
            else :
                if response_naver['items']:
                    movieImg = response_naver['items'][0]['image']
                    link = response_naver['items'][0]['link']
                    movie.poster_url = response_naver['items'][0]['image']
                    html = urlopen(link)
                    source = html.read()
                    html.close()
                    soup = BeautifulSoup(source, 'html.parser')
                    if soup.select_one('p.con_tx').text:
                        discrip = soup.select_one('p.con_tx').text
                    else:
                        discrip = ''
                    movie.discription = discrip
                    div = soup.find('div', 'people')
                    img_tag = div.find_all('img')
                    for img in img_tag:
                        if 'alt' in img.attrs and 'src' in img.attrs['src']:
                            for peopleNm, peopleCd in peopleCan:
                                if peopleNm == img.attrs['alt']:
                                    actor = Actor()
                                    actor.code = peopleCd
                                    actor.img = img.attrs['src']
                                    actor.name = peopleNm
                                    try :
                                        actor.save()
                                    except:
                                        pass
                                    break
                else :
                    movie.poster_url = ''
                    movie.discription = ''
                # image = response['items'][0]['image']
                # link = response['items'][0]['link']
                # print(image)
                # print(link)
            try :
                movie.save()
                # embed()
                movie = Movie.objects.filter(code=movieCd).first()
                drt = Director.objects.filter(code=directorCd).first()
                drt.movies.add(movie)
                for i in genres:
                    genre = Genre.objects.filter(name=i['genreNm']).first()
                    movie.genres.add(genre)

                for peopleNm, peopleCd in peopleCan:
                    actor = Actor.objects.filter(code=peopleCd).first()
                    actor.movies.add(movie)

            except:
                continue