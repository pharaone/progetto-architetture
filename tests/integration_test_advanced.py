#!/usr/bin/env python3
"""
Test di Integrazione Avanzati
Testa scenari multipli, edge cases, e flussi complessi
"""

import requests
import time
import uuid
import sys
from typing import List, Dict

# Configurazione servizi
MENU_SERVICE_URL = "http://localhost:9999"
KITCHEN_SERVICE_1_URL = "http://localhost:8001/api"
KITCHEN_SERVICE_2_URL = "http://localhost:8002/api"

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
    print(f"{BLUE}🧪 TEST: {name}{NC}")
    print(f"{BLUE}{'='*80}{NC}")

def print_pass(message: str):
    print(f"{GREEN}  ✅ PASS: {message}{NC}")

def print_fail(message: str):
    print(f"{RED}  ❌ FAIL: {message}{NC}")

def print_info(message: str):
    print(f"{YELLOW}  ℹ️  {message}{NC}")


class AdvancedIntegrationTests:
    
    def __init__(self):
        self.results = []
        
    def add_result(self, test_name: str, passed: bool, message: str = ""):
        self.results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })
        if passed:
            print_pass(message or test_name)
        else:
            print_fail(message or test_name)
    
    # ==================== TEST 1: Menu Management ====================
    
    def test_menu_crud(self) -> bool:
        """Test completo CRUD del menu"""
        print_test("Menu CRUD Operations")
        
        test_passed = True
        dish_id = str(uuid.uuid4())
        
        try:
            # CREATE
            print_info("1. Creazione piatto...")
            dish_data = {
                "dish_id": dish_id,
                "name": "Pasta Carbonara Test",
                "price": 15.00,
                "available_quantity": 5
            }
            
            response = requests.post(
                f"{KITCHEN_SERVICE_1_URL}/menu/dishes",
                json=dish_data,
                headers=HEADERS
            )
            
            if response.status_code == 201:
                self.add_result("Create Dish", True, f"Piatto creato con ID {dish_id[:8]}...")
            else:
                self.add_result("Create Dish", False, f"Status {response.status_code}")
                test_passed = False
            
            # READ
            print_info("2. Lettura piatto...")
            response = requests.get(f"{KITCHEN_SERVICE_1_URL}/menu/dishes/{dish_id}")
            
            if response.status_code == 200:
                dish = response.json()
                if dish['name'] == "Pasta Carbonara Test" and dish['price'] == 15.00:
                    self.add_result("Read Dish", True, "Piatto letto correttamente")
                else:
                    self.add_result("Read Dish", False, "Dati non corrispondono")
                    test_passed = False
            else:
                self.add_result("Read Dish", False, f"Status {response.status_code}")
                test_passed = False
            
            # LIST
            print_info("3. Lista piatti...")
            response = requests.get(f"{KITCHEN_SERVICE_1_URL}/menu/dishes")
            
            if response.status_code == 200:
                dishes = response.json()
                found = any(d['dish_id'] == dish_id for d in dishes)
                self.add_result("List Dishes", found, f"Trovati {len(dishes)} piatti")
            else:
                self.add_result("List Dishes", False, f"Status {response.status_code}")
                test_passed = False
            
            # RESTOCK
            print_info("4. Restock piatto...")
            response = requests.patch(
                f"{KITCHEN_SERVICE_1_URL}/menu/dishes/{dish_id}/restock?amount=10",
                headers=HEADERS
            )
            
            if response.status_code == 200:
                updated_dish = response.json()
                if updated_dish['available_quantity'] == 15:  # 5 + 10
                    self.add_result("Restock Dish", True, f"Quantità: 5 → 15")
                else:
                    self.add_result("Restock Dish", False, f"Quantità errata: {updated_dish['available_quantity']}")
                    test_passed = False
            else:
                self.add_result("Restock Dish", False, f"Status {response.status_code}")
                test_passed = False
            
            # DELETE
            print_info("5. Eliminazione piatto...")
            response = requests.delete(
                f"{KITCHEN_SERVICE_1_URL}/menu/dishes/{dish_id}",
                headers=HEADERS
            )
            
            if response.status_code in [200, 204]:
                self.add_result("Delete Dish", True, "Piatto eliminato")
            else:
                self.add_result("Delete Dish", False, f"Status {response.status_code}")
                test_passed = False
            
        except Exception as e:
            self.add_result("Menu CRUD", False, str(e))
            test_passed = False
        
        return test_passed
    
    # ==================== TEST 2: Order Lifecycle ====================
    
    def test_order_lifecycle(self) -> bool:
        """Test completo del ciclo di vita di un ordine"""
        print_test("Order Lifecycle - Complete Flow")
        
        test_passed = True
        
        try:
            # Setup: Crea un piatto
            dish_id = str(uuid.uuid4())
            dish_data = {
                "dish_id": dish_id,
                "name": "Pizza Margherita Test",
                "price": 10.00,
                "available_quantity": 3
            }
            
            requests.post(
                f"{KITCHEN_SERVICE_1_URL}/menu/dishes",
                json=dish_data,
                headers=HEADERS
            )
            
            # Crea utente
            print_info("Creazione utente...")
            timestamp = int(time.time() % 10000)
            user_response = requests.post(
                f"{MENU_SERVICE_URL}/users/register",
                json={
                    "email": f"test_order_{timestamp}@test.com",
                    "password": "test123"
                },
                params={"region": "Centro"}
            )
            user_id = user_response.json()['user_id']
            
            # Ottieni carico iniziale
            kitchen_status = requests.get(f"{KITCHEN_SERVICE_1_URL}/kitchen").json()
            initial_load = kitchen_status['current_load']
            print_info(f"Carico iniziale: {initial_load}")
            
            # Crea ordine
            print_info("Creazione ordine...")
            response = requests.post(
                f"{MENU_SERVICE_URL}/orders/new_order",
                params={"dish_id": dish_id, "user_id": user_id}
            )
            
            if response.status_code != 200:
                self.add_result("Order Creation", False, f"Status {response.status_code}")
                return False
            
            order = response.json()
            order_id = order['id']
            self.add_result("Order Creation", True, f"Order ID: {order_id[:8]}...")
            
            # Attendi assegnazione (il routing service usa una finestra di 15 secondi)
            time.sleep(18)
            
            # Verifica assegnazione e carico
            kitchen_status = requests.get(f"{KITCHEN_SERVICE_1_URL}/kitchen").json()
            load_after_assignment = kitchen_status['current_load']
            
            if load_after_assignment > initial_load:
                self.add_result("Load Increment", True, f"Carico: {initial_load} → {load_after_assignment}")
            else:
                self.add_result("Load Increment", False, f"Carico non incrementato")
                test_passed = False
            
            # Test transizioni di stato
            transitions = [
                ("received", "Received"),
                ("preparing", "Preparing"),
                ("ready_for_pickup", "Ready for Pickup"),
                ("completed", "Completed")
            ]
            
            for status_value, status_name in transitions:
                print_info(f"Cambio stato → {status_name}...")
                response = requests.patch(
                    f"{KITCHEN_SERVICE_1_URL}/orders/{order_id}/status",
                    json={"status": status_value},
                    headers=HEADERS
                )
                
                if response.status_code == 200:
                    self.add_result(f"Status → {status_name}", True)
                    time.sleep(1)
                else:
                    self.add_result(f"Status → {status_name}", False, f"Status {response.status_code}")
                    test_passed = False
            
            # Verifica carico finale
            time.sleep(2)
            kitchen_status = requests.get(f"{KITCHEN_SERVICE_1_URL}/kitchen").json()
            final_load = kitchen_status['current_load']
            
            # Il carico dovrebbe essere tornato al valore iniziale (decrementato al completamento)
            if final_load <= initial_load:
                self.add_result("Load Decrement", True, f"Carico finale: {final_load} (iniziale: {initial_load})")
            else:
                self.add_result("Load Decrement", False, f"Carico non decrementato: {final_load}")
                test_passed = False
            
            # Cleanup
            requests.delete(f"{KITCHEN_SERVICE_1_URL}/menu/dishes/{dish_id}", headers=HEADERS)
            
        except Exception as e:
            self.add_result("Order Lifecycle", False, str(e))
            test_passed = False
        
        return test_passed
    
    # ==================== TEST 3: Multiple Orders ====================
    
    def test_multiple_orders(self) -> bool:
        """Test con ordini multipli simultanei"""
        print_test("Multiple Concurrent Orders")
        
        test_passed = True
        
        try:
            # Crea un piatto
            dish_id = str(uuid.uuid4())
            dish_data = {
                "dish_id": dish_id,
                "name": "Lasagna Test",
                "price": 12.00,
                "available_quantity": 10
            }
            
            requests.post(
                f"{KITCHEN_SERVICE_1_URL}/menu/dishes",
                json=dish_data,
                headers=HEADERS
            )
            
            # Carico iniziale
            kitchen_status = requests.get(f"{KITCHEN_SERVICE_1_URL}/kitchen").json()
            initial_load = kitchen_status['current_load']
            
            # Crea 3 ordini
            print_info("Creazione di 3 ordini...")
            order_ids = []
            
            for i in range(3):
                # Crea utente per questo ordine
                timestamp = int(time.time() % 10000)
                user_response = requests.post(
                    f"{MENU_SERVICE_URL}/users/register",
                    json={
                        "email": f"test_multi_{timestamp}_{i}@test.com",
                        "password": "test123"
                    },
                    params={"region": "Centro"}
                )
                user_id = user_response.json()['user_id']
                
                response = requests.post(
                    f"{MENU_SERVICE_URL}/orders/new_order",
                    params={"dish_id": dish_id, "user_id": user_id}
                )
                
                if response.status_code == 200:
                    order = response.json()
                    order_ids.append(order['id'])
                    print_info(f"  Ordine {i+1} creato: {order['id'][:8]}...")
            
            # Attendi assegnazione (il routing service usa una finestra di 15 secondi)
            time.sleep(18)
            
            # Verifica carico
            kitchen_status = requests.get(f"{KITCHEN_SERVICE_1_URL}/kitchen").json()
            load_with_orders = kitchen_status['current_load']
            
            expected_load = initial_load + len(order_ids)
            if load_with_orders >= initial_load + len(order_ids):
                self.add_result("Multiple Orders Load", True, f"Carico: {initial_load} → {load_with_orders}")
            else:
                self.add_result("Multiple Orders Load", False, f"Carico: {load_with_orders}, atteso: {expected_load}")
                test_passed = False
            
            # Completa tutti gli ordini
            print_info("Completamento di tutti gli ordini...")
            for i, order_id in enumerate(order_ids):
                requests.patch(
                    f"{KITCHEN_SERVICE_1_URL}/orders/{order_id}/status",
                    json={"status": "completed"},
                    headers=HEADERS
                )
                time.sleep(0.5)
            
            time.sleep(2)
            
            # Verifica carico finale
            kitchen_status = requests.get(f"{KITCHEN_SERVICE_1_URL}/kitchen").json()
            final_load = kitchen_status['current_load']
            
            if final_load <= initial_load:
                self.add_result("Multiple Orders Cleanup", True, f"Carico finale: {final_load}")
            else:
                self.add_result("Multiple Orders Cleanup", False, f"Carico non decrementato correttamente")
                test_passed = False
            
            # Cleanup
            requests.delete(f"{KITCHEN_SERVICE_1_URL}/menu/dishes/{dish_id}", headers=HEADERS)
            
        except Exception as e:
            self.add_result("Multiple Orders", False, str(e))
            test_passed = False
        
        return test_passed
    
    # ==================== TEST 4: Kitchen Isolation ====================
    
    def test_kitchen_isolation(self) -> bool:
        """Verifica che le cucine siano isolate tra loro"""
        print_test("Kitchen Isolation")
        
        test_passed = True
        
        try:
            # Crea piatto in Kitchen 1
            dish1_id = str(uuid.uuid4())
            dish1_data = {
                "dish_id": dish1_id,
                "name": "Piatto Kitchen 1",
                "price": 10.00,
                "available_quantity": 5
            }
            
            response = requests.post(
                f"{KITCHEN_SERVICE_1_URL}/menu/dishes",
                json=dish1_data,
                headers=HEADERS
            )
            
            if response.status_code == 201:
                self.add_result("Create in Kitchen 1", True)
            else:
                self.add_result("Create in Kitchen 1", False)
                test_passed = False
            
            # Crea piatto in Kitchen 2
            dish2_id = str(uuid.uuid4())
            dish2_data = {
                "dish_id": dish2_id,
                "name": "Piatto Kitchen 2",
                "price": 20.00,
                "available_quantity": 3
            }
            
            response = requests.post(
                f"{KITCHEN_SERVICE_2_URL}/menu/dishes",
                json=dish2_data,
                headers=HEADERS
            )
            
            if response.status_code == 201:
                self.add_result("Create in Kitchen 2", True)
            else:
                self.add_result("Create in Kitchen 2", False)
                test_passed = False
            
            # Verifica isolamento: Kitchen 1 non deve avere dish2
            time.sleep(1)
            response1 = requests.get(f"{KITCHEN_SERVICE_1_URL}/menu/dishes")
            dishes1 = response1.json()
            
            has_dish1 = any(d['dish_id'] == dish1_id for d in dishes1)
            has_dish2 = any(d['dish_id'] == dish2_id for d in dishes1)
            
            if has_dish1 and not has_dish2:
                self.add_result("Kitchen 1 Isolation", True, "Ha solo i suoi piatti")
            else:
                self.add_result("Kitchen 1 Isolation", False, f"dish1={has_dish1}, dish2={has_dish2}")
                test_passed = False
            
            # Verifica isolamento: Kitchen 2 non deve avere dish1
            response2 = requests.get(f"{KITCHEN_SERVICE_2_URL}/menu/dishes")
            dishes2 = response2.json()
            
            has_dish1_k2 = any(d['dish_id'] == dish1_id for d in dishes2)
            has_dish2_k2 = any(d['dish_id'] == dish2_id for d in dishes2)
            
            if has_dish2_k2 and not has_dish1_k2:
                self.add_result("Kitchen 2 Isolation", True, "Ha solo i suoi piatti")
            else:
                self.add_result("Kitchen 2 Isolation", False, f"dish1={has_dish1_k2}, dish2={has_dish2_k2}")
                test_passed = False
            
            # Cleanup
            requests.delete(f"{KITCHEN_SERVICE_1_URL}/menu/dishes/{dish1_id}", headers=HEADERS)
            requests.delete(f"{KITCHEN_SERVICE_2_URL}/menu/dishes/{dish2_id}", headers=HEADERS)
            
        except Exception as e:
            self.add_result("Kitchen Isolation", False, str(e))
            test_passed = False
        
        return test_passed
    
    # ==================== TEST 5: Order Status Transitions ====================
    
    def test_order_status_transitions(self) -> bool:
        """Test di tutte le transizioni di stato possibili"""
        print_test("Order Status Transitions")
        
        test_passed = True
        
        try:
            # Setup
            dish_id = str(uuid.uuid4())
            requests.post(
                f"{KITCHEN_SERVICE_1_URL}/menu/dishes",
                json={
                    "dish_id": dish_id,
                    "name": "Test Status Transitions",
                    "price": 8.00,
                    "available_quantity": 5
                },
                headers=HEADERS
            )
            
            # Crea utente
            timestamp = int(time.time() % 10000)
            user_response = requests.post(
                f"{MENU_SERVICE_URL}/users/register",
                json={
                    "email": f"test_transitions_{timestamp}@test.com",
                    "password": "test123"
                },
                params={"region": "Centro"}
            )
            user_id = user_response.json()['user_id']
            
            # Crea ordine
            response = requests.post(
                f"{MENU_SERVICE_URL}/orders/new_order",
                params={"dish_id": dish_id, "user_id": user_id}
            )
            order = response.json()
            order_id = order['id']
            
            time.sleep(18)  # Attendi assegnazione (routing service usa finestra di 15 secondi)
            
            # Test transizioni
            transitions = [
                ("received", "Received"),
                ("preparing", "Preparing"),
                ("ready_for_pickup", "Ready for Pickup"),
                ("completed", "Completed")
            ]
            
            for status_value, status_name in transitions:
                response = requests.patch(
                    f"{KITCHEN_SERVICE_1_URL}/orders/{order_id}/status",
                    json={"status": status_value},
                    headers=HEADERS
                )
                
                if response.status_code == 200:
                    self.add_result(f"Transition → {status_name}", True)
                else:
                    self.add_result(f"Transition → {status_name}", False, f"Status {response.status_code}")
                    test_passed = False
                
                time.sleep(1)
            
            # Cleanup
            requests.delete(f"{KITCHEN_SERVICE_1_URL}/menu/dishes/{dish_id}", headers=HEADERS)
            
        except Exception as e:
            self.add_result("Status Transitions", False, str(e))
            test_passed = False
        
        return test_passed
    
    # ==================== TEST 6: Direct Completion ====================
    
    def test_direct_completion(self) -> bool:
        """Test passaggio diretto a COMPLETED"""
        print_test("Direct Completion (PREPARING → COMPLETED)")
        
        test_passed = True
        
        try:
            # Setup
            dish_id = str(uuid.uuid4())
            requests.post(
                f"{KITCHEN_SERVICE_1_URL}/menu/dishes",
                json={
                    "dish_id": dish_id,
                    "name": "Test Direct Completion",
                    "price": 9.00,
                    "available_quantity": 2
                },
                headers=HEADERS
            )
            
            # Crea utente
            timestamp = int(time.time() % 10000)
            user_response = requests.post(
                f"{MENU_SERVICE_URL}/users/register",
                json={
                    "email": f"test_direct_{timestamp}@test.com",
                    "password": "test123"
                },
                params={"region": "Centro"}
            )
            user_id = user_response.json()['user_id']
            
            # Carico iniziale
            kitchen_status = requests.get(f"{KITCHEN_SERVICE_1_URL}/kitchen").json()
            initial_load = kitchen_status['current_load']
            
            # Crea ordine
            response = requests.post(
                f"{MENU_SERVICE_URL}/orders/new_order",
                params={"dish_id": dish_id, "user_id": user_id}
            )
            order = response.json()
            order_id = order['id']
            
            time.sleep(18)  # Attendi assegnazione (routing service usa finestra di 15 secondi)
            
            # Carico dopo assegnazione
            kitchen_status = requests.get(f"{KITCHEN_SERVICE_1_URL}/kitchen").json()
            load_after_assignment = kitchen_status['current_load']
            
            # Passa direttamente a COMPLETED (senza stati intermedi)
            print_info("Passaggio diretto a COMPLETED...")
            response = requests.patch(
                f"{KITCHEN_SERVICE_1_URL}/orders/{order_id}/status",
                json={"status": "completed"},
                headers=HEADERS
            )
            
            if response.status_code == 200:
                self.add_result("Direct Completion API", True)
            else:
                self.add_result("Direct Completion API", False)
                test_passed = False
            
            time.sleep(2)
            
            # Verifica carico decrementato
            kitchen_status = requests.get(f"{KITCHEN_SERVICE_1_URL}/kitchen").json()
            final_load = kitchen_status['current_load']
            
            print_info(f"Carico: {initial_load} → {load_after_assignment} → {final_load}")
            
            if final_load <= initial_load:
                self.add_result("Load Decremented", True, f"Carico tornato a {final_load}")
            else:
                self.add_result("Load Decremented", False, f"Carico non decrementato")
                test_passed = False
            
            # Cleanup
            requests.delete(f"{KITCHEN_SERVICE_1_URL}/menu/dishes/{dish_id}", headers=HEADERS)
            
        except Exception as e:
            self.add_result("Direct Completion", False, str(e))
            test_passed = False
        
        return test_passed
    
    # ==================== RUN ALL ====================
    
    def run_all_tests(self):
        """Esegue tutti i test"""
        print(f"\n{BLUE}{'='*80}{NC}")
        print(f"{BLUE}🧪 TEST DI INTEGRAZIONE AVANZATI{NC}")
        print(f"{BLUE}{'='*80}{NC}\n")
        
        # Esegui tutti i test
        self.test_menu_crud()
        self.test_kitchen_isolation()
        self.test_order_lifecycle()
        self.test_direct_completion()
        self.test_multiple_orders()
        
        # Riepilogo
        print(f"\n{BLUE}{'='*80}{NC}")
        print(f"{BLUE}📊 RIEPILOGO COMPLETO{NC}")
        print(f"{BLUE}{'='*80}{NC}\n")
        
        passed = sum(1 for r in self.results if r['passed'])
        failed = sum(1 for r in self.results if not r['passed'])
        total = len(self.results)
        
        print(f"   Totale test: {total}")
        print(f"   {GREEN}Passati: {passed}{NC}")
        print(f"   {RED}Falliti: {failed}{NC}")
        print(f"   Success rate: {(passed/total*100):.1f}%\n")
        
        # Dettaglio fallimenti
        if failed > 0:
            print(f"{RED}Test falliti:{NC}")
            for r in self.results:
                if not r['passed']:
                    print(f"  ❌ {r['test']}: {r['message']}")
        
        if failed == 0:
            print(f"\n{GREEN}{'='*80}{NC}")
            print(f"{GREEN}🎉 TUTTI I {total} TEST PASSATI!{NC}")
            print(f"{GREEN}{'='*80}{NC}\n")
            return True
        else:
            print(f"\n{RED}{'='*80}{NC}")
            print(f"{RED}⚠️  {failed} TEST FALLITI SU {total}{NC}")
            print(f"{RED}{'='*80}{NC}\n")
            return False


if __name__ == "__main__":
    tests = AdvancedIntegrationTests()
    success = tests.run_all_tests()
    sys.exit(0 if success else 1)

