from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.home, name='home'),

    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),

    path('operation/add/', views.add_operation, name='add_operation'),
    path('operation/add-smart/', views.add_operation_with_suggestion, name='add_operation_smart'),
    path('operation/move/', views.move_product, name='move_product'),

    path('operations/', views.operation_history, name='operation_history'),

    path('dashboard/', views.dashboard, name='dashboard'),

    # RAPORTY CSV
    path('reports/stock/', views.report_stock_csv, name='report_stock'),
    path('reports/operations/', views.report_operations_csv, name='report_operations'),

    # RAPORTY PDF
    path('reports/stock/pdf/', views.report_stock_pdf, name='report_stock_pdf'),
    path('reports/operations/pdf/', views.report_operations_pdf, name='report_operations_pdf'),
    path('reports/locations/pdf/', views.report_locations_pdf, name='report_locations_pdf'),

    path('reports/', views.reports_view, name='reports'),

    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),



]

