from django.contrib import admin
from django.urls import path
from . import views 
urlpatterns = [
    path('', views.home),
    path('main/',views.main),
    path('logout/',views.logout,name="logout"),
    path('signup',views.signup,name="signup"),
    path('Host_profile/',views.hostprofile,name="hostprofile"),
    path('Create_stage',views.createpage,name="createpage"),
    path('main/stage/<stagecode>',views.stage,name="stage"),
    path('<stagecode>/participateup',views.participateup,name="participateup"),
    path('enterstagesubmission/',views.individualsubmission,name="individualsubmissions")
]
