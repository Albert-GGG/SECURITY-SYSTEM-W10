import sqlite3
from datetime import date

# CREATE TABLE AND ADD A NEW REGISTER:

# Create a table (execute a single time)
def crearT():
    db = sqlite3.connect('DB_REGISTERS.db')
    with db:
        cursor = db.cursor()
        sql1 = '''CREATE TABLE IF NOT EXISTS registros(Num_dia INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL, config TEXT NOT NULL, con_epp INTEGER NOT NULL, sin_epp INTEGER NOT NULL)'''
        cursor.execute(sql1)
        db.commit()

    db.close()

# Insert a single register of initialization
def INS_REG():

    today = date.today()
    d1 = today.strftime("%d/%m/%Y")
    
    db = sqlite3.connect('DB_REGISTERS.db')

    with db:
        cursor = db.cursor()
        
        sql2 = '''INSERT INTO registros(fecha, config, con_epp, sin_epp)
                   VALUES(?,?,?,?)'''
        cursor.execute(sql2,(d1, 'Ca', 1, 0))
      
        db.commit()

    db.close()

# Call functions
crearT()
INS_REG()
