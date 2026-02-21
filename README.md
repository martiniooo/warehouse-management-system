# 📦 Aplikacja webowa do zarządzania magazynem

Projekt pracy licencjackiej przedstawiający implementację aplikacji webowej wspierającej zarządzanie magazynem.  
System umożliwia monitorowanie stanów produktów, realizację operacji magazynowych oraz optymalizację wykorzystania przestrzeni.

---

## 🎯 Cel projektu

Celem aplikacji jest stworzenie systemu umożliwiającego:

- ewidencjonowanie produktów i ich lokalizacji,
- obsługę operacji magazynowych (IN / OUT / MOVE),
- monitorowanie pojemności magazynów,
- kontrolę dostępu użytkowników poprzez role,
- generowanie raportów CSV oraz PDF,
- rejestrowanie historii operacji jako mechanizmu audytu.

---

## 🛠 Technologie

- Python 3.11
- Django 5.x
- SQLite (środowisko deweloperskie)
- HTML / CSS (szablony Django)
- ReportLab (raporty PDF)
- Git (kontrola wersji)

---

## 👤 Role użytkowników

System obsługuje trzy role:

- OWNER – pełny dostęp do systemu
- WORKER – operacje magazynowe
- VIEWER – dostęp tylko do podglądu danych

Dostęp do funkcji kontrolowany jest w interfejsie oraz po stronie backendu (403 Forbidden).

---

## ⚙ Funkcjonalności

- Rejestracja i logowanie użytkowników
- Zarządzanie produktami i lokalizacjami
- Operacje magazynowe (IN / OUT / MOVE)
- Optymalizacja przestrzeni magazynowej
- Dashboard monitorowania magazynów
- Historia operacji
- Eksport raportów CSV i PDF
- Moduł zgłaszania błędów

---

## 🚀 Uruchomienie lokalne

1. Klonowanie repozytorium:

```bash
git clone https://github.com/TWOJ_LOGIN/warehouse-management-system.git
cd warehouse-management-system

2. Utworzenie środowiska wirtualnego:

python -m venv venv
venv\Scripts\activate


3. Instalacja zależności:

pip install -r requirements.txt


4. Migracje:

python manage.py migrate


5. Uruchomienie serwera:

python manage.py runserver


Aplikacja dostępna pod adresem:
http://127.0.0.1:8000/