from django.db import models
from icon_app.models import IconsModel
from django.contrib.auth import get_user_model

User=  get_user_model()

class AbstractBaseCategory(models.Model):
    title = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')

    class Meta:
        abstract = True

    def __str__(self):
        return self.title

class CategoryType(models.TextChoices):
    INCOME = 'income', 'Income'
    EXPENSE = 'expense', 'Expense'
    TASK = 'task', 'Task'

class GlobalCategoryModel(AbstractBaseCategory):
    type = models.CharField(max_length=10, choices=CategoryType.choices)
    color = models.CharField(max_length=10, blank=True, null=True)
    icon_code = models.ForeignKey(IconsModel, to_field='icon_code', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Global Category'
        verbose_name_plural = 'Global Categories'
        constraints = [
            models.UniqueConstraint(fields=['title'], name='unique_global_category')
        ]

    def save(self, *args, **kwargs):
        # Ensure subcategories do not have color or icon_code
        if self.parent:
            self.color = None
            self.icon_code = None
        super().save(*args, **kwargs)


class CategoryModel(AbstractBaseCategory):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_categories")
    type = models.CharField(max_length=10, choices=CategoryType.choices)
    color = models.CharField(max_length=10, blank=True, null=True)
    icon_code = models.ForeignKey(IconsModel, to_field='icon_code', on_delete=models.SET_NULL, null=True, blank=True)
    is_custom = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        constraints = [
            models.UniqueConstraint(fields=['user', 'title'], name='unique_user_category')
        ]

    def save(self, *args, **kwargs):
        # Ensure subcategories do not have color or icon_code
        if self.parent:
            self.color = None
            self.icon_code = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.title}"
