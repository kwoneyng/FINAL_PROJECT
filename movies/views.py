from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
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
        movie_list = Movie.objects.all()
        context = { 'movie_list': movie_list }
        return render(request, 'movies/index.html', context)
    return redirect('accounts:login')


@login_required
def detail(request, movie_pk):
    movie = get_object_or_404(Movie, pk=movie_pk)
    genres = movie.genres.all()
    actors = movie.actors.all()
    directors = movie.directors.all()
    review_form = ReviewForm()
    reviews = movie.reviews.all()
    context = {
        'movie': movie,
        'genres': genres,
        'reviews': reviews,
        'review_form': review_form,
        'actors': actors,
        'directors': directors,
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

def like(request, movie_pk):
    user = request.user
    movie = get_object_or_404(Movie, pk=movie_pk)

    if user in movie.liked_user.all():
        user.liked_movies.remove(movie)
        liked = False
    else:
        user.liked_movies.add(movie)
        liked = True
    context = {
        'liked': liked,
    }
    return JsonResponse(context)


def mylist(request):
    user = request.user
    movies = user.liked_movies.all()
    context = {
        'movies': movies
    }
    return render(request, 'movies/mylist.html', context)
    

def push(request):
    key = config('KEY')
    # targetDt = '20191101'
    client_id =  config('CLIENT_ID')
    client_secret = config('CLIENT_SECRET')
    HEADERS = {
                'X-Naver-Client-Id' : client_id,
                'X-Naver-Client-Secret' : client_secret,
            }

    for i in range(1):
        print('==================================')
        print(f'{i}주차 영화 시작!')
        targetDt = datetime(2019, 11, 23) - timedelta(weeks=i)
        targetDt = targetDt.strftime('%Y%m%d')
        DAILY_BOXOFFICE_API_URL = f'http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json?key={key}&targetDt={targetDt}'
        response = requests.get(DAILY_BOXOFFICE_API_URL).json()['boxOfficeResult']['dailyBoxOfficeList']
        movie_info_url = f"http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json?key={key}&movieCd="
        for each_movie in response:
            movieNm = each_movie['movieNm']
            print(f'{movieNm}영화 시작')
            movieCd = each_movie['movieCd']
            if Movie.objects.filter(code=movieCd):
                continue
            # print(each_movie)
            audience = each_movie['audiCnt']
            openyear = each_movie['openDt'][:4]
            # response 초기화 : 영화진흥원 영화 상세 API
            response_movieCd = requests.get(movie_info_url+movieCd).json()['movieInfoResult']['movieInfo']
            if response_movieCd['showTm']:
                showtime = response_movieCd['showTm']
            else:
                showtime = ''

            if response_movieCd['audits']:
                watchgrade = response_movieCd['audits'][0]['watchGradeNm']
            else:
                watchgrade = ''

            if response_movieCd['companys']:
                company = response_movieCd['companys'][0]['companyNm']
            else:
                company = ''

            actors = []
            for people in response_movieCd['actors']:
                actors.append(people['peopleNm'])

            directors = []
            for people in response_movieCd['directors']:
                directors.append(people['peopleNm'])

            genres = []
            if response_movieCd['genres']:
                for genre in response_movieCd['genres']:
                    if Genre.objects.filter(name=genre['genreNm']):
                        continue
                    gen = Genre()
                    gen.name = genre['genreNm']
                    gen.save()
                    genres.append(genre['genreNm'])

            movie_people_url = f"http://www.kobis.or.kr/kobisopenapi/webservice/rest/people/searchPeopleList.json?key={key}&peopleNm="
            selActor = []
            for actor in actors:
                response_peopleNm = requests.get(movie_people_url+actor).json()['peopleListResult']['peopleList']
                for people in response_peopleNm:
                    if movieNm in people['filmoNames'].split('|'):
                        selActor.append([people['peopleCd'], actor])
            
            selDirector = []
            for director in directors:
                response_peopleNm = requests.get(movie_people_url+director).json()['peopleListResult']['peopleList']
                for people in response_peopleNm:
                    if movieNm in people['filmoNames'].split('|'):
                        selDirector.append([people['peopleCd'], director])

            naver_url = "https://openapi.naver.com/v1/search/movie.json?query="
            response_naver = requests.get(naver_url+movieNm, headers=HEADERS).json()
            if response_naver['display'] > 1:
                for movie in response_naver['items']:
                    select = 0
                    for cd, nm in selDirector:
                        if nm in movie['director'].split('|'):
                            select = 1
                            link = movie['link']
                            break
                    if select == 1 :
                        link = movie['link']
                        rating = movie['userRating']
                        break
                html = urlopen(link)
                source = html.read()
                html.close()
                soup = BeautifulSoup(source, 'html.parser')
                div_poster = soup.find('div', 'poster')
                imgTag = div_poster.find_all('img')
                for tag in imgTag:
                    if 'src' in tag.attrs:
                        poster_url = tag.attrs['src'].split('jpg?')[0]+'jpg'

                div_people = soup.find('div', 'people')
                imgPtag = div_people.find_all('img')

                for tag in imgPtag:
                    if 'alt' in tag.attrs and 'src' in tag.attrs:
                        for cd, nm in selActor:
                            # print(cd,nm)
                            if nm == tag.attrs['alt']:
                                if Actor.objects.filter(code=cd):
                                    continue
                                # print(f'{nm} 생성')
                                actor = Actor()
                                actor.code = cd
                                actor.img = tag.attrs['src']
                                actor.name = nm
                                actor.save()
                        for cd, nm in selDirector:
                            # print(cd,nm)
                            if nm == tag.attrs['alt']:
                                if Director.objects.filter(code=cd):
                                    continue
                                # print(f'{nm} 생성')
                                direct = Director()
                                direct.code = cd
                                direct.img = tag.attrs['src']
                                direct.name = nm
                                direct.save()
                if soup.select_one('p.con_tx'):
                    discrip = soup.select_one('p.con_tx').text
                else:
                    discrip = ''
                
            else:
                # print('display = 1')
                movie = response_naver['items'][0]
                link = movie['link']
                rating = movie['userRating']
                html = urlopen(link)
                source = html.read()
                html.close()
                soup = BeautifulSoup(source, 'html.parser')
                div_poster = soup.find('div', 'poster')
                imgTag = div_poster.find_all('img')
                for tag in imgTag:
                    if 'src' in tag.attrs:
                        poster_url = tag.attrs['src'].split('jpg?')[0]+'jpg'
                
                div_people = soup.find('div', 'people')
                imgPtag = div_people.find_all('img')

                for tag in imgPtag:
                    if 'alt' in tag.attrs and 'src' in tag.attrs:
                        for cd, nm in selActor:
                            # print(cd, nm)
                            if nm == tag.attrs['alt']:
                                if Actor.objects.filter(code=cd):
                                    continue
                                # print(f'{nm} 생성')
                                actor = Actor()
                                actor.code = cd
                                actor.img = tag.attrs['src']
                                actor.name = nm
                                actor.save()
                        for cd, nm in selDirector:
                            # print(cd, nm)
                            if nm == tag.attrs['alt']:
                                if Director.objects.filter(code=cd):
                                    continue
                                # print(f'{nm} 생성')
                                direct = Director()
                                direct.code = cd
                                direct.img = tag.attrs['src']
                                direct.name = nm
                                direct.save()
                if soup.select_one('p.con_tx'):
                    discrip = soup.select_one('p.con_tx').text
                else:
                    discrip = ''

            movieform = Movie()
            movieform.title = movieNm
            movieform.code = movieCd
            movieform.openyear = openyear
            movieform.showtime = showtime
            movieform.watchgrade = watchgrade
            movieform.company = company
            movieform.audience = audience
            movieform.discription = discrip
            movieform.poster_url = poster_url
            movieform.rating = float(rating)
            movieform.save()

            movie = Movie.objects.filter(code=movieCd).first()
            print(selActor)
            print(selDirector)
            print(genres)

            for cd, nm in selActor:
                act = Actor.objects.filter(code=cd).first()
                if act:
                    act.movies.add(movie)
            
            for cd, nm in selDirector:
                dirt = Director.objects.filter(code=cd).first()
                if dirt :
                    dirt.movies.add(movie)
            
            for nm in genres:
                gen = Genre.objects.filter(name=nm).first()
                if gen:
                    gen.movies.add(movie)



            # response_naver = requests.get(url,headers=HEADERS).json()
            # if response_naver['display'] > 1:
            #     for i in response_naver['items']:
            #         if i['director'][:dirlen] == director:
            #             movieImg = i['image']
            #             link = i['link']
            #             movie.poster_url = i['image']
            #             html = urlopen(link)
            #             source = html.read()
            #             html.close()
            #             soup = BeautifulSoup(source, 'html.parser')
            #             if soup.select_one('p.con_tx').text:
            #                 discrip = soup.select_one('p.con_tx').text
            #             else:
            #                 discrip = ''
            #             movie.discription = discrip   
            #             div = soup.find('div', 'people')
            #             img_tag = div.find_all('img')
            #             for img in img_tag:
            #                 if 'alt' in img.attrs and 'src' in img.attrs:
            #                     for peopleNm, peopleCd in peopleCan:
            #                         if peopleNm == img.attrs['alt']:
            #                             actor = Actor()
            #                             actor.code = peopleCd
            #                             actor.img = img.attrs['src']
            #                             actor.name = peopleNm                                        
            #                             try:
            #                                 actor.save()
            #                             except:
            #                                 pass
            #                     if director == img.attrs['alt']:
            #                         drt = Director()
            #                         drt.name = director
            #                         drt.img = img.attrs['src']
            #                         drt.code = directorCd
            #                         try :
            #                             drt.save()
            #                         except:
            #                             pass

                        
            # else :
            #     if response_naver['items']:
            #         movieImg = response_naver['items'][0]['image']
            #         link = response_naver['items'][0]['link']
            #         movie.poster_url = response_naver['items'][0]['image']
            #         html = urlopen(link)
            #         source = html.read()
            #         html.close()
            #         soup = BeautifulSoup(source, 'html.parser')
            #         if soup.select_one('p.con_tx').text:
            #             discrip = soup.select_one('p.con_tx').text
            #         else:
            #             discrip = ''
            #         movie.discription = discrip
            #         div = soup.find('div', 'people')
            #         img_tag = div.find_all('img')
            #         for img in img_tag:
            #             if 'alt' in img.attrs and 'src' in img.attrs['src']:
            #                 for peopleNm, peopleCd in peopleCan:
            #                     if peopleNm == img.attrs['alt']:
            #                         actor = Actor()
            #                         actor.code = peopleCd
            #                         actor.img = img.attrs['src']
            #                         actor.name = peopleNm
            #                         try :
            #                             actor.save()
            #                         except:
            #                             pass
            #                         break
            #     else :
            #         movie.poster_url = ''
            #         movie.discription = ''
                # image = response['items'][0]['image']
                # link = response['items'][0]['link']
                # print(image)
                # print(link)
                # movie.save()
                # embed()
                # movie = Movie.objects.filter(code=movieCd).first()
                # drt = Director.objects.filter(code=directorCd).first()
                # drt.movies.add(movie)
                # for i in genres:
                #     genre = Genre.objects.filter(name=i['genreNm']).first()
                #     movie.genres.add(genre)
                # for peopleNm, peopleCd in peopleCan:
                #     actor = Actor.objects.filter(code=peopleCd).first()
                #     actor.movies.add(movie)
