from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import CategoryModel, CategoryType
from .serializer import RootCategorySerializer

# class GlobalCategoryView(generics.ListCreateAPIView):
#     queryset = GlobalCategoryModel.objects.filter(parent=None)
#     serializer_class = RootCategorySerializer

class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = RootCategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        category_type= self.request.query_params.get('type', None)
        if category_type is not None:
            if category_type in CategoryType.values:
                return CategoryModel.objects.filter(user=self.request.user, parent=None, type= category_type)
            else:
                raise ValidationError({"error": "Not a valid type"})
        
                    
        else:
            return CategoryModel.objects.filter(user=self.request.user, parent=None)

    def perform_create(self, serializer):
        try:
            serializer.save(user=self.request.user, is_custom=True)
        except IntegrityError:
            raise ValidationError({
                "error": "A category with this title already exists for this user."
            })


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RootCategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CategoryModel.objects.filter(user=self.request.user)
    

    def perform_update(self, serializer):
        try:
            serializer.save()
        except IntegrityError:
            raise ValidationError({
                "error": "A category with this title already exists for this user."
            })
