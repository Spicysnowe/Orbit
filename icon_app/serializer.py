from rest_framework import serializers
from .models import IconCategoryModel, IconsModel

class IconSerializer(serializers.ModelSerializer):
    class Meta:
        model = IconsModel
        fields = ['icon_code', 'icon_name', 'icon_url']

class IconCategorySerializer(serializers.ModelSerializer):
    icons_list = IconSerializer(source='icons', many=True, read_only=True)

    class Meta:
        model = IconCategoryModel
        fields = ['icon_category_title', 'icons_list']
