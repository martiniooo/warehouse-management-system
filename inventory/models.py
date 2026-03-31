from django.db import models
from django.conf import settings
from django.contrib.auth.models import User


class Organization(models.Model):
    name = models.CharField(max_length=150)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_organizations'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Location(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
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
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
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

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Wykonał"
    )

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

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
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


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('OWNER', 'Właściciel'),
        ('WORKER', 'Magazynier'),
        ('VIEWER', 'Tylko podgląd'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        org_name = self.organization.name if self.organization else 'Brak organizacji'
        return f"{self.user.username} – {self.get_role_display()} – {org_name}"