from datetime import datetime, timedelta, timezone
from app import create_app
from models import db, User, Product, InventoryTransaction, AIInsight

def seed_database():
    """Populate the database with realistic sample users, products, and transaction history."""
    print("=" * 60)
    print(" Seeding AI-Powered Inventory Monitor Database")
    print("=" * 60)

    app = create_app()
    with app.app_context():
        # Clean existing data for a fresh seed
        print("Clearing existing records...")
        db.session.query(AIInsight).delete()
        db.session.query(InventoryTransaction).delete()
        db.session.query(Product).delete()
        db.session.query(User).delete()
        db.session.commit()

        # 1. Create Default Users
        print("Creating users...")
        admin = User(
            username="admin",
            email="admin@inventory.local",
            role="admin"
        )
        admin.set_password("admin123")

        manager = User(
            username="manager",
            email="manager@inventory.local",
            role="manager"
        )
        manager.set_password("manager123")

        db.session.add_all([admin, manager])
        db.session.commit()
        print(f"[OK] Users created: 'admin' (password: admin123), 'manager' (password: manager123)")

        # 2. Create Sample Products
        print("Creating catalog products...")
        sample_products = [
            {
                "product_name": "UltraBook Pro Laptop 15\"",
                "category": "Computers",
                "description": "Intel Core i7, 16GB RAM, 512GB SSD professional workstation",
                "price": 1299.99,
                "quantity": 18,
                "minimum_stock": 5,
                "supplier": "Dell Commercial Tech"
            },
            {
                "product_name": "Wireless Optical Mouse",
                "category": "Accessories",
                "description": "Ergonomic 2.4GHz wireless mouse with silent clicks",
                "price": 29.99,
                "quantity": 4,          # LOW_STOCK (<= 10)
                "minimum_stock": 10,
                "supplier": "Logitech Logistics"
            },
            {
                "product_name": "Mechanical RGB Keyboard",
                "category": "Accessories",
                "description": "Cherry MX Blue switches, per-key RGB backlighting",
                "price": 89.99,
                "quantity": 3,          # LOW_STOCK (<= 8)
                "minimum_stock": 8,
                "supplier": "Corsair Peripherals"
            },
            {
                "product_name": "27-inch 4K UHD Monitor",
                "category": "Displays",
                "description": "IPS panel, 99% sRGB color gamut with HDR10",
                "price": 349.50,
                "quantity": 12,
                "minimum_stock": 6,
                "supplier": "LG Display Solutions"
            },
            {
                "product_name": "Enterprise Color Laser Printer",
                "category": "Office Equipment",
                "description": "Duplex fast color laser multifunction network printer",
                "price": 599.00,
                "quantity": 0,          # OUT_OF_STOCK
                "minimum_stock": 4,
                "supplier": "HP Enterprise"
            },
            {
                "product_name": "Dual-Band Wi-Fi 6 Router",
                "category": "Networking",
                "description": "AX3000 Gigabit speed router with beamforming and WPA3",
                "price": 119.99,
                "quantity": 15,
                "minimum_stock": 5,
                "supplier": "Cisco Linksys"
            },
            {
                "product_name": "1080p HD Streaming Webcam",
                "category": "Accessories",
                "description": "Full HD webcam with dual stereo noise-cancelling mics",
                "price": 69.99,
                "quantity": 2,          # LOW_STOCK (<= 7)
                "minimum_stock": 7,
                "supplier": "Anker Tech"
            },
            {
                "product_name": "Noise-Cancelling USB Headset",
                "category": "Audio",
                "description": "Active noise cancelling with boom mic for office meetings",
                "price": 79.99,
                "quantity": 0,          # OUT_OF_STOCK
                "minimum_stock": 5,
                "supplier": "Jabra Communications"
            },
            {
                "product_name": "1TB NVMe Portable SSD",
                "category": "Storage",
                "description": "USB 3.2 Gen 2 rugged high-speed external solid state drive",
                "price": 109.99,
                "quantity": 25,
                "minimum_stock": 10,
                "supplier": "Samsung Memory"
            },
            {
                "product_name": "Thunderbolt 4 Docking Station",
                "category": "Accessories",
                "description": "Triple 4K display output, 96W Power Delivery passthrough",
                "price": 189.99,
                "quantity": 1,          # LOW_STOCK (<= 5)
                "minimum_stock": 5,
                "supplier": "Belkin Hubs"
            },
            {
                "product_name": "24-Port Gigabit Ethernet Switch",
                "category": "Networking",
                "description": "Managed rackmount switch with VLAN support and QoS",
                "price": 220.00,
                "quantity": 8,
                "minimum_stock": 4,
                "supplier": "TP-Link Enterprise"
            },
            {
                "product_name": "Ergonomic Vertical Mouse",
                "category": "Accessories",
                "description": "Contoured vertical handshake position to prevent wrist strain",
                "price": 45.00,
                "quantity": 0,          # OUT_OF_STOCK
                "minimum_stock": 6,
                "supplier": "Logitech Logistics"
            }
        ]

        products_dict = {}
        for p_data in sample_products:
            prod = Product(**p_data)
            db.session.add(prod)
            db.session.flush()
            products_dict[prod.product_name] = prod

        db.session.commit()
        print(f"[OK] Created {len(sample_products)} catalog products.")

        # 3. Create Inventory Transactions
        print("Creating historical transaction audit log...")
        now = datetime.now(timezone.utc)
        transactions = [
            # Initial stock ins
            InventoryTransaction(
                product_id=products_dict["UltraBook Pro Laptop 15\""].id,
                transaction_type="STOCK_IN",
                quantity=20,
                previous_quantity=0,
                new_quantity=20,
                remarks="Initial bulk purchase order PO-2026-001",
                created_at=now - timedelta(days=10)
            ),
            InventoryTransaction(
                product_id=products_dict["Wireless Optical Mouse"].id,
                transaction_type="STOCK_IN",
                quantity=25,
                previous_quantity=0,
                new_quantity=25,
                remarks="Initial shipment from Logitech",
                created_at=now - timedelta(days=9)
            ),
            InventoryTransaction(
                product_id=products_dict["Enterprise Color Laser Printer"].id,
                transaction_type="STOCK_IN",
                quantity=5,
                previous_quantity=0,
                new_quantity=5,
                remarks="Department procurement shipment",
                created_at=now - timedelta(days=8)
            ),
            InventoryTransaction(
                product_id=products_dict["Noise-Cancelling USB Headset"].id,
                transaction_type="STOCK_IN",
                quantity=12,
                previous_quantity=0,
                new_quantity=12,
                remarks="Quarterly audio accessories shipment",
                created_at=now - timedelta(days=7)
            ),
            # Stock outs leading to low/out-of-stock
            InventoryTransaction(
                product_id=products_dict["Wireless Optical Mouse"].id,
                transaction_type="STOCK_OUT",
                quantity=21,
                previous_quantity=25,
                new_quantity=4,
                remarks="Bulk dispatch for Engineering Lab workstations",
                created_at=now - timedelta(days=3)
            ),
            InventoryTransaction(
                product_id=products_dict["Enterprise Color Laser Printer"].id,
                transaction_type="STOCK_OUT",
                quantity=5,
                previous_quantity=5,
                new_quantity=0,
                remarks="Dispatched to Finance & Administration buildings",
                created_at=now - timedelta(days=2)
            ),
            InventoryTransaction(
                product_id=products_dict["Noise-Cancelling USB Headset"].id,
                transaction_type="STOCK_OUT",
                quantity=12,
                previous_quantity=12,
                new_quantity=0,
                remarks="Assigned to Remote Staff & Support Team",
                created_at=now - timedelta(days=1)
            ),
            InventoryTransaction(
                product_id=products_dict["Thunderbolt 4 Docking Station"].id,
                transaction_type="STOCK_OUT",
                quantity=4,
                previous_quantity=5,
                new_quantity=1,
                remarks="Allocated to Senior Research Engineers",
                created_at=now - timedelta(hours=14)
            ),
            InventoryTransaction(
                product_id=products_dict["1080p HD Streaming Webcam"].id,
                transaction_type="STOCK_OUT",
                quantity=8,
                previous_quantity=10,
                new_quantity=2,
                remarks="Equipped for Conference Room B & C",
                created_at=now - timedelta(hours=8)
            ),
            InventoryTransaction(
                product_id=products_dict["UltraBook Pro Laptop 15\""].id,
                transaction_type="STOCK_OUT",
                quantity=2,
                previous_quantity=20,
                new_quantity=18,
                remarks="Issued to New Faculty Members",
                created_at=now - timedelta(hours=3)
            ),
            # Adjustment
            InventoryTransaction(
                product_id=products_dict["Mechanical RGB Keyboard"].id,
                transaction_type="ADJUSTMENT",
                quantity=2,
                previous_quantity=5,
                new_quantity=3,
                remarks="Physical audit reconciliation - 2 damaged units removed",
                created_at=now - timedelta(hours=2)
            )
        ]

        db.session.add_all(transactions)
        db.session.commit()
        print(f"[OK] Created {len(transactions)} historical audit transactions.")

        # 4. Create Initial AI Insights
        print("Creating baseline AI insights...")
        insights = [
            AIInsight(
                product_id=products_dict["Enterprise Color Laser Printer"].id,
                insight_type="RISK_ALERT",
                recommendation="CRITICAL OUT OF STOCK: 'Enterprise Color Laser Printer' has 0 units remaining. Department printing workflows may be disrupted. Recommend urgent procurement of at least 8 units.",
                priority="HIGH",
                created_at=now - timedelta(hours=5)
            ),
            AIInsight(
                product_id=products_dict["Noise-Cancelling USB Headset"].id,
                insight_type="RISK_ALERT",
                recommendation="CRITICAL OUT OF STOCK: 'Noise-Cancelling USB Headset' inventory is fully depleted after recent team onboarding. Reorder 15 units immediately.",
                priority="HIGH",
                created_at=now - timedelta(hours=4)
            ),
            AIInsight(
                product_id=products_dict["Wireless Optical Mouse"].id,
                insight_type="RESTOCK_RECOMMENDATION",
                recommendation="LOW STOCK WARNING: 'Wireless Optical Mouse' stock is at 4 units (minimum threshold: 10). High consumption velocity observed in past 3 days. Recommend restocking 25 units.",
                priority="MEDIUM",
                created_at=now - timedelta(hours=2)
            ),
            AIInsight(
                product_id=None,
                insight_type="SUMMARY_ANALYSIS",
                recommendation="INVENTORY DIAGNOSTIC: Total catalog consists of 12 active products with a total valuation of $38,400+. Currently, 3 products are OUT_OF_STOCK and 4 are LOW_STOCK. The Accessories category faces the highest stock turnover rate.",
                priority="HIGH",
                created_at=now - timedelta(minutes=45)
            )
        ]

        db.session.add_all(insights)
        db.session.commit()
        print(f"[OK] Created {len(insights)} baseline AI insights.")

    print("=" * 60)
    print(" Seeding finished successfully!")
    print(" Default Login Credentials:")
    print("   Admin:   username = admin    password = admin123")
    print("   Manager: username = manager  password = manager123")
    print("=" * 60)

if __name__ == "__main__":
    seed_database()
