from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login

from functools import wraps

from .models import Organization, StockOperation, Product, Location, BugReport, UserProfile

import csv
import os

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ==========================
# HELPERS
# ==========================

def _parse_positive_int(value, default=None):
    """Zwraca int > 0 lub default."""
    try:
        iv = int(str(value).strip())
        return iv if iv > 0 else default
    except (ValueError, TypeError):
        return default


# ==========================
# ROLE ACCESS CONTROL
# ==========================

def get_user_role(user):
    if not user.is_authenticated:
        return None

    if user.is_superuser:
        return 'OWNER'

    # Bez side-effectów (nie tworzymy profilu w trakcie requestu)
    if not hasattr(user, 'userprofile'):
        return 'WORKER'  # albo 'VIEWER' jeśli wolisz ostrożniej

    return user.userprofile.role

def get_user_organization(user):
    if not user.is_authenticated:
        return None

    if hasattr(user, 'userprofile') and user.userprofile.organization:
        return user.userprofile.organization

    return None

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            role = get_user_role(request.user)
            if role not in allowed_roles:
                return render(request, 'inventory/403.html', status=403)
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


# ==========================
# AUTH: REGISTER
# ==========================

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        organization_name = request.POST.get('organization_name', '').strip()

        if not username or not password or not password2 or not organization_name:
            return render(request, 'registration/register.html', {
                'error': 'Uzupełnij wszystkie pola.'
            })

        if password != password2:
            return render(request, 'registration/register.html', {
                'error': 'Hasła nie są takie same.'
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'registration/register.html', {
                'error': 'Użytkownik już istnieje.'
            })

        user = User.objects.create_user(username=username, password=password)

        organization = Organization.objects.create(
            name=organization_name,
            owner=user
        )

        UserProfile.objects.create(
            user=user,
            role='OWNER',
            organization=organization
        )

        login(request, user)
        return redirect('home')

    return render(request, 'registration/register.html')

@login_required
@role_required(['OWNER'])
def add_staff_user(request):
    owner_org = get_user_organization(request.user)

    if not owner_org:
        return render(request, 'inventory/error.html', {
            'message': 'Nie znaleziono organizacji właściciela.'
        })

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        role = request.POST.get('role', '').strip()

        if not username or not password or not password2 or not role:
            return render(request, 'inventory/add_staff_user.html', {
                'error': 'Uzupełnij wszystkie pola.'
            })

        if password != password2:
            return render(request, 'inventory/add_staff_user.html', {
                'error': 'Hasła nie są takie same.'
            })

        if role not in ['WORKER', 'VIEWER']:
            return render(request, 'inventory/add_staff_user.html', {
                'error': 'Wybierz poprawną rolę.'
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'inventory/add_staff_user.html', {
                'error': 'Użytkownik o takiej nazwie już istnieje.'
            })

        user = User.objects.create_user(username=username, password=password)
        UserProfile.objects.create(
            user=user,
            role=role,
            organization=owner_org
        )

        messages.success(request, f'Utworzono konto użytkownika "{username}".')
        return redirect('home')

    return render(request, 'inventory/add_staff_user.html')


# ==========================
# HOME (bugs) - ALL ROLES
# ==========================

@login_required
@role_required(['OWNER', 'WORKER', 'VIEWER'])
def home(request):
    org = get_user_organization(request.user)

    if not org:
        return render(request, 'inventory/error.html', {
            'message': 'Brak przypisanej organizacji.'
        })

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()

        if not title or not description:
            messages.error(request, 'Uzupełnij tytuł i opis zgłoszenia.')
        else:
            BugReport.objects.create(
                title=title,
                description=description,
                created_by=request.user,
                organization=org
            )
            messages.success(request, 'Zgłoszenie zostało zapisane. Dziękujemy!')
            return redirect('home')

    return render(request, 'inventory/home.html', {
        'role': get_user_role(request.user),
        'organization_name': org.name,
    })


@login_required
@role_required(['OWNER', 'WORKER', 'VIEWER'])
def my_bug_reports(request):
    org = get_user_organization(request.user)

    reports = BugReport.objects.filter(
        created_by=request.user,
        organization=org
    ).order_by('-created_at')

    return render(request, 'inventory/my_bug_reports.html', {
        'reports': reports
    })


@login_required
@role_required(['OWNER', 'WORKER', 'VIEWER'])
def bug_report_detail(request, report_id):
    org = get_user_organization(request.user)

    report = get_object_or_404(
        BugReport,
        id=report_id,
        created_by=request.user,
        organization=org
    )

    return render(request, 'inventory/bug_report_detail.html', {
        'report': report
    })


@login_required
@role_required(['OWNER', 'WORKER', 'VIEWER'])
def edit_bug_report(request, report_id):
    org = get_user_organization(request.user)

    report = get_object_or_404(
        BugReport,
        id=report_id,
        created_by=request.user,
        organization=org
    )

    if report.status == 'DONE':
        messages.error(request, 'Nie można edytować zamkniętego zgłoszenia.')
        return redirect('bug_report_detail', report_id=report.id)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()

        if not title or not description:
            messages.error(request, 'Uzupełnij tytuł i opis zgłoszenia.')
        else:
            report.title = title
            report.description = description
            report.save()
            messages.success(request, 'Zgłoszenie zostało zaktualizowane.')
            return redirect('bug_report_detail', report_id=report.id)

    return render(request, 'inventory/edit_bug_report.html', {
        'report': report
    })

# ==========================
# LOCATIONS
# ==========================

@login_required
@role_required(['OWNER', 'WORKER'])
def location_list(request):
    org = get_user_organization(request.user)
    locations = Location.objects.filter(organization=org).order_by('name')

    enriched_locations = []
    for loc in locations:
        products = Product.objects.filter(location=loc, quantity__gt=0, organization=org)
        used = sum(p.volume * p.quantity for p in products)
        free = loc.capacity - used

        enriched_locations.append({
            'id': loc.id,
            'name': loc.name,
            'capacity': loc.capacity,
            'used_capacity': used,
            'free_capacity': free,
        })

    return render(request, 'inventory/location_list.html', {
        'locations': enriched_locations,
        'role': get_user_role(request.user),
    })


@login_required
@role_required(['OWNER', 'WORKER'])
def add_location(request):
    org = get_user_organization(request.user)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        capacity_raw = request.POST.get('capacity', '').strip()

        if not name or not capacity_raw:
            messages.error(request, 'Uzupełnij wszystkie pola.')
            return redirect('add_location')

        try:
            capacity = float(capacity_raw.replace(',', '.'))
        except ValueError:
            messages.error(request, 'Pojemność musi być poprawną liczbą.')
            return redirect('add_location')

        if capacity <= 0:
            messages.error(request, 'Pojemność musi być większa od 0.')
            return redirect('add_location')

        if Location.objects.filter(name__iexact=name, organization=org).exists():
            messages.error(request, 'Lokalizacja o takiej nazwie już istnieje.')
            return redirect('add_location')

        Location.objects.create(
            name=name,
            capacity=capacity,
            organization=org
        )
        messages.success(request, 'Lokalizacja została dodana.')
        return redirect('location_list')

    return render(request, 'inventory/add_location.html')


@login_required
@role_required(['OWNER', 'WORKER'])
def edit_location(request, location_id):
    org = get_user_organization(request.user)

    location = get_object_or_404(
        Location,
        id=location_id,
        organization=org
    )

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        capacity_raw = request.POST.get('capacity', '').strip()

        if not name or not capacity_raw:
            messages.error(request, 'Uzupełnij wszystkie pola.')
            return redirect('edit_location', location_id=location.id)

        try:
            new_capacity = float(capacity_raw.replace(',', '.'))
        except ValueError:
            messages.error(request, 'Pojemność musi być poprawną liczbą.')
            return redirect('edit_location', location_id=location.id)

        if new_capacity <= 0:
            messages.error(request, 'Pojemność musi być większa od 0.')
            return redirect('edit_location', location_id=location.id)

        used_capacity = location.used_capacity()
        if new_capacity < used_capacity:
            messages.error(
                request,
                f'Nie można ustawić pojemności mniejszej niż aktualnie zajęta ({used_capacity:.2f} m³).'
            )
            return redirect('edit_location', location_id=location.id)

        duplicate = (
            Location.objects
            .filter(name__iexact=name, organization=org)
            .exclude(id=location.id)
            .exists()
        )
        if duplicate:
            messages.error(request, 'Inna lokalizacja o takiej nazwie już istnieje.')
            return redirect('edit_location', location_id=location.id)

        location.name = name
        location.capacity = new_capacity
        location.save()

        messages.success(request, 'Lokalizacja została zaktualizowana.')
        return redirect('location_list')

    return render(request, 'inventory/edit_location.html', {
        'location': location
    })


@login_required
@role_required(['OWNER'])
def delete_location(request, location_id):
    org = get_user_organization(request.user)

    location = get_object_or_404(
        Location,
        id=location_id,
        organization=org
    )

    has_products = Product.objects.filter(
        location=location,
        quantity__gt=0,
        organization=org
    ).exists()

    if has_products:
        messages.error(request, 'Nie można usunąć lokalizacji, ponieważ znajdują się w niej produkty.')
        return redirect('location_list')

    if request.method == 'POST':
        location.delete()
        messages.success(request, 'Lokalizacja została usunięta.')
        return redirect('location_list')

    return render(request, 'inventory/delete_location.html', {
        'location': location
    })


# ==========================
# PRODUCTS - LIST (ALL ROLES)
# ==========================

@login_required
@role_required(['OWNER', 'WORKER', 'VIEWER'])
def product_list(request):
    org = get_user_organization(request.user)

    products = (
        Product.objects
        .filter(organization=org)
        .values('category', 'name')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('category', 'name')
    )

    grouped_products = {}
    for product in products:
        category = product['category'].strip() if product['category'] else 'Bez kategorii'
        if category not in grouped_products:
            grouped_products[category] = []
        grouped_products[category].append(product)

    return render(request, 'inventory/product_list.html', {
        'grouped_products': grouped_products,
        'role': get_user_role(request.user),
    })


@login_required
@role_required(['OWNER'])
def delete_product(request, product_name):
    org = get_user_organization(request.user)
    product_name = product_name.strip()

    total_quantity = (
        Product.objects
        .filter(name=product_name, organization=org)
        .aggregate(total=Sum('quantity'))
        .get('total') or 0
    )

    if total_quantity > 0:
        messages.error(
            request,
            'Nie można usunąć produktu, ponieważ jego stan magazynowy jest większy od 0.'
        )
        return redirect('product_list')

    if request.method == 'POST':
        Product.objects.filter(name=product_name, organization=org).delete()
        messages.success(request, f'Produkt "{product_name}" został usunięty.')
        return redirect('product_list')

    return render(request, 'inventory/delete_product.html', {
        'product_name': product_name
    })


# ==========================
# PRODUCTS - ADD (OWNER/WORKER)
# ==========================

@login_required
@role_required(['OWNER', 'WORKER'])
def add_product(request):
    org = get_user_organization(request.user)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', '').strip()
        volume_raw = request.POST.get('volume', '').strip()
        quantity_raw = request.POST.get('quantity', '').strip()
        location_id = request.POST.get('location_id')

        if not name or not category or not volume_raw or not quantity_raw or not location_id:
            messages.error(request, 'Uzupełnij wszystkie pola.')
            return redirect('add_product')

        try:
            volume = float(volume_raw.replace(',', '.'))
        except ValueError:
            messages.error(request, 'Niepoprawny format objętości.')
            return redirect('add_product')

        quantity = _parse_positive_int(quantity_raw)
        if quantity is None:
            messages.error(request, 'Ilość musi być liczbą większą od 0.')
            return redirect('add_product')

        if volume <= 0:
            messages.error(request, 'Objętość musi być większa od 0.')
            return redirect('add_product')

        location = get_object_or_404(Location, id=location_id, organization=org)

        required_volume = volume * quantity
        if location.free_capacity() < required_volume:
            messages.error(request, 'Brak miejsca w wybranej lokalizacji magazynowej.')
            return redirect('add_product')

        product, created = Product.objects.get_or_create(
            name=name,
            category=category,
            volume=volume,
            location=location,
            organization=org,
            defaults={'quantity': 0}
        )
        product.quantity += quantity
        product.save()

        messages.success(request, 'Produkt został dodany.')
        return redirect('product_list')

    locations = Location.objects.filter(organization=org).order_by('name')
    return render(request, 'inventory/add_product.html', {'locations': locations})
# ==========================
# OPERATIONS ADD (OWNER/WORKER)
# ==========================

@login_required
@role_required(['OWNER', 'WORKER'])
def add_operation(request):
    org = get_user_organization(request.user)

    if request.method == 'POST':
        product_name = request.POST.get('product_name', '').strip()
        operation_type = request.POST.get('operation_type', '').strip()
        quantity = _parse_positive_int(request.POST.get('quantity'))

        if not product_name or not operation_type:
            return render(request, 'inventory/error.html', {'message': 'Brakuje danych operacji.'})

        if quantity is None:
            return render(request, 'inventory/error.html', {'message': 'Podaj poprawną ilość (> 0).'})

        product_ref = (
            Product.objects
            .filter(name=product_name, organization=org)
            .order_by('-quantity')
            .first()
        )

        if not product_ref:
            return render(request, 'inventory/error.html', {'message': 'Nie znaleziono produktu'})

        if operation_type == 'IN':
            location_id = request.POST.get('location_id')
            if not location_id:
                return render(request, 'inventory/error.html', {'message': 'Wybierz lokalizację (magazyn) dla przyjęcia'})

            location = get_object_or_404(Location, id=location_id, organization=org)

            required_volume = product_ref.volume * quantity
            if location.free_capacity() < required_volume:
                return render(request, 'inventory/error.html', {'message': 'Brak miejsca w wybranej lokalizacji'})

            target_product, _ = Product.objects.get_or_create(
                name=product_ref.name,
                category=product_ref.category,
                volume=product_ref.volume,
                location=location,
                organization=org,
                defaults={'quantity': 0}
            )
            target_product.quantity += quantity
            target_product.save()

            StockOperation.objects.create(
                product=target_product,
                location=location,
                organization=org,
                operation_type='IN',
                quantity=quantity
            )

            return redirect('product_list')

        elif operation_type == 'OUT':
            total_available = (
                Product.objects
                .filter(name=product_name, organization=org)
                .aggregate(total=Sum('quantity'))['total'] or 0
            )

            if total_available < quantity:
                return render(request, 'inventory/error.html', {'message': 'Brak wystarczającej ilości produktu'})

            remaining = quantity
            batches = (
                Product.objects
                .filter(name=product_name, quantity__gt=0, organization=org)
                .order_by('-quantity')
            )

            for b in batches:
                if remaining <= 0:
                    break

                take = min(b.quantity, remaining)
                b.quantity -= take
                b.save()

                StockOperation.objects.create(
                    product=b,
                    location=b.location,
                    organization=org,
                    operation_type='OUT',
                    quantity=take
                )

                remaining -= take

            return redirect('product_list')

        return render(request, 'inventory/error.html', {'message': 'Nieznany typ operacji'})

    products = (
        Product.objects
        .filter(organization=org)
        .values('name')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('name')
    )

    locations = Location.objects.filter(organization=org).order_by('name')

    return render(request, 'inventory/add_operation.html', {
        'products': products,
        'locations': locations
    })

# ==========================
# HISTORY (ALL ROLES)
# ==========================

@login_required
@role_required(['OWNER', 'WORKER', 'VIEWER'])
def operation_history(request):
    org = get_user_organization(request.user)
    operations = (
        StockOperation.objects
        .filter(organization=org)
        .select_related('product', 'location')
        .order_by('-timestamp')
    )
    return render(request, 'inventory/operation_history.html', {'operations': operations})


# ==========================
# MOVE (OWNER/WORKER) - AUDYT: OUT + IN
# ==========================

@login_required
@role_required(['OWNER', 'WORKER'])
def move_product(request):
    org = get_user_organization(request.user)

    if request.method == 'POST':
        product_id = request.POST.get('product')
        target_location_id = request.POST.get('target_location')
        quantity = _parse_positive_int(request.POST.get('quantity'))

        if not product_id or not target_location_id:
            return render(request, 'inventory/error.html', {'message': 'Brakuje danych przesunięcia.'})

        if quantity is None:
            return render(request, 'inventory/error.html', {'message': 'Podaj poprawną ilość (> 0).'})

        product = get_object_or_404(Product, id=product_id, organization=org)
        source_location = product.location
        target_location = get_object_or_404(Location, id=target_location_id, organization=org)

        if source_location and target_location and source_location.id == target_location.id:
            return render(request, 'inventory/error.html', {
                'message': 'Lokalizacja docelowa nie może być taka sama jak źródłowa'
            })

        if product.quantity < quantity:
            return render(request, 'inventory/error.html', {
                'message': 'Brak wystarczającej ilości produktu w lokalizacji źródłowej'
            })

        required_volume = product.volume * quantity
        if target_location.free_capacity() < required_volume:
            return render(request, 'inventory/error.html', {
                'message': 'Brak miejsca w lokalizacji docelowej'
            })

        # 1) zdejmujemy ze źródła
        product.quantity -= quantity
        product.save()

        # 2) dodajemy do celu
        target_product, created = Product.objects.get_or_create(
            name=product.name,
            category=product.category,
            volume=product.volume,
            location=target_location,
            organization=org,
            defaults={'quantity': 0}
        )
        target_product.quantity += quantity
        target_product.save()

        # 3) AUDYT: zapisujemy OUT ze źródła + IN do celu
        StockOperation.objects.create(
            product=product,
            location=source_location,
            organization=org,
            operation_type='OUT',
            quantity=quantity
        )
        StockOperation.objects.create(
            product=target_product,
            location=target_location,
            organization=org,
            operation_type='IN',
            quantity=quantity
        )

        return redirect('product_list')

    products = (
        Product.objects
        .select_related('location')
        .filter(quantity__gt=0, organization=org)
        .order_by('name', 'location__name')
    )

    locations = Location.objects.filter(organization=org).order_by('name')

    return render(request, 'inventory/move_product.html', {
        'products': products,
        'locations': locations
    })

# ==========================
# SMART IN (OWNER/WORKER)
# ==========================

@login_required
@role_required(['OWNER', 'WORKER'])
def add_operation_with_suggestion(request):
    org = get_user_organization(request.user)

    def get_best_location(product_ref, quantity):
        required_volume = product_ref.volume * quantity
        all_locations = Location.objects.filter(organization=org)

        matching_category_locations = []
        other_locations = []

        for loc in all_locations:
            free_capacity = loc.free_capacity()
            if free_capacity < required_volume:
                continue

            has_same_category = Product.objects.filter(
                location=loc,
                category=product_ref.category,
                quantity__gt=0,
                organization=org
            ).exists()

            location_data = {
                'location': loc,
                'free_capacity': free_capacity,
            }

            if has_same_category:
                matching_category_locations.append(location_data)
            else:
                other_locations.append(location_data)

        matching_category_locations.sort(key=lambda x: x['free_capacity'], reverse=True)
        other_locations.sort(key=lambda x: x['free_capacity'], reverse=True)

        if matching_category_locations:
            return matching_category_locations[0]['location']

        if other_locations:
            return other_locations[0]['location']

        return None

    if request.method == 'POST':
        product_name = request.POST.get('product_name', '').strip()
        quantity = _parse_positive_int(request.POST.get('quantity'))
        location_id = request.POST.get('location_id')

        if not product_name:
            return render(request, 'inventory/error.html', {'message': 'Wybierz produkt.'})

        if quantity is None:
            return render(request, 'inventory/error.html', {'message': 'Podaj poprawną ilość (> 0).'})

        product_ref = (
            Product.objects
            .filter(name=product_name, organization=org)
            .order_by('-quantity')
            .first()
        )

        if not product_ref:
            return render(request, 'inventory/error.html', {'message': 'Nie znaleziono produktu.'})

        # jeśli użytkownik nie wybierze lokalizacji albo wybierze pustą -> użyj sugestii
        if location_id:
            location = get_object_or_404(Location, id=location_id, organization=org)
        else:
            location = get_best_location(product_ref, quantity)

        if not location:
            return render(request, 'inventory/error.html', {
                'message': 'Brak lokalizacji z wystarczającą wolną pojemnością dla tego produktu.'
            })

        required_volume = product_ref.volume * quantity
        if location.free_capacity() < required_volume:
            return render(request, 'inventory/error.html', {
                'message': 'Wybrana lokalizacja nie ma wystarczającej pojemności.'
            })

        target_product, created = Product.objects.get_or_create(
            name=product_ref.name,
            category=product_ref.category,
            volume=product_ref.volume,
            location=location,
            organization=org,
            defaults={'quantity': 0}
        )

        target_product.quantity += quantity
        target_product.save()

        StockOperation.objects.create(
            product=target_product,
            location=location,
            organization=org,
            operation_type='IN',
            quantity=quantity
        )

        messages.success(
            request,
            f'Przyjęto {quantity} szt. produktu "{target_product.name}" do lokalizacji "{location.name}".'
        )
        return redirect('product_list')

    raw_products = (
        Product.objects
        .filter(organization=org)
        .values('name', 'category')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('category', 'name')
    )

    products_with_suggestions = []
    for item in raw_products:
        product_ref = (
            Product.objects
            .filter(name=item['name'], organization=org)
            .order_by('-quantity')
            .first()
        )

        suggested_location = None
        if product_ref:
            suggested_location = get_best_location(product_ref, 1)

        products_with_suggestions.append({
            'name': item['name'],
            'category': item['category'],
            'total_quantity': item['total_quantity'],
            'suggested_location_id': suggested_location.id if suggested_location else '',
            'suggested_location_name': suggested_location.name if suggested_location else 'Brak sugestii',
        })

    locations = Location.objects.filter(organization=org).order_by('name')

    return render(request, 'inventory/add_operation_smart.html', {
        'products': products_with_suggestions,
        'locations': locations
    })

# ==========================
# DASHBOARD (ALL ROLES)
# ==========================

@login_required
@role_required(['OWNER', 'WORKER', 'VIEWER'])
def dashboard(request):
    org = get_user_organization(request.user)

    locations = Location.objects.filter(organization=org).order_by('name')
    dashboard_data = []

    total_capacity = 0
    total_used = 0

    for loc in locations:
        products = Product.objects.filter(location=loc, quantity__gt=0, organization=org)

        products_map = {}
        used_volume = 0

        for p in products:
            product_volume = p.volume * p.quantity
            used_volume += product_volume

            if p.name not in products_map:
                products_map[p.name] = {
                    'name': p.name,
                    'quantity': 0,
                    'used_volume': 0
                }

            products_map[p.name]['quantity'] += p.quantity
            products_map[p.name]['used_volume'] += product_volume

        products_details = [
            {
                'name': v['name'],
                'quantity': v['quantity'],
                'used_volume': round(v['used_volume'], 2)
            }
            for v in products_map.values()
        ]

        free_volume = loc.capacity - used_volume
        usage_percent = (used_volume / loc.capacity) * 100 if loc.capacity > 0 else 0

        total_capacity += loc.capacity
        total_used += used_volume

        dashboard_data.append({
            'location': loc,
            'used': round(used_volume, 2),
            'free': round(free_volume, 2),
            'usage_percent': round(usage_percent, 2),
            'status': (
                'pełna' if usage_percent >= 90 else
                'średnia' if usage_percent >= 50 else
                'pusta'
            ),
            'products': products_details
        })

    total_usage_percent = ((total_used / total_capacity) * 100 if total_capacity > 0 else 0)

    return render(request, 'inventory/dashboard.html', {
        'dashboard_data': dashboard_data,
        'total_capacity': total_capacity,
        'total_used': round(total_used, 2),
        'total_usage_percent': round(total_usage_percent, 2)
    })

# ==========================
# REPORTS (OWNER)
# ==========================

@login_required
@role_required(['OWNER'])
def reports_view(request):
    return render(request, 'inventory/reports.html')


@login_required
@role_required(['OWNER'])
def report_stock_csv(request):
    org = get_user_organization(request.user)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="stan_magazynu.csv"'
    response.write('\ufeff')
    
    writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_ALL)
    
    writer.writerow([
        'Produkt',
        'Lokalizacja',
        'Ilość (szt.)',
        'Objętość jednostkowa (m³)',
        'Zajęta objętość (m³)'
    ])

    products = (
        Product.objects
        .filter(quantity__gt=0, organization=org)
        .select_related('location')
    )

    grouped = {}

    for p in products:
        loc_name = p.location.name if p.location else 'Brak'
        key = (p.name, loc_name)

        if key not in grouped:
            grouped[key] = {
                'name': p.name,
                'location': loc_name,
                'total_qty': 0,
                'used_volume': 0.0,
                'volumes': set()
            }

        grouped[key]['total_qty'] += p.quantity
        grouped[key]['used_volume'] += float(p.volume) * p.quantity
        grouped[key]['volumes'].add(float(p.volume))

    for (name, loc_name) in sorted(grouped.keys(), key=lambda x: (x[0], x[1])):
        row = grouped[(name, loc_name)]

        if len(row['volumes']) == 1:
            unit_volume = f"{next(iter(row['volumes'])):.2f}"
        else:
            unit_volume = "—"

        writer.writerow([
            row['name'],
            row['location'],
            row['total_qty'],
            unit_volume,
            f"{row['used_volume']:.2f}"
        ])

    return response


@login_required
@role_required(['OWNER'])
def report_operations_csv(request):
    org = get_user_organization(request.user)

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="historia_operacji.csv"'
    response.write('\ufeff')

    writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_ALL)

    writer.writerow([
        'Data',
        'Produkt',
        'Lokalizacja',
        'Typ operacji',
        'Ilość'
    ])

    operations = (
        StockOperation.objects
        .select_related('product', 'location')
        .filter(quantity__gt=0, organization=org)
        .order_by('-timestamp', '-id')
    )

    op_type_map = dict(StockOperation.OPERATION_TYPES)

    for op in operations:
        op_type_label = op_type_map.get(op.operation_type, op.operation_type)
        loc_name = op.location.name if op.location else '—'

        writer.writerow([
            op.timestamp.strftime('%Y-%m-%d %H:%M'),
            op.product.name,
            loc_name,
            op_type_label,
            op.quantity
        ])

    return response

# ==========================
# PDF FONT HELPER (Windows)
# ==========================

def _register_windows_font():
    arial_path = r"C:\Windows\Fonts\arial.ttf"

    if os.path.exists(arial_path):
        try:
            pdfmetrics.registerFont(TTFont("ArialPL", arial_path))
            return "ArialPL"
        except Exception:
            pass

    return "Helvetica"


# ==========================
# PDF REPORTS (OWNER)
# ==========================

@login_required
@role_required(['OWNER'])
def report_stock_pdf(request):
    org = get_user_organization(request.user)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="stan_magazynu.pdf"'

    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    font_name = _register_windows_font()

    c.setFont(font_name, 14)
    c.drawString(40, height - 50, "Raport stanu magazynu (produkt + lokalizacja)")

    c.setFont(font_name, 10)
    y = height - 80

    headers = ["Produkt", "Lokalizacja", "Ilość", "Obj. jedn. (m³)", "Zajęte (m³)"]
    x = [40, 200, 360, 420, 500]

    for i, h in enumerate(headers):
        c.drawString(x[i], y, h)
    y -= 15
    c.line(40, y, width - 40, y)
    y -= 15

    products = (
        Product.objects
        .filter(quantity__gt=0, organization=org)
        .select_related('location')
        .order_by('name', 'location__name')
    )

    for p in products:
        used_volume = p.volume * p.quantity

        row = [
            p.name,
            p.location.name if p.location else "Brak",
            str(p.quantity),
            f"{p.volume:.2f}",
            f"{used_volume:.2f}"
        ]

        for i, value in enumerate(row):
            c.drawString(x[i], y, value[:45])

        y -= 14
        if y < 60:
            c.showPage()
            c.setFont(font_name, 10)
            y = height - 60

    c.showPage()
    c.save()
    return response


@login_required
@role_required(['OWNER'])
def report_operations_pdf(request):
    org = get_user_organization(request.user)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="historia_operacji.pdf"'

    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    font_name = _register_windows_font()

    c.setFont(font_name, 14)
    c.drawString(40, height - 50, "Raport historii operacji")

    c.setFont(font_name, 10)
    y = height - 80

    headers = ["Data", "Produkt", "Lokalizacja", "Typ", "Ilość"]
    x = [40, 140, 320, 460, 520]

    for i, h in enumerate(headers):
        c.drawString(x[i], y, h)
    y -= 15
    c.line(40, y, width - 40, y)
    y -= 15

    operations = (
        StockOperation.objects
        .filter(organization=org)
        .select_related('product', 'location')
        .order_by('-timestamp')
    )

    for op in operations:
        op_type = dict(StockOperation.OPERATION_TYPES).get(op.operation_type, op.operation_type)

        row = [
            op.timestamp.strftime('%Y-%m-%d %H:%M'),
            op.product.name,
            op.location.name if op.location else "—",
            op_type,
            str(op.quantity)
        ]

        for i, value in enumerate(row):
            c.drawString(x[i], y, value[:38])

        y -= 14
        if y < 60:
            c.showPage()
            c.setFont(font_name, 10)
            y = height - 60

    c.showPage()
    c.save()
    return response

@login_required
@role_required(['OWNER'])
def report_locations_pdf(request):
    org = get_user_organization(request.user)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="stan_magazynow.pdf"'

    c = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    font_name = _register_windows_font()

    c.setFont(font_name, 14)
    c.drawString(40, height - 50, "Raport stanu magazynów (lokalizacji)")

    c.setFont(font_name, 10)
    y = height - 80

    headers = ["Magazyn", "Pojemność (m³)", "Zajęte (m³)", "Wolne (m³)", "Wykorzystanie"]
    x = [40, 220, 320, 420, 520]

    for i, h in enumerate(headers):
        c.drawString(x[i], y, h)
    y -= 15
    c.line(40, y, width - 40, y)
    y -= 15

    locations = Location.objects.filter(organization=org).order_by('name')

    for loc in locations:
        products = Product.objects.filter(location=loc, quantity__gt=0, organization=org)
        used = sum(p.volume * p.quantity for p in products)
        free = loc.capacity - used
        percent = (used / loc.capacity) * 100 if loc.capacity > 0 else 0

        row = [
            loc.name,
            f"{loc.capacity:.2f}",
            f"{used:.2f}",
            f"{free:.2f}",
            f"{percent:.2f}%"
        ]

        for i, value in enumerate(row):
            c.drawString(x[i], y, value[:35])

        y -= 14
        if y < 60:
            c.showPage()
            c.setFont(font_name, 10)
            y = height - 60

    c.showPage()
    c.save()
    return response
