#!/usr/bin/env python3
"""
Test di Integrazione End-to-End
Verifica l'intero flusso: creazione menu → creazione ordine → cambio stato → completamento
"""

import requests
import time
import uuid
from typing import Dict, Any

# Configurazione servizi
MENU_SERVICE_URL = "http://localhost:9999"
KITCHEN_SERVICE_1_URL = "http://localhost:8001/api"
KITCHEN_SERVICE_2_URL = "http://localhost:8002/api"
ROUTING_SERVICE_URL = "http://localhost:8080"

API_KEY = "changeme123"
HEADERS = {"X-API-Key": API_KEY}

# Colori per output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_step(step: str):
    print(f"\n{BLUE}{'='*80}{NC}")
    print(f"{BLUE}📋 {step}{NC}")
    print(f"{BLUE}{'='*80}{NC}")

def print_success(message: str):
    print(f"{GREEN}✅ {message}{NC}")

def print_error(message: str):
    print(f"{RED}❌ {message}{NC}")

def print_info(message: str):
    print(f"{YELLOW}ℹ️  {message}{NC}")

def print_data(label: str, data: Any):
    print(f"   {label}: {data}")


class IntegrationTest:
    def __init__(self):
        self.test_user_id = None
        self.test_dish_id = None
        self.test_order_id = None
        self.kitchen_1_initial_load = None
        
    def check_services_health(self) -> bool:
        """Verifica che tutti i servizi siano raggiungibili"""
        print_step("1. Verifica Salute Servizi")
        
        services = {
            "Menu Service": (f"{MENU_SERVICE_URL}/api/docs", True),  # OpenAPI docs
            "Kitchen Service 1": (f"{KITCHEN_SERVICE_1_URL.replace('/api', '')}/health", False),
            "Kitchen Service 2": (f"{KITCHEN_SERVICE_2_URL.replace('/api', '')}/health", False),
        }
        
        all_healthy = True
        for name, (url, is_optional) in services.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print_success(f"{name} è online")
                else:
                    if is_optional:
                        print_info(f"{name} risponde (status {response.status_code}) - proseguo comunque")
                    else:
                        print_error(f"{name} risponde ma con status {response.status_code}")
                        all_healthy = False
            except Exception as e:
                if is_optional:
                    print_info(f"{name} non raggiungibile - proseguo comunque")
                else:
                    print_error(f"{name} non raggiungibile: {e}")
                    all_healthy = False
        
        return all_healthy
    
    def get_kitchen_status(self, kitchen_url: str) -> Dict:
        """Ottiene lo stato attuale di una cucina"""
        response = requests.get(f"{kitchen_url}/kitchen")
        response.raise_for_status()
        return response.json()
    
    def create_test_user(self) -> bool:
        """Crea un utente di test nel menu service"""
        print_step("2. Creazione Utente di Test")
        
        # Genera email univoca
        timestamp = int(time.time() % 10000)
        email = f"test_user_{timestamp}@test.com"
        password = "test123"
        region = "Centro"
        
        try:
            # Registra nuovo utente
            response = requests.post(
                f"{MENU_SERVICE_URL}/users/register",
                json={
                    "email": email,
                    "password": password
                },
                params={"region": region}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.test_user_id = result['user_id']  # Mantieni come UUID string
                
                print_success("Utente creato")
                print_data("User ID", self.test_user_id)
                print_data("Email", email)
                print_data("Regione", region)
                return True
            else:
                # Prova a fare login se l'utente esiste già
                print_info("Utente potrebbe esistere, provo login...")
                response = requests.post(
                    f"{MENU_SERVICE_URL}/users/login",
                    json={
                        "email": email,
                        "password": password
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.test_user_id = result['user_id']  # Mantieni come UUID string
                    print_success("Login utente esistente")
                    print_data("User ID", self.test_user_id)
                    return True
                else:
                    print_error(f"Errore: {response.status_code}")
                    return False
            
        except Exception as e:
            print_error(f"Errore nella creazione utente: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print_error(f"Response: {e.response.text}")
            return False
    
    def create_menu_item(self, kitchen_url: str, kitchen_name: str) -> bool:
        """Crea un piatto nel menu della cucina"""
        print_step(f"3. Creazione Piatto nel Menu - {kitchen_name}")
        
        self.test_dish_id = str(uuid.uuid4())
        
        dish_data = {
            "dish_id": self.test_dish_id,
            "name": f"Test Dish {int(time.time() % 1000)}",
            "price": 12.50,
            "available_quantity": 10
        }
        
        try:
            response = requests.post(
                f"{kitchen_url}/menu/dishes",
                json=dish_data,
                headers=HEADERS
            )
            response.raise_for_status()
            
            dish = response.json()
            print_success(f"Piatto creato: {dish['name']}")
            print_data("Dish ID", self.test_dish_id)
            print_data("Prezzo", f"€{dish['price']}")
            print_data("Quantità", dish['available_quantity'])
            
            return True
            
        except Exception as e:
            print_error(f"Errore nella creazione piatto: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print_error(f"Response: {e.response.text}")
            return False
    
    def get_menu_items(self, kitchen_url: str) -> int:
        """Ottiene tutti i piatti del menu"""
        try:
            response = requests.get(f"{kitchen_url}/menu/dishes")
            response.raise_for_status()
            dishes = response.json()
            print_info(f"Piatti nel menu: {len(dishes)}")
            return len(dishes)
        except Exception as e:
            print_error(f"Errore nel recupero menu: {e}")
            return 0
    
    def create_order(self) -> bool:
        """Crea un nuovo ordine"""
        print_step("4. Creazione Ordine")
        
        # Salva il carico iniziale
        kitchen_status = self.get_kitchen_status(KITCHEN_SERVICE_1_URL)
        self.kitchen_1_initial_load = kitchen_status['current_load']
        print_info(f"Carico iniziale cucina: {self.kitchen_1_initial_load}")
        
        try:
            response = requests.post(
                f"{MENU_SERVICE_URL}/orders/new_order",
                params={
                    "dish_id": self.test_dish_id,
                    "user_id": self.test_user_id
                }
            )
            response.raise_for_status()
            
            order = response.json()
            self.test_order_id = order['id']
            
            print_success(f"Ordine creato")
            print_data("Order ID", self.test_order_id)
            print_data("Dish ID", order['dish_id'])
            print_data("User ID", order['user_id'])
            print_data("Status", order['status'])
            
            # Attendi che l'ordine venga processato (routing service usa finestra di 15 secondi)
            print_info("Attendo 18 secondi per il processing...")
            time.sleep(18)
            
            return True
            
        except Exception as e:
            print_error(f"Errore nella creazione ordine: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print_error(f"Response: {e.response.text}")
            return False
    
    def verify_order_assigned(self) -> bool:
        """Verifica che l'ordine sia stato assegnato a una cucina"""
        print_step("5. Verifica Assegnazione Ordine")
        
        try:
            # Verifica ordini nella cucina 1
            response = requests.get(f"{KITCHEN_SERVICE_1_URL}/orders")
            response.raise_for_status()
            
            orders = response.json()
            print_info(f"Ordini totali in Kitchen 1: {len(orders)}")
            
            # Cerca il nostro ordine
            our_order = None
            for order in orders:
                if order['order_id'] == self.test_order_id:
                    our_order = order
                    break
            
            if our_order:
                print_success(f"Ordine trovato in Kitchen 1")
                print_data("Status", our_order['status'])
                print_data("Dish ID", our_order.get('dish_id', 'N/A'))
                
                # Verifica carico aumentato
                kitchen_status = self.get_kitchen_status(KITCHEN_SERVICE_1_URL)
                new_load = kitchen_status['current_load']
                print_data("Carico cucina", f"{self.kitchen_1_initial_load} → {new_load}")
                
                if new_load > self.kitchen_1_initial_load:
                    print_success("✓ Carico cucina aumentato correttamente")
                else:
                    print_error("✗ Carico cucina NON aumentato")
                
                return True
            else:
                print_error("Ordine NON trovato nella cucina")
                return False
                
        except Exception as e:
            print_error(f"Errore nella verifica ordine: {e}")
            return False
    
    def update_order_status(self, new_status: str) -> bool:
        """Aggiorna lo stato dell'ordine"""
        print_step(f"6. Aggiornamento Stato Ordine → {new_status}")
        
        try:
            response = requests.patch(
                f"{KITCHEN_SERVICE_1_URL}/orders/{self.test_order_id}/status",
                json={"status": new_status},
                headers=HEADERS
            )
            response.raise_for_status()
            
            print_success(f"Stato aggiornato a: {new_status}")
            
            # Attendi propagazione
            time.sleep(1)
            
            return True
            
        except Exception as e:
            print_error(f"Errore nell'aggiornamento stato: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print_error(f"Response: {e.response.text}")
            return False
    
    def verify_order_status(self, expected_status: str) -> bool:
        """Verifica lo stato corrente dell'ordine"""
        try:
            response = requests.get(f"{KITCHEN_SERVICE_1_URL}/orders")
            response.raise_for_status()
            
            orders = response.json()
            for order in orders:
                if order['order_id'] == self.test_order_id:
                    actual_status = order['status']
                    if actual_status == expected_status:
                        print_success(f"✓ Stato verificato: {actual_status}")
                        return True
                    else:
                        print_error(f"✗ Stato errato: {actual_status} (atteso: {expected_status})")
                        return False
            
            print_error("Ordine non trovato")
            return False
            
        except Exception as e:
            print_error(f"Errore nella verifica stato: {e}")
            return False
    
    def verify_load_decreased(self) -> bool:
        """Verifica che il carico sia diminuito dopo il completamento"""
        print_step("7. Verifica Decremento Carico")
        
        try:
            kitchen_status = self.get_kitchen_status(KITCHEN_SERVICE_1_URL)
            final_load = kitchen_status['current_load']
            
            print_data("Carico iniziale", self.kitchen_1_initial_load)
            print_data("Carico finale", final_load)
            
            if final_load == self.kitchen_1_initial_load:
                print_success("✓ Carico ritornato al valore iniziale")
                return True
            else:
                print_error(f"✗ Carico non corretto (differenza: {final_load - self.kitchen_1_initial_load})")
                return False
                
        except Exception as e:
            print_error(f"Errore nella verifica carico: {e}")
            return False
    
    def cleanup(self):
        """Pulizia: elimina il piatto di test"""
        print_step("8. Pulizia")
        
        try:
            response = requests.delete(
                f"{KITCHEN_SERVICE_1_URL}/menu/dishes/{self.test_dish_id}",
                headers=HEADERS
            )
            if response.status_code in [200, 204]:
                print_success("Piatto di test eliminato")
            else:
                print_info(f"Piatto non eliminato (status: {response.status_code})")
        except Exception as e:
            print_info(f"Cleanup piatto: {e}")
    
    def run_full_test(self) -> bool:
        """Esegue l'intero test di integrazione"""
        print(f"\n{BLUE}{'='*80}{NC}")
        print(f"{BLUE}🚀 INIZIO TEST DI INTEGRAZIONE END-TO-END{NC}")
        print(f"{BLUE}{'='*80}{NC}\n")
        
        results = []
        
        # 1. Verifica servizi
        if not self.check_services_health():
            print_error("\n⛔ Test interrotto: servizi non disponibili")
            return False
        results.append(True)
        
        # 2. Crea utente
        results.append(self.create_test_user())
        
        # 3. Crea piatto nel menu
        results.append(self.create_menu_item(KITCHEN_SERVICE_1_URL, "Kitchen 1"))
        
        # 3.1 Verifica menu
        menu_count = self.get_menu_items(KITCHEN_SERVICE_1_URL)
        
        # 4. Crea ordine
        results.append(self.create_order())
        
        # 5. Verifica assegnazione
        results.append(self.verify_order_assigned())
        
        # 6. Aggiorna stato a PREPARING
        results.append(self.update_order_status("preparing"))
        results.append(self.verify_order_status("preparing"))
        
        # 7. Aggiorna stato a COMPLETED
        results.append(self.update_order_status("completed"))
        results.append(self.verify_order_status("completed"))
        
        # 8. Verifica carico decrementato
        results.append(self.verify_load_decreased())
        
        # 9. Cleanup
        self.cleanup()
        
        # Riepilogo
        print(f"\n{BLUE}{'='*80}{NC}")
        print(f"{BLUE}📊 RIEPILOGO TEST{NC}")
        print(f"{BLUE}{'='*80}{NC}")
        
        passed = sum(results)
        total = len(results)
        
        print(f"\n   Test passati: {passed}/{total}")
        
        if all(results):
            print(f"\n{GREEN}{'='*80}{NC}")
            print(f"{GREEN}🎉 TUTTI I TEST PASSATI CON SUCCESSO!{NC}")
            print(f"{GREEN}{'='*80}{NC}\n")
            return True
        else:
            print(f"\n{RED}{'='*80}{NC}")
            print(f"{RED}❌ ALCUNI TEST SONO FALLITI{NC}")
            print(f"{RED}{'='*80}{NC}\n")
            return False


if __name__ == "__main__":
    test = IntegrationTest()
    success = test.run_full_test()
    exit(0 if success else 1)

