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
    repo.kitchen_id = uuid.uuid4()  # Simula il kitchen_id del repository
    repo.get_by_id = mock.MagicMock()
    repo.update_fields = mock.MagicMock()
    return repo

@pytest.fixture
def mock_menu_service():
    """Mock per MenuService."""
    return mock.MagicMock()

@pytest.fixture
def mock_producer():
    """Mock per EventProducer."""
    return mock.MagicMock()

@pytest.fixture
def mock_status_service():
    """Mock per OrderStatusService."""
    return mock.MagicMock()

@pytest.fixture
def kitchen_service(mock_kitchen_repo, mock_menu_service, mock_producer, mock_status_service):
    """Crea un'istanza di KitchenService con tutti i mock necessari."""
    return KitchenService(
        kitchen_repo=mock_kitchen_repo,
        menu_service=mock_menu_service,
        producer=mock_producer,
        status_service=mock_status_service
    )

# --- Test per increment_load (ora funzioneranno) ---

@pytest.mark.asyncio
async def test_increment_load_success(kitchen_service, mock_kitchen_repo):
    """
    Verifica che il carico venga incrementato correttamente quando la cucina è operativa
    e non al massimo della capacità.
    """
    initial_kitchen = KitchenAvailability(
        kitchen_id=mock_kitchen_repo.kitchen_id, max_load=10, current_load=5, is_operational=True
    )
    mock_kitchen_repo.get_by_id.return_value = initial_kitchen
    mock_kitchen_repo.update_fields.return_value = True

    result = await kitchen_service.increment_load()

    assert result is True
    mock_kitchen_repo.get_by_id.assert_called_once()
    mock_kitchen_repo.update_fields.assert_called_once_with(
        current_load=6, is_operational=True
    )

@pytest.mark.asyncio
async def test_increment_load_reaches_max_load(kitchen_service, mock_kitchen_repo):
    """
    Verifica che is_operational diventi False quando il carico raggiunge il massimo.
    """
    initial_kitchen = KitchenAvailability(
        kitchen_id=mock_kitchen_repo.kitchen_id, max_load=10, current_load=9, is_operational=True
    )
    mock_kitchen_repo.get_by_id.return_value = initial_kitchen
    mock_kitchen_repo.update_fields.return_value = True

    result = await kitchen_service.increment_load()

    assert result is True
    mock_kitchen_repo.get_by_id.assert_called_once()
    mock_kitchen_repo.update_fields.assert_called_once_with(
        current_load=10, is_operational=False
    )

@pytest.mark.asyncio
async def test_increment_load_exceeds_max_load(kitchen_service, mock_kitchen_repo):
    """
    Verifica che is_operational diventi False quando il carico supera il massimo.
    """
    initial_kitchen = KitchenAvailability(
        kitchen_id=mock_kitchen_repo.kitchen_id, max_load=10, current_load=10, is_operational=True
    )
    mock_kitchen_repo.get_by_id.return_value = initial_kitchen
    mock_kitchen_repo.update_fields.return_value = True

    result = await kitchen_service.increment_load()

    assert result is True
    mock_kitchen_repo.get_by_id.assert_called_once()
    mock_kitchen_repo.update_fields.assert_called_once_with(
        current_load=11, is_operational=False
    )

@pytest.mark.asyncio
async def test_increment_load_kitchen_not_found(kitchen_service, mock_kitchen_repo):
    """
    Verifica che la funzione ritorni False se la cucina non esiste.
    """
    mock_kitchen_repo.get_by_id.return_value = None

    result = await kitchen_service.increment_load()

    assert result is False
    mock_kitchen_repo.get_by_id.assert_called_once()
    mock_kitchen_repo.update_fields.assert_not_called()

@pytest.mark.asyncio
async def test_increment_load_kitchen_not_operational(kitchen_service, mock_kitchen_repo):
    """
    Verifica che la funzione ritorni False se la cucina non è già operativa.
    """
    initial_kitchen = KitchenAvailability(
        kitchen_id=mock_kitchen_repo.kitchen_id, max_load=10, current_load=5, is_operational=False
    )
    mock_kitchen_repo.get_by_id.return_value = initial_kitchen

    result = await kitchen_service.increment_load()

    assert result is False
    mock_kitchen_repo.get_by_id.assert_called_once()
    mock_kitchen_repo.update_fields.assert_not_called()

# --- Test per decrement_load ---

@pytest.mark.asyncio
async def test_decrement_load_success(kitchen_service, mock_kitchen_repo):
    """
    Verifica che il carico venga decrementato correttamente.
    """
    initial_kitchen = KitchenAvailability(
        kitchen_id=mock_kitchen_repo.kitchen_id, max_load=10, current_load=5, is_operational=True
    )
    mock_kitchen_repo.get_by_id.return_value = initial_kitchen
    mock_kitchen_repo.update_fields.return_value = True

    result = await kitchen_service.decrement_load()

    assert result is True
    mock_kitchen_repo.get_by_id.assert_called_once()
    mock_kitchen_repo.update_fields.assert_called_once_with(
        current_load=4, is_operational=True
    )

@pytest.mark.asyncio
async def test_decrement_load_becomes_operational(kitchen_service, mock_kitchen_repo):
    """
    Verifica che la cucina torni operativa quando il carico scende sotto il massimo.
    """
    initial_kitchen = KitchenAvailability(
        kitchen_id=mock_kitchen_repo.kitchen_id, max_load=10, current_load=10, is_operational=False
    )
    mock_kitchen_repo.get_by_id.return_value = initial_kitchen
    mock_kitchen_repo.update_fields.return_value = True

    result = await kitchen_service.decrement_load()

    assert result is True
    mock_kitchen_repo.get_by_id.assert_called_once()
    mock_kitchen_repo.update_fields.assert_called_once_with(
        current_load=9, is_operational=True
    )

@pytest.mark.asyncio
async def test_decrement_load_at_zero(kitchen_service, mock_kitchen_repo):
    """
    Verifica che il decremento fallisca se il carico è già a zero.
    """
    initial_kitchen = KitchenAvailability(
        kitchen_id=mock_kitchen_repo.kitchen_id, max_load=10, current_load=0, is_operational=True
    )
    mock_kitchen_repo.get_by_id.return_value = initial_kitchen

    result = await kitchen_service.decrement_load()

    assert result is False
    mock_kitchen_repo.get_by_id.assert_called_once()
    mock_kitchen_repo.update_fields.assert_not_called()

@pytest.mark.asyncio
async def test_decrement_load_kitchen_not_found(kitchen_service, mock_kitchen_repo):
    """
    Verifica che il decremento fallisca se la cucina non viene trovata.
    """
    mock_kitchen_repo.get_by_id.return_value = None

    result = await kitchen_service.decrement_load()

    assert result is False
    mock_kitchen_repo.get_by_id.assert_called_once()
    mock_kitchen_repo.update_fields.assert_not_called()

# --- Test per set_operational_status ---

@pytest.mark.asyncio
async def test_set_operational_status_to_true(kitchen_service, mock_kitchen_repo):
    """
    Verifica che lo stato operativo venga impostato correttamente a True.
    """
    mock_kitchen_repo.update_fields.return_value = True

    result = await kitchen_service.set_operational_status(True)

    assert result is True
    mock_kitchen_repo.update_fields.assert_called_once_with(is_operational=True)

@pytest.mark.asyncio
async def test_set_operational_status_to_false(kitchen_service, mock_kitchen_repo):
    """
    Verifica che lo stato operativo venga impostato correttamente a False.
    """
    mock_kitchen_repo.update_fields.return_value = True

    result = await kitchen_service.set_operational_status(False)

    assert result is True
    mock_kitchen_repo.update_fields.assert_called_once_with(is_operational=False)

@pytest.mark.asyncio
async def test_set_operational_status_failure(kitchen_service, mock_kitchen_repo):
    """
    Verifica la gestione del fallimento, ad esempio se l'ID non esiste e il repo ritorna False.
    """
    mock_kitchen_repo.update_fields.return_value = False

    result = await kitchen_service.set_operational_status(True)

    assert result is False
    mock_kitchen_repo.update_fields.assert_called_once_with(is_operational=True)