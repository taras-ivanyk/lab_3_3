from django.shortcuts import render, get_object_or_404, redirect
from activities.models import Comment
from .forms import CommentForm
from django.contrib.auth.decorators import login_required
from .NetworkHelper import NetworkHelper

def comment_list(request):
    """Список всіх коментарів з посиланнями на деталі"""
    comments = Comment.objects.select_related('activity', 'user').all()
    return render(request, 'lab33/comment_list.html', {'comments': comments})

def comment_detail(request, pk):
    """Деталі конкретного коментаря"""
    comment = get_object_or_404(Comment, pk=pk)
    return render(request, 'lab33/comment_detail.html', {'comment': comment})

@login_required
def comment_create(request):
    """Створення коментаря"""
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user  # Прив'язуємо до поточного юзера
            comment.save()
            return redirect('lab33:comment_list')
    else:
        form = CommentForm()
    return render(request, 'lab33/comment_form.html', {'form': form, 'action': 'Create'})

@login_required
def comment_update(request, pk):
    """Редагування коментаря"""
    comment = get_object_or_404(Comment, pk=pk)

    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('lab33:comment_detail', pk=comment.pk)
    else:
        form = CommentForm(instance=comment)
    return render(request, 'lab33/comment_form.html', {'form': form, 'action': 'Update'})

@login_required
def comment_delete(request, pk):
    """Видалення коментаря"""
    comment = get_object_or_404(Comment, pk=pk)
    if request.method == "POST":
        comment.delete()
        return redirect('lab33:comment_list')
    return render(request, 'lab33/comment_confirm_delete.html', {'comment': comment})


def external_activity_list(request):
    """Відображення даних, отриманих через requests"""
    helper = NetworkHelper()

    # Отримуємо список із "чужого" проекту
    activities = helper.get_list()

    return render(request, 'lab33/external_list.html', {'activities': activities})


def external_activity_delete(request, pk):
    """Видалення об'єкта у 'чужому' проекті"""
    if request.method == "POST":
        helper = NetworkHelper()
        success = helper.delete_item(pk)
        if success:
            print("Успішно видалено!")
        else:
            print("Помилка видалення!")

    return redirect('lab33:external_list')