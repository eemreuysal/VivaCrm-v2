"""
Enhanced Excel import/export functionality for the Products app.
"""
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from .models import Category, ProductFamily
import re

def validate_category_enhanced(category_name):
    """
    Enhanced category validation with better matching and auto-creation.
    """
    if not category_name:
        raise ValidationError("Category is required")
    
    # Clean the category name
    category_name = str(category_name).strip()
    
    # Try exact match first
    categories = Category.objects.filter(name__iexact=category_name)
    if categories.exists():
        return categories.first()
    
    # Try with normalized spaces
    normalized_name = ' '.join(category_name.split())
    categories = Category.objects.filter(name__iexact=normalized_name)
    if categories.exists():
        return categories.first()
    
    # Try partial match for common patterns
    if "muslin" in category_name.lower():
        categories = Category.objects.filter(name__icontains="Muslin")
        if categories.exists():
            return categories.first()
    
    if "waffle" in category_name.lower() and "robe" in category_name.lower():
        categories = Category.objects.filter(name__icontains="Waffle Robe")
        if categories.exists():
            return categories.first()
    
    # Create new category if not found
    slug = slugify(category_name)
    # Make slug unique if needed
    if Category.objects.filter(slug=slug).exists():
        counter = 1
        while Category.objects.filter(slug=f"{slug}-{counter}").exists():
            counter += 1
        slug = f"{slug}-{counter}"
    
    category = Category.objects.create(
        name=category_name,
        slug=slug,
        description=f"Auto-created from Excel import: {category_name}",
        is_active=True
    )
    return category


def validate_family_enhanced(family_name):
    """
    Enhanced product family validation with better matching and auto-creation.
    """
    if not family_name:
        return None  # Family is optional
    
    # Clean the family name
    family_name = str(family_name).strip()
    
    # Try exact match first
    families = ProductFamily.objects.filter(name__iexact=family_name)
    if families.exists():
        return families.first()
    
    # Try with normalized spaces
    normalized_name = ' '.join(family_name.split())
    families = ProductFamily.objects.filter(name__iexact=normalized_name)
    if families.exists():
        return families.first()
    
    # Create new family if not found
    slug = slugify(family_name)
    # Make slug unique if needed
    if ProductFamily.objects.filter(slug=slug).exists():
        counter = 1
        while ProductFamily.objects.filter(slug=f"{slug}-{counter}").exists():
            counter += 1
        slug = f"{slug}-{counter}"
    
    family = ProductFamily.objects.create(
        name=family_name,
        slug=slug,
        description=f"Auto-created from Excel import: {family_name}"
    )
    return family