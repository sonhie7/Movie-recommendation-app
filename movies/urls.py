# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('movie/<int:movie_id>/', views.movie_detail, name="movie_detail"),
    path('login/', views.login, name="login"),
    path('logout/', views.logout, name="logout"),
    path('rate/<int:movie_id>/', views.rate_movie, name="rate_movie"),
    path('watchlist/', views.watchlist, name="watchlist"),
    path('watchlist/add/<int:movie_id>/', views.add_to_watchlist_view, name="add_to_watchlist"),
    path('watchlist/remove/<int:movie_id>/', views.remove_from_watchlist_view, name="remove_from_watchlist"),
    path('profile/', views.profile, name="profile"),
    path('trending/', views.trending, name='trending'),
]