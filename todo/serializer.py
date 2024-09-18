from rest_framework import serializers
from .models import TaskModel,TaskSteps
from categories_app.serializer import CategorySerializer
from icon_app.serializer import IconSerializer
from datetime import datetime

class TaskStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskSteps
        fields = ['id', 'title', 'is_completed', 'order']
        read_only_fields = ['id']

class TaskSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(read_only=True)
    icon_detail= IconSerializer(read_only= True)
    steps = TaskStepSerializer(many=True, required=False)

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
            else:

                
                    data['end_date'] = data['start_date'] if data.get('end_date') is None else data.get('end_date')
                    start_datetime = datetime.combine(data.get('start_date'), data.get('start_time'))
                    end_datetime = datetime.combine(data['end_date'], data.get('end_time'))

                    if start_datetime >= end_datetime:
                        raise serializers.ValidationError(
                            'The start date and time must be before the end date and time.'
                        )
                    data['is_unstructured_task'] = False
                
        
        if data.get('is_reminder') is True and data.get('reminder_time') is None:
            raise serializers.ValidationError({
                     'error': "If is_reminder is true reminder_time can't be null"
                 })
        elif data.get('reminder_time') is not None and  data.get('is_reminder')  is not True:
            data['is_reminder']=True
        
        parent_task = data.get('parent_id')


        if parent_task:
            # Combine parent's start and end date with time
            parent_start_datetime = datetime.combine(parent_task.start_date, parent_task.start_time)
            parent_end_datetime = datetime.combine(parent_task.end_date, parent_task.end_time)

            if (parent_task.end_date - parent_task.start_date).days < 2:
                raise serializers.ValidationError(
                    'Parent task span should be atleast two days.'
                )

            # Get the child task's start and end datetime from the validated data
            child_start_date = data.get('start_date')
            child_start_time = data.get('start_time')
            child_end_date = data.get('end_date')
            child_end_time = data.get('end_time')

            # Ensure the child task's start and end date/time are provided
            if child_start_date and child_start_time and child_end_date and child_end_time:
                # Combine child task's start and end date with time
                child_start_datetime = datetime.combine(child_start_date, child_start_time)
                child_end_datetime = datetime.combine(child_end_date, child_end_time)

                # Validation: Child task's datetime should be within parent's datetime range
                if not (parent_start_datetime <= child_start_datetime <= parent_end_datetime) or \
                   not (parent_start_datetime <= child_end_datetime <= parent_end_datetime):
                    raise serializers.ValidationError(
                        'Child task’s start and end datetime must be within the parent task’s start and end datetime.'
                    )
            
        return data
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['category_detail'] = CategorySerializer(instance.category).data
        representation['icon_detail']= IconSerializer(instance.icon_code).data
        representation['steps'] = TaskStepSerializer(instance.tasksteps_set.all(), many=True).data
        return representation
    


    def create(self, validated_data):
        steps_data = validated_data.pop('steps', [])
        # Set the user from the context (request) 
        # to link the task to authenticated user
        user = self.context['request'].user
        validated_data['user'] = user
        task = super().create(validated_data)

        for step_data in steps_data:
            TaskSteps.objects.create(task=task, **step_data)
        
        return task



'''
        CREATE:
         parent can only be there if task is more than of 2 days✅
         i parent is there : task st date time end time date should be between of parent task✅
         a task with no parent but with child will be a longtask✅
         
         UPDATE:
         parent startdtae tim update error agar kam kari child se , child ki agar jyada kri to error
         if already on going parent/ parent child? then update?
         for now: a task cannot be converted into child task

         GET:
          *** especially in case of list and retrieve (sometimes in update)***
          on calling parent task child mai list of child task aaye

'''



'''
    CREATE:
    steps model: done boolean? , step name✅
    steps creation ✅

    UPDTAE:
    if task already started then?


    GET:
    get all steps associated with task
'''
'''
    repition
    icon code automate 
    validation task past part update
    completion
'''
'''
analysis
'''