from django.forms import model_to_dict
from rest_framework import serializers
from .models import TaskModel, TaskActionItem, TaskReminder, TaskRecurranceModel, TaskSteps, TaskSubParts, RecurruranceType,ProgressStateType
from categories_app.serializer import CategorySerializer
from icon_app.serializer import IconSerializer
from datetime import datetime
from django.db import transaction
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from datetime import date


class TaskActionItemSerializer(serializers.ModelSerializer):
    action_id=serializers.IntegerField(write_only=True, required=False)
    class Meta:
        model = TaskActionItem
        fields = ['id', 'title', 'progress_rate', 'order', 'action_id']
        read_only_fields = ['id','created_on','updated_on']
        extra_fields= ['action_id']

class TaskReminderSerializer(serializers.ModelSerializer):
    reminder_id = serializers.IntegerField(write_only=True, required=False)
    class Meta: 
        model = TaskReminder
        fields= ['id', 'reminder_note', 'reminderEnabled', 'reminder_time', 'created_on', 'updated_on','reminder_id' ]
        read_only_fields= ['created_on','updated_on']
        extra_fields=['reminder_id']


class TaskRecurranceSerializer(serializers.ModelSerializer):
    # start_date = serializers.DateField(write_only=True, required=False)
    class Meta:
        model= TaskRecurranceModel
        exclude=['task', 'total_repeats', 'is_auto_extend']
        read_only_fields = ['id','created_on','updated_on']
        # extra_fields=['start_date']
    

    def validate(self, data):
        print("lets validate recurrance ", data.get('effective_date'))

        existing_instance= None
        if 'recrrance_id' in data:
            try:
                # Fetch the existing child instance
                existing_instance = TaskRecurranceModel.objects.get(id=data['recrrance_id'])
                
            except TaskRecurranceModel.DoesNotExist:
                existing_instance= None
            
            
        instance =   existing_instance if existing_instance is not None  else  self.instance
        
        
        type = data.get('recurrurance_type') or (instance.recurrurance_type if instance else None)
        recurrurance_data= data.get('recurrurance_data') or (instance.recurrurance_data if instance else None)
        repeat_forever = data.get('repeat_forever',)  or (instance.repeat_forever if instance else False)
        repeat_end_date = data.get('repeat_end_date')or(instance.repeat_end_date if instance else None)
        repeat_count = data.get('repeat_count') or (instance.repeat_count if instance else 1)
        effective_date= data.get('effective_date') or (instance.effective_date if instance else None)


        print("type", type)

        if type is None:
            raise serializers.ValidationError({"error":"Type must be provided"})
        
        elif type=="once":
            data['recurrurance_data']={}
            data['repeat_forever']=False
            data['repeat_end_date']=None
            data['repeat_count']=1

        
        else:
            if recurrurance_data is None:
                raise serializers.ValidationError({"error":"recurrurance_data needs to be provided"})
            
            required_keys = []
            if type== "daily":
                required_keys = ['repeat_every_x_days']            
            elif type== "weekly":
                required_keys = ['repeat_every_x_weeks', 'repeat_on_days']
            elif type== "monthly":
                required_keys = ['repeat_every_x_month', 'repeat_on_month_days']
            elif type== "weekly_times":
                required_keys = ['repeat_every_x_weeks', 'times_per_week']
            elif type== "monthly_times":
                required_keys = ['repeat_every_x_month', 'times_per_month']
            
            missing_keys = [key for key in required_keys if key not in recurrurance_data]
            if missing_keys:
                raise serializers.ValidationError(f"Missing required keys: {', '.join(missing_keys)}")
            

            conditions = [
                repeat_forever is True,               # True 
                repeat_end_date is not None,   # Check if a date is set
                repeat_count > 1              # Count greater than default
            ]

            if sum(conditions) < 1:
                raise serializers.ValidationError(
                    "One of 'repeat_forever', 'repeat_end_date', or 'repeat_count' must be provided "
                )
            elif sum(conditions) < 1:
                raise serializers.ValidationError(
                    "Only one of 'repeat_forever', 'repeat_end_date', or 'repeat_count' should be set."
                )
            
          


           
            if repeat_forever is True:
                data['total_repeats']=-1
                data['is_auto_extend']=True
            elif repeat_end_date: 
                print("effective_date", effective_date,"repeat_end_date",repeat_end_date )
                if effective_date is not None:
                    if effective_date.date()  >= repeat_end_date:
                        raise serializers.ValidationError(
                            f'The repeat_end_date must be after {effective_date} '
                        )
                    total_reps, dates= get_total_repeats(effective_date.date() ,repeat_end_date, type, recurrurance_data)
                    data['total_repeats']=total_reps
                    data['is_auto_extend']=total_reps >30
                    pass
                else:
                    data['total_repeats']=1
                    data['is_auto_extend']=False                  
            
            elif repeat_count:
                data['total_repeats']=repeat_count #(will be greater than executed one suppose 10 repeats already happened it will be 10+)
                data['is_auto_extend']=repeat_count>30
            
        
            # on normal rep update check if repeat is different from prev one
                #then if task is not started
                    # then update the data in the original instance of recurrance only
                    # then delete all parts and on new basis of recurrance create new subparts
                # if task is started   
                    # create new recurrance instance
                    # then delete future parts and on new basis of recurrance create new subparts
            
                
            
            


        return data
    
    def create(self, validated_data):
        instance = super().create(validated_data)
        return instance


class TaskStepsSerializer(serializers.ModelSerializer):

    class Meta:
        model= TaskSteps
        fields= ['title','order','progress_rate', 'task_steps_id']
        read_only_fields= ['id','created_on','updated_on']
    
    def validate(self, data):
        if self.instance is None:
            if data.get('progress_rate'):                
                data['progress_rate']=0                
        return data
    

class TaskSubPartsSerializer(serializers.ModelSerializer):
    steps= TaskStepsSerializer(many=True, read_only=True)
    class Meta:
        model= TaskSubParts
        fields='__all__'
        read_only_fields = ['id','created_on','updated_on']

    def create(self, validated_data):
        instance = super().create(validated_data)
        return instance

class TaskSerializer(serializers.ModelSerializer):
    is_all_day_long= serializers.BooleanField(write_only=True, required=False)
    category_detail = CategorySerializer(read_only=True)
    icon_detail= IconSerializer(read_only= True)
    reminders= TaskReminderSerializer(many=True, required=False)
    action_items = TaskActionItemSerializer(many=True, required=False)
    task_recurrance = TaskRecurranceSerializer(many=True, required=False) #while creating/ updating give a list but with only 1 instance
    task_sub_parts = TaskSubPartsSerializer(many=True, read_only=True) #getting automatically created based on other task and recurrance data
    task_steps= TaskStepsSerializer(many=True, write_only=True, required=False)


    class Meta:
        model= TaskModel
        fields= '__all__'
        read_only_fields= ['id','created_on','updated_on','user', 'is_long_task', 'progressState']
        extra_fields = ['icon_detail','category_detail','is_all_day_long','task_steps']
    
    def __init__(self, *args, **kwargs):
        # Initialize the serializer with request context
        request = kwargs.get('context', {}).get('request', None)
        super().__init__(*args, **kwargs)
        
        # Exclude the `category_id` field for GET requests
        if request and request.method == 'GET':
            self.fields.pop('category')
            self.fields.pop('icon_code')
    
    def to_internal_value(self, data):
        print("to_internal_value")
        instance = self.instance
        # Extract start_date from the TaskSerializer data
        start_date = data.get('start_date') or (instance.start_date if instance else None)
        current_date = date.today()

        # if the task is just created , new recurring instance will be created
        # if task not started, update existing recurring instance,  recrrance_id
        # else if task started create new recurring instance

        isTaskStarted= False        
        # checking especially for case if a task has already been started but since this is the first update/get so hasnt got updated in db
        if instance is not None and (instance.progressState is not ProgressStateType.NOTSTARTED or (instance.is_unstructured_task is False and current_date>=instance.start_date)):
            isTaskStarted= True
        
        recurrance_ids=[]
        if instance is not None:
            recurrance_ids = instance.task_recurrance.values_list('id', flat=True) 
            print(f"Associated Recurrence IDs: {list(recurrance_ids)}") 
        
        

        # Inject start_date into each task_recurrance entry
        task_recurrances_data = data.get('task_recurrance', [])
        for index,task_recurrance_data in enumerate(task_recurrances_data):
            task_recurrance_data['effective_date'] = start_date if  isTaskStarted is False else datetime.now()
            if instance is not None and isTaskStarted is False:
                task_recurrance_data['recrrance_id'] = recurrance_ids[index]


        # Call the parent class's to_internal_value method
        return super().to_internal_value(data)

    def validate(self, data):
        # HACK for now: not keeping validation on start date time to be after curren tdate/time 
        # HACK and so update validations must not confilct with creation of  task in past as well

        instance = self.instance  # This contains the existing instance if updating
        # Retrieve the relevant values
        start_date = data.get('start_date') or (instance.start_date if instance else None)
        begin_time = data.get('begin_time') or (instance.begin_time if instance else None)
        finish_time = data.get('finish_time') or (instance.finish_time if instance else None)
        end_date = data.get('end_date') or (instance.end_date if instance else None)
        is_unstructured_task = data.get('is_unstructured_task') or (instance.is_unstructured_task if instance else None)

        current_date = date.today()

        # while creating task is_active cannot be set 
        if instance is None:
            if data.get('is_active'):
                data['is_active']=True
               

            
                

        isTaskStarted= False
        
        # checking especially for case if a task has already been started but since this is the first update/get so hasnt got updated in db
        if instance is not None and (instance.progressState is not ProgressStateType.NOTSTARTED or (instance.is_unstructured_task is False and current_date>=instance.start_date)):
            isTaskStarted= True

        
        if isTaskStarted:
            if start_date is None or begin_time is None or finish_time is None or end_date is None:
                raise serializers.ValidationError({"error":"Date times of a task cannot be made null after its start"})
            else:
                start_datetime = datetime.combine(start_date,begin_time)
                end_datetime = datetime.combine(end_date, finish_time)
                is_instance_long_task= instance.is_long_task

                if start_datetime >= end_datetime:
                    raise serializers.ValidationError(
                        'The start date and time must be before the end date and time.'
                    )
                
                if is_instance_long_task is True :
                    if (end_datetime - start_datetime).days <= 1:
                        raise serializers.ValidationError(
                            'A long task cannot be converted into a short task'
                        )
                    elif data.get('start_date') or data.get('begin_time'):
                        raise serializers.ValidationError(
                        'The start date and begin time cannot be changed of a long task.'
                        )
                    
                    else:
                        # if end date time check child and error
                        child_tasks = instance.child.all()
                        for child in child_tasks:
                            child_end_datetime = datetime.combine(child.end_date, child.finish_time)                           
                            if child_end_datetime > end_date:
                                raise serializers.ValidationError(
                                    f"Child task '{child.title}' has end date time {child_end_datetime}, which is after the new end date time{end_date}."
                                )


                elif is_instance_long_task is False :
                    if (end_datetime - start_datetime).days > 1:
                        raise serializers.ValidationError(
                            'A short task cannot be converted into a long task'
                        )
                    
                    elif data.get('start_date') or data.get('end_date'):
                        raise serializers.ValidationError(
                        'The start date and end_date cannot be changed of a long task.'
                        )
                    # no conditions are on begin and finsish time
                    # TODO: but update future subparts
                    
                
                

                
        else:

            data['progress_percentage']=0
            
            if data.get('is_all_day_long'):
                if start_date is None:
                    raise serializers.ValidationError({
                        'error': "start_date cannot be null if is_all_day_long is true"
                    })
                
                else:
                    data['end_date'] = start_date
                    data['begin_time'] = "00:00:00"
                    data['finish_time'] = "23:59:59"
            
                    
            # print("whats up")
            if start_date is None or begin_time is None or finish_time is None or end_date is None:
                data['is_unstructured_task'] = True
                data['is_long_task']=False
            else:                
                        print("lets check time ")
                        start_datetime = datetime.combine(start_date,begin_time)
                        end_datetime = datetime.combine(end_date, finish_time)

                        if start_datetime >= end_datetime:
                            raise serializers.ValidationError(
                                'The start date and time must be before the end date and time.'
                            )
                        

                        elif (end_datetime - start_datetime).days > 1:
                            
                            data['is_long_task']=True
                        else:
                            data['is_long_task']=False
                    
            
           
        
        is_task_long = data['is_long_task'] if data['is_long_task'] is not None else instance.is_long_task if instance else False

        if is_task_long and data.get('task_recurrance'):
            raise serializers.ValidationError({"error":"Long tasks cannot have recuraance"})
        if is_task_long and data.get('task_steps'):
            raise serializers.ValidationError({"error":"Long tasks cannot have task_steps"})
        if is_task_long is False and data.get('action_items'):
            raise serializers.ValidationError({"error":"Short tasks cannot have action items"})
        
       
        
       
       
        # parent id can be set only during creation and not during update
        data['parent_id']=data.get('parent_id') if instance is None else instance.parent_id
        parent_task = data['parent_id']

        if parent_task:
            if parent_task.is_unstructured_task is False and data.get('is_unstructured_task') is False:
                # Combine parent's start and end date with time
                parent_start_datetime = datetime.combine(parent_task.start_date, parent_task.begin_time)
                parent_end_datetime = datetime.combine(parent_task.end_date, parent_task.finish_time)
            

                if parent_task.is_long_task is not True:
                    raise serializers.ValidationError(
                        'Parent task span should be atleast one day.'
                    )

                # Get the child task's start and end datetime from the validated data
                child_start_date = start_date
                child_start_time =begin_time
                child_end_date = end_date
                child_end_time = finish_time

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
            else: 
                data['is_unstructured_task']= True
                
            
        return data
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['category_detail'] = CategorySerializer(instance.category).data
        representation['icon_detail']= IconSerializer(instance.icon_code).data
        representation['reminders']=TaskReminderSerializer(instance.reminders.all(), many=True).data
        representation['action_items'] = TaskActionItemSerializer(instance.action_items.all(), many=True).data
    
        return representation

    def create(self, validated_data):
        '''
        ifclashing data is coming in request  like
          with short or null or is_all_day_long: action items -> then error
          with is_all_day_long: long date time-> auto set
          with long date time: task_recurrance,subparts -> error
          with long date time: task_steps-> error         
        '''
        
        reminders_data = validated_data.pop('reminders', [])
        action_items_data = validated_data.pop('action_items', [])
        task_recurrance=  validated_data.pop('task_recurrance', [])
        is_all_day_long=  validated_data.pop('is_all_day_long', False)
        task_steps=  validated_data.pop('task_steps', [])
        # Set the user from the context (request) 
        # to link the task to authenticated user
        user = self.context['request'].user
        validated_data['user'] = user
        task = super().create(validated_data)

        if task.is_long_task is False:

            recurrance_data = task_recurrance[0] if task_recurrance and task_recurrance[0] else {
                'effective_date': datetime.combine(task.start_date, datetime.min.time()) if task.start_date is not None else task.start_date,              
            }
            recurrance=TaskRecurranceModel.objects.create(task=task, **recurrance_data)            
            
            print("recurrance", recurrance)

            create_task_subparts(task, recurrance, is_all_day_long,task_steps)
                

        for action_item_data in action_items_data:
            TaskActionItem.objects.create(task=task, **action_item_data)
        for reminder_data in reminders_data:
            TaskReminder.objects.create(task=task, **reminder_data)
        
        return task
     
    def update(self, instance, validated_data):
        print(f"validated_data: {validated_data}")
        task_recurrance=  validated_data.pop('task_recurrance', [])
        original_task_is_long= instance.is_long_task
        reminders_data = validated_data.pop('reminders', [])
        action_items_data = validated_data.pop('action_items', [])
        is_all_day_long=  validated_data.pop('is_all_day_long', None)
        task_steps=  validated_data.pop('task_steps', None)#handle error above

        with transaction.atomic():
            # Update the task instance
            task = super().update(instance, validated_data)

            recurrance_result= handle_task_recurrance_update(original_task_is_long, task, task_recurrance)
            handle_task_subparts_update(original_task_is_long, task, task_recurrance, recurrance_result, is_all_day_long,task_steps)




            # Update or create action items
            existing_action_items = {action_item.id: action_item for action_item in task.action_items.all()}
            incoming_actions_ids = []
            for action_item_data in action_items_data:
                action_item_id = action_item_data.get('action_id')  # Assuming each action item has an 'id' for updates
                if action_item_id and action_item_id in existing_action_items:
                    incoming_actions_ids.append(action_item_id)
                    action_item = existing_action_items[action_item_id]
                    for attr, value in action_item_data.items():
                        setattr(action_item, attr, value)
                    action_item.save()
                elif action_item_id:
                    raise serializers.ValidationError(f"Action item with id {action_item_id} not found.")
                else:
                    TaskActionItem.objects.create(task=task, **action_item_data)
            for action_item_id, action_item in existing_action_items.items():
                if action_item_id not in incoming_actions_ids:
                    action_item.delete()

            # Update or create reminders
            existing_reminders = {reminder.id: reminder for reminder in task.reminders.all()}
            incoming_reminder_ids = []
            for reminder_data in reminders_data:
                reminder_id = reminder_data.get('reminder_id')  # Get the id for the reminder
                if reminder_id and reminder_id in existing_reminders:
                    incoming_reminder_ids.append(reminder_id)
                    reminder = existing_reminders[reminder_id]
                    for attr, value in reminder_data.items():
                        setattr(reminder, attr, value)
                    reminder.save()
                elif reminder_id:
                    raise serializers.ValidationError(f"Reminder with id {reminder_id} not found.")
                else:
                    TaskReminder.objects.create(task=task, **reminder_data)
            for reminder_id, reminder in existing_reminders.items():
                if reminder_id not in incoming_reminder_ids:
                    reminder.delete()

        return task


def create_task_subparts(task, recurrance, is_all_day_long,task_steps):
    
    subparts_list=[]
    start_date= recurrance.effective_date.date()
    subpart_counts= 30 if recurrance.total_repeats==-1 or recurrance.total_repeats>30  else recurrance.total_repeats
    if recurrance.recurrurance_type== RecurruranceType.ONCE or start_date is None:
        subpart_data={
            'date':start_date,
            'start_time': task.begin_time,
            'end_time':task.finish_time,
            'recurrance_id': recurrance.id,
            'is_all_day_long': is_all_day_long,
            'task': task.id
        }
        subparts_list.append(
            subpart_data
        )

    elif recurrance.recurrurance_type== RecurruranceType.DAILY:
        repeat_every_x_days = recurrance.recurrurance_data.get('repeat_every_x_days', 0)
       
        for i in range(subpart_counts):
            subpart_data={
                'date':start_date,
                'start_time': task.begin_time,
                'end_time':task.finish_time,
                'recurrance_id': recurrance.id,
                'task': task.id,
                'is_all_day_long': is_all_day_long,
            }        
            subparts_list.append(subpart_data)
            start_date += timedelta(days=repeat_every_x_days)          
    
    elif recurrance.recurrurance_type== RecurruranceType.WEEKLY:
        repeat_every_x_weeks = recurrance.recurrurance_data.get('repeat_every_x_weeks', 0)
        repeat_on_days = recurrance.recurrurance_data.get('repeat_on_days', 0)

        current_date = start_date
        
        for _ in range(subpart_counts):
            for day in repeat_on_days:
                next_date = current_date + timedelta(days=(day - current_date.weekday() + 7) % 7)
                
                if next_date >= start_date:
                    subpart_data = {
                        'date': next_date,
                        'start_time': task.begin_time,
                        'end_time': task.finish_time,
                        'recurrance_id': recurrance.id,
                        'task': task.id,
                        'is_all_day_long': is_all_day_long,
                    }
                    subparts_list.append(subpart_data)
                    
                    # Stop if we have created the required number of subparts
                    if len(subparts_list) >= subpart_counts:
                        break

            # Move to the next week block based on `repeat_every_x_weeks`
            current_date += timedelta(weeks=repeat_every_x_weeks)
        

    elif recurrance.recurrurance_type== RecurruranceType.MONTHLY:
        repeat_every_x_month = recurrance.recurrurance_data.get('repeat_every_x_month', 0)
        repeat_on_month_days = recurrance.recurrurance_data.get('repeat_on_month_days', 0)
        

        current_date = start_date
        
        for _ in range(subpart_counts):
            for day in repeat_on_month_days:
                # Create a potential next date
                try:
                    next_date = current_date.replace(day=day)
                except ValueError:
                    # If the day is invalid for the month, adjust to the next valid date
                    next_date = current_date + relativedelta(months=1)
                    next_date = next_date.replace(day=1)  # Go to the first of next month

                if next_date >= start_date:
                    subpart_data = {
                        'date': next_date,
                        'start_time': task.begin_time,
                        'end_time': task.finish_time,
                        'recurrance_id': recurrance.id,
                        'task': task.id,
                        'is_all_day_long': is_all_day_long,
                    }
                    subparts_list.append(subpart_data)

                    # Stop if we have created the required number of subparts
                    if len(subparts_list) >= subpart_counts:
                        break

            # Move to the next month block based on `repeat_every_x_month`
            current_date += relativedelta(months=repeat_every_x_month)
   
    else:
        pass
        #TODO WEEKLY MONTHLY TIMES CASE

    for subpart in subparts_list:
        task_subpart_serializer = TaskSubPartsSerializer(data=subpart)
        task_subpart_serializer.is_valid(raise_exception=True)  # This will validate the entire model
        created_subpart= task_subpart_serializer.save()


        for steps in task_steps:
            TaskSteps.objects.create(task=created_subpart, **steps)
      
            

def get_total_repeats(effective_date, end_date, type, recurrance_data):
    current_date = effective_date
    dates = []
    if type== 'daily':
        repeat_every_x_days = recurrance_data.get('repeat_every_x_days', 0)
        while current_date <= end_date:
            dates.append(current_date.strftime('%d-%b-%Y'))
            current_date += timedelta(days=repeat_every_x_days)

        pass
    elif type== 'weekly':
        repeat_every_x_weeks = recurrance_data.get('repeat_every_x_weeks', 1)  # Default to 1 week
        repeat_on_days = recurrance_data.get('repeat_on_days', [1])  # Default to Monday if not provided

        # Start generating dates
        for week_offset in range((end_date - effective_date).days // (7 * repeat_every_x_weeks) + 1): 
            for day in repeat_on_days:
                # Calculate the next occurrence of 'day' in the current week
                next_date = effective_date + timedelta(weeks=week_offset * repeat_every_x_weeks)
                next_date += timedelta(days=(day - 1))  # Adjust for 0-based index (Monday = 0)

                if next_date <= end_date:
                    dates.append(next_date.strftime('%d-%b-%Y'))

        
    elif type== 'monthly':
        repeat_every_x_month = recurrance_data.get('repeat_every_x_month', 1)
        repeat_on_month_days = recurrance_data.get('repeat_on_month_days', [1])

        # Iterate over months until the end_date
        while current_date <= end_date:
            for day in repeat_on_month_days:
                # Create a potential next date
                try:
                    next_date = current_date.replace(day=day)
                except ValueError:
                    # If the day is invalid for the month, adjust to the next valid date
                    next_date = current_date + relativedelta(months=1)
                    next_date = next_date.replace(day=1)  # Go to the first of next month

                if next_date <= end_date:
                    # Only add if it's not already in the list
                    if next_date.strftime('%d-%b-%Y') not in dates:
                        dates.append(next_date.strftime('%d-%b-%Y'))
                    else:
                        # Increment the date by one day
                        next_date += timedelta(days=1)
                        dates.append(next_date.strftime('%d-%b-%Y'))

            # Move to the next month block based on `repeat_every_x_month`
            current_date += relativedelta(months=repeat_every_x_month)
    else:
        pass
        #TODO WEEKLY MONTHLY TIMES CASE
    
    return len(dates), dates

    

def handle_task_recurrance_update(original_task_is_long,  task,task_recurrance ):
    recurrance= None

    # long->long (for both started/ not started task )
    if original_task_is_long is True and task.is_long_task is True:
        # do nothing to keep recurrance []
        pass

    # short->long (for not started task)
    elif original_task_is_long is False and task.is_long_task is True:

        # delete the recurrance instance
        task.task_recurrance.all().delete()
        

    # long->short (for not started task)
    elif original_task_is_long is True and task.is_long_task is False:

        # cretae a recurrance instance wth given data or default
        recurrance_data = task_recurrance[0] if task_recurrance and task_recurrance[0] else {
        'effective_date': datetime.combine(task.start_date, datetime.min.time()) if task.start_date is not None else task.start_date,              
        }
        recurrance=TaskRecurranceModel.objects.create(task=task, **recurrance_data)     
        

    # short->short (for both started/ not started task )
    else:
        # if task is not started
        if task.progressState is ProgressStateType.NOTSTARTED:
            # partial update
            if task_recurrance and task_recurrance[0]:
                instance_id= task_recurrance[0].pop('recrrance_id', None)
                recurrance_data = task_recurrance[0]
                if instance_id is not None:
                    affected_rows = TaskRecurranceModel.objects.filter(id=instance_id).update(**recurrance_data)
                    recurrance = None if affected_rows == 0 else affected_rows
                else:
                    recurrance = None            
        else:
            # create new if updates provided
            recurrance_data = task_recurrance[0] if task_recurrance and task_recurrance[0] else None
            recurrance=TaskRecurranceModel.objects.create(task=task, **recurrance_data) if recurrance_data is not None else None

    return recurrance
                    
    


def handle_task_subparts_update(original_task_is_long,  task, recurrance_result,is_all_day_long,task_steps ):
            
            # long->long (for both started/ not started task )
            if original_task_is_long is True and task.is_long_task is True:
                # do nothing to keep subparts []
                pass

            # short->long (for not started task)
            elif original_task_is_long is False and task.is_long_task is True:
                # delete subparts
                task.task_sub_parts.all().delete()


            # long->short (for not started task)
            elif original_task_is_long is True and task.is_long_task is False:
                # create subparts
                '''
                if is_all_day_long not given by user then keep it false as there are no subpart instances currently 
                i.e. we are creating completely new so that's why by default it can be false
                '''              
                is_all_day_long= False if is_all_day_long is None else is_all_day_long
                task_steps= [] if task_steps is None else task_steps
                create_task_subparts(task, recurrance_result, is_all_day_long,task_steps)  


            # short->short (for both started/ not started task )
            else:
                # update in recurrance
                if recurrance_result is not None:
                    # if task not started  (task unstructured h and start date h aaj to isliye if else krna pda to include this scenario too)
                    if task.progressState is ProgressStateType.NOTSTARTED:
                        # delete all instances
                        first_sub_part= task.task_sub_parts.first()
                        is_all_day_long= first_sub_part.is_all_day_long if is_all_day_long is None else is_all_day_long
                        task.task_sub_parts.all().delete()                       
                    else:
                        # delete future instances (tommowrow's date)
                        tomorrow = datetime.now().date() + timedelta(days=1)
                        subparts_to_delete = TaskSubParts.objects.filter(date__gte=tomorrow)
                        first_sub_part = subparts_to_delete.first()
                        is_all_day_long= first_sub_part.is_all_day_long if is_all_day_long is None else is_all_day_long
                        deleted_count, _ = subparts_to_delete.delete()                                            
                    
                    # create new instances old or coming updated data
                    create_task_subparts(task, recurrance_result, is_all_day_long,task_steps) 
                    
                    
                else:
                    # if task not started  (task unstructured h and start date h aaj to isliye if else krna pda to include this scenario too)
                    

                    if task.progressState is ProgressStateType.NOTSTARTED:
                        # update all instances with updated data
                        first_sub_part = task.task_sub_parts.first()
                        is_all_day_long= first_sub_part.is_all_day_long if is_all_day_long is None else is_all_day_long
                        update_data={
                            'start_time': task.begin_time,
                            'end_time':task.finish_time,
                            'is_all_day_long': is_all_day_long,
                        }
                        TaskSubParts.objects.all().update(**update_data)


                        
                    else:
                        # update future instances with updated data(tommowrow's date)
                        tomorrow = datetime.now().date() + timedelta(days=1)
                        filtered_instances = TaskSubParts.objects.filter(date__gte=tomorrow)
                        first_sub_part = filtered_instances.first()
                        is_all_day_long= first_sub_part.is_all_day_long if is_all_day_long is None else is_all_day_long
                        update_data={
                            'start_time': task.begin_time,
                            'end_time':task.finish_time,
                            'is_all_day_long': is_all_day_long,
                        }
                        filtered_instances.update(**update_data)
                        
                    

               
def handle_task_steps_update(task,old_subpart_instance, task_steps):
    existing_steps= old_subpart_instance.steps.all()
    ids_in_request=[]
    for task_step in task_steps:
        if 'task_step_id' in task_step:
            # if task step id is there-> update
            ids_in_request.append(task_step.get('task_step_id'))
            TaskSteps.objects.filter(id=task_step.get('task_step_id')).update(**task_step)
            
            
        else:
            # if no id-> create
            for subpart in task.task_sub_parts.all():
                TaskSteps.objects.create(task=subpart, **task_step)
            pass



     # those whose ids left-> delete
    existing_step_ids = [step.task_step_id for step in existing_steps]
    deleted_ids= set(existing_step_ids) - set(ids_in_request)

    if deleted_ids:
        TaskSteps.objects.filter(task_step_id__in=deleted_ids).delete()
   
    
                    

















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
    CREATE:
    for task with child: repition= null
    for task without child and parent : unlimited repition
    for task without child but with parent: repition till parent enddate


    UPDATE:
    a task with chil: remove child: parent task rep=null as earlier
    a task witout child gets : gets child: rep= null
    a task with parent : end dtaes change: reps limit date change


'''


'''
    
    icon code automate 
    validation task past part update
    completion
'''
'''
analysis
'''