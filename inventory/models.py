from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class Location(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.FloatField(help_text="Pojemność m³")

    def used_capacity(self):
        products = Product.objects.filter(location=self)
        return sum(p.volume * p.quantity for p in products)

    def free_capacity(self):
        return self.capacity - self.used_capacity()

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    volume = models.FloatField(help_text="Objętość jednostkowa m³")
    quantity = models.PositiveIntegerField()
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name


class StockOperation(models.Model):
    OPERATION_TYPES = [
        ('IN', 'Przyjęcie'),
        ('OUT', 'Wydanie'),
        ('MOVE', 'Przesunięcie'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    operation_type = models.CharField(max_length=4, choices=OPERATION_TYPES)
    quantity = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_operation_type_display()} – {self.product.name}"


class BugReport(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'Nowe'),
        ('IN_PROGRESS', 'W trakcie'),
        ('DONE', 'Zamknięte'),
    ]

    title = models.CharField(max_length=120)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NEW'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    title = models.CharField(max_length=120)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NEW'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('OWNER', 'Właściciel'),
        ('WORKER', 'Magazynier'),
        ('VIEWER', 'Tylko podgląd'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} – {self.get_role_display()}"

