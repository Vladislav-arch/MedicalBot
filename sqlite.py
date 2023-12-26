import sqlite3 as sq

from datetime import date
import re


async def db_start():
    global db, cur
    db = sq.connect('Workers.db')
    cur = db.cursor()

    cur.execute(
        'CREATE TABLE IF NOT EXISTS workers(id INTEGER PRIMARY KEY AUTOINCREMENT, registration_date varchar, '
        'name varchar, phone_num varchar(100))')
    db.commit()
    cur.execute(
        'CREATE TABLE IF NOT EXISTS examination(id INTEGER PRIMARY KEY AUTOINCREMENT, date_of_holding varchar, '
        'description varchar, scheduling_time varchar, every_day varchar)')
    db.commit()


async def get_ids():
    cur.execute('SELECT id FROM workers')
    ids = cur.fetchall()

    return ids


async def upload_data_to_db(state):
    async with state.proxy() as data:
        cur.execute(
            "INSERT INTO workers(registration_date, name, phone_num) VALUES(?, ?, ?)",
            (data['registration_date'], data['name'], data['phone_num']))
        db.commit()
        cur.execute(
            "INSERT INTO examination(date_of_holding, description, scheduling_time, every_day) VALUES(?, ?, ?, ?)",
            ('Не проведено', 'Не проведено', 'Не заплановано', False))
        db.commit()


async def download_all_data_for_examination(state, id):
    async with state.proxy() as data:
        cur.execute(f"UPDATE examination SET date_of_holding=?, description=? WHERE id=?",
                    (data['examination_date'], data['examination_res'], id))
        db.commit()


async def upload_data_to_examination(data, column, id):
    cur.execute(f"UPDATE examination SET {column}=? WHERE id=?", (data, id))
    db.commit()


async def upload_data_to_workers(data, column, id):
    cur.execute(f"UPDATE workers SET {column}=? WHERE id=?", (data, id))
    db.commit()


async def get_examination_data(id):
    cur.execute(f"SELECT * FROM examination WHERE id=?", (id,))
    examination = cur.fetchone()

    return examination


async def get_workers_data(id):
    cur.execute(f"SELECT * FROM workers WHERE id=?", (id,))
    workers = cur.fetchone()

    return workers


async def workers_switches(switches, id):
    cur.execute(f"SELECT * FROM workers WHERE id=?", (id,))
    workers = cur.fetchone()
    cur.execute(f"SELECT * FROM examination WHERE id=?", (id,))
    examination = cur.fetchone()

    if switches == 1:
        info = (
            f'<pre>Id:        {workers[0]}        {workers[1]}</pre>\n'
            f'\n'
            f'<pre>➡️Ім`я•      {workers[2]}</pre>\n'
            f'<pre>Телефон•   {workers[3]}</pre>\n'
            f'______________ _ _  _  _  _   _     _  \n'
            f'<pre>Обстеження\n  Проведено: {examination[1]}\n  Опис: {examination[2]}\n\n  Заплановано:{examination[3]}</pre>'

        )

    if switches == 2:
        info = (
            f'<pre>Id:        {workers[0]}        {workers[1]}</pre>\n'
            f'\n'
            f'<pre>Ім`я•      {workers[2]}</pre>\n'
            f'<pre>➡️Телефон•   {workers[3]}</pre>\n'
            f'______________ _ _  _  _  _   _     _  \n'
            f'<pre>Обстеження\n  Проведено: {examination[1]}\n  Опис: {examination[2]}\n\n  Заплановано:{examination[3]}</pre>'

        )

    return info


async def get_profile(id):
    cur.execute(f"SELECT * FROM workers WHERE id=?", (id,))
    workers = cur.fetchone()
    cur.execute(f"SELECT * FROM examination WHERE id=?", (id,))
    examination = cur.fetchone()

    info = (
        f'<pre>Id:        {workers[0]}        {workers[1]}</pre>\n'
        f'\n'
        f'<pre>Ім`я•      {workers[2]}</pre>\n'
        f'<pre>Телефон•   {workers[3]}</pre>\n'
        f'______________ _ _  _  _  _   _     _  \n'
        f'<pre>Обстеження\n  Проведено: {examination[1]}\n  Опис: {examination[2]}\n\n  Заплановано:{examination[3]}</pre>'

    )
    return info


async def delete_table_row(id):
    delete_workers = f'DELETE FROM workers WHERE id = {id};'
    delete_examination = f'DELETE FROM examination WHERE id = {id};'
    cur.execute(delete_workers)
    db.commit()
    cur.execute(delete_examination)
    db.commit()
