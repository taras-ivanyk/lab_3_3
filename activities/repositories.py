from typing import List, Optional
from django.contrib.auth.models import User
from django.db import IntegrityError
from .models import (
    Activity, Profile, Comment, Kudos, Follower, ActivityPoint, UserMonthlyStats
)
from django.db.models import Sum, Count, Avg, Max, F  # For aggregation


class BaseRepository:
    """
    (КОНТРАКТ)
    Вимагає, щоб кожен дочірній репозиторій реалізував ці методи.
    """

    def get_by_id(self, model_id: int):
        raise NotImplementedError

    def get_all(self):
        raise NotImplementedError

    def add(self, **kwargs):
        raise NotImplementedError

    def update(self, model_id: int, **kwargs) -> bool:
        raise NotImplementedError

    def delete(self, **kwargs) -> bool:
        raise NotImplementedError


# --- РЕПОЗИТОРІЙ 1: USER ---
class UserRepository(BaseRepository):

    def get_by_id(self, model_id: int) -> Optional[User]:
        try:
            return User.objects.get(id=model_id)
        except User.DoesNotExist:
            return None

    def get_all(self) -> List[User]:
        return User.objects.all()

    def add(self, **kwargs) -> User:
        # Ваш UserSerializer.create() подбає про хешування
        return User.objects.create_user(**kwargs)

    def update(self, model_id: int, **kwargs) -> bool:
        if 'password' in kwargs and kwargs['password'] is None:
            del kwargs['password']

        # Оновлюємо звичайні поля
        count = User.objects.filter(id=model_id).update(**kwargs)

        if 'password' in kwargs and kwargs['password'] is not None:
            user = self.get_by_id(model_id)
            if user:
                user.set_password(kwargs['password'])
                user.save()
        return count > 0

    def delete(self, **kwargs) -> bool:
        count, _ = User.objects.filter(id=kwargs.get('id')).delete()
        return count > 0

    def get_user_stats_report(self):
        """Звіт: Агрегована статистика по користувачам"""
        return User.objects.aggregate(
            total_users=Count('id'),
            users_with_profiles=Count('profile')
        )


# --- РЕПОЗИТОРІЙ 2: PROFILE ---
class ProfileRepository(BaseRepository):

    def get_by_id(self, model_id: int) -> Optional[Profile]:
        """
        ВИПРАВЛЕНО: Profile.id - це user.id, оскільки це OneToOneField.
        Тому ми шукаємо по 'user_id', а не 'id'.
        """
        try:
            return Profile.objects.get(user_id=model_id)
        except Profile.DoesNotExist:
            return None

    def get_all(self) -> List[Profile]:
        return Profile.objects.all()

    def add(self, **kwargs) -> Profile:
        # kwargs має містити 'user' або 'user_id'
        return Profile.objects.create(**kwargs)

    def update(self, model_id: int, **kwargs) -> bool:
        # 'model_id' тут - це user_id
        count = Profile.objects.filter(user_id=model_id).update(**kwargs)
        return count > 0

    def delete(self, **kwargs) -> bool:
        count, _ = Profile.objects.filter(user_id=kwargs.get('id')).delete()
        return count > 0

    def get_global_profiles_stats_report(self):
        """
        Звіт: Агрегована статистика по профілях.
        """
        return Profile.objects.aggregate(
            total_profiles=Count('user'),
            average_age=Avg('age'),
            average_weight_kg=Avg('weight_kg'),
            average_height_cm=Avg('height_cm')
        )


# --- РЕПОЗИТОРІЙ 3: ACTIVITY ---
class ActivityRepository(BaseRepository):

    def get_by_id(self, model_id: int) -> Optional[Activity]:
        try:
            return Activity.objects.get(id=model_id)
        except Activity.DoesNotExist:
            return None

    def get_all(self) -> List[Activity]:
        return Activity.objects.all()

    def add(self, **kwargs) -> Activity:
        return Activity.objects.create(**kwargs)

    def update(self, model_id: int, **kwargs) -> bool:
        count = Activity.objects.filter(id=model_id).update(**kwargs)
        return count > 0

    def delete(self, **kwargs) -> bool:
        count, _ = Activity.objects.filter(id=kwargs.get('id')).delete()
        return count > 0

    def get_global_stats_report(self):
        """Звіт: Агрегована статистика по всіх активностях"""
        return Activity.objects.aggregate(
            total_activities=Count('id'),
            total_distance_meters=Sum('distance_m'),
            total_duration_seconds=Sum('duration_sec'),
            average_elevation_gain=Avg('elevation_gain_m')
        )


# --- РЕПОЗИТОРІЙ 4: COMMENT ---
class CommentRepository(BaseRepository):

    def get_by_id(self, model_id: int) -> Optional[Comment]:
        try:
            return Comment.objects.get(id=model_id)
        except Comment.DoesNotExist:
            return None

    def get_all(self) -> List[Comment]:
        return Comment.objects.all()

    def add(self, **kwargs) -> Comment:
        return Comment.objects.create(**kwargs)

    def update(self, model_id: int, **kwargs) -> bool:
        count = Comment.objects.filter(id=model_id).update(**kwargs)
        return count > 0

    def delete(self, **kwargs) -> bool:
        count, _ = Comment.objects.filter(id=kwargs.get('id')).delete()
        return count > 0

    def get_comment_stats_report(self):
        """Звіт: Найбільш коментовані активності"""
        return Comment.objects.values('activity_id').annotate(
            comment_count=Count('id')
        ).order_by('-comment_count')


# --- РЕПОЗИТОРІЙ 5: KUDOS ---
class KudosRepository(BaseRepository):

    def get_by_id(self, model_id: int) -> Optional[Kudos]:
        try:
            return Kudos.objects.get(id=model_id)
        except Kudos.DoesNotExist:
            return None

    def get_all(self) -> List[Kudos]:
        return Kudos.objects.all()

    def add(self, **kwargs) -> Kudos:
        return Kudos.objects.create(**kwargs)

    def update(self, model_id: int, **kwargs) -> bool:
        count = Kudos.objects.filter(id=model_id).update(**kwargs)
        return count > 0

    def delete(self, **kwargs) -> bool:
        count, _ = Kudos.objects.filter(id=kwargs.get('id')).delete()
        return count > 0

    def get_kudos_stats_report(self):
        """Звіт: Активності з найбільшою кількістю 'kudos'"""
        return Kudos.objects.values('activity_id').annotate(
            kudos_count=Count('id')
        ).order_by('-kudos_count')


# --- РЕПОЗИТОРІЙ 6: FOLLOWER ---
class FollowerRepository(BaseRepository):

    def get_by_id(self, model_id: int):
        raise NotImplementedError("Використовуйте get_by_composite_key")

    def get_by_composite_key(self, follower_id: int, followee_id: int) -> Optional[Follower]:
        try:
            return Follower.objects.get(follower_id=follower_id, followee_id=followee_id)
        except Follower.DoesNotExist:
            return None

    def get_all(self) -> List[Follower]:
        return Follower.objects.all()

    def add(self, **kwargs) -> Follower:
        # kwargs: {'follower': User_obj, 'followee': User_obj}
        return Follower.objects.create(**kwargs)

    def update(self, model_id: int, **kwargs) -> bool:
        raise NotImplementedError("Follower не оновлюється, а видаляється/створюється")

    def delete(self, **kwargs) -> bool:
        # kwargs: {'follower_id': 1, 'followee_id': 2}
        count, _ = Follower.objects.filter(
            follower_id=kwargs.get('follower_id'),
            followee_id=kwargs.get('followee_id')
        ).delete()
        return count > 0

    def get_follower_stats_report(self):
        """Звіт: Топ-10 найпопулярніших користувачів (кого найбільше фоловлять)"""
        return Follower.objects.values('followee_id').annotate(
            follower_count=Count('id')
        ).order_by('-follower_count')[:10]


# --- РЕПОЗИТОРІЙ 7: ACTIVITYPOINT ---
class ActivityPointRepository(BaseRepository):

    def get_by_id(self, model_id: int) -> Optional[ActivityPoint]:
        try:
            return ActivityPoint.objects.get(id=model_id)
        except ActivityPoint.DoesNotExist:
            return None

    def get_all(self) -> List[ActivityPoint]:
        return ActivityPoint.objects.all()

    def add(self, **kwargs) -> ActivityPoint:
        return ActivityPoint.objects.create(**kwargs)

    def update(self, model_id: int, **kwargs) -> bool:
        count = ActivityPoint.objects.filter(id=model_id).update(**kwargs)
        return count > 0

    def delete(self, **kwargs) -> bool:
        count, _ = ActivityPoint.objects.filter(id=kwargs.get('id')).delete()
        return count > 0


# --- РЕПОЗИТОРІЙ 8: USERMONTHLYSTATS ---
class UserMonthlyStatsRepository(BaseRepository):

    def get_by_id(self, model_id: int):
        raise NotImplementedError("Використовуйте get_by_composite_key")

    def get_by_composite_key(self, user_id: int, year: int, month: int) -> Optional[UserMonthlyStats]:
        try:
            return UserMonthlyStats.objects.get(user_id=user_id, year=year, month=month)
        except UserMonthlyStats.DoesNotExist:
            return None

    def get_all(self) -> List[UserMonthlyStats]:
        return UserMonthlyStats.objects.all()

    def add(self, **kwargs) -> UserMonthlyStats:
        return UserMonthlyStats.objects.create(**kwargs)

    def update(self, model_id, **kwargs):
        user = kwargs.get('user')
        year = kwargs.get('year')
        month = kwargs.get('month')

        if not all([user, year, month]):
            raise ValueError("Для оновлення UserMonthlyStats потрібні user, year, month")

        stats, created = UserMonthlyStats.objects.update_or_create(
            user=user,
            year=year,
            month=month,
            defaults=kwargs
        )
        return not created

    def delete(self, **kwargs) -> bool:
        count, _ = UserMonthlyStats.objects.filter(
            user_id=kwargs.get('user_id'),
            year=kwargs.get('year'),
            month=kwargs.get('month')
        ).delete()
        return count > 0

    def get_distance_leaderboard_report(self):
        """Звіт: Глобальний лідерборд по загальній дистанції"""
        return UserMonthlyStats.objects.values('user__username').annotate(
            total_distance=Sum('total_distance_m')
        ).order_by('-total_distance')


# --- ЄДИНА ТОЧКА ДОСТУПУ (DataAccessLayer) ---
class DataAccessLayer:
    def __init__(self):
        self.users = UserRepository()
        self.profiles = ProfileRepository()
        self.activities = ActivityRepository()
        self.activity_points = ActivityPointRepository()
        self.comments = CommentRepository()
        self.followers = FollowerRepository()
        self.kudos = KudosRepository()
        self.user_stats = UserMonthlyStatsRepository()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass