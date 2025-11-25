from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from .models import (
    Activity, Profile, Comment, Kudos, Follower, ActivityPoint, UserMonthlyStats
)
from .serializer import (
    ActivitySerializer,
    ProfileSerializer,
    CommentSerializer,
    KudosSerializer,
    FollowerSerializer,
    ActivityPointSerializer,
    UserMonthlyStatsSerializer,
    UserSerializer
)
from .repositories import DataAccessLayer
from django.db import IntegrityError
from django.http import Http404


# --- БАЗОВИЙ КЛАС, ЯКИЙ ВИКОНУЄ УМОВУ 3 ---
class RepositoryViewSet(viewsets.ModelViewSet):
    """
    Кастомний ViewSet, який змушує DRF використовувати наш DataAccessLayer
    замість стандартного `Model.objects.all()`.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Умова 3: Доступ до даних через репозиторій [cite: repositories.py]
        self.db = DataAccessLayer()
        # Встановлюємо 'repo' на основі 'queryset.model.__name__'
        model_name = self.queryset.model._meta.model_name.lower()

        # Спеціальні випадки для 'user' та 'activitypoint'
        if model_name == 'user':
            self.repo = self.db.users
        elif model_name == 'profile':
            self.repo = self.db.profiles
        elif model_name == 'activity':
            self.repo = self.db.activities
        elif model_name == 'comment':
            self.repo = self.db.comments
        elif model_name == 'kudos':
            self.repo = self.db.kudos
        elif model_name == 'follower':
            self.repo = self.db.followers
        elif model_name == 'activitypoint':
            self.repo = self.db.activity_points
        elif model_name == 'usermonthlystats':
            self.repo = self.db.user_stats
        else:
            raise ValueError(f"Repository for model {model_name} not found in DataAccessLayer")

    def get_queryset(self):
        return self.repo.get_all()

    def get_object(self):
        obj = self.repo.get_by_id(self.kwargs["pk"])
        if not obj:
            raise Http404
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_create(self, serializer):
        # 'serializer.save()' тепер викличе 'self.repo.add()'
        serializer.save(repository=self.repo)

    def perform_update(self, serializer):
        # 'serializer.save()' тепер викличе 'self.repo.update()'
        serializer.save(repository=self.repo, model_id=self.kwargs["pk"])

    def perform_destroy(self, instance):
        self.repo.delete(id=instance.pk)


# --- CRUD ДЛЯ USER ---
class UserViewSet(RepositoryViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        # Дозволити будь-кому 'create' (реєстрація),
        # але вимагати логін для 'list', 'retrieve' і т.д.
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]


# --- CRUD ДЛЯ PROFILE ---
class ProfileViewSet(RepositoryViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        try:
            # Передаємо 'user' у репозиторій
            serializer.save(repository=self.repo, user=self.request.user)
        except IntegrityError:
            return Response(
                {"error": "Profile for this user already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_object(self):
        # Профіль прив'язаний до User ID (pk)
        obj = self.repo.get_by_id(self.kwargs["pk"])
        if not obj:
            raise Http404
        self.check_object_permissions(self.request, obj)
        return obj

    # 💡 Додаємо логіку безпеки для 'update'
    def perform_update(self, serializer):
        profile = self.get_object()
        if profile.user != self.request.user:
            return Response({"error": "You can only edit your own profile."}, status=status.HTTP_403_FORBIDDEN)
        serializer.save(repository=self.repo, model_id=self.kwargs["pk"])

    # 💡 Додаємо логіку безпеки для 'destroy'
    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            return Response({"error": "You can only delete your own profile."}, status=status.HTTP_403_FORBIDDEN)
        self.repo.delete(id=instance.pk)


# --- CRUD ДЛЯ ACTIVITY ---
class ActivityViewSet(RepositoryViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(repository=self.repo, user=self.request.user)


# --- CRUD ДЛЯ COMMENT ---
class CommentViewSet(RepositoryViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(repository=self.repo, user=self.request.user)


# --- CRUD ДЛЯ KUDOS ---
class KudosViewSet(RepositoryViewSet):
    queryset = Kudos.objects.all()
    serializer_class = KudosSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        try:
            serializer.save(repository=self.repo, user=self.request.user)
        except IntegrityError:
            return Response(
                {"error": "You already gave kudos to this activity."},
                status=status.HTTP_400_BAD_REQUEST
            )


# --- CRUD ДЛЯ ACTIVITYPOINT ---
class ActivityPointViewSet(RepositoryViewSet):
    queryset = ActivityPoint.objects.all()
    serializer_class = ActivityPointSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        activity = serializer.validated_data['activity']
        if activity.user != self.request.user:
            return Response({"error": "You can only add points to your own activities."},
                            status=status.HTTP_403_FORBIDDEN)
        serializer.save(repository=self.repo)


# --- CRUD ДЛЯ FOLLOWER ---
class FollowerViewSet(RepositoryViewSet):
    queryset = Follower.objects.all()
    serializer_class = FollowerSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        if serializer.validated_data['followee'] == self.request.user:
            return Response(
                {"error": "You cannot follow yourself."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            serializer.save(repository=self.repo, follower=self.request.user)
        except IntegrityError:
            return Response(
                {"error": "You are already following this user."},
                status=status.HTTP_400_BAD_REQUEST
            )

    # 💡 Кастомний 'destroy' для композитного ключа
    def perform_destroy(self, instance):
        # 'instance' - це об'єкт Follower
        if instance.follower != self.request.user:
            return Response(
                {"error": "You can only unfollow for yourself."},
                status=status.HTTP_403_FORBIDDEN
            )
        self.repo.delete(follower_id=instance.follower.id, followee_id=instance.followee.id)


# --- READ-ONLY ДЛЯ USERMONTHLYSTATS ---
class UserMonthlyStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserMonthlyStats.objects.all()
    serializer_class = UserMonthlyStatsSerializer
    permission_classes = [IsAuthenticated]
    # Цей ViewSet не використовує RepositoryViewSet, оскільки він ReadOnly
    # і не потребує кастомних 'create', 'update'


# --- Агрегований Звіт (Умова 2) ---
class GlobalStatsReport(viewsets.ViewSet):
    """
    Окремий ViewSet (не ModelViewSet) для звіту.
    Він реалізує тільки 'list' (для GET /api/reports/global-stats/).
    """
    permission_classes = [AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DataAccessLayer()  # Умова 3: Доступ через репозиторій

    def list(self, request):
        """
        Умова 2: Агрегований звіт у JSON
        """
        report_data = {
            "activities_overview": self.db.activities.get_global_stats_report(),
            "profiles_overview": self.db.profiles.get_global_profiles_stats_report(),
            "users_overview": self.db.users.get_user_stats_report(),
            "most_commented_activities": self.db.comments.get_comment_stats_report(),
            "most_liked_activities": self.db.kudos.get_kudos_stats_report(),
            "most_followed_users": self.db.followers.get_follower_stats_report(),
            "global_distance_leaderboard": self.db.user_stats.get_distance_leaderboard_report()
        }

        # Перевірка, чи є хоч якісь дані
        if not report_data["activities_overview"] or report_data["activities_overview"].get('total_activities') is None:
            return Response({"error": "No data available to report."}, status=status.HTTP_404_NOT_FOUND)

        return Response(report_data, status=status.HTTP_200_OK)