# Asystent ZUS

Prosta aplikacja typu chatbot zbudowana przy użyciu frameworka Streamlit. Projekt służy jako interfejs konwersacyjny (obecnie w wersji demo).

## Wymagania

*   Python 3.8 lub nowszy
*   Biblioteka Streamlit

## Instalacja

1.  **Sklonuj repozytorium lub pobierz pliki projektu.**

2.  **Stwórz i aktywuj środowisko wirtualne** (zalecane):
    ```bash
    # Linux / macOS
    python3 -m venv .venv
    source .venv/bin/activate

    # Windows
    python -m venv .venv
    .venv\Scripts\activate
    ```

3.  **Zainstaluj wymagane biblioteki:**
    Jeśli posiadasz plik `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
    W przeciwnym wypadku zainstaluj Streamlit ręcznie:
    ```bash
    pip install streamlit
    ```
    Kiedy prosi o email wystarczy wcisnąć Enter 

## Uruchomienie

Aby uruchomić aplikację, wykonaj w terminalu poniższe polecenie (upewniając się, że jesteś w głównym katalogu projektu):

```bash
streamlit run main.py