# cartella: repository/menu_repository.py

import redis
from redis.cluster import RedisCluster, ClusterNode
from typing import Optional, List, Dict
from uuid import UUID
from model.menu import MenuItem, Menu # Assumendo che i tuoi modelli siano in model/menu.py

# ======================================================================
# --- Script Lua per Operazioni Atomiche sulla Quantità ---
# Questi script sono l'aggiunta chiave per garantire aggiornamenti sicuri.
# ======================================================================

DECREMENT_QUANTITY_SCRIPT = """
local dish_json = redis.call('HGET', KEYS[1], ARGV[1])
if not dish_json then return -1 end
local quantity_str = string.match(dish_json, '"available_quantity":%s*(%d+)')
if not quantity_str then return -2 end
local quantity = tonumber(quantity_str)
if quantity <= 0 then return -3 end
local new_quantity = quantity - 1
local new_dish_json = string.gsub(dish_json, '"available_quantity":%s*'..quantity_str, '"available_quantity":'..tostring(new_quantity))
redis.call('HSET', KEYS[1], ARGV[1], new_dish_json)
return new_quantity
"""
# (Puoi aggiungere script simili per INCREMENT e SET)

class MenuRepository:
    def __init__(self, redis_cluster_nodes: List[ClusterNode]):
        """
        MIGLIORAMENTO: Sostituisce il dizionario in-memory con una connessione a Redis Cluster.
        """
        try:
            self.redis = RedisCluster(startup_nodes=redis_cluster_nodes, decode_responses=True)
            self.redis.ping()
            print("✅ REPOSITORY: Connesso a Redis Cluster.")
        except redis.exceptions.RedisClusterException as e:
            print(f"🔥 ERRORE CRITICO: Impossibile connettersi a Redis Cluster. Dettagli: {e}")
            raise
            
        # Registra lo script Lua per renderlo efficiente
        self.decrement_script = self.redis.register_script(DECREMENT_QUANTITY_SCRIPT)

    def _menu_key(self, kitchen_id: UUID) -> str:
        """Helper per generare la chiave Redis per il menu di una cucina."""
        return f"menu:{str(kitchen_id)}"

    # --- Metodi Esistenti, Adattati per Redis ---

    def create_menu_item(self, kitchen_id: UUID, menu_item: MenuItem) -> None:
        """
        MIGLIORAMENTO: Crea o aggiorna un piatto usando HSET in Redis.
        """
        key = self._menu_key(kitchen_id)
        # HSET in Redis aggiunge o aggiorna un campo in un hash. Perfetto per questo caso.
        self.redis.hset(key, str(menu_item.dish_id), menu_item.json())

    def get_menu_item(self, kitchen_id: UUID, dish_id: UUID) -> Optional[MenuItem]:
        """
        MIGLIORAMENTO: Recupera un piatto specifico usando HGET da Redis.
        """
        key = self._menu_key(kitchen_id)
        item_json = self.redis.hget(key, str(dish_id))
        
        if not item_json:
            return None
        return MenuItem.parse_raw(item_json)

    def delete_menu_item(self, kitchen_id: UUID, dish_id: UUID) -> bool:
        """
        MIGLIORAMENTO: Elimina un piatto dal menu usando HDEL di Redis.
        """
        key = self._menu_key(kitchen_id)
        # HDEL restituisce 1 se il campo è stato eliminato, 0 altrimenti.
        result = self.redis.hdel(key, str(dish_id))
        return result == 1

    def get_menu(self, kitchen_id: UUID) -> Optional[Menu]:
        """
        MIGLIORAMENTO: Recupera tutti i piatti di un menu usando HGETALL da Redis.
        """
        key = self._menu_key(kitchen_id)
        all_items_json = self.redis.hgetall(key)
        
        if not all_items_json:
            return None
            
        # Deserializza tutti i JSON dei piatti
        items = [MenuItem.parse_raw(item_json) for item_json in all_items_json.values()]
        
        return Menu(kitchen_id=kitchen_id, items=items)

    # --- NUOVI Metodi Atomici per Aggiornare la Quantità ---

    def atomic_decrement_quantity(self, kitchen_id: UUID, dish_id: UUID) -> int:
        """
        NUOVO: Decrementa la quantità di un piatto in modo sicuro e atomico.
        Restituisce un codice di stato che il Service dovrà interpretare.
        """
        key = self._menu_key(kitchen_id)
        result = self.decrement_script(keys=[key], args=[str(dish_id)])
        return int(result)