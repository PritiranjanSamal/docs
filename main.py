from fastmcp import FastMCP
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP("ExpenseTracker")

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                day_part TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)

init_db()

def get_day_part(hour):
    '''Determine day part based on hour.'''
    if 0 <= hour < 6:
        return "Night"
    elif 6 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 18:
        return "Afternoon"
    else:
        return "Evening"

# @mcp.tool()
# def add_expense(date, amount, category, subcategory="", note=""):
#     '''Add a new expense entry to the database.'''
#     with sqlite3.connect(DB_PATH) as c:
#         cur = c.execute(
#             "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
#             (date, amount, category, subcategory, note)
#         )
#         return {"status": "ok", "id": cur.lastrowid}
    
@mcp.tool()
def add_expense(amount, category, subcategory="", note=""):
    '''Add a new expense entry to the database.'''
    current_dt = datetime.now()
    expense_date = current_dt.strftime("%Y-%m-%d")
    expense_time = current_dt.strftime("%H:%M:%S")
    day_part = get_day_part(current_dt.hour)
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """INSERT INTO expenses(date, time, day_part, amount, category, subcategory, note)
            VALUES (?,?,?,?,?,?,?)
            """,
            (expense_date, expense_time, day_part, amount, category, subcategory, note)
        )

        return {"status": "ok", "id": cur.lastrowid, "date": expense_date, "time": expense_time, "day_part": day_part}

@mcp.tool()
def list_expenses(start_date, end_date):
    '''List expense entries within an inclusive date range.'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """,
            (start_date, end_date)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

# @mcp.tool()
# def modify_expense(expense_id, date=None, amount=None, category=None, subcategory=None, note=None):
#     '''Modify an existing expense entry.'''
#     with sqlite3.connect(DB_PATH) as c:
#         cur = c.execute(
#             "SELECT id FROM expenses WHERE id = ?",
#             (expense_id,)
#         )

#         if not cur.fetchone():
#             return {
#                 "status": "error",
#                 "message": f"Expense ID {expense_id} not found"
#             }

#         updates = []
#         params = []

#         if date is not None:
#             updates.append("date = ?")
#             params.append(date)

#         if amount is not None:
#             updates.append("amount = ?")
#             params.append(amount)

#         if category is not None:
#             updates.append("category = ?")
#             params.append(category)

#         if subcategory is not None:
#             updates.append("subcategory = ?")
#             params.append(subcategory)

#         if note is not None:
#             updates.append("note = ?")
#             params.append(note)

#         if not updates:
#             return {
#                 "status": "error",
#                 "message": "No fields provided for update"
#             }

#         params.append(expense_id)

#         query = f"""
#             UPDATE expenses
#             SET {', '.join(updates)}
#             WHERE id = ?
#         """

#         c.execute(query, params)

#         return {
#             "status": "ok",
#             "id": expense_id
#         }

@mcp.tool()
def modify_expense(date, day_part, time=None, new_amount=None, new_category=None, new_subcategory=None, new_note=None):
    '''Modify an existing expense entry using date, day_part and optionally exact time.'''
    with sqlite3.connect(DB_PATH) as c:
        query = """SELECT id FROM expenses WHERE date = ? AND day_part = ?"""

        params = [date, day_part]

        if time:
            query += " AND time = ?"
            params.append(time)

        cur = c.execute(query, params)

        matches = cur.fetchall()

        if not matches:
            return {
                "status": "error",
                "message": "No matching expense found"
            }

        if len(matches) > 1:
            return {
                "status": "error",
                "message": (
                    f"{len(matches)} expenses found. "
                    "Please provide exact time."
                )
            }

        expense_id = matches[0][0]

        updates = []
        update_params = []

        if new_amount is not None:
            updates.append("amount = ?")
            update_params.append(new_amount)

        if new_category is not None:
            updates.append("category = ?")
            update_params.append(new_category)

        if new_subcategory is not None:
            updates.append("subcategory = ?")
            update_params.append(new_subcategory)

        if new_note is not None:
            updates.append("note = ?")
            update_params.append(new_note)

        if not updates:
            return {
                "status": "error",
                "message": "No fields provided for update"
            }

        update_params.append(expense_id)

        c.execute(
            f"""
            UPDATE expenses
            SET {', '.join(updates)}
            WHERE id = ?
            """,
            update_params
        )

        return {
            "status": "ok",
            "message": "Expense updated successfully"
        }

# @mcp.tool()
# def delete_expense(expense_id):
#     '''Delete an expense entry by ID.'''

#     with sqlite3.connect(DB_PATH) as c:

#         cur = c.execute(
#             "SELECT id FROM expenses WHERE id = ?",
#             (expense_id,)
#         )

#         if not cur.fetchone():
#             return {
#                 "status": "error",
#                 "message": f"Expense ID {expense_id} not found"
#             }

#         c.execute(
#             "DELETE FROM expenses WHERE id = ?",
#             (expense_id,)
#         )

#         return {
#             "status": "ok",
#             "deleted_id": expense_id
#         }

@mcp.tool()
def delete_expense(date, day_part, time=None):
    '''Delete an expense entry using date, day_part and optionally exact time.'''

    with sqlite3.connect(DB_PATH) as c:

        query = """SELECT id FROM expenses WHERE date = ? AND day_part = ?"""

        params = [date, day_part]

        if time:
            query += " AND time = ?"
            params.append(time)

        cur = c.execute(query, params)

        matches = cur.fetchall()

        if not matches:
            return {
                "status": "error",
                "message": "No matching expense found"
            }

        if len(matches) > 1:
            return {
                "status": "error",
                "message": (
                    f"{len(matches)} expenses found. "
                    "Please provide exact time."
                )
            }

        expense_id = matches[0][0]

        c.execute(
            "DELETE FROM expenses WHERE id = ?",
            (expense_id,)
        )

        return {
            "status": "ok",
            "message": "Expense deleted successfully"
        }

@mcp.tool()
def summarize(start_date, end_date, category=None):
    '''Summarize expenses by category within an inclusive date range.'''
    with sqlite3.connect(DB_PATH) as c:
        query = (
            """
            SELECT category, SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
            """
        )
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY category ASC"

        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    # Read fresh each time so you can edit the file without restarting
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    mcp.run()
