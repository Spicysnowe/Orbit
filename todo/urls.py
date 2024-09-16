from django.urls import path
from .views import TaskListCreateView, TaskRetrieveUpdateView
urlpatterns = [
    path('', TaskListCreateView.as_view(), name='task-create-list'),
    path('<int:pk>/', TaskRetrieveUpdateView.as_view(), name='task-update-get'),

    
]