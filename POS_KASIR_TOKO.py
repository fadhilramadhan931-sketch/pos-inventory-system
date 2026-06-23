#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTEM KASIR DAN MANAJEMEN STOK TOKO
Console Edition - Single File Version

Upgrade dari codingan original dengan:
- SQLite Database (persistent)
- Authentication (login system)
- Better UI (colors, tables)
- Stock tracking
- Detailed reports
"""

import os
import sys
import sqlite3
import math
from datetime import datetime, timedelta
from hashlib import sha256

# =====================
# TERMINAL COLORS
# =====================
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'

# =====================
# HELPER FUNCTIONS
# =====================
def clear():
    """Clear screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.CYAN}ℹ {msg}{Colors.RESET}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")

def print_header(title):
    """Print formatted header"""
    print(f"\n{Colors.CYAN}" + "="*60)
    print(f" {title.center(58)} ")
    print("="*60 + f"{Colors.RESET}")

def format_currency(amount):
    """Format as currency"""
    return f"Rp {amount:,.0f}"

def print_table(headers, rows):
    """Print formatted table"""
    if not rows:
        print_info("Tidak ada data")
        return
    
    # Calculate widths
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    
    # Print header
    header_str = " | ".join(str(h).ljust(w) for h, w in zip(headers, widths))
    print(f"\n{Colors.BOLD}{header_str}{Colors.RESET}")
    print("-" * len(header_str))
    
    # Print rows
    for row in rows:
        row_str = " | ".join(str(c).ljust(w) for c, w in zip(row, widths))
        print(row_str)

def input_number(prompt):
    """Input validated number"""
    while True:
        try:
            return float(input(f"{Colors.YELLOW}{prompt}{Colors.RESET}"))
        except ValueError:
            print_error("Input harus angka!")

def input_int(prompt):
    """Input validated integer"""
    while True:
        try:
            return int(input(f"{Colors.YELLOW}{prompt}{Colors.RESET}"))
        except ValueError:
            print_error("Input harus angka bulat!")

# =====================
# DATABASE HANDLER
# =====================
class Database:
    def __init__(self, db_name='pos_system.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()
        self.init_db()
    
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
    
    def execute(self, sql, params=None):
        """Execute SQL"""
        if params:
            self.cursor.execute(sql, params)
        else:
            self.cursor.execute(sql)
        self.conn.commit()
    
    def fetch_one(self, sql, params=None):
        """Fetch one row"""
        if params:
            self.cursor.execute(sql, params)
        else:
            self.cursor.execute(sql)
        return self.cursor.fetchone()
    
    def fetch_all(self, sql, params=None):
        """Fetch all rows"""
        if params:
            self.cursor.execute(sql, params)
        else:
            self.cursor.execute(sql)
        return self.cursor.fetchall()
    
    def init_db(self):
        """Create tables"""
        # Users
        self.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'cashier',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Products
        self.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                sku TEXT UNIQUE NOT NULL,
                category TEXT,
                price REAL NOT NULL,
                cost REAL,
                stock INTEGER DEFAULT 0,
                min_stock INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Transactions
        self.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                subtotal REAL NOT NULL,
                discount_amount REAL DEFAULT 0,
                discount_percent REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                total_amount REAL NOT NULL,
                payment_method TEXT DEFAULT 'cash',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Transaction Items
        self.execute('''
            CREATE TABLE IF NOT EXISTS transaction_items (
                id INTEGER PRIMARY KEY,
                transaction_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                subtotal REAL NOT NULL
            )
        ''')
        
        # Stock History
        self.execute('''
            CREATE TABLE IF NOT EXISTS stock_history (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                quantity_change INTEGER NOT NULL,
                type TEXT,
                reference_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create default users if not exist
        user = self.fetch_one('SELECT * FROM users WHERE username = ?', ('admin',))
        if not user:
            admin_pass = sha256('admin123'.encode()).hexdigest()
            cashier_pass = sha256('cashier123'.encode()).hexdigest()
            
            self.execute(
                'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                ('admin', admin_pass, 'admin')
            )
            self.execute(
                'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                ('cashier', cashier_pass, 'cashier')
            )

# =====================
# SERVICES
# =====================
class ProductService:
    def __init__(self, db):
        self.db = db
    
    def get_all(self):
        """Get all products"""
        return self.db.fetch_all('SELECT * FROM products ORDER BY name')
    
    def get_by_id(self, product_id):
        """Get product by ID"""
        return self.db.fetch_one('SELECT * FROM products WHERE id = ?', (product_id,))
    
    def add(self, name, sku, category, price, cost, stock, min_stock):
        """Add product"""
        try:
            self.db.execute(
                'INSERT INTO products (name, sku, category, price, cost, stock, min_stock) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (name, sku, category, price, cost, stock, min_stock)
            )
            return True
        except:
            return False
    
    def update_stock(self, product_id, qty_change, change_type, ref_id=None):
        """Update product stock"""
        product = self.get_by_id(product_id)
        if not product:
            return False
        
        new_stock = product['stock'] + qty_change
        if new_stock < 0:
            return False
        
        self.db.execute(
            'UPDATE products SET stock = ? WHERE id = ?',
            (new_stock, product_id)
        )
        
        # Record history
        self.db.execute(
            'INSERT INTO stock_history (product_id, quantity_change, type, reference_id) VALUES (?, ?, ?, ?)',
            (product_id, qty_change, change_type, ref_id)
        )
        
        return True
    
    def get_low_stock(self):
        """Get products with low stock"""
        return self.db.fetch_all('SELECT * FROM products WHERE stock <= min_stock')

class TransactionService:
    def __init__(self, db):
        self.db = db
    
    def calculate_discount(self, subtotal):
        """Calculate auto discount"""
        if subtotal > 500000:
            return 15
        elif subtotal > 200000:
            return 10
        elif subtotal > 100000:
            return 5
        return 0
    
    def create(self, user_id, items, discount_persen=0):
        """Create transaction"""
        try:
            # Calculate
            subtotal = sum(item['subtotal'] for item in items)
            discount_amount = subtotal * discount_persen / 100
            after_discount = subtotal - discount_amount
            tax_amount = after_discount * 0.11
            total_amount = math.ceil(after_discount + tax_amount)
            
            # Insert transaction
            self.db.execute(
                'INSERT INTO transactions (user_id, subtotal, discount_amount, discount_percent, tax_amount, total_amount) VALUES (?, ?, ?, ?, ?, ?)',
                (user_id, subtotal, discount_amount, discount_persen, tax_amount, total_amount)
            )
            
            # Get transaction ID
            tx = self.db.fetch_one('SELECT id FROM transactions ORDER BY id DESC LIMIT 1')
            tx_id = tx['id']
            
            # Insert items
            for item in items:
                self.db.execute(
                    'INSERT INTO transaction_items (transaction_id, product_id, quantity, unit_price, subtotal) VALUES (?, ?, ?, ?, ?)',
                    (tx_id, item['product_id'], item['qty'], item['price'], item['subtotal'])
                )
            
            return tx_id, subtotal, discount_amount, tax_amount, total_amount
        except Exception as e:
            print_error(f"Error: {str(e)}")
            return None
    
    def get_all(self):
        """Get all transactions"""
        return self.db.fetch_all('SELECT * FROM transactions ORDER BY created_at DESC')

class ReportService:
    def __init__(self, db):
        self.db = db
    
    def daily_report(self, date=None):
        """Daily report"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        txs = self.db.fetch_all(
            "SELECT * FROM transactions WHERE DATE(created_at) = ?",
            (date,)
        )
        
        if not txs:
            return None
        
        total_sales = sum(t['total_amount'] for t in txs)
        total_discount = sum(t['discount_amount'] for t in txs)
        
        return {
            'date': date,
            'count': len(txs),
            'total_sales': total_sales,
            'total_discount': total_discount,
            'avg': total_sales / len(txs) if txs else 0,
        }
    
    def top_products(self, limit=10):
        """Top selling products"""
        return self.db.fetch_all('''
            SELECT p.name, p.sku, SUM(ti.quantity) as qty, SUM(ti.subtotal) as revenue
            FROM transaction_items ti
            JOIN products p ON ti.product_id = p.id
            GROUP BY p.id
            ORDER BY qty DESC
            LIMIT ?
        ''', (limit,))

# =====================
# MENU SYSTEM
# =====================
class MenuSystem:
    def __init__(self, db, user):
        self.db = db
        self.user = user
        self.product_service = ProductService(db)
        self.transaction_service = TransactionService(db)
        self.report_service = ReportService(db)
    
    def run(self):
        """Main menu loop"""
        while True:
            clear()
            print_header(f"SISTEM KASIR - {self.user['username']} ({self.user['role']})")
            
            print("\n1. Transaksi Baru")
            print("2. Kelola Produk")
            print("3. Lihat Stok")
            print("4. Laporan")
            if self.user['role'] == 'admin':
                print("5. Kelola User")
            print("\n0. Logout")
            
            choice = input(f"\n{Colors.YELLOW}Pilih Menu: {Colors.RESET}")
            
            if choice == '1':
                self.menu_transaction()
            elif choice == '2':
                self.menu_product()
            elif choice == '3':
                self.menu_stock()
            elif choice == '4':
                self.menu_report()
            elif choice == '5' and self.user['role'] == 'admin':
                self.menu_admin()
            elif choice == '0':
                print_info("Logout berhasil. Terima kasih!")
                break
            else:
                print_error("Menu tidak tersedia!")
            
            if choice in ['1', '2', '3', '4', '5']:
                input(f"{Colors.YELLOW}\nTekan Enter untuk melanjutkan...{Colors.RESET}")
    
    def menu_transaction(self):
        """Transaction menu"""
        clear()
        print_header("TRANSAKSI BARU")
        
        products = self.product_service.get_all()
        if not products:
            print_error("Tidak ada produk!")
            return
        
        keranjang = []
        
        while True:
            clear()
            print_header(f"TRANSAKSI - Keranjang: {len(keranjang)} item")
            
            rows = [(p['id'], p['name'], p['sku'], format_currency(p['price']), p['stock']) 
                    for p in products]
            print_table(['No', 'Nama', 'SKU', 'Harga', 'Stok'], rows)
            
            print(f"\n{Colors.YELLOW}0 = Selesai, q = Batal{Colors.RESET}")
            pilihan = input(f"{Colors.YELLOW}Pilih produk: {Colors.RESET}")
            
            if pilihan.lower() == 'q':
                return
            
            if pilihan == '0':
                break
            
            try:
                product_id = int(pilihan)
                product = self.product_service.get_by_id(product_id)
                
                if not product:
                    print_error("Produk tidak ditemukan!")
                    continue
                
                if product['stock'] <= 0:
                    print_error("Stok tidak tersedia!")
                    continue
                
                qty = input_int(f"\nJumlah {product['name']}: ")
                
                if qty > product['stock']:
                    print_error("Stok tidak cukup!")
                    continue
                
                # Check if already in cart
                found = False
                for item in keranjang:
                    if item['product_id'] == product_id:
                        item['qty'] += qty
                        item['subtotal'] = item['qty'] * item['price']
                        found = True
                        break
                
                if not found:
                    keranjang.append({
                        'product_id': product_id,
                        'name': product['name'],
                        'price': product['price'],
                        'qty': qty,
                        'subtotal': qty * product['price'],
                    })
                
                print_success(f"{product['name']} x{qty} ditambahkan")
            
            except ValueError:
                print_error("Input tidak valid!")
        
        if not keranjang:
            print_info("Transaksi dibatalkan")
            return
        
        # Calculate
        subtotal = sum(item['subtotal'] for item in keranjang)
        auto_discount = self.transaction_service.calculate_discount(subtotal)
        
        clear()
        print_header("RINGKASAN TRANSAKSI")
        
        rows = [(item['name'], item['qty'], format_currency(item['price']), format_currency(item['subtotal'])) 
                for item in keranjang]
        print_table(['Produk', 'Qty', 'Harga', 'Subtotal'], rows)
        
        discount_amount = subtotal * auto_discount / 100
        after_discount = subtotal - discount_amount
        tax_amount = after_discount * 0.11
        total = after_discount + tax_amount
        
        print(f"\nSubtotal        : {format_currency(subtotal)}")
        print(f"Diskon {auto_discount}%      : {format_currency(discount_amount)}")
        print(f"Setelah Diskon  : {format_currency(after_discount)}")
        print(f"PPN 11%         : {format_currency(tax_amount)}")
        print(f"{Colors.BOLD}Total Bayar     : {format_currency(total)}{Colors.RESET}")
        
        # Payment
        while True:
            uang = input_number(f"\nUang Tunai: Rp ")
            if uang < total:
                print_error("Uang tidak cukup!")
                continue
            break
        
        kembalian = uang - total
        
        # Process transaction
        result = self.transaction_service.create(self.user['id'], keranjang, auto_discount)
        
        if result:
            tx_id = result[0]
            
            # Update stock
            for item in keranjang:
                self.product_service.update_stock(item['product_id'], -item['qty'], 'sale', f'TRX{tx_id}')
            
            print_success("\nTransaksi berhasil!")
            print(f"Kembalian       : {format_currency(kembalian)}")
            
            # Print receipt
            print(f"\n{Colors.CYAN}" + "="*60)
            print("TOKO PARA IMO")
            print("KASIR IMO")
            print("="*60 + f"{Colors.RESET}")
            
            for item in keranjang:
                print(f"{item['name']} x{item['qty']}")
                print(f"  {format_currency(item['price'])} = {format_currency(item['subtotal'])}")
            
            print(f"{Colors.CYAN}-" * 60 + f"{Colors.RESET}")
            print(f"Subtotal        : {format_currency(subtotal)}")
            print(f"Diskon {auto_discount}%      : {format_currency(discount_amount)}")
            print(f"PPN 11%         : {format_currency(tax_amount)}")
            print(f"{Colors.BOLD}Total Bayar     : {format_currency(total)}{Colors.RESET}")
            print(f"Tunai           : {format_currency(uang)}")
            print(f"Kembalian       : {format_currency(kembalian)}")
            print(f"{Colors.CYAN}-" * 60)
            print(f"Tanggal         : {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
            print("="*60 + f"{Colors.RESET}")
        else:
            print_error("Transaksi gagal!")
    
    def menu_product(self):
        """Product management menu"""
        while True:
            clear()
            print_header("KELOLA PRODUK")
            
            print("\n1. Lihat Produk")
            print("2. Tambah Produk")
            print("0. Kembali")
            
            choice = input(f"\n{Colors.YELLOW}Pilih Menu: {Colors.RESET}")
            
            if choice == '1':
                self._view_products()
            elif choice == '2':
                self._add_product()
            elif choice == '0':
                break
            
            if choice in ['1', '2']:
                input(f"{Colors.YELLOW}\nTekan Enter...{Colors.RESET}")
    
    def _view_products(self):
        """View all products"""
        clear()
        print_header("DAFTAR PRODUK")
        
        products = self.product_service.get_all()
        rows = [(p['id'], p['name'], p['sku'], format_currency(p['price']), p['stock']) 
                for p in products]
        print_table(['No', 'Nama', 'SKU', 'Harga', 'Stok'], rows)
    
    def _add_product(self):
        """Add product"""
        clear()
        print_header("TAMBAH PRODUK")
        
        name = input(f"{Colors.YELLOW}Nama Produk: {Colors.RESET}")
        sku = input(f"{Colors.YELLOW}SKU: {Colors.RESET}")
        category = input(f"{Colors.YELLOW}Kategori: {Colors.RESET}")
        price = input_number("Harga: Rp ")
        cost = input_number("Biaya Modal: Rp ")
        stock = input_int("Stok Awal: ")
        min_stock = input_int("Stok Minimum: ")
        
        if self.product_service.add(name, sku, category, price, cost, stock, min_stock):
            print_success("Produk berhasil ditambahkan!")
        else:
            print_error("Gagal menambahkan produk!")
    
    def menu_stock(self):
        """Stock menu"""
        clear()
        print_header("LIHAT STOK")
        
        products = self.product_service.get_all()
        rows = [(p['id'], p['name'], p['sku'], p['stock'], p['min_stock']) 
                for p in products]
        print_table(['No', 'Nama', 'SKU', 'Stok', 'Min'], rows)
        
        # Low stock alert
        low_stock = self.product_service.get_low_stock()
        if low_stock:
            print(f"\n{Colors.RED}⚠ Produk dengan stok rendah:{Colors.RESET}")
            for p in low_stock:
                print(f"  - {p['name']}: {p['stock']} (min: {p['min_stock']})")
    
    def menu_report(self):
        """Reports menu"""
        while True:
            clear()
            print_header("LAPORAN")
            
            print("\n1. Laporan Harian")
            print("2. Top 10 Produk")
            print("0. Kembali")
            
            choice = input(f"\n{Colors.YELLOW}Pilih Menu: {Colors.RESET}")
            
            if choice == '1':
                report = self.report_service.daily_report()
                if report:
                    clear()
                    print_header("LAPORAN HARIAN")
                    print(f"Tanggal         : {report['date']}")
                    print(f"Total Transaksi : {report['count']}")
                    print(f"Total Penjualan : {format_currency(report['total_sales'])}")
                    print(f"Total Diskon    : {format_currency(report['total_discount'])}")
                    print(f"Rata-rata       : {format_currency(report['avg'])}")
                else:
                    print_info("Tidak ada data untuk hari ini")
            
            elif choice == '2':
                clear()
                print_header("TOP 10 PRODUK TERLARIS")
                products = self.report_service.top_products(10)
                rows = [(p['name'], p['sku'], p['qty'], format_currency(p['revenue'])) 
                        for p in products]
                print_table(['Produk', 'SKU', 'Qty', 'Revenue'], rows)
            
            elif choice == '0':
                break
            
            if choice in ['1', '2']:
                input(f"{Colors.YELLOW}\nTekan Enter...{Colors.RESET}")
    
    def menu_admin(self):
        """Admin menu"""
        clear()
        print_header("MENU ADMIN")
        
        print("\n1. Lihat User")
        print("2. Tambah User")
        print("0. Kembali")
        
        choice = input(f"\n{Colors.YELLOW}Pilih Menu: {Colors.RESET}")
        
        if choice == '1':
            clear()
            print_header("DAFTAR USER")
            users = self.db.fetch_all('SELECT id, username, role, created_at FROM users')
            rows = [(u['id'], u['username'], u['role'], u['created_at']) for u in users]
            print_table(['ID', 'Username', 'Role', 'Created'], rows)
        
        elif choice == '2':
            clear()
            print_header("TAMBAH USER")
            username = input(f"{Colors.YELLOW}Username: {Colors.RESET}")
            password = input(f"{Colors.YELLOW}Password: {Colors.RESET}")
            role = input(f"{Colors.YELLOW}Role (admin/cashier): {Colors.RESET}")
            
            pass_hash = sha256(password.encode()).hexdigest()
            try:
                self.db.execute(
                    'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                    (username, pass_hash, role)
                )
                print_success("User berhasil dibuat!")
            except:
                print_error("Username sudah ada!")
        
        input(f"{Colors.YELLOW}\nTekan Enter...{Colors.RESET}")

# =====================
# AUTH SYSTEM
# =====================
def login(db):
    """User login"""
    clear()
    print_header("SISTEM KASIR DAN MANAJEMEN STOK TOKO")
    print(f"{Colors.CYAN}Console Edition{Colors.RESET}")
    
    while True:
        username = input(f"\n{Colors.YELLOW}Username: {Colors.RESET}")
        password = input(f"{Colors.YELLOW}Password: {Colors.RESET}")
        
        pass_hash = sha256(password.encode()).hexdigest()
        user = db.fetch_one(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, pass_hash)
        )
        
        if user:
            print_success(f"Login berhasil! Selamat datang {username}")
            return dict(user)
        else:
            print_error("Username atau password salah!")

# =====================
# MAIN
# =====================
def main():
    """Main application"""
    try:
        # Initialize database
        db = Database()
        
        # Login
        user = login(db)
        
        # Run menu
        menu = MenuSystem(db, user)
        menu.run()
        
        print_info("\nTerima kasih telah menggunakan Sistem Kasir!")
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Program dihentikan.{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
