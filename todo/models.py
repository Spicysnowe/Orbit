from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from icon_app.models import IconsModel
from categories_app.models import CategoryModel,CategoryType
from rest_framework.exceptions import ValidationError
from base_app.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _

User= get_user_model()

class ProgressStateType(models.TextChoices):
    NOTSTARTED = 'notstarted', 'NotStarted'
    ONGOING = 'ongoing', 'Ongoing'
    PENDING = 'pending', 'Pending'
    COMPLETED= 'completed','Completed'


class TaskModel(TimeStampedModel):
    title= models.CharField(max_length=100, blank=False, null=False)
    icon_code= models.ForeignKey(IconsModel, to_field='icon_code', on_delete=models.SET_NULL, null=True)
    task_color= models.CharField(max_length=10, blank=False, null = False)
    category = models.ForeignKey(CategoryModel,on_delete=models.SET_NULL,null=True)
    priority = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        blank=False, null= False,default=0
    )#0 is default lowest 1 is a bit higher  5 is highest
    # connected with reminder model  
    start_date = models.DateField(blank=False, null=True)        
    begin_time = models.TimeField(blank=False, null=True)        
    end_date = models.DateField(blank=False, null=True)          
    finish_time = models.TimeField(blank=False, null=True)
    # recurrance
    # subparts
    parent_id= models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child')
    is_long_task= models.BooleanField(default=False)
    # actionitems    
    is_unstructured_task= models.BooleanField(default=True)
    is_active= models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_tasks")
    
    progress_percentage= models.PositiveSmallIntegerField(default=0)
    progressState= models.CharField(max_length=15, choices=ProgressStateType.choices, default=ProgressStateType.NOTSTARTED)
    
    
    
    '''
    
    repition
    
    status
    completion rate
    iscompleted

    icon code automate 
    validation task past part update

    '''
    def save(self, *args, **kwargs):
        # Ensure that the category is of type 'task'
        if self.category:
            if self.category.user != self.user:
                raise ValidationError(_(f'This category does not belong to the logged-in user.'))
            if self.category.type != CategoryType.TASK:
                raise ValidationError('Tasks can only be linked to categories of type "Task".')
        super().save(*args, **kwargs)

       
    def __str__(self):
        return self.title
    
class TaskReminder(TimeStampedModel):
    reminder_note = models.CharField(max_length= 100, blank=True, null=False)
    reminderEnabled=models.BooleanField(default=False)
    reminder_time= models.TimeField(blank=False, null=False)
    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE, related_name="reminders")  

    def __str__(self):
        return f"{self.id} {self.task}: time- {self.reminder_time}"

class TaskActionItem(TimeStampedModel):
    title = models.CharField(max_length=255, blank=False)
    progress_rate= models.PositiveSmallIntegerField(default=0)
    order = models.PositiveIntegerField(null=False)
    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE, related_name="action_items")  
    

    class Meta:
        ordering = ['order']  

    def __str__(self):
        return self.title

class RecurruranceType(models.TextChoices):
    ONCE = 'once', 'Once'
    DAILY = 'daily', 'Daily'
    WEEKLY = 'weekly', 'Weekly'
    WEEKLYTIMES= 'weekly_times', 'Weekly_Times'
    MONTHLY = 'monthly', 'Monthly'
    MONTHLYTIMES= 'monthly_times', 'Monthly_Times'


class TaskRecurranceModel(TimeStampedModel):
    recurrurance_type= models.CharField(max_length=15, choices=RecurruranceType, default=RecurruranceType.ONCE)
    recurrurance_data = models.JSONField(null=False, blank=False, default=dict)
    
    repeat_forever= models.BooleanField(default=False)#for frontend
    repeat_end_date= models.DateField(blank=False, null=True)   #for frontend
    repeat_count= models.PositiveBigIntegerField(default=0) #for frontend

    # for backend
    total_repeats= models.IntegerField(default=1)
    is_auto_extend= models.BooleanField(default=False)
    
    effective_date= models.DateTimeField(blank=False, null=True)# the date after which this new created will apply instead of old one
    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE, related_name="task_recurrance")  

    class Meta:
        ordering = ['effective_date'] 

    def __str__(self):
        return f'{self.task}: {self.recurrurance_type}'



class TaskSubParts(TimeStampedModel):
    date= models.DateField(blank=False, null=True)
    start_time = models.TimeField(blank=False, null=True)        
    end_time = models.TimeField(blank=False, null=True)
    is_all_day_long= models.BooleanField(default=False)
    progress_rate= models.PositiveSmallIntegerField(default=0)
    progressState= models.CharField(max_length=15, choices=ProgressStateType.choices, default=ProgressStateType.NOTSTARTED)
    recurrance_id= models.ForeignKey(TaskRecurranceModel, on_delete=models.CASCADE, related_name="task_sub_parts")
    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE, related_name="task_sub_parts")  

    class Meta:
        ordering = ['date'] 

    def __str__(self):
        return f'{self.task}: {self.date}'

class TaskSteps(TimeStampedModel):
    title = models.CharField(max_length=255, blank=False)
    progress_rate= models.PositiveSmallIntegerField(default=0)
    order = models.PositiveIntegerField(null=False)
    task = models.ForeignKey(TaskSubParts, on_delete=models.CASCADE, related_name="steps")  
    task_steps_id= models.CharField(max_length=255, blank=False, editable=False)

    class Meta:
        ordering = ['order']  

    def save(self, *args, **kwargs):
        if not self.task_steps_id:
            related_steps = TaskSteps.objects.filter(task__task=self.task.task).order_by('id')
            last_step = related_steps.last()
            next_id= 1 if last_step is None else int(last_step.task_steps_id.split('_')[-1])+1
            self.task_steps_id = f'task_{self.task.task.id}_{next_id}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.task_steps_id}_{self.task.id} : {self.title}'
    
'''
for not long task :
if no reccurance in db then by default create once recurrance
if recurrance is their then if new comes and same as old one just update details no need to create new one
otherwise create a new one
and get the last one from order(latest)
and inke respect mai subparts
'''