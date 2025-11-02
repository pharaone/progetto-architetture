import uuid
import pytest
from unittest.mock import MagicMock

from service.user_service import UserService
from model.user import User
from repository.user_repository import UserRepository


@pytest.fixture
def mock_user_repo():
    """Mock per UserRepository."""
    repo = MagicMock(spec=UserRepository)
    repo.get_all = MagicMock()
    repo.get_by_id = MagicMock()
    repo.add = MagicMock()
    return repo


@pytest.fixture
def user_service(mock_user_repo):
    """Istanza di UserService con repository mockato."""
    return UserService(mock_user_repo)


# ============================================================
# TEST: new_user
# ============================================================
def test_new_user_success(user_service, mock_user_repo):
    """Test creazione nuovo utente."""
    email = "test@test.com"
    password = "password123"
    region = "Centro"
    
    mock_user_repo.get_all.return_value = []  # Nessun utente esistente
    expected_user = User(email=email, password=user_service.hash_password(password), region=region)
    mock_user_repo.add.return_value = expected_user
    
    result = user_service.new_user(email, password, region)
    
    assert result == expected_user
    mock_user_repo.get_all.assert_called_once()
    mock_user_repo.add.assert_called_once()


def test_new_user_already_exists(user_service, mock_user_repo):
    """Test creazione utente già esistente."""
    email = "test@test.com"
    password = "password123"
    region = "Centro"
    
    existing_user = User(email=email, password="hashed", region=region)
    mock_user_repo.get_all.return_value = [existing_user]
    
    with pytest.raises(ValueError, match="User with this email already exists"):
        user_service.new_user(email, password, region)
    
    mock_user_repo.add.assert_not_called()


# ============================================================
# TEST: get_user (authentication)
# ============================================================
def test_get_user_success(user_service, mock_user_repo):
    """Test autenticazione utente con credenziali corrette."""
    email = "test@test.com"
    password = "password123"
    hashed_pw = user_service.hash_password(password)
    
    user = User(email=email, password=hashed_pw, region="Centro")
    mock_user_repo.get_all.return_value = [user]
    
    result = user_service.get_user(email, password)
    
    assert result == user
    mock_user_repo.get_all.assert_called_once()


def test_get_user_wrong_password(user_service, mock_user_repo):
    """Test autenticazione con password errata."""
    email = "test@test.com"
    
    user = User(email=email, password=user_service.hash_password("correct_password"), region="Centro")
    mock_user_repo.get_all.return_value = [user]
    
    result = user_service.get_user(email, "wrong_password")
    
    assert result is None
    mock_user_repo.get_all.assert_called_once()


def test_get_user_not_found(user_service, mock_user_repo):
    """Test autenticazione utente non esistente."""
    mock_user_repo.get_all.return_value = []
    
    result = user_service.get_user("notfound@test.com", "password")
    
    assert result is None
    mock_user_repo.get_all.assert_called_once()


# ============================================================
# TEST: confirm_user
# ============================================================
def test_confirm_user_success(user_service, mock_user_repo):
    """Test conferma utente con credenziali corrette."""
    email = "test@test.com"
    password = "password123"
    hashed_pw = user_service.hash_password(password)
    
    user = User(email=email, password=hashed_pw, region="Centro")
    mock_user_repo.get_all.return_value = [user]
    
    result = user_service.confirm_user(email, password)
    
    assert result is True
    mock_user_repo.get_all.assert_called_once()


def test_confirm_user_wrong_password(user_service, mock_user_repo):
    """Test conferma con password errata."""
    email = "test@test.com"
    
    user = User(email=email, password=user_service.hash_password("correct"), region="Centro")
    mock_user_repo.get_all.return_value = [user]
    
    result = user_service.confirm_user(email, "wrong_password")
    
    assert result is False
    mock_user_repo.get_all.assert_called_once()


def test_confirm_user_not_found(user_service, mock_user_repo):
    """Test conferma utente non esistente."""
    mock_user_repo.get_all.return_value = []
    
    result = user_service.confirm_user("notfound@test.com", "password")
    
    assert result is False
    mock_user_repo.get_all.assert_called_once()


# ============================================================
# TEST: hash_password
# ============================================================
def test_hash_password(user_service):
    """Test hashing password."""
    password = "test123"
    hashed = user_service.hash_password(password)
    
    # Verifica che sia una stringa hex di 64 caratteri (SHA-256)
    assert isinstance(hashed, str)
    assert len(hashed) == 64
    assert all(c in '0123456789abcdef' for c in hashed)
    
    # Verifica determinismo
    assert hashed == user_service.hash_password(password)

