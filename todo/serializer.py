from rest_framework import serializers
from .models import TaskModel
from categories_app.serializer import CategorySerializer
from icon_app.serializer import IconSerializer

class TaskSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(read_only=True)
    icon_detail= IconSerializer(read_only= True)

    class Meta:
        model= TaskModel
        fields= '__all__'
        read_only_fields= ['id','user', 'is_unstructured_task']
        extra_fields = ['icon_detail','category_detail']
    
    def __init__(self, *args, **kwargs):
        # Initialize the serializer with request context
        request = kwargs.get('context', {}).get('request', None)
        super().__init__(*args, **kwargs)
        
        # Exclude the `category_id` field for GET requests
        if request and request.method == 'GET':
            self.fields.pop('category')
            self.fields.pop('icon_code')
    
    def validate(self, data):
        # HACK for now: not keeping validation on start date time to be after curren tdate/time 
        # HACK and so update validations must not confilct with creation of past task as well


        if data.get('is_all_day_long'):
            if data.get('start_date') is None:
                 raise serializers.ValidationError({
                     'error': "start_date cannot be null if is_all_day_long is true"
                 })
            
            else:
                data['end_date'] = data['start_date']
                data['start_time'] = "00:00:00"
                data['end_time'] = "23:59:59"
                data['is_unstructured_task'] = False
        else:       
            if data.get('start_date') is None or data.get('start_time') is None or data.get('end_time') is None:
                data['is_unstructured_task'] = True
            elif data.get('end_date') is None:
                data['end_date'] = data['start_date']
                data['is_unstructured_task'] = False
            else:
                data['is_unstructured_task'] = False
            
        return data
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['category_detail'] = CategorySerializer(instance.category).data
        representation['icon_detail']= IconSerializer(instance.icon_code).data
        return representation
    


    def create(self, validated_data):
        # Set the user from the context (request) 
        # to link the task to authenticated user
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)