from rest_framework import generics
from .models import IconCategoryModel
from .serializer import IconCategorySerializer

class IconCategoryListView(generics.ListAPIView):
    queryset = IconCategoryModel.objects.all()
    serializer_class = IconCategorySerializer
