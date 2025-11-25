from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Створюємо роутер
router = DefaultRouter()

# Реєструємо всі наші ViewSet-и
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'profiles', views.ProfileViewSet, basename='profile')
router.register(r'activities', views.ActivityViewSet, basename='activity')
router.register(r'comments', views.CommentViewSet, basename='comment')
router.register(r'kudos', views.KudosViewSet, basename='kudos')
router.register(r'followers', views.FollowerViewSet, basename='follower')
router.register(r'activity-points', views.ActivityPointViewSet, basename='activitypoint')
router.register(r'user-stats', views.UserMonthlyStatsViewSet, basename='userstats')

# Реєструємо звіт (оскільки це не ModelViewSet)
router.register(r'reports/global-stats', views.GlobalStatsReport, basename='report-stats')

# urlpatterns тепер автоматично генеруються роутером
urlpatterns = [
    path('', include(router.urls)),
]