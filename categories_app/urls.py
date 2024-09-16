from django.urls import path
from .views import CategoryDetailView, CategoryListCreateView

urlpatterns = [
    # path('global/', GlobalCategoryView.as_view(), name='category-list'),

    path('', CategoryListCreateView.as_view(), name='user-category-list-create'),
    path('<int:pk>/', CategoryDetailView.as_view(), name='user-category-detail'),
]
