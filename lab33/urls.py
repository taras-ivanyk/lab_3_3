from django.urls import path
from . import views

app_name = 'lab33'

urlpatterns = [
    path('comments/', views.comment_list, name='comment_list'),
    path('comments/<int:pk>/', views.comment_detail, name='comment_detail'),
    path('comments/create/', views.comment_create, name='comment_create'),
    path('comments/<int:pk>/edit/', views.comment_update, name='comment_update'),
    path('comments/<int:pk>/delete/', views.comment_delete, name='comment_delete'),

    # Зовнішнє API
    path('external-activities/', views.external_activity_list, name='external_list'),
    path('external-activities/<int:pk>/delete/', views.external_activity_delete, name='external_delete'),
]