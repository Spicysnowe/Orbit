from django.urls import path
from .views import IconCategoryListView

urlpatterns = [
    path('', IconCategoryListView.as_view(), name='icon-category-list'),
]
