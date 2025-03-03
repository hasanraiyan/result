import sqlite3
from rich.console import Console
from rich.table import Table

def display_results():
    conn = sqlite3.connect("results.db")
    cursor = conn.cursor()

    # Fetch data sorted by CGPA (assuming SGPA column stores CGPA)
    cursor.execute("SELECT registration_no, student_name, sgpa FROM results ORDER BY sgpa DESC")
    rows = cursor.fetchall()
    
    conn.close()

    # Create a rich table
    console = Console()
    table = Table(title="Students in Information Technology Course (Sorted by CGPA)", show_lines=True)

    table.add_column("Index", style="cyan", justify="center")
    table.add_column("Registration No", style="green", justify="center")
    table.add_column("Name", style="magenta", justify="left")
    table.add_column("CGPA", style="yellow", justify="center")

    # Add rows to the table
    for index, (reg_no, name, cgpa) in enumerate(rows, start=1):
        table.add_row(str(index), reg_no, name, str(cgpa))

    console.print(table)

# Call the function
display_results()
