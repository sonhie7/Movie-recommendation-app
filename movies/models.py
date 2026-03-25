from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    watchlist = models.ManyToManyField('Movie', blank=True, through='UserProfile_watchlist')

    def __str__(self):
        return self.user.username


class Movie(models.Model):
    MOVIE_ID = models.IntegerField(primary_key=True)
    TITLE = models.CharField(max_length=255)
    genres = models.CharField(max_length=255)

    def __str__(self):
        return self.TITLE


class UserProfile_watchlist(models.Model):
    userprofile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('userprofile', 'movie')  # prevent duplicates