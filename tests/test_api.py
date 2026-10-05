import unittest
import json
from app import create_app
from models import db, User, Product, InventoryTransaction, AIInsight

class TestAPI(unittest.TestCase):
    """Automated test suite for AI-Powered Inventory Monitor endpoints and business rules."""

    @classmethod
    def setUpClass(cls):
        """Initialize test app and in-memory test database."""
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def test_01_health_endpoint(self):
        """Verify GET /api/health reports correct status and service details."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "AI Inventory Monitor")
        self.assertIn("microsoft_foundry_configured", data)

    def test_02_auth_register_and_login(self):
        """Verify user registration and authentication workflows."""
        # Register a unique test user
        user_payload = {
            "username": "tester_qa",
            "email": "tester_qa@example.com",
            "password": "securepassword123",
            "role": "manager"
        }
        res_reg = self.client.post("/api/auth/register", json=user_payload)
        self.assertIn(res_reg.status_code, [201, 409])  # 201 if fresh, 409 if exists

        # Successful login
        login_payload = {
            "username": "tester_qa",
            "password": "securepassword123"
        }
        res_login = self.client.post("/api/auth/login", json=login_payload)
        self.assertEqual(res_login.status_code, 200)
        data = res_login.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["user"]["username"], "tester_qa")

        # Invalid password check
        bad_login = {
            "username": "tester_qa",
            "password": "wrongpassword"
        }
        res_bad = self.client.post("/api/auth/login", json=bad_login)
        self.assertEqual(res_bad.status_code, 401)
        self.assertFalse(res_bad.get_json()["success"])

    def test_03_products_crud(self):
        """Verify Product CRUD operations and input validation."""
        # 1. Create Product
        new_prod = {
            "product_name": "Test Wireless Earbuds",
            "category": "Audio",
            "description": "Bluetooth 5.3 water-resistant earbuds",
            "price": 49.99,
            "quantity": 15,
            "minimum_stock": 5,
            "supplier": "Test Audio Corp"
        }
        res_create = self.client.post("/api/products", json=new_prod)
        self.assertEqual(res_create.status_code, 201)
        prod_data = res_create.get_json()["product"]
        prod_id = prod_data["id"]
        self.assertEqual(prod_data["product_name"], "Test Wireless Earbuds")
        self.assertEqual(prod_data["quantity"], 15)
        self.assertEqual(prod_data["status"], "NORMAL")

        # 2. Get Product By ID
        res_get = self.client.get(f"/api/products/{prod_id}")
        self.assertEqual(res_get.status_code, 200)

        # 3. Update Product
        res_update = self.client.put(f"/api/products/{prod_id}", json={
            "price": 54.99,
            "supplier": "Premium Audio Corp"
        })
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(res_update.get_json()["product"]["price"], 54.99)

        # 4. Input validation (negative price rejection)
        res_neg = self.client.put(f"/api/products/{prod_id}", json={"price": -10})
        self.assertEqual(res_neg.status_code, 400)

        # 5. Delete Product
        res_del = self.client.delete(f"/api/products/{prod_id}")
        self.assertEqual(res_del.status_code, 200)

        # 6. Verify 404 after deletion
        res_not_found = self.client.get(f"/api/products/{prod_id}")
        self.assertEqual(res_not_found.status_code, 404)

    def test_04_inventory_stock_in(self):
        """Verify stock-in increases inventory and writes a STOCK_IN transaction record."""
        # Create dedicated product for testing
        res = self.client.post("/api/products", json={
            "product_name": "Test Stock-In Item",
            "category": "Testing",
            "price": 10.0,
            "quantity": 5,
            "minimum_stock": 5
        })
        prod_id = res.get_json()["product"]["id"]

        # Perform Stock-In of 10 units
        res_in = self.client.post("/api/inventory/stock-in", json={
            "product_id": prod_id,
            "quantity": 10,
            "remarks": "Test shipment received"
        })
        self.assertEqual(res_in.status_code, 200)
        data = res_in.get_json()
        self.assertEqual(data["data"]["product"]["quantity"], 15)
        self.assertEqual(data["data"]["transaction"]["transaction_type"], "STOCK_IN")
        self.assertEqual(data["data"]["transaction"]["quantity"], 10)
        self.assertEqual(data["data"]["transaction"]["previous_quantity"], 5)
        self.assertEqual(data["data"]["transaction"]["new_quantity"], 15)

    def test_05_inventory_stock_out_and_rules(self):
        """Verify stock-out decreases inventory, enforces non-negative constraints, and logs transactions."""
        # Create product with 8 units
        res = self.client.post("/api/products", json={
            "product_name": "Test Stock-Out Item",
            "category": "Testing",
            "price": 20.0,
            "quantity": 8,
            "minimum_stock": 4
        })
        prod_id = res.get_json()["product"]["id"]

        # Valid stock-out of 3 units -> balance 5 (NORMAL)
        res_out = self.client.post("/api/inventory/stock-out", json={
            "product_id": prod_id,
            "quantity": 3,
            "remarks": "Dispatched to client"
        })
        self.assertEqual(res_out.status_code, 200)
        self.assertEqual(res_out.get_json()["data"]["product"]["quantity"], 5)

        # Valid stock-out of 2 units -> balance 3 (LOW_STOCK <= 4)
        res_out2 = self.client.post("/api/inventory/stock-out", json={
            "product_id": prod_id,
            "quantity": 2,
            "remarks": "Dispatched to office"
        })
        self.assertEqual(res_out2.status_code, 200)
        prod = res_out2.get_json()["data"]["product"]
        self.assertEqual(prod["quantity"], 3)
        self.assertEqual(prod["status"], "LOW_STOCK")

        # Invalid stock-out: request 10 units when only 3 available
        res_excess = self.client.post("/api/inventory/stock-out", json={
            "product_id": prod_id,
            "quantity": 10,
            "remarks": "Excess dispatch attempt"
        })
        self.assertEqual(res_excess.status_code, 400)
        self.assertIn("Insufficient stock", res_excess.get_json()["error"])

    def test_06_low_stock_and_out_of_stock_endpoints(self):
        """Verify GET /api/inventory/low-stock and /api/inventory/out-of-stock."""
        res_low = self.client.get("/api/inventory/low-stock")
        self.assertEqual(res_low.status_code, 200)
        data_low = res_low.get_json()
        self.assertTrue(data_low["success"])
        for p in data_low["products"]:
            self.assertEqual(p["status"], "LOW_STOCK")
            self.assertGreater(p["quantity"], 0)
            self.assertLessEqual(p["quantity"], p["minimum_stock"])

        res_out = self.client.get("/api/inventory/out-of-stock")
        self.assertEqual(res_out.status_code, 200)
        data_out = res_out.get_json()
        self.assertTrue(data_out["success"])
        for p in data_out["products"]:
            self.assertEqual(p["status"], "OUT_OF_STOCK")
            self.assertEqual(p["quantity"], 0)

    def test_07_dashboard_endpoint(self):
        """Verify GET /api/dashboard returns complete metrics and aggregates."""
        res = self.client.get("/api/dashboard")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        stats = data["data"]
        self.assertIn("total_products", stats)
        self.assertIn("total_units", stats)
        self.assertIn("total_value", stats)
        self.assertIn("low_stock_count", stats)
        self.assertIn("out_of_stock_count", stats)
        self.assertIn("category_distribution", stats)
        self.assertIn("recent_transactions", stats)

    def test_08_ai_insights_endpoint(self):
        """Verify GET /api/ai/insights returns stored insights from SQLite."""
        res = self.client.get("/api/ai/insights")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIsInstance(data["insights"], list)

    def test_09_ai_chat_graceful_configuration_handling(self):
        """
        Verify POST /api/ai/chat gathers SQLite context and, if Microsoft Foundry
        credentials are not configured or invalid, returns a clean error without crashing.
        """
        payload = {"message": "Which products need immediate restocking?"}
        res = self.client.post("/api/ai/chat", json=payload)
        # Should return 200 (if Foundry credentials valid) or 503 (if unconfigured/unavailable)
        self.assertIn(res.status_code, [200, 503])
        data = res.get_json()
        if res.status_code == 503:
            self.assertFalse(data["success"])
            self.assertIn("Microsoft Foundry", data["error"])

    def test_10_ai_analyze_graceful_configuration_handling(self):
        """
        Verify POST /api/ai/analyze handles Microsoft Foundry calls or reports configuration cleanly.
        """
        res = self.client.post("/api/ai/analyze")
        self.assertIn(res.status_code, [200, 503])
        data = res.get_json()
        if res.status_code == 503:
            self.assertFalse(data["success"])
            self.assertIn("Microsoft Foundry", data["error"])

if __name__ == "__main__":
    unittest.main()
