# cartella: repository/menu_repository.py

import redis
from redis.cluster import RedisCluster, ClusterNode
from typing import Optional, List
from uuid import UUID
from model.menu import MenuItem 

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

INCREMENT_QUANTITY_SCRIPT = """
local dish_json = redis.call('HGET', KEYS[1], ARGV[1])
if not dish_json then return -1 end
local quantity_str = string.match(dish_json, '"available_quantity":%s*(%d+)')
if not quantity_str then return -2 end
local quantity = tonumber(quantity_str)
local amount = tonumber(ARGV[2])
local new_quantity = quantity + amount
local new_dish_json = string.gsub(dish_json, '"available_quantity":%s*'..quantity_str, '"available_quantity":'..tostring(new_quantity))
redis.call('HSET', KEYS[1], ARGV[1], new_dish_json)
return new_quantity
"""


class MenuRepository:
    def __init__(self, redis_cluster_nodes: List[ClusterNode]):
        try:
            self.redis = RedisCluster(startup_nodes=redis_cluster_nodes, decode_responses=True, host_port_remap=True)
            self.redis.ping()
            print("✅ REPOSITORY: Connesso a Redis Cluster.")
        except redis.exceptions.RedisClusterException as e:
            print(f"🔥 ERRORE CRITICO: Impossibile connettersi a Redis Cluster. Dettagli: {e}")
            raise
            
        # Registra gli script Lua
        self.decrement_script = self.redis.register_script(DECREMENT_QUANTITY_SCRIPT)
        self.increment_script = self.redis.register_script(INCREMENT_QUANTITY_SCRIPT)

    def _menu_key(self) -> str:
        """Restituisce la chiave Redis fissa per tutti i piatti."""
        return "menu_global"

    # --- Metodi Redis ---

    def create_menu_item(self, menu_item: MenuItem) -> None:
        """Crea o aggiorna un piatto usando HSET."""
        key = self._menu_key()
        self.redis.hset(key, str(menu_item.dish_id), menu_item.json())

    def get_menu_item(self, dish_id: UUID) -> Optional[MenuItem]:
        """Recupera un piatto specifico usando HGET."""
        key = self._menu_key()
        item_json = self.redis.hget(key, str(dish_id))
        if not item_json:
            return None
        return MenuItem.parse_raw(item_json)

    def get_all_menu_items(self) -> List[MenuItem]:
        """Recupera tutti i piatti del menu usando HGETALL."""
        key = self._menu_key()
        all_items = self.redis.hgetall(key)
        menu_items = []
        for dish_id, item_json in all_items.items():
            try:
                menu_items.append(MenuItem.parse_raw(item_json))
            except Exception as e:
                print(f"⚠️ Errore parsing piatto {dish_id}: {e}")
                continue
        return menu_items

    def delete_menu_item(self, dish_id: UUID) -> bool:
        """Elimina un piatto usando HDEL."""
        key = self._menu_key()
        result = self.redis.hdel(key, str(dish_id))
        return result == 1

    # --- Metodi atomici per quantità ---

    def atomic_decrement_quantity(self, dish_id: UUID) -> int:
        """Decrementa la quantità di un piatto in modo atomico."""
        key = self._menu_key()
        result = self.decrement_script(keys=[key], args=[str(dish_id)])
        return int(result)
    
    def atomic_increment_quantity(self, dish_id: UUID, amount: int = 1) -> int:
        """Incrementa la quantità di un piatto in modo atomico."""
        key = self._menu_key()
        result = self.increment_script(keys=[key], args=[str(dish_id), str(amount)])
        return int(result)
