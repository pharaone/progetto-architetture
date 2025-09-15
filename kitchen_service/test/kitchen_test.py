import uuid
import pytest
from unittest import mock

# Assicurati che questi import puntino ai tuoi file reali
# Ad esempio: from service.kitchen_service import KitchenService
# from model.kitchen import KitchenAvailability
from service.kitchen_service import KitchenService
from model.kitchen import KitchenAvailability 

# --- Fixture per l'impostazione dei test (CORRETTA) ---

@pytest.fixture
def mock_kitchen_repo():
    """Crea un mock per KitchenAvailabilityRepository."""
    repo = mock.MagicMock()
    # I metodi del repo sono sincroni perché vengono chiamati con asyncio.to_thread.
    # Quindi usiamo MagicMock, non AsyncMock.
    repo.get_by_id = mock.MagicMock()
    repo.update_fields = mock.MagicMock()
    return repo

@pytest.fixture
def kitchen_service(mock_kitchen_repo):
    """Crea un'istanza di KitchenService con il repository mockato."""
    return KitchenService(mock_kitchen_repo)

# --- Test per increment_load (ora funzioneranno) ---

@pytest.mark.asyncio
async def test_increment_load_success(kitchen_service, mock_kitchen_repo):
    """
    Verifica che il carico venga incrementato correttamente quando la cucina è operativa
    e non al massimo della capacità.
    """
    kitchen_id = uuid.uuid4()
    initial_kitchen = KitchenAvailability(
        id=kitchen_id, max_load=10, current_load=5, is_operational=True
    )
    mock_kitchen_repo.get_by_id.return_value = initial_kitchen
    mock_kitchen_repo.update_fields.return_value = True

    result = await kitchen_service.increment_load(kitchen_id)

    assert result is True
    mock_kitchen_repo.get_by_id.assert_called_once_with(kitchen_id)
    mock_kitchen_repo.update_fields.assert_called_once_with(
        kitchen_id=kitchen_id, current_load=6, is_operational=True
    )

@pytest.mark.asyncio
async def test_increment_load_reaches_max_load(kitchen_service, mock_kitchen_repo):
    """
    Verifica che is_operational diventi False quando il carico raggiunge il massimo.
    """
    kitchen_id = uuid.uuid4()
    initial_kitchen = KitchenAvailability(
        id=kitchen_id, max_load=10, current_load=9, is_operational=True
    )
    mock_kitchen_repo.get_by_id.return_value = initial_kitchen
    mock_kitchen_repo.update_fields.return_value = True

    result = await kitchen_service.increment_load(kitchen_id)

    assert result is True
    mock_kitchen_repo.get_by_id.assert_called_once_with(kitchen_id)
    mock_kitchen_repo.update_fields.assert_called_once_with(
        kitchen_id=kitchen_id, current_load=10, is_operational=False
    )

@pytest.mark.asyncio
async def test_increment_load_exceeds_max_load(kitchen_service, mock_kitchen_repo):
    """
    Verifica che is_operational diventi False quando il carico supera il massimo.
    """
    kitchen_id = uuid.uuid4()
    initial_kitchen = KitchenAvailability(
        id=kitchen_id, max_load=10, current_load=10, is_operational=True
    )
    mock_kitchen_repo.get_by_id.return_value = initial_kitchen
    mock_kitchen_repo.update_fields.return_value = True

    result = await kitchen_service.increment_load(kitchen_id)

    assert result is True
    mock_kitchen_repo.get_by_id.assert_called_once_with(kitchen_id)
    mock_kitchen_repo.update_fields.assert_called_once_with(
        kitchen_id=kitchen_id, current_load=11, is_operational=False
    )

@pytest.mark.asyncio
async def test_increment_load_kitchen_not_found(kitchen_service, mock_kitchen_repo):
    """
    Verifica che la funzione ritorni False se la cucina non esiste.
    """
    kitchen_id = uuid.uuid4()
    mock_kitchen_repo.get_by_id.return_value = None

    result = await kitchen_service.increment_load(kitchen_id)

    assert result is False
    mock_kitchen_repo.get_by_id.assert_called_once_with(kitchen_id)
    mock_kitchen_repo.update_fields.assert_not_called()

@pytest.mark.asyncio
async def test_increment_load_kitchen_not_operational(kitchen_service, mock_kitchen_repo):
    """
    Verifica che la funzione ritorni False se la cucina non è già operativa.
    """
    kitchen_id = uuid.uuid4()
    initial_kitchen = KitchenAvailability(
        id=kitchen_id, max_load=10, current_load=5, is_operational=False
    )
    mock_kitchen_repo.get_by_id.return_value = initial_kitchen

    result = await kitchen_service.increment_load(kitchen_id)

    assert result is False
    mock_kitchen_repo.get_by_id.assert_called_once_with(kitchen_id)
    mock_kitchen_repo.update_fields.assert_not_called()

# --- Test per decrement_load ---

@pytest.mark.asyncio
async def test_decrement_load_success(kitchen_service, mock_kitchen_repo):
    """
    Verifica che il carico venga decrementato correttamente.
    """
    kitchen_id = uuid.uuid4()
    initial_kitchen = KitchenAvailability(
        id=kitchen_id, max_load=10, current_load=5, is_operational=True
    )
    mock_kitchen_repo.get_by_id.return_value = initial_kitchen
    mock_kitchen_repo.update_fields.return_value = True

    result = await kitchen_service.decrement_load(kitchen_id)

    assert result is True
    mock_kitchen_repo.get_by_id.assert_called_once_with(kitchen_id)
    mock_kitchen_repo.update_fields.assert_called_once_with(
        kitchen_id=kitchen_id, current_load=4, is_operational=True
    )

@pytest.mark.asyncio
async def test_decrement_load_becomes_operational(kitchen_service, mock_kitchen_repo):
    """
    Verifica che la cucina torni operativa quando il carico scende sotto il massimo.
    """
    kitchen_id = uuid.uuid4()
    initial_kitchen = KitchenAvailability(
        id=kitchen_id, max_load=10, current_load=10, is_operational=False
    )
    mock_kitchen_repo.get_by_id.return_value = initial_kitchen
    mock_kitchen_repo.update_fields.return_value = True

    result = await kitchen_service.decrement_load(kitchen_id)

    assert result is True
    mock_kitchen_repo.get_by_id.assert_called_once_with(kitchen_id)
    mock_kitchen_repo.update_fields.assert_called_once_with(
        kitchen_id=kitchen_id, current_load=9, is_operational=True
    )

@pytest.mark.asyncio
async def test_decrement_load_at_zero(kitchen_service, mock_kitchen_repo):
    """
    Verifica che il decremento fallisca se il carico è già a zero.
    """
    kitchen_id = uuid.uuid4()
    initial_kitchen = KitchenAvailability(
        id=kitchen_id, max_load=10, current_load=0, is_operational=True
    )
    mock_kitchen_repo.get_by_id.return_value = initial_kitchen

    result = await kitchen_service.decrement_load(kitchen_id)

    assert result is False
    mock_kitchen_repo.get_by_id.assert_called_once_with(kitchen_id)
    mock_kitchen_repo.update_fields.assert_not_called()

@pytest.mark.asyncio
async def test_decrement_load_kitchen_not_found(kitchen_service, mock_kitchen_repo):
    """
    Verifica che il decremento fallisca se la cucina non viene trovata.
    """
    kitchen_id = uuid.uuid4()
    mock_kitchen_repo.get_by_id.return_value = None

    result = await kitchen_service.decrement_load(kitchen_id)

    assert result is False
    mock_kitchen_repo.get_by_id.assert_called_once_with(kitchen_id)
    mock_kitchen_repo.update_fields.assert_not_called()

# --- Test per set_operational_status ---

@pytest.mark.asyncio
async def test_set_operational_status_to_true(kitchen_service, mock_kitchen_repo):
    """
    Verifica che lo stato operativo venga impostato correttamente a True.
    """
    kitchen_id = uuid.uuid4()
    mock_kitchen_repo.update_fields.return_value = True

    result = await kitchen_service.set_operational_status(kitchen_id, True)

    assert result is True
    mock_kitchen_repo.update_fields.assert_called_once_with(kitchen_id, is_operational=True)

@pytest.mark.asyncio
async def test_set_operational_status_to_false(kitchen_service, mock_kitchen_repo):
    """
    Verifica che lo stato operativo venga impostato correttamente a False.
    """
    kitchen_id = uuid.uuid4()
    mock_kitchen_repo.update_fields.return_value = True

    result = await kitchen_service.set_operational_status(kitchen_id, False)

    assert result is True
    mock_kitchen_repo.update_fields.assert_called_once_with(kitchen_id, is_operational=False)

@pytest.mark.asyncio
async def test_set_operational_status_failure(kitchen_service, mock_kitchen_repo):
    """
    Verifica la gestione del fallimento, ad esempio se l'ID non esiste e il repo ritorna False.
    """
    kitchen_id = uuid.uuid4()
    mock_kitchen_repo.update_fields.return_value = False

    result = await kitchen_service.set_operational_status(kitchen_id, True)

    assert result is False
    mock_kitchen_repo.update_fields.assert_called_once_with(kitchen_id, is_operational=True)