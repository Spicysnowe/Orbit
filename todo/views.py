from django.shortcuts import render
from .serializer import TaskSerializer
from rest_framework import generics, permissions
from .models import TaskModel
from datetime import datetime
from rest_framework.exceptions import ValidationError

class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        
        user = self.request.user
        
        task_date = self.request.query_params.get('date', None)
        is_task_unstructured=self.request.query_params.get('is_unstructured',None)

        if is_task_unstructured is not None:
            is_task_unstructured = is_task_unstructured.lower() == 'true'


        if  is_task_unstructured is True:
            return TaskModel.objects.filter(user=user,is_active=True, is_unstructured= True).order_by('start_date__isnull','start_date','start_time__isnull','start_time')
        elif  is_task_unstructured is False:
            if task_date:
                try:                
                    task_date = datetime.strptime(task_date, '%Y-%m-%d').date()
                except ValueError:
                    raise ValidationError({"message": "You are retrieving structured tasks" ,"date": "Date format should be YYYY-MM-DD"})
            return TaskModel.objects.filter(user=user,is_active=True, is_unstructured= False, start_date__lte=task_date,end_date__gte=task_date ).order_by('start_time')
        else:
            # all task of authenticted user
            # without filtering by unstructured, active, date, time
            return TaskModel.objects.filter(user=user).order_by('start_date').order_by('start_time')

        

    def get_serializer_context(self):
        # Pass the request to the serializer context
        return {'request': self.request}

class TaskRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TaskModel.objects.filter(user=self.request.user)
