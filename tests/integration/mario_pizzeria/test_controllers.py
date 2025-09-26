"""
Integration tests for Mario's Pizzeria API controllers
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Get absolute paths
current_dir = Path(__file__).parent
root_dir = current_dir.parent.parent.parent
src_dir = root_dir / "src"
samples_dir = root_dir / "samples" / "mario-pizzeria"

# Add to Python path
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(samples_dir))

# Change to samples directory for import
original_cwd = os.getcwd()
os.chdir(str(samples_dir))

try:
    from main import create_pizzeria_app
finally:
    os.chdir(original_cwd)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_app(temp_data_dir):
    """Create test application with temporary data directory"""
    app = create_pizzeria_app(data_dir=temp_data_dir)
    return app


@pytest.fixture
def test_client(test_app):
    """Create test client for the application"""
    return TestClient(test_app)


@pytest.fixture
def sample_menu_data(temp_data_dir):
    """Create sample menu data for testing"""
    menu_dir = Path(temp_data_dir) / "menu"
    menu_dir.mkdir(exist_ok=True)

    menu_data = [
        {
            "name": "Margherita",
            "base_price": 12.99,
            "available_sizes": {"small": 0.8, "medium": 1.0, "large": 1.3},
            "available_toppings": {"extra cheese": 1.50, "mushrooms": 1.00, "olives": 1.00},
        },
        {
            "name": "Pepperoni",
            "base_price": 14.99,
            "available_sizes": {"small": 0.8, "medium": 1.0, "large": 1.3},
            "available_toppings": {"extra cheese": 1.50, "mushrooms": 1.00, "peppers": 1.00},
        },
    ]

    with open(menu_dir / "menu.json", "w") as f:
        json.dump(menu_data, f)

    return menu_data


@pytest.mark.integration
class TestOrdersController:
    """Integration tests for OrdersController"""

    def test_place_order_success(self, test_client, sample_menu_data):
        """Test successful order placement"""
        # Arrange
        order_data = {
            "customer_name": "Mario Rossi",
            "customer_phone": "+1-555-0123",
            "customer_address": "123 Pizza Street, Little Italy",
            "pizzas": [{"name": "Margherita", "size": "large", "toppings": ["extra cheese"]}],
            "payment_method": "credit_card",
        }

        # Act
        response = test_client.post("/api/orders/", json=order_data)

        # Assert
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["customer_name"] == "Mario Rossi"
        assert data["status"] == "placed"
        assert len(data["pizzas"]) == 1
        assert data["pizzas"][0]["name"] == "Margherita"
        assert data["pizzas"][0]["size"] == "large"
        assert data["total"] > 0

    def test_place_order_invalid_pizza(self, test_client, sample_menu_data):
        """Test order placement with invalid pizza"""
        # Arrange
        order_data = {
            "customer_name": "Test Customer",
            "customer_phone": "+1-555-0123",
            "customer_address": "Test Address",
            "pizzas": [{"name": "NonexistentPizza", "size": "large", "toppings": []}],
            "payment_method": "credit_card",
        }

        # Act
        response = test_client.post("/orders", json=order_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not found in menu" in data["detail"]

    def test_place_order_invalid_size(self, test_client, sample_menu_data):
        """Test order placement with invalid pizza size"""
        # Arrange
        order_data = {
            "customer_name": "Test Customer",
            "customer_phone": "+1-555-0123",
            "customer_address": "Test Address",
            "pizzas": [{"name": "Margherita", "size": "extra_large", "toppings": []}],
            "payment_method": "credit_card",
        }

        # Act
        response = test_client.post("/orders", json=order_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not available in size" in data["detail"]

    def test_place_order_missing_fields(self, test_client):
        """Test order placement with missing required fields"""
        # Arrange
        order_data = {
            "customer_name": "Test Customer",
            # Missing required fields
        }

        # Act
        response = test_client.post("/orders", json=order_data)

        # Assert
        assert response.status_code == 422

    def test_get_order_success(self, test_client, sample_menu_data):
        """Test successful order retrieval"""
        # Arrange - First place an order
        order_data = {
            "customer_name": "Test Customer",
            "customer_phone": "+1-555-0123",
            "customer_address": "Test Address",
            "pizzas": [{"name": "Margherita", "size": "medium", "toppings": []}],
            "payment_method": "cash",
        }

        create_response = test_client.post("/orders", json=order_data)
        assert create_response.status_code == 201
        order_id = create_response.json()["id"]

        # Act
        response = test_client.get(f"/orders/{order_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
        assert data["customer_name"] == "Test Customer"
        assert data["status"] == "placed"

    def test_get_order_not_found(self, test_client):
        """Test order retrieval with nonexistent ID"""
        # Act
        response = test_client.get("/orders/nonexistent_id")

        # Assert
        assert response.status_code == 404

    def test_update_order_status_success(self, test_client, sample_menu_data):
        """Test successful order status update"""
        # Arrange - First place an order
        order_data = {
            "customer_name": "Test Customer",
            "customer_phone": "+1-555-0123",
            "customer_address": "Test Address",
            "pizzas": [{"name": "Pepperoni", "size": "small", "toppings": []}],
            "payment_method": "credit_card",
        }

        create_response = test_client.post("/orders", json=order_data)
        order_id = create_response.json()["id"]

        # Act - Start cooking
        status_data = {"status": "cooking"}
        response = test_client.put(f"/orders/{order_id}/status", json=status_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cooking"
        assert data["cooking_started_at"] is not None

    def test_get_orders_by_status(self, test_client, sample_menu_data):
        """Test retrieving orders by status"""
        # Arrange - Place multiple orders
        order_data_1 = {
            "customer_name": "Customer 1",
            "customer_phone": "+1-555-0001",
            "customer_address": "Address 1",
            "pizzas": [{"name": "Margherita", "size": "medium", "toppings": []}],
            "payment_method": "cash",
        }

        order_data_2 = {
            "customer_name": "Customer 2",
            "customer_phone": "+1-555-0002",
            "customer_address": "Address 2",
            "pizzas": [{"name": "Pepperoni", "size": "large", "toppings": []}],
            "payment_method": "credit_card",
        }

        test_client.post("/orders", json=order_data_1)
        test_client.post("/orders", json=order_data_2)

        # Act
        response = test_client.get("/orders/status/placed")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        for order in data:
            assert order["status"] == "placed"


@pytest.mark.integration
class TestMenuController:
    """Integration tests for MenuController"""

    def test_get_menu_success(self, test_client, sample_menu_data):
        """Test successful menu retrieval"""
        # Act
        response = test_client.get("/menu")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Check menu structure
        margherita = next((item for item in data if item["name"] == "Margherita"), None)
        assert margherita is not None
        assert "base_price" in margherita
        assert "available_sizes" in margherita
        assert "available_toppings" in margherita

    def test_get_menu_empty(self, test_client):
        """Test menu retrieval when no menu exists"""
        # Act
        response = test_client.get("/menu")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_pizza_by_name_success(self, test_client, sample_menu_data):
        """Test successful pizza retrieval by name"""
        # Act
        response = test_client.get("/menu/Margherita")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Margherita"
        assert data["base_price"] == 12.99

    def test_get_pizza_by_name_not_found(self, test_client, sample_menu_data):
        """Test pizza retrieval with nonexistent name"""
        # Act
        response = test_client.get("/menu/NonexistentPizza")

        # Assert
        assert response.status_code == 404


@pytest.mark.integration
class TestKitchenController:
    """Integration tests for KitchenController"""

    def test_get_kitchen_status_success(self, test_client):
        """Test successful kitchen status retrieval"""
        # Act
        response = test_client.get("/kitchen/status")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "capacity" in data
        assert "current_load" in data
        assert "available" in data
        assert "current_orders" in data

    def test_start_cooking_success(self, test_client, sample_menu_data):
        """Test successful cooking start"""
        # Arrange - First place an order
        order_data = {
            "customer_name": "Test Customer",
            "customer_phone": "+1-555-0123",
            "customer_address": "Test Address",
            "pizzas": [{"name": "Margherita", "size": "medium", "toppings": []}],
            "payment_method": "cash",
        }

        create_response = test_client.post("/orders", json=order_data)
        order_id = create_response.json()["id"]

        # Act
        response = test_client.post(f"/kitchen/start-cooking/{order_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cooking"
        assert data["cooking_started_at"] is not None

    def test_start_cooking_nonexistent_order(self, test_client):
        """Test cooking start with nonexistent order"""
        # Act
        response = test_client.post("/kitchen/start-cooking/nonexistent_id")

        # Assert
        assert response.status_code == 404

    def test_complete_order_success(self, test_client, sample_menu_data):
        """Test successful order completion"""
        # Arrange - Place order and start cooking
        order_data = {
            "customer_name": "Test Customer",
            "customer_phone": "+1-555-0123",
            "customer_address": "Test Address",
            "pizzas": [{"name": "Pepperoni", "size": "large", "toppings": ["mushrooms"]}],
            "payment_method": "credit_card",
        }

        create_response = test_client.post("/orders", json=order_data)
        order_id = create_response.json()["id"]

        # Start cooking first
        test_client.post(f"/kitchen/start-cooking/{order_id}")

        # Act
        response = test_client.post(f"/kitchen/complete/{order_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["ready_at"] is not None

    def test_complete_order_wrong_status(self, test_client, sample_menu_data):
        """Test order completion with wrong status"""
        # Arrange - Place order but don't start cooking
        order_data = {
            "customer_name": "Test Customer",
            "customer_phone": "+1-555-0123",
            "customer_address": "Test Address",
            "pizzas": [{"name": "Margherita", "size": "small", "toppings": []}],
            "payment_method": "cash",
        }

        create_response = test_client.post("/orders", json=order_data)
        order_id = create_response.json()["id"]

        # Act - Try to complete without starting cooking
        response = test_client.post(f"/kitchen/complete/{order_id}")

        # Assert
        assert response.status_code == 400


@pytest.mark.integration
class TestApplicationWorkflow:
    """Integration tests for complete application workflow"""

    def test_complete_order_lifecycle(self, test_client, sample_menu_data):
        """Test complete order lifecycle from placement to completion"""
        # Step 1: Place order
        order_data = {
            "customer_name": "Mario Rossi",
            "customer_phone": "+1-555-0123",
            "customer_address": "123 Pizza Street",
            "pizzas": [
                {"name": "Margherita", "size": "large", "toppings": ["extra cheese", "mushrooms"]},
                {"name": "Pepperoni", "size": "medium", "toppings": []},
            ],
            "payment_method": "credit_card",
        }

        create_response = test_client.post("/orders", json=order_data)
        assert create_response.status_code == 201
        order_id = create_response.json()["id"]

        # Step 2: Check order status
        get_response = test_client.get(f"/orders/{order_id}")
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "placed"

        # Step 3: Check kitchen status before cooking
        kitchen_response = test_client.get("/kitchen/status")
        assert kitchen_response.status_code == 200
        initial_load = kitchen_response.json()["current_load"]

        # Step 4: Start cooking
        start_response = test_client.post(f"/kitchen/start-cooking/{order_id}")
        assert start_response.status_code == 200
        assert start_response.json()["status"] == "cooking"

        # Step 5: Verify kitchen load increased
        kitchen_response = test_client.get("/kitchen/status")
        assert kitchen_response.json()["current_load"] == initial_load + 1

        # Step 6: Complete cooking
        complete_response = test_client.post(f"/kitchen/complete/{order_id}")
        assert complete_response.status_code == 200
        assert complete_response.json()["status"] == "ready"

        # Step 7: Verify kitchen load decreased
        kitchen_response = test_client.get("/kitchen/status")
        assert kitchen_response.json()["current_load"] == initial_load

        # Step 8: Check final order status
        final_response = test_client.get(f"/orders/{order_id}")
        assert final_response.status_code == 200
        order_data = final_response.json()
        assert order_data["status"] == "ready"
        assert order_data["total"] > 0
        assert order_data["placed_at"] is not None
        assert order_data["cooking_started_at"] is not None
        assert order_data["ready_at"] is not None

    def test_multiple_orders_kitchen_management(self, test_client, sample_menu_data):
        """Test kitchen capacity management with multiple orders"""
        placed_orders = []

        # Place multiple orders
        for i in range(3):
            order_data = {
                "customer_name": f"Customer {i+1}",
                "customer_phone": f"+1-555-000{i+1}",
                "customer_address": f"Address {i+1}",
                "pizzas": [{"name": "Margherita", "size": "medium", "toppings": []}],
                "payment_method": "credit_card",
            }

            response = test_client.post("/orders", json=order_data)
            assert response.status_code == 201
            placed_orders.append(response.json()["id"])

        # Start cooking all orders
        for order_id in placed_orders:
            response = test_client.post(f"/kitchen/start-cooking/{order_id}")
            assert response.status_code == 200

        # Check kitchen status
        kitchen_response = test_client.get("/kitchen/status")
        kitchen_data = kitchen_response.json()
        assert kitchen_data["current_load"] == 3
        assert len(kitchen_data["current_orders"]) == 3

        # Complete one order
        response = test_client.post(f"/kitchen/complete/{placed_orders[0]}")
        assert response.status_code == 200

        # Check kitchen load decreased
        kitchen_response = test_client.get("/kitchen/status")
        assert kitchen_response.json()["current_load"] == 2

        # Check orders by status
        placed_response = test_client.get("/orders/status/cooking")
        cooking_orders = placed_response.json()
        assert len(cooking_orders) == 2

        ready_response = test_client.get("/orders/status/ready")
        ready_orders = ready_response.json()
        assert len(ready_orders) == 1
