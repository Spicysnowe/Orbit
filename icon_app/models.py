from django.db import models

class IconCategoryModel(models.Model):
    icon_category_title = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.icon_category_title

class IconsModel(models.Model):
    icon_category = models.ForeignKey(IconCategoryModel, on_delete=models.CASCADE, related_name="icons")
    icon_code = models.CharField(max_length=10, unique=True, primary_key=True)
    icon_name = models.CharField(max_length=100)
    icon_url = models.URLField()

    def __str__(self):
        return f'{self.icon_code} : {self.icon_name}'