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

import pandas as pd
from rest_framework.decorators import action

class AnalyticsViewSet(viewsets.ViewSet):

    permission_classes = [AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DataAccessLayer()

    def _process_pandas_response(self, queryset, fields, stats_columns=None, group_by_col=None):

        if fields:
            data = list(queryset.values(*fields))
        else:
            data = list(queryset)

        df = pd.DataFrame(data)

        if df.empty:
            return Response({"message": "No data available", "statistics": {}})

        stats = {}
        if stats_columns:
            for col in stats_columns:
                if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                    stats[col] = {
                        "mean": df[col].mean(),
                        "median": df[col].median(),
                        "min": df[col].min(),
                        "max": df[col].max(),
                        "std_dev": df[col].std()
                    }

        grouped_data = None
        if group_by_col and group_by_col in df.columns and stats_columns:
            grouped_df = df.groupby(group_by_col)[stats_columns].mean()
            grouped_data = grouped_df.to_dict()

        response_data = {
            "dataset": df.to_dict(orient="records"),
            "statistics": stats,
            "grouped_analysis": grouped_data
        }
        return Response(response_data)

    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        qs = self.db.analytics.get_top_distance_users()
        return self._process_pandas_response(
            qs,
            fields=['username', 'total_distance'],
            stats_columns=['total_distance']
        )

    @action(detail=False, methods=['get'])
    def social_engagement(self, request):
        qs = self.db.analytics.get_social_activities()
        return self._process_pandas_response(
            qs,
            fields=['id', 'user__username', 'comments_count', 'kudos_count', 'engagement_score'],
            stats_columns=['engagement_score', 'comments_count', 'kudos_count']
        )

    @action(detail=False, methods=['get'])
    def monthly_trends(self, request):
        qs = self.db.analytics.get_monthly_activity_stats()
        return self._process_pandas_response(
            qs,
            fields=None,
            stats_columns=['total_distance', 'avg_duration']
        )

    @action(detail=False, methods=['get'])
    def influencers(self, request):
        qs = self.db.analytics.get_influential_users()
        return self._process_pandas_response(
            qs,
            fields=['username', 'followers_count'],
            stats_columns=['followers_count']
        )

    @action(detail=False, methods=['get'])
    def activity_performance(self, request):
        qs = self.db.analytics.get_activity_type_performance()
        return self._process_pandas_response(
            qs,
            fields=None,
            stats_columns=['avg_distance', 'max_elevation']
        )

    @action(detail=False, methods=['get'])
    def user_levels(self, request):
        qs = self.db.analytics.get_user_activity_levels()
        return self._process_pandas_response(
            qs,
            fields=None,
            stats_columns=['activities_count'],
            group_by_col='status'
        )


class RepositoryViewSet(viewsets.ModelViewSet):
    """
    Кастомний ViewSet, який змушує DRF використовувати наш DataAccessLayer
    замість стандартного `Model.objects.all()`.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DataAccessLayer()
        model_name = self.queryset.model._meta.model_name.lower()

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


class UserViewSet(RepositoryViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):

        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]


class ProfileViewSet(RepositoryViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        try:
            serializer.save(repository=self.repo, user=self.request.user)
        except IntegrityError:
            return Response(
                {"error": "Profile for this user already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get_object(self):
        obj = self.repo.get_by_id(self.kwargs["pk"])
        if not obj:
            raise Http404
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_update(self, serializer):
        profile = self.get_object()
        if profile.user != self.request.user:
            return Response({"error": "You can only edit your own profile."}, status=status.HTTP_403_FORBIDDEN)
        serializer.save(repository=self.repo, model_id=self.kwargs["pk"])

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            return Response({"error": "You can only delete your own profile."}, status=status.HTTP_403_FORBIDDEN)
        self.repo.delete(id=instance.pk)


class ActivityViewSet(RepositoryViewSet):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(repository=self.repo, user=self.request.user)


class CommentViewSet(RepositoryViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(repository=self.repo, user=self.request.user)


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

    def perform_destroy(self, instance):
        # 'instance' - це об'єкт Follower
        if instance.follower != self.request.user:
            return Response(
                {"error": "You can only unfollow for yourself."},
                status=status.HTTP_403_FORBIDDEN
            )
        self.repo.delete(follower_id=instance.follower.id, followee_id=instance.followee.id)


class UserMonthlyStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserMonthlyStats.objects.all()
    serializer_class = UserMonthlyStatsSerializer
    permission_classes = [IsAuthenticated]
    # Цей ViewSet не використовує RepositoryViewSet, оскільки він ReadOnly
    # і не потребує кастомних 'create', 'update'


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