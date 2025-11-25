from django.contrib import admin
from .models import (
    Activity,
    Profile,
    Comment,
    Kudos,
    Follower,
    ActivityPoint,
    UserMonthlyStats
)

# Реєструємо всі ваші моделі, щоб ви бачили їх в /admin/
admin.site.register(Activity)
admin.site.register(Profile)
admin.site.register(Comment)
admin.site.register(Kudos)
admin.site.register(Follower)
admin.site.register(ActivityPoint)
admin.site.register(UserMonthlyStats)