from django.contrib import admin
from .models import TaskModel, TaskActionItem, TaskReminder,TaskRecurranceModel, TaskSteps,TaskSubParts
admin.site.register(TaskModel)  
admin.site.register(TaskActionItem)  
admin.site.register(TaskReminder) 
admin.site.register(TaskRecurranceModel) 
admin.site.register(TaskSteps) 
admin.site.register(TaskSubParts)  