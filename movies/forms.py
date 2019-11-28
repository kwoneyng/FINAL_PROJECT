from django import forms
from .models import Review, Movie


class ReviewForm(forms.ModelForm):
    
    class Meta:
        model = Review
        fields = ['content', 'score', ]


class MovieForm(forms.ModelForm):

    class Meta:
        model = Movie
        fields = ['title', 'openyear', 'showtime', 'watchgrade', 'audience', 'poster_url', 'rating' ,]
        # fields = '__all__'
