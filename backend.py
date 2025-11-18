import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseConnection:
    """Database connection manager"""
    
    def __init__(self, db_path: str = "finance.db"):
        self.db_path = db_path
        self._create_tables()
    
    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Simple transactions table with type (income/expense)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL,
                    type TEXT CHECK(type IN ('income', 'expense')) NOT NULL,
                    remarks TEXT,
                    date TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()

class Transaction:
    """Transaction class representing financial transactions"""
    
    def __init__(self, id: int, amount: float, type: str, remarks: str, 
                 date: str, created_at: str = None):
        self.id = id
        self.amount = amount
        self.type = type  # 'income' or 'expense'
        self.remarks = remarks
        self.date = date
        self.created_at = created_at or datetime.now().isoformat()
    
    def __repr__(self):
        return f"Transaction(id={self.id}, type='{self.type}', amount={self.amount}, remarks='{self.remarks}')"

class FinanceManager:
    """Main finance management class"""
    
    def __init__(self, db_path: str = "finance.db"):
        self.db = DatabaseConnection(db_path)
        self.db_path = db_path
    
    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def add_transaction(self, amount: float, type: str, remarks: str = "", date: str = None) -> bool:
        """Add a new transaction (income or expense)"""
        try:
            if type not in ['income', 'expense']:
                raise ValueError("Type must be 'income' or 'expense'")
            
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO transactions (amount, type, remarks, date)
                    VALUES (?, ?, ?, ?)
                """, (amount, type, remarks, date))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding transaction: {e}")
            return False
    
    def get_transactions(self, start_date: str = None, end_date: str = None, 
                        type: str = None) -> List[Transaction]:
        """Get transactions with optional filters"""
        try:
            query = """
                SELECT id, amount, type, remarks, date, created_at
                FROM transactions
            """
            params = []
            
            conditions = []
            if start_date:
                conditions.append("date >= ?")
                params.append(start_date)
            if end_date:
                conditions.append("date <= ?")
                params.append(end_date)
            if type:
                conditions.append("type = ?")
                params.append(type)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY date DESC, created_at DESC"
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                transactions = []
                for row in results:
                    transaction = Transaction(
                        id=row[0], amount=row[1], type=row[2],
                        remarks=row[3], date=row[4], created_at=row[5]
                    )
                    transactions.append(transaction)
                
                return transactions
        except Exception as e:
            print(f"Error getting transactions: {e}")
            return []
    
    def get_balance(self) -> float:
        """Calculate current balance (total income - total expenses)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Get total income
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM transactions 
                    WHERE type = 'income'
                """)
                total_income = cursor.fetchone()[0]
                
                # Get total expenses
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM transactions 
                    WHERE type = 'expense'
                """)
                total_expenses = cursor.fetchone()[0]
                
                return total_income - total_expenses
        except Exception as e:
            print(f"Error calculating balance: {e}")
            return 0.0
    
    def get_income_total(self) -> float:
        """Get total income"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'income'")
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error getting income total: {e}")
            return 0.0
    
    def get_expense_total(self) -> float:
        """Get total expenses"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'expense'")
                return cursor.fetchone()[0]
        except Exception as e:
            print(f"Error getting expense total: {e}")
            return 0.0
    
    def get_monthly_summary(self, year: int = None, month: int = None) -> Dict:
        """Get monthly summary of income and expenses"""
        try:
            if year is None:
                year = datetime.now().year
            if month is None:
                month = datetime.now().month
            
            start_date = f"{year:04d}-{month:02d}-01"
            if month == 12:
                end_date = f"{year+1:04d}-01-01"
            else:
                end_date = f"{year:04d}-{month+1:02d}-01"
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Monthly income
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0)
                    FROM transactions
                    WHERE type = 'income' AND date >= ? AND date < ?
                """, (start_date, end_date))
                monthly_income = cursor.fetchone()[0]
                
                # Monthly expenses
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0)
                    FROM transactions
                    WHERE type = 'expense' AND date >= ? AND date < ?
                """, (start_date, end_date))
                monthly_expenses = cursor.fetchone()[0]
                
                return {
                    'monthly_income': monthly_income,
                    'monthly_expenses': monthly_expenses,
                    'monthly_balance': monthly_income - monthly_expenses,
                    'month': month,
                    'year': year
                }
        except Exception as e:
            print(f"Error getting monthly summary: {e}")
            return {}
    
    def delete_transaction(self, transaction_id: int) -> bool:
        """Delete a transaction"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error deleting transaction: {e}")
            return False
    
    def update_transaction(self, transaction_id: int, amount: float = None, 
                          type: str = None, remarks: str = None, date: str = None) -> bool:
        """Update a transaction"""
        try:
            updates = []
            params = []
            
            if amount is not None:
                updates.append("amount = ?")
                params.append(amount)
            if type is not None:
                if type not in ['income', 'expense']:
                    raise ValueError("Type must be 'income' or 'expense'")
                updates.append("type = ?")
                params.append(type)
            if remarks is not None:
                updates.append("remarks = ?")
                params.append(remarks)
            if date is not None:
                updates.append("date = ?")
                params.append(date)
            
            if not updates:
                return False
            
            params.append(transaction_id)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE transactions 
                    SET {', '.join(updates)} 
                    WHERE id = ?
                """, params)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating transaction: {e}")
            return False




# # Initialize
# fm = FinanceManager()

# # Add income
# fm.add_transaction(1000.00, 'income', 'Salary payment')

# # Add expense  
# fm.add_transaction(50.00, 'expense', 'Lunch with client')

# # Get all transactions
# transactions = fm.get_transactions()

# # Get only income
# income = fm.get_transactions(type='income')

# # Get only expenses
# expenses = fm.get_transactions(type='expense')

# # Check balance
# balance = fm.get_balance()

# # Get monthly summary
# summary = fm.get_monthly_summary(2024, 1)