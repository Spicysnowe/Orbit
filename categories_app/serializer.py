from rest_framework import serializers
from .models import GlobalCategoryModel,CategoryModel
from icon_app.serializer import IconSerializer
class GlobalCategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = GlobalCategoryModel
        fields = ['id', 'title', 'type', 'color', 'icon_code', 'parent', 'subcategories']

    def get_subcategories(self, obj):
        # Get all categories where the parent is the current category
        subcategories = GlobalCategoryModel.objects.filter(parent=obj)
        return GlobalCategorySerializer(subcategories, many=True).data

# Serializer for listing only top-level categories (those without a parent)
class RootGlobalCategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = GlobalCategoryModel
        fields = ['id', 'title', 'type', 'color', 'icon_code', 'parent', 'subcategories']

    def get_subcategories(self, obj):
        # Recursively fetch subcategories
        return GlobalCategorySerializer(obj.subcategories.all(), many=True).data

class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = CategoryModel
        fields = ['id', 'title', 'type', 'color', 'icon_code', 'is_custom','parent', 'subcategories']

    def get_subcategories(self, obj):
        # Get all categories where the parent is the current category
        subcategories = CategoryModel.objects.filter(parent=obj)
        return CategorySerializer(subcategories, many=True).data

# Serializer for listing only top-level categories (those without a parent)
class RootCategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    icon_detail= IconSerializer(read_only= True)

    class Meta:
        model = CategoryModel
        fields = ['id', 'title', 'type', 'color', 'icon_code', 'is_custom','parent', 'subcategories', 'icon_detail']
    
    def __init__(self, *args, **kwargs):
        # Initialize the serializer with request context
        request = kwargs.get('context', {}).get('request', None)
        super().__init__(*args, **kwargs)
        
        # Exclude the `category_id` field for GET requests
        if request and request.method == 'GET':
            self.fields.pop('icon_code')
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['icon_detail']= IconSerializer(instance.icon_code).data
        return representation
    
    def validate(self, data):
        if not self.partial:
            if data.get('parent') is None and (data.get('color') is None or data.get('icon_code') is None):
                raise serializers.ValidationError({
                    'error': "Category must have icon and color"
                })
        else:
            if self.instance.parent is None:
                if 'icon_code' in data and data['icon_code'] is None:
                    raise serializers.ValidationError({
                        'error': "Top-level categories cannot have icon_code set to null."
                    })
                if 'color' in data and data['color'] is None:
                    raise serializers.ValidationError({
                        'error': "Top-level categories cannot have color set to null."
                    })
        return data

    def get_subcategories(self, obj):
        # Recursively fetch subcategories
        return CategorySerializer(obj.subcategories.all(), many=True).data
