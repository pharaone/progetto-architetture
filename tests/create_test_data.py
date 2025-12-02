#!/usr/bin/env python3
"""
Script per creare dati di test nei kitchen services
Utile per popolare i database prima di eseguire i test
"""

import requests
import uuid
import sys

KITCHEN_1_URL = "http://localhost:8001/api"
KITCHEN_2_URL = "http://localhost:8002/api"
API_KEY = "changeme123"
HEADERS = {"X-API-Key": API_KEY}

GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
NC = '\033[0m'

def create_sample_dishes():
    """Crea alcuni piatti di esempio in Kitchen 1"""
    print(f"\n{YELLOW}🍽️  Creazione piatti di esempio in Kitchen 1...{NC}\n")
    
    dishes = [
        {
            "dish_id": str(uuid.uuid4()),
            "name": "Spaghetti Carbonara",
            "price": 12.50,
            "available_quantity": 10
        },
        {
            "dish_id": str(uuid.uuid4()),
            "name": "Pizza Margherita",
            "price": 8.00,
            "available_quantity": 15
        },
        {
            "dish_id": str(uuid.uuid4()),
            "name": "Lasagna",
            "price": 14.00,
            "available_quantity": 8
        },
        {
            "dish_id": str(uuid.uuid4()),
            "name": "Risotto ai Funghi",
            "price": 13.50,
            "available_quantity": 12
        },
        {
            "dish_id": str(uuid.uuid4()),
            "name": "Tiramisù",
            "price": 6.00,
            "available_quantity": 20
        }
    ]
    
    created_count = 0
    for dish in dishes:
        try:
            response = requests.post(
                f"{KITCHEN_1_URL}/menu/dishes",
                json=dish,
                headers=HEADERS
            )
            
            if response.status_code == 201:
                print(f"{GREEN}✅ {dish['name']}{NC} - €{dish['price']} ({dish['available_quantity']} disponibili)")
                created_count += 1
            else:
                print(f"⚠️  {dish['name']} - Errore {response.status_code}")
        except Exception as e:
            print(f"❌ {dish['name']} - Errore: {e}")
    
    print(f"\n{GREEN}Creati {created_count}/{len(dishes)} piatti{NC}\n")

def create_sample_dishes_kitchen2():
    """Crea piatti diversi in Kitchen 2"""
    print(f"\n{YELLOW}🍽️  Creazione piatti di esempio in Kitchen 2...{NC}\n")
    
    dishes = [
        {
            "dish_id": str(uuid.uuid4()),
            "name": "Pasta al Pesto",
            "price": 11.00,
            "available_quantity": 7
        },
        {
            "dish_id": str(uuid.uuid4()),
            "name": "Bistecca Fiorentina",
            "price": 25.00,
            "available_quantity": 5
        },
        {
            "dish_id": str(uuid.uuid4()),
            "name": "Panna Cotta",
            "price": 5.50,
            "available_quantity": 15
        }
    ]
    
    created_count = 0
    for dish in dishes:
        try:
            response = requests.post(
                f"{KITCHEN_2_URL}/menu/dishes",
                json=dish,
                headers=HEADERS
            )
            
            if response.status_code == 201:
                print(f"{GREEN}✅ {dish['name']}{NC} - €{dish['price']} ({dish['available_quantity']} disponibili)")
                created_count += 1
            else:
                print(f"⚠️  {dish['name']} - Errore {response.status_code}")
        except Exception as e:
            print(f"❌ {dish['name']} - Errore: {e}")
    
    print(f"\n{GREEN}Creati {created_count}/{len(dishes)} piatti{NC}\n")

def show_current_status():
    """Mostra lo stato attuale delle cucine"""
    print(f"\n{YELLOW}📊 STATO ATTUALE CUCINE{NC}\n")
    
    for name, url in [("Kitchen 1", KITCHEN_1_URL), ("Kitchen 2", KITCHEN_2_URL)]:
        try:
            # Stato cucina
            response = requests.get(f"{url}/kitchen")
            status = response.json()
            
            # Menu
            response_menu = requests.get(f"{url}/menu/dishes")
            dishes = response_menu.json()
            
            # Ordini
            response_orders = requests.get(f"{url}/orders")
            orders = response_orders.json()
            
            print(f"{GREEN}━━━ {name} ━━━{NC}")
            print(f"  Kitchen ID: {status['kitchen_id']}")
            print(f"  Operational: {'✅' if status['is_operational'] else '❌'} {status['is_operational']}")
            print(f"  Load: {status['current_load']}/{status['max_load']}")
            print(f"  Piatti nel menu: {len(dishes)}")
            print(f"  Ordini attivi: {len([o for o in orders if o['status'] not in ['completed', 'cancelled']])}")
            print(f"  Ordini totali: {len(orders)}")
            print()
            
        except Exception as e:
            print(f"{RED}❌ {name}: {e}{NC}\n")

if __name__ == "__main__":
    print(f"\n{BLUE}{'='*80}{NC}")
    print(f"{BLUE}🔧 CREAZIONE DATI DI TEST{NC}")
    print(f"{BLUE}{'='*80}{NC}")
    
    print("\nCosa vuoi fare?")
    print("1) Crea piatti di esempio in Kitchen 1")
    print("2) Crea piatti di esempio in Kitchen 2")
    print("3) Crea in entrambe le cucine")
    print("4) Mostra solo stato attuale")
    print("5) Esci")
    
    choice = input("\nScelta (1-5): ")
    
    if choice == "1":
        create_sample_dishes()
        show_current_status()
    elif choice == "2":
        create_sample_dishes_kitchen2()
        show_current_status()
    elif choice == "3":
        create_sample_dishes()
        create_sample_dishes_kitchen2()
        show_current_status()
    elif choice == "4":
        show_current_status()
    elif choice == "5":
        print("👋 Ciao!")
    else:
        print(f"{RED}Scelta non valida{NC}")
        sys.exit(1)
    
    print(f"\n{GREEN}✅ Operazione completata!{NC}\n")

