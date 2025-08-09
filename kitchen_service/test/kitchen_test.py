import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock

# Il percorso di importazione potrebbe variare in base alla struttura del tuo progetto
from model.kitchen import KitchenAvailability
from repository.kitchen_repository import KitchenAvailabilityRepository
from service.kitchen_service import KitchenService

# --- Test per il KitchenService ---

@pytest.mark.asyncio
async def test_increment_load_makes_kitchen_not_operational_at_max_capacity():
    """
    TEST: Verifica che increment_load imposti is_operational a False 
    quando current_load raggiunge max_load.
    """
    # 1. SETUP: Prepariamo il nostro "scenario"
    
    kitchen_id = uuid.uuid4()
    
    # Creiamo un oggetto finto che rappresenta lo stato della cucina PRIMA dell'operazione.
    # Nota: il carico è a un passo dal massimo.
    initial_kitchen_state = KitchenAvailability(
        kitchen_id=kitchen_id,
        current_load=9,  # Un ordine in meno della capacità massima
        max_load=10,
        is_operational=True
    )

    # 2. MOCKING: Creiamo il finto repository (il nostro "assistente")
    
    # Creiamo un mock del repository. MagicMock è molto potente.
    mock_repo = MagicMock(spec=KitchenAvailabilityRepository)
    
    # Diciamo al mock come comportarsi: "Quando qualcuno chiama il tuo metodo
    # 'get_by_id' con questo specifico ID, restituisci l'oggetto 'initial_kitchen_state'".
    # Usiamo AsyncMock perché il metodo del repository è asincrono.
    mock_repo.get_by_id = AsyncMock(return_value=initial_kitchen_state)
    
    # Diciamo anche che il metodo 'save' è asincrono (non ci interessa cosa fa, solo che venga chiamato).
    mock_repo.save = AsyncMock()

    # 3. ESECUZIONE: Avviamo la logica che vogliamo testare
    
    # Creiamo un'istanza del nostro servizio, ma gli passiamo il repository Finto.
    kitchen_service = KitchenService(kitchen_repo=mock_repo)
    
    # Chiamiamo il metodo che vogliamo testare.
    result = await kitchen_service.increment_load(kitchen_id)

    # 4. VERIFICA (ASSERT): Controlliamo che sia successo quello che ci aspettavamo
    
    # Il risultato dell'operazione dovrebbe essere True (successo).
    assert result is True
    
    # Controlliamo che il metodo 'get_by_id' del nostro mock sia stato chiamato una volta.
    mock_repo.get_by_id.assert_called_once_with(kitchen_id)
    
    # Controlliamo che il metodo 'save' sia stato chiamato.
    mock_repo.save.assert_called_once()
    
    # Questa è la verifica più importante della nostra logica di business:
    # L'oggetto che è stato passato al metodo 'save' deve avere:
    # - current_load incrementato a 10
    # - is_operational impostato a False
    saved_kitchen_object = mock_repo.save.call_args[0][0] # Estraiamo l'oggetto passato a save()
    
    assert saved_kitchen_object.current_load == 10
    assert saved_kitchen_object.is_operational is False

