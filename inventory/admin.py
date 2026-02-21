from django.contrib import admin
from .models import Product, Location, StockOperation, BugReport


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'location')
    list_filter = ('category', 'location')
    search_fields = ('name',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity')
    search_fields = ('name',)


@admin.register(StockOperation)
class StockOperationAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'product', 'operation_type', 'quantity', 'location')
    list_filter = ('operation_type', 'location', 'timestamp')
    search_fields = ('product__name',)


@admin.register(BugReport)
class BugReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)

