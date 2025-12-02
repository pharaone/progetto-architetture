#!/usr/bin/env python3
"""
Test di Integrazione Kitchen Service
Testa solo i kitchen services (senza dipendenze da menu service)
"""

import requests
import time
import uuid
import sys

# Configurazione
KITCHEN_1_URL = "http://localhost:8001/api"
KITCHEN_2_URL = "http://localhost:8002/api"
API_KEY = "changeme123"
HEADERS = {"X-API-Key": API_KEY}

# Colori
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def print_test(name: str):
    print(f"\n{BLUE}{'='*80}{NC}")
    print(f"{BLUE}🧪 {name}{NC}")
    print(f"{BLUE}{'='*80}{NC}")

def print_pass(msg: str):
    print(f"{GREEN}  ✅ {msg}{NC}")

def print_fail(msg: str):
    print(f"{RED}  ❌ {msg}{NC}")

def print_info(msg: str):
    print(f"{YELLOW}  ℹ️  {msg}{NC}")


class KitchenIntegrationTest:
    
    def __init__(self):
        self.results = []
    
    def test_kitchen_health(self):
        """Test 1: Verifica salute cucine"""
        print_test("Kitchen Services Health")
        
        for name, url in [("Kitchen 1", KITCHEN_1_URL), ("Kitchen 2", KITCHEN_2_URL)]:
            try:
                response = requests.get(url.replace('/api', '/health'), timeout=5)
                if response.status_code == 200:
                    print_pass(f"{name} is online")
                    self.results.append(True)
                else:
                    print_fail(f"{name} status: {response.status_code}")
                    self.results.append(False)
            except Exception as e:
                print_fail(f"{name}: {e}")
                self.results.append(False)
    
    def test_kitchen_status(self):
        """Test 2: Verifica stato cucina"""
        print_test("Kitchen Status API")
        
        try:
            response = requests.get(f"{KITCHEN_1_URL}/kitchen")
            response.raise_for_status()
            
            status = response.json()
            print_info(f"Kitchen ID: {status['kitchen_id']}")
            print_info(f"Operational: {status['is_operational']}")
            print_info(f"Current Load: {status['current_load']}")
            print_info(f"Max Load: {status['max_load']}")
            
            # Verifica campi obbligatori
            required_fields = ['kitchen_id', 'is_operational', 'current_load', 'max_load']
            if all(field in status for field in required_fields):
                print_pass("Tutti i campi presenti")
                self.results.append(True)
            else:
                print_fail("Campi mancanti")
                self.results.append(False)
                
        except Exception as e:
            print_fail(str(e))
            self.results.append(False)
    
    def test_menu_operations(self):
        """Test 3: Operazioni sul menu"""
        print_test("Menu Operations (Kitchen 1)")
        
        dish_id = str(uuid.uuid4())
        
        try:
            # CREATE
            print_info("CREATE: Aggiunta piatto...")
            dish_data = {
                "dish_id": dish_id,
                "name": "Spaghetti Carbonara Test",
                "price": 12.50,
                "available_quantity": 8
            }
            
            response = requests.post(
                f"{KITCHEN_1_URL}/menu/dishes",
                json=dish_data,
                headers=HEADERS
            )
            
            if response.status_code == 201:
                print_pass("Piatto creato")
                self.results.append(True)
            else:
                print_fail(f"Status: {response.status_code}")
                self.results.append(False)
                return
            
            # READ
            print_info("READ: Lettura piatto...")
            response = requests.get(f"{KITCHEN_1_URL}/menu/dishes/{dish_id}")
            
            if response.status_code == 200:
                dish = response.json()
                if dish['dish_id'] == dish_id and dish['name'] == "Spaghetti Carbonara Test":
                    print_pass("Piatto letto correttamente")
                    self.results.append(True)
                else:
                    print_fail("Dati non corrispondono")
                    self.results.append(False)
            else:
                print_fail(f"Status: {response.status_code}")
                self.results.append(False)
            
            # LIST
            print_info("LIST: Lista tutti i piatti...")
            response = requests.get(f"{KITCHEN_1_URL}/menu/dishes")
            
            if response.status_code == 200:
                dishes = response.json()
                found = any(d['dish_id'] == dish_id for d in dishes)
                if found:
                    print_pass(f"Piatto trovato nella lista ({len(dishes)} totali)")
                    self.results.append(True)
                else:
                    print_fail("Piatto non nella lista")
                    self.results.append(False)
            else:
                print_fail(f"Status: {response.status_code}")
                self.results.append(False)
            
            # RESTOCK
            print_info("UPDATE: Restock piatto (+5)...")
            response = requests.patch(
                f"{KITCHEN_1_URL}/menu/dishes/{dish_id}/restock?amount=5",
                headers=HEADERS
            )
            
            if response.status_code == 200:
                updated = response.json()
                if updated['available_quantity'] == 13:  # 8 + 5
                    print_pass(f"Quantità aggiornata: 8 → 13")
                    self.results.append(True)
                else:
                    print_fail(f"Quantità errata: {updated['available_quantity']}")
                    self.results.append(False)
            else:
                print_fail(f"Status: {response.status_code}")
                self.results.append(False)
            
            # DELETE
            print_info("DELETE: Eliminazione piatto...")
            response = requests.delete(
                f"{KITCHEN_1_URL}/menu/dishes/{dish_id}",
                headers=HEADERS
            )
            
            if response.status_code in [200, 204]:
                print_pass("Piatto eliminato")
                self.results.append(True)
            else:
                print_fail(f"Status: {response.status_code}")
                self.results.append(False)
            
            # Verifica eliminazione
            response = requests.get(f"{KITCHEN_1_URL}/menu/dishes/{dish_id}")
            if response.status_code == 404:
                print_pass("Eliminazione verificata (404)")
                self.results.append(True)
            else:
                print_fail("Piatto ancora presente")
                self.results.append(False)
                
        except Exception as e:
            print_fail(str(e))
            self.results.append(False)
    
    def test_kitchen_isolation(self):
        """Test 4: Isolamento tra cucine"""
        print_test("Kitchen Isolation Test")
        
        dish1_id = str(uuid.uuid4())
        dish2_id = str(uuid.uuid4())
        
        try:
            # Crea piatto in Kitchen 1
            print_info("Creazione piatto in Kitchen 1...")
            response = requests.post(
                f"{KITCHEN_1_URL}/menu/dishes",
                json={
                    "dish_id": dish1_id,
                    "name": "Piatto Kitchen 1",
                    "price": 10.00,
                    "available_quantity": 5
                },
                headers=HEADERS
            )
            
            if response.status_code != 201:
                print_fail("Creazione in Kitchen 1 fallita")
                self.results.append(False)
                return
            
            # Crea piatto in Kitchen 2
            print_info("Creazione piatto in Kitchen 2...")
            response = requests.post(
                f"{KITCHEN_2_URL}/menu/dishes",
                json={
                    "dish_id": dish2_id,
                    "name": "Piatto Kitchen 2",
                    "price": 20.00,
                    "available_quantity": 3
                },
                headers=HEADERS
            )
            
            if response.status_code != 201:
                print_fail("Creazione in Kitchen 2 fallita")
                self.results.append(False)
                return
            
            time.sleep(1)
            
            # Verifica che Kitchen 1 non abbia il piatto di Kitchen 2
            print_info("Verifica isolamento Kitchen 1...")
            response = requests.get(f"{KITCHEN_1_URL}/menu/dishes")
            dishes1 = response.json()
            
            has_own = any(d['dish_id'] == dish1_id for d in dishes1)
            has_other = any(d['dish_id'] == dish2_id for d in dishes1)
            
            if has_own and not has_other:
                print_pass("Kitchen 1: ha solo i suoi piatti")
                self.results.append(True)
            else:
                print_fail(f"Kitchen 1: isolamento fallito (own={has_own}, other={has_other})")
                self.results.append(False)
            
            # Verifica che Kitchen 2 non abbia il piatto di Kitchen 1
            print_info("Verifica isolamento Kitchen 2...")
            response = requests.get(f"{KITCHEN_2_URL}/menu/dishes")
            dishes2 = response.json()
            
            has_own2 = any(d['dish_id'] == dish2_id for d in dishes2)
            has_other2 = any(d['dish_id'] == dish1_id for d in dishes2)
            
            if has_own2 and not has_other2:
                print_pass("Kitchen 2: ha solo i suoi piatti")
                self.results.append(True)
            else:
                print_fail(f"Kitchen 2: isolamento fallito (own={has_own2}, other={has_other2})")
                self.results.append(False)
            
            # Cleanup
            requests.delete(f"{KITCHEN_1_URL}/menu/dishes/{dish1_id}", headers=HEADERS)
            requests.delete(f"{KITCHEN_2_URL}/menu/dishes/{dish2_id}", headers=HEADERS)
            
        except Exception as e:
            print_fail(str(e))
            self.results.append(False)
    
    def test_kitchen_operational_toggle(self):
        """Test 5: Toggle stato operativo cucina"""
        print_test("Kitchen Operational Status Toggle")
        
        try:
            # Ottieni stato iniziale
            response = requests.get(f"{KITCHEN_1_URL}/kitchen")
            initial_status = response.json()
            initial_operational = initial_status['is_operational']
            
            print_info(f"Stato iniziale: {'Operativa' if initial_operational else 'Non operativa'}")
            
            # Toggle a non operativa
            print_info("Toggle a non operativa...")
            response = requests.patch(
                f"{KITCHEN_1_URL}/kitchen?is_operational=false",
                headers=HEADERS
            )
            
            if response.status_code == 200:
                # Verifica
                response = requests.get(f"{KITCHEN_1_URL}/kitchen")
                status = response.json()
                
                if not status['is_operational']:
                    print_pass("Cucina impostata a non operativa")
                    self.results.append(True)
                else:
                    print_fail("Stato non cambiato")
                    self.results.append(False)
            else:
                print_fail(f"Status: {response.status_code}")
                self.results.append(False)
            
            # Riporta allo stato iniziale
            print_info(f"Ripristino stato iniziale...")
            requests.patch(
                f"{KITCHEN_1_URL}/kitchen?is_operational={str(initial_operational).lower()}",
                headers=HEADERS
            )
            
        except Exception as e:
            print_fail(str(e))
            self.results.append(False)
    
    def test_orders_list(self):
        """Test 6: Lista ordini"""
        print_test("Orders List API")
        
        try:
            response = requests.get(f"{KITCHEN_1_URL}/orders")
            response.raise_for_status()
            
            orders = response.json()
            print_info(f"Ordini trovati: {len(orders)}")
            
            # Verifica che sia una lista
            if isinstance(orders, list):
                print_pass("Risposta è una lista valida")
                self.results.append(True)
                
                # Se ci sono ordini, verifica struttura
                if len(orders) > 0:
                    first_order = orders[0]
                    required_fields = ['order_id', 'status', 'kitchen_id']
                    
                    if all(field in first_order for field in required_fields):
                        print_pass("Struttura ordine valida")
                        print_info(f"  Esempio: {first_order['order_id'][:8]}... - {first_order['status']}")
                        self.results.append(True)
                    else:
                        print_fail("Campi mancanti nell'ordine")
                        self.results.append(False)
            else:
                print_fail("Risposta non è una lista")
                self.results.append(False)
                
        except Exception as e:
            print_fail(str(e))
            self.results.append(False)
    
    def run_all_tests(self):
        """Esegue tutti i test"""
        print(f"\n{BLUE}{'='*80}{NC}")
        print(f"{BLUE}🧪 TEST DI INTEGRAZIONE KITCHEN SERVICE{NC}")
        print(f"{BLUE}{'='*80}{NC}\n")
        
        # Esegui test
        self.test_kitchen_health()
        self.test_kitchen_status()
        self.test_menu_operations()
        self.test_kitchen_isolation()
        self.test_kitchen_operational_toggle()
        self.test_orders_list()
        
        # Riepilogo
        print(f"\n{BLUE}{'='*80}{NC}")
        print(f"{BLUE}📊 RIEPILOGO{NC}")
        print(f"{BLUE}{'='*80}{NC}\n")
        
        passed = sum(self.results)
        total = len(self.results)
        
        print(f"   Test passati: {passed}/{total}")
        print(f"   Success rate: {(passed/total*100):.1f}%\n")
        
        if passed == total:
            print(f"{GREEN}{'='*80}{NC}")
            print(f"{GREEN}🎉 TUTTI I {total} TEST PASSATI!{NC}")
            print(f"{GREEN}{'='*80}{NC}\n")
            return True
        else:
            print(f"{RED}{'='*80}{NC}")
            print(f"{RED}⚠️  {total - passed} TEST FALLITI{NC}")
            print(f"{RED}{'='*80}{NC}\n")
            return False


if __name__ == "__main__":
    test = KitchenIntegrationTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)

