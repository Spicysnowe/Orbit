from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from icon_app.models import IconsModel
from categories_app.models import CategoryModel,CategoryType
from rest_framework.exceptions import ValidationError

User= get_user_model()


class TaskModel(models.Model):
    title= models.CharField(max_length=100, blank=False, null=False)
    task_color= models.CharField(max_length=10, blank=False, null = False)
    start_date = models.DateField(blank=False, null=True)        
    start_time = models.TimeField(blank=False, null=True)        
    end_date = models.DateField(blank=False, null=True)          
    end_time = models.TimeField(blank=False, null=True)
    priority = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        blank=False, null= False
    )
    is_unstructured_task= models.BooleanField(blank=False, null=False)
    is_all_day_long= models.BooleanField(blank=False, null=False)
    is_active= models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_tasks")
    icon_code= models.ForeignKey(IconsModel, to_field='icon_code', on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(CategoryModel,on_delete=models.SET_NULL,null=True)
    '''
    category
    repition
    reminder with note
    parent tasks
    steps

    status
    completion rate
    iscompleted

    '''
    def save(self, *args, **kwargs):
        # Ensure that the category is of type 'task'
        if self.category and self.category.type != CategoryType.TASK:
            raise ValidationError('Tasks can only be linked to categories of type "Task".')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title