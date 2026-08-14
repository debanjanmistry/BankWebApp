import mysql.connector
import os
from datetime import date, datetime, timedelta
import random
from dateutil.relativedelta import relativedelta
from decimal import Decimal

# --- Database Configuration (replace with your MySQL details) ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Dkaustav@392',
    'database': 'bankdb'
}

conn = None
cursor = None

def connect_db():
    global conn, cursor
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(buffered=True)
        print("Connected to database successfully!")
        ensure_transaction_tables()
        return True
    except mysql.connector.Error as err:
        print(f"Connection failed: {err}")
        return False

def close_db():
    if cursor:
        cursor.close()
    if conn and conn.is_connected():
        conn.close()
        print("Database connection closed.")

def ensure_transaction_tables():
    """Create tables if they don't already exist."""
    global conn, cursor
    if not conn or not cursor:
        return
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                account_no   BIGINT PRIMARY KEY,
                name         VARCHAR(100) NOT NULL,
                father_name  VARCHAR(100),
                mother_name  VARCHAR(100),
                phone        VARCHAR(15),
                email        VARCHAR(100),
                address      TEXT,
                aadhar_no    VARCHAR(20) NOT NULL,
                dob          DATE NOT NULL,
                age          INT,
                pin          VARCHAR(4) NOT NULL,
                balance      DECIMAL(15,2) DEFAULT 0.00
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deposit (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                account_no BIGINT(12)    NOT NULL,
                amount     DECIMAL(15,2) NOT NULL,
                time       DATETIME      NOT NULL,
                FOREIGN KEY (account_no) REFERENCES customers(account_no) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS withdraw (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                account_no BIGINT(12)    NOT NULL,
                amount     DECIMAL(15,2) NOT NULL,
                time       DATETIME      NOT NULL,
                FOREIGN KEY (account_no) REFERENCES customers(account_no) ON DELETE CASCADE
            )
        """)
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Error creating transaction tables: {err}")

def log_deposit(acc_no, amount):
    """Insert a record into the deposit table."""
    global conn, cursor
    try:
        cursor.execute(
            "INSERT INTO deposit (account_no, amount, time) VALUES (%s, %s, %s)",
            (acc_no, amount, datetime.now())
        )
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Warning: Could not log deposit transaction: {err}")

def log_withdraw(acc_no, amount):
    """Insert a record into the withdraw table."""
    global conn, cursor
    try:
        cursor.execute(
            "INSERT INTO withdraw (account_no, amount, time) VALUES (%s, %s, %s)",
            (acc_no, amount, datetime.now())
        )
        conn.commit()
    except mysql.connector.Error as err:
        print(f"Warning: Could not log withdraw transaction: {err}")

def get_transaction_history(acc_no):
    """Return combined deposit/withdraw history for an account, newest first."""
    global conn, cursor
    history = []
    try:
        cursor.execute(
            "SELECT amount, time, 'deposit' AS type FROM deposit WHERE account_no = %s "
            "UNION ALL "
            "SELECT amount, time, 'withdraw' AS type FROM withdraw WHERE account_no = %s "
            "ORDER BY time DESC",
            (acc_no, acc_no)
        )
        history = cursor.fetchall()
    except mysql.connector.Error as err:
        print(f"Error fetching transaction history: {err}")
    return history

def get_chart_data(acc_no, interval='day'):
    """
    Return aggregated deposit/withdraw totals grouped by time interval.
    interval: 'day' | 'month' | 'year'
    Returns list of dicts: {label, deposit, withdraw}
    """
    global conn, cursor
    fmt_map = {
        'day':   '%Y-%m-%d',
        'month': '%Y-%m',
        'year':  '%Y',
    }
    fmt = fmt_map.get(interval, '%Y-%m-%d')
    results = {}
    try:
        # Deposits
        cursor.execute(
            f"SELECT DATE_FORMAT(time, %s) AS period, SUM(amount) "
            f"FROM deposit WHERE account_no = %s GROUP BY period ORDER BY period",
            (fmt, acc_no)
        )
        for period, total in cursor.fetchall():
            results.setdefault(period, {'label': period, 'deposit': 0.0, 'withdraw': 0.0})
            results[period]['deposit'] = float(total)

        # Withdrawals
        cursor.execute(
            f"SELECT DATE_FORMAT(time, %s) AS period, SUM(amount) "
            f"FROM withdraw WHERE account_no = %s GROUP BY period ORDER BY period",
            (fmt, acc_no)
        )
        for period, total in cursor.fetchall():
            results.setdefault(period, {'label': period, 'deposit': 0.0, 'withdraw': 0.0})
            results[period]['withdraw'] = float(total)

    except mysql.connector.Error as err:
        print(f"Error fetching chart data: {err}")

    return sorted(results.values(), key=lambda x: x['label'])

def main_menu():
    while True:
        print("\n===== MAIN MENU =====")
        print("1. Open New Account")
        print("2. Already Have an Account")
        print("3. Close Account")
        print("4. Exit")
        choice = input("Enter choice: ")

        if choice == '1':
            open_new_account()
        elif choice == '2':
            account_login()
        elif choice == '3':
            close_account()
        elif choice == '4':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Try again.")

def open_new_account():
    global conn, cursor
    print("\n--- Open New Account ---")
    if not conn or not cursor:
        print("Database not connected. Please ensure connection is established.")
        return

    try:
        name = input("Enter Name: ")
        father_name = input("Enter Father Name: ")
        mother_name = input("Enter Mother Name: ")
        phone = input("Enter Phone No: ")
        email = input("Enter Email ID: ")
        address = input("Enter Address: ")
        aadhar = input("Enter Aadhar No: ")
        dob_str = input("Enter DOB (YYYY-MM-DD): ")
        dob = date.fromisoformat(dob_str)
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        if age < 18:
            print("Account cannot be opened. Applicant must be at least 18 years old.")
            return

        pin = input("Create 4-digit PIN: ")

        # Generate unique account number (12 digits)
        acc_no = random.randint(100000000000, 999999999999) # 12-digit number

        query = "INSERT INTO customers(account_no, name, father_name, mother_name, phone, email, address, aadhar_no, dob, age, pin, balance) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        data = (acc_no, name, father_name, mother_name, phone, email, address, aadhar, dob, age, pin, Decimal('0.00')) # Initialize balance as Decimal

        cursor.execute(query, data)
        conn.commit()
        print(f"Account opened successfully! Account No: {acc_no}")
        # create_debit_card(acc_no) # This will be implemented later

    except ValueError:
        print("Invalid input. Please ensure DOB is in YYYY-MM-DD format and other inputs are valid.")
    except mysql.connector.Error as err:
        print(f"Error opening account: {err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def balance_inquiry(acc_no):
    global conn, cursor
    print("\n--- Balance Inquiry ---")
    if not conn or not cursor:
        print("Database not connected. Please ensure connection is established.")
        return
    try:
        query = "SELECT balance FROM customers WHERE account_no = %s"
        cursor.execute(query, (acc_no,))
        result = cursor.fetchone()
        if result:
            print(f"Current Balance: ${result[0]:.2f}")
        else:
            print("Account not found.")
    except mysql.connector.Error as err:
        print(f"Error during balance inquiry: {err}")

def deposit(acc_no):
    global conn, cursor
    print("\n--- Deposit ---")
    if not conn or not cursor:
        print("Database not connected. Please ensure connection is established.")
        return

    try:
        amount = Decimal(input("Enter amount to deposit: ")) # Convert to Decimal
        if amount <= 0:
            print("Deposit amount must be positive.")
            return

        # Fetch current balance
        query_select = "SELECT balance FROM customers WHERE account_no = %s"
        cursor.execute(query_select, (acc_no,))
        result = cursor.fetchone()

        if result:
            current_balance = result[0]
            new_balance = current_balance + amount

            # Update balance
            query_update = "UPDATE customers SET balance = %s WHERE account_no = %s"
            cursor.execute(query_update, (new_balance, acc_no))
            conn.commit()
            log_deposit(acc_no, amount)
            print(f"Successfully deposited ${amount:.2f}. New balance: ${new_balance:.2f}")
        else:
            print("Account not found.")
    except ValueError:
        print("Invalid amount. Please enter a numeric value.")
    except mysql.connector.Error as err:
        print(f"Error during deposit: {err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def withdraw(acc_no):
    global conn, cursor
    print("\n--- Withdraw ---")
    if not conn or not cursor:
        print("Database not connected. Please ensure connection is established.")
        return

    try:
        amount = Decimal(input("Enter amount to withdraw: ")) # Convert to Decimal
        if amount <= 0:
            print("Withdrawal amount must be positive.")
            return

        # Fetch current balance
        query_select = "SELECT balance FROM customers WHERE account_no = %s"
        cursor.execute(query_select, (acc_no,))
        result = cursor.fetchone()

        if result:
            current_balance = result[0]
            if current_balance >= amount:
                new_balance = current_balance - amount
                # Update balance
                query_update = "UPDATE customers SET balance = %s WHERE account_no = %s"
                cursor.execute(query_update, (new_balance, acc_no))
                conn.commit()
                log_withdraw(acc_no, amount)
                print(f"Successfully withdrew ${amount:.2f}. New balance: ${new_balance:.2f}")
            else:
                print("Insufficient funds.")
        else:
            print("Account not found.")
    except ValueError:
        print("Invalid amount. Please enter a numeric value.")
    except mysql.connector.Error as err:
        print(f"Error during withdrawal: {err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def transfer(acc_no):
    global conn, cursor
    print("\n--- Transfer ---")
    if not conn or not cursor:
        print("Database not connected. Please ensure connection is established.")
        return

    try:
        dest_acc_no = int(input("Enter destination account number: "))
        amount = Decimal(input("Enter amount to transfer: ")) # Convert to Decimal

        if amount <= 0:
            print("Transfer amount must be positive.")
            return

        if acc_no == dest_acc_no:
            print("Cannot transfer to the same account.")
            return

        # Check if destination account exists
        query_dest_exists = "SELECT account_no FROM customers WHERE account_no = %s"
        cursor.execute(query_dest_exists, (dest_acc_no,))
        if not cursor.fetchone():
            print("Destination account not found.")
            return

        # Fetch current balance of source account
        query_source_balance = "SELECT balance FROM customers WHERE account_no = %s"
        cursor.execute(query_source_balance, (acc_no,))
        source_result = cursor.fetchone()

        if source_result:
            source_balance = source_result[0]
            if source_balance >= amount:
                # Removed: conn.start_transaction()

                # Deduct from source account
                new_source_balance = source_balance - amount
                query_update_source = "UPDATE customers SET balance = %s WHERE account_no = %s"
                cursor.execute(query_update_source, (new_source_balance, acc_no))

                # Add to destination account
                query_dest_balance = "SELECT balance FROM customers WHERE account_no = %s"
                cursor.execute(query_dest_balance, (dest_acc_no,))
                dest_balance = cursor.fetchone()[0]
                new_dest_balance = dest_balance + amount
                query_update_dest = "UPDATE customers SET balance = %s WHERE account_no = %s"
                cursor.execute(query_update_dest, (new_dest_balance, dest_acc_no))

                conn.commit()
                print(f"Successfully transferred ${amount:.2f} to account {dest_acc_no}.")
                print(f"Your new balance: ${new_source_balance:.2f}")
            else:
                print("Insufficient funds in your account.")
        else:
            print("Source account not found (this should not happen during a logged-in session).")

    except ValueError:
        print("Invalid input. Account number and amount must be numeric.")
    except mysql.connector.Error as err:
        conn.rollback() # Rollback transaction on error
        print(f"Error during transfer: {err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def change_pin(acc_no):
    global conn, cursor
    print("\n--- Change PIN ---")
    if not conn or not cursor:
        print("Database not connected. Please ensure connection is established.")
        return

    try:
        current_pin = input("Enter current 4-digit PIN: ")
        if not (current_pin.isdigit() and len(current_pin) == 4):
            print("Invalid current PIN. PIN must be a 4-digit number.")
            return

        new_pin = input("Enter new 4-digit PIN: ")

        if not (new_pin.isdigit() and len(new_pin) == 4):
            print("Invalid new PIN. PIN must be a 4-digit number.")
            return

        # Verify current PIN
        query_verify = "SELECT * FROM customers WHERE account_no = %s AND pin = %s"
        cursor.execute(query_verify, (acc_no, current_pin))
        result = cursor.fetchone()

        if result:
            query_update = "UPDATE customers SET pin = %s WHERE account_no = %s"
            cursor.execute(query_update, (new_pin, acc_no))
            conn.commit()
            print("PIN changed successfully!")
        else:
            print("Invalid current PIN.")

    except mysql.connector.Error as err:
        print(f"Error during PIN change: {err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def account_menu(acc_no):
    while True:
        print(f"\n--- Account Menu for Account No: {acc_no} ---")
        print("1. Balance Inquiry")
        print("2. Deposit")
        print("3. Withdraw")
        print("4. Transfer")
        print("5. Change PIN")
        print("6. Back to Main Menu")
        choice = input("Enter choice: ")

        if choice == '1':
            balance_inquiry(acc_no)
        elif choice == '2':
            deposit(acc_no)
        elif choice == '3':
            withdraw(acc_no)
        elif choice == '4':
            transfer(acc_no)
        elif choice == '5':
            change_pin(acc_no)
        elif choice == '6':
            print("Returning to Main Menu...")
            break
        else:
            print("Invalid choice. Try again.")

def account_login():
    global conn, cursor
    print("\n--- Account Login ---")
    if not conn or not cursor:
        print("Database not connected. Please ensure connection is established.")
        return

    try:
        acc_no = int(input("Enter Account No: "))
        pin = input("Enter PIN: ")

        query = "SELECT * FROM customers WHERE account_no = %s AND pin = %s"
        cursor.execute(query, (acc_no, pin))
        result = cursor.fetchone()

        if result:
            print("Login successful!")
            account_menu(acc_no)
        else:
            print("Invalid account number or PIN.")
    except ValueError:
        print("Invalid input. Account number must be a number.")
    except mysql.connector.Error as err:
        print(f"Error during account login: {err}")

def close_account():
    global conn, cursor
    print("\n--- Close Account ---")
    if not conn or not cursor:
        print("Database not connected. Please ensure connection is established.")
        return

    try:
        acc_no = int(input("Enter Account No: "))
        pin = input("Enter PIN: ")

        query = "DELETE FROM customers WHERE account_no = %s AND pin = %s"
        cursor.execute(query, (acc_no, pin))
        conn.commit()

        if cursor.rowcount > 0:
            print("Account closed successfully.")
        else:
            print("Invalid account or PIN.")
    except ValueError:
        print("Invalid input. Account number must be a number.")
    except mysql.connector.Error as err:
        print(f"Error during closing account: {err}")


if __name__ == "__main__":
    if connect_db():
        main_menu()
        close_db()
    else:
        print("Application cannot run without a database connection.")
