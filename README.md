# 📦 Aplikacja webowa do zarządzania magazynem

Projekt pracy licencjackiej przedstawiający implementację aplikacji webowej wspierającej zarządzanie magazynem.
System umożliwia monitorowanie stanów produktów, realizację operacji magazynowych oraz optymalizację wykorzystania przestrzeni.

---

## 🎯 Cel projektu

Celem aplikacji jest stworzenie systemu umożliwiającego:

* ewidencjonowanie produktów i ich lokalizacji,
* obsługę operacji magazynowych (IN / OUT / MOVE),
* monitorowanie pojemności magazynów,
* kontrolę dostępu użytkowników poprzez role,
* generowanie raportów CSV oraz PDF,
* rejestrowanie historii operacji jako mechanizmu audytu.

---

## 🛠 Technologie

* Python 3.11
* Django 5.x
* SQLite (środowisko deweloperskie oraz wdrożeniowe – Azure Free Tier)
* HTML / CSS (szablony Django)
* ReportLab (raporty PDF)
* Git (kontrola wersji)

---

## 🧠 Architektura systemu

Aplikacja została zbudowana w oparciu o architekturę **MVC (Model–View–Template)** wykorzystywaną w Django:

* **Models** – reprezentacja danych (Product, Location, StockOperation, BugReport)
* **Views** – logika biznesowa systemu
* **Templates** – warstwa prezentacji (HTML + CSS)

Dodatkowo zastosowano:

* wieloorganizacyjność (multi-tenant – każda organizacja widzi tylko swoje dane)
* kontrolę dostępu opartą o role użytkowników
* walidację danych po stronie backendu

---

## 👤 Role użytkowników

System obsługuje trzy role:

* **OWNER** – pełny dostęp (zarządzanie użytkownikami, raporty)
* **WORKER** – operacje magazynowe (IN / OUT / MOVE)
* **VIEWER** – dostęp tylko do podglądu danych

Dostęp do funkcji kontrolowany jest:

* w widokach (`@role_required`)
* oraz poprzez odpowiedzi 403 dla nieuprawnionych użytkowników

---

## ⚙ Funkcjonalności

### 📦 Zarządzanie magazynem

* dodawanie i edycja lokalizacji
* kontrola pojemności magazynu (m³)
* blokada przepełnienia magazynu

### 📊 Zarządzanie produktami

* dodawanie produktów
* grupowanie produktów po nazwie i kategorii
* sumowanie stanów magazynowych

### 🔄 Operacje magazynowe

* **IN** – przyjęcie produktu
* **OUT** – wydanie produktu
* **MOVE** – przesunięcie między lokalizacjami (z pełnym audytem)

### 🧠 Optymalizacja przestrzeni

* automatyczny dobór najlepszej lokalizacji
* uwzględnienie wolnej przestrzeni i kategorii produktu

### 📈 Dashboard

* podgląd zajętości magazynów
* statusy:

  * pusta
  * w porządku
  * pełna
* agregacja danych produktów w lokalizacjach

### 🕒 Historia operacji

* zapis każdej operacji magazynowej
* sortowanie po czasie
* pełny mechanizm audytu

### 📄 Raporty

* eksport CSV (Excel-friendly)
* eksport PDF (ReportLab)
* raporty:

  * stan magazynu
  * historia operacji
  * stan lokalizacji

### 🐞 Moduł zgłoszeń

* zgłaszanie błędów przez użytkowników
* podgląd własnych zgłoszeń
* edycja zgłoszeń

---

## 📂 Struktura projektu

```
inventory/
│
├── models.py
├── views.py
├── urls.py
│
├── templates/
│   └── inventory/
│       ├── home.html
│       ├── dashboard.html
│       ├── product_list.html
│       ├── add_operation.html
│       ├── reports.html
│
├── static/
│   └── images/
```

---

## 🚀 Uruchomienie aplikacji

### 🖥 Uruchomienie lokalne

#### 1. Klonowanie repozytorium

```bash
git clone https://github.com/TWOJ_LOGIN/warehouse-management-system.git
cd warehouse-management-system
```

#### 2. Utworzenie środowiska wirtualnego

```bash
python -m venv venv
venv\Scripts\activate
```

#### 3. Instalacja zależności

```bash
pip install -r requirements.txt
```

#### 4. Migracje bazy danych

```bash
python manage.py migrate
```

#### 5. Uruchomienie serwera

```bash
python manage.py runserver
```

Aplikacja dostępna pod adresem:
👉 http://127.0.0.1:8000/

---

### ☁️ Wdrożenie na Azure

Aplikacja może zostać wdrożona na platformie **Azure App Service**.

#### 1. Przygotowanie projektu

Upewnij się, że projekt zawiera:

* `requirements.txt`
* repozytorium GitHub
* konfigurację `ALLOWED_HOSTS`

```python
ALLOWED_HOSTS = ['twoja-aplikacja.azurewebsites.net']
```

---

#### 2. Utworzenie App Service

W Azure:

* Runtime: Python 3.11
* System: Linux
* Plan: Free Tier

---

#### 3. Deployment

* połącz repozytorium GitHub z Azure
* wybierz branch `main`
* Azure automatycznie:

  * zainstaluje zależności
  * uruchomi aplikację

---

#### 4. Konfiguracja

* ustaw `DEBUG = False`
* dodaj zmienne środowiskowe (jeśli potrzebne)

---

#### 5. Baza danych

* używana: SQLite
* brak potrzeby konfiguracji zewnętrznej bazy

---

#### 6. Dostęp

Po wdrożeniu aplikacja dostępna jest pod adresem:

👉 https://twoja-aplikacja.azurewebsites.net

---

## 📌 Uwagi

* pierwsze konto tworzy organizację i ma rolę OWNER
* system wykorzystuje kontrolę dostępu opartą o role
* wszystkie operacje są zapisywane w historii (audyt)

---

## 👨‍💻 Autor

Projekt wykonany w ramach pracy licencjackiej.
