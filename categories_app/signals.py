from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import GlobalCategoryModel, CategoryModel
from django.contrib.auth import get_user_model

User= get_user_model()

@receiver(post_save, sender=User)
def copy_global_categories(sender, instance, created, **kwargs):
    print("Im in copy func")
    if created:
        # Fetch all global categories
        global_categories = GlobalCategoryModel.objects.all()

        # Create root categories first (those without parents)
        root_categories = []
        for global_category in global_categories.filter(parent__isnull=True):
            root_category = CategoryModel(
                user=instance,
                title=global_category.title,
                parent=None,  # Root categories have no parent
                type=global_category.type,
                color=global_category.color,
                icon_code=global_category.icon_code,
                is_custom=False
            )
            root_categories.append(root_category)

        # Bulk create root categories
        CategoryModel.objects.bulk_create(root_categories)

        # Create subcategories (those with parents)
        for global_category in global_categories.filter(parent__isnull=False):
            try:
                # Ensure that parent category exists for the user before creating subcategories
                parent_category = CategoryModel.objects.get(
                    user=instance,
                    title=global_category.parent.title,
                    is_custom=False  # Scope it to non-custom categories
                )
                
                # Create subcategory under the parent
                CategoryModel.objects.create(
                    user=instance,
                    title=global_category.title,
                    parent=parent_category,  # Assign the user-specific parent category
                    type=global_category.type,
                    color=global_category.color,
                    icon_code=global_category.icon_code,
                    is_custom=False
                )
            except CategoryModel.DoesNotExist:
                # Log or handle cases where the parent is not found
                print(f"Parent category {global_category.parent.title} not found for user {instance.username}")
