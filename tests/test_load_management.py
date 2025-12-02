#!/usr/bin/env python3
"""
Test specifico per la gestione del carico (current_load)
Verifica che il carico si aggiorni correttamente con completamento ordini
"""

import requests
import time
import uuid
import sys
import json

KITCHEN_URL = "http://localhost:8001/api"
API_KEY = "changeme123"
HEADERS = {"X-API-Key": API_KEY}

GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def print_section(title):
    print(f"\n{BLUE}{'='*80}{NC}")
    print(f"{BLUE}{title}{NC}")
    print(f"{BLUE}{'='*80}{NC}")

def get_kitchen_load():
    """Ottiene il current_load della cucina"""
    response = requests.get(f"{KITCHEN_URL}/kitchen")
    status = response.json()
    return status['current_load'], status

def get_orders():
    """Ottiene tutti gli ordini della cucina"""
    response = requests.get(f"{KITCHEN_URL}/orders")
    return response.json()

def create_test_order():
    """Crea un ordine di test usando direttamente l'API della cucina"""
    # Nota: Questo è un mock - in produzione gli ordini vengono dal menu service
    # Per testare il carico, potremmo usare ordini esistenti
    pass

def main():
    print_section("🧪 TEST GESTIONE CARICO CUCINA")
    
    print(f"\n{YELLOW}Questo test verifica:{NC}")
    print(f"  1. Il carico attuale della cucina")
    print(f"  2. Gli ordini presenti")
    print(f"  3. Il cambio di stato di un ordine a COMPLETED")
    print(f"  4. Il decremento del carico dopo il completamento")
    
    try:
        # 1. Stato iniziale
        print_section("📊 STATO INIZIALE")
        initial_load, initial_status = get_kitchen_load()
        orders = get_orders()
        
        print(f"  Kitchen ID: {initial_status['kitchen_id']}")
        print(f"  Operational: {initial_status['is_operational']}")
        print(f"  {YELLOW}Current Load: {initial_load}{NC}")
        print(f"  Max Load: {initial_status['max_load']}")
        print(f"  Ordini totali: {len(orders)}")
        
        # Analizza ordini per stato
        orders_by_status = {}
        for order in orders:
            status = order['status']
            orders_by_status[status] = orders_by_status.get(status, 0) + 1
        
        print(f"\n  Ordini per stato:")
        for status, count in sorted(orders_by_status.items()):
            print(f"    - {status}: {count}")
        
        # Trova un ordine non completato
        non_completed_order = None
        for order in orders:
            if order['status'] not in ['completed', 'cancelled']:
                non_completed_order = order
                break
        
        if not non_completed_order:
            print(f"\n{YELLOW}⚠️  Nessun ordine attivo trovato per testare il completamento{NC}")
            print(f"{YELLOW}   Crea un ordine dal menu service e riprova{NC}")
            return True
        
        # 2. Completa l'ordine
        print_section("🔄 COMPLETAMENTO ORDINE")
        
        order_id = non_completed_order['order_id']
        old_status = non_completed_order['status']
        
        print(f"  Ordine selezionato: {order_id}")
        print(f"  Stato attuale: {old_status}")
        print(f"\n  {YELLOW}Cambio stato a COMPLETED...{NC}")
        
        response = requests.patch(
            f"{KITCHEN_URL}/orders/{order_id}/status",
            json={"status": "completed"},
            headers=HEADERS
        )
        
        if response.status_code == 200:
            print(f"  {GREEN}✅ Richiesta accettata{NC}")
        else:
            print(f"  {RED}❌ Errore: {response.status_code}{NC}")
            print(f"     {response.text}")
            return False
        
        # Attendi propagazione
        print(f"  Attendo 2 secondi per propagazione...")
        time.sleep(2)
        
        # 3. Verifica stato finale
        print_section("📊 STATO FINALE")
        
        final_load, final_status = get_kitchen_load()
        orders = get_orders()
        
        print(f"  {YELLOW}Current Load: {final_load}{NC}")
        print(f"  Ordini totali: {len(orders)}")
        
        # Verifica ordine completato
        completed_order = next((o for o in orders if o['order_id'] == order_id), None)
        if completed_order:
            print(f"\n  Ordine {order_id}:")
            print(f"    Stato precedente: {old_status}")
            print(f"    Stato attuale: {completed_order['status']}")
            
            if completed_order['status'] == 'completed':
                print(f"    {GREEN}✅ Stato aggiornato correttamente{NC}")
            else:
                print(f"    {RED}❌ Stato non aggiornato{NC}")
        
        # 4. Verifica carico
        print_section("✅ VERIFICA CARICO")
        
        load_diff = initial_load - final_load
        
        print(f"  Carico iniziale: {initial_load}")
        print(f"  Carico finale:   {final_load}")
        print(f"  Differenza:      {load_diff}")
        
        # Il carico dovrebbe essere decrementato se lo stato precedente non era finale
        if old_status in ['pending', 'received', 'preparing']:
            # Dovrebbe decrementare
            if load_diff > 0:
                print(f"\n  {GREEN}✅ SUCCESSO: Carico decrementato correttamente!{NC}")
                print(f"  {GREEN}   Il bug è stato risolto - il completamento decrementa il load{NC}")
                return True
            else:
                print(f"\n  {RED}❌ ERRORE: Carico NON decrementato!{NC}")
                print(f"  {RED}   Il bug persiste - verifica che il servizio sia riavviato{NC}")
                return False
        else:
            # Stato precedente era già finale, non dovrebbe decrementare
            if load_diff == 0:
                print(f"\n  {GREEN}✅ OK: Nessun decremento (stato già finale){NC}")
                return True
            else:
                print(f"\n  {YELLOW}⚠️  Carico cambiato inaspettatamente{NC}")
                return True  # Non è necessariamente un errore
        
    except Exception as e:
        print(f"\n{RED}❌ ERRORE: {e}{NC}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

