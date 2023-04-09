import sqlite3
from datetime import datetime, timedelta

from person import Person


class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.create_table_if_needed()

    def create_table_if_needed(self):
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "CREATE TABLE IF NOT EXISTS people (id INTEGER PRIMARY KEY, name TEXT, birthday DATE)"
                )
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")

    def insert_person(self, name, birthday):
        if not all([name, birthday]):
            raise ValueError("Name and birthday must be provided.")
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO people (name, birthday) VALUES (?, ?)",
                (name, datetime.strptime(birthday, '%d-%m-%Y').date())
            )
            conn.commit()

    def get_people(self) -> list[Person]:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM people")
            rows = cursor.fetchall()
            people_list = [Person(row[1], row[2], row[0]) for row in rows]
            cursor.close()
            return people_list

    def get_person(self, person_id) -> Person | None:
        if not person_id:
            raise ValueError("Person ID must be provided.")
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM people WHERE id = ?",
                (person_id,)
            )

            person_data = cursor.fetchone()  # fetches the first row of the result
            if not person_data:
                return None

            return Person(person_data[1], person_data[2], person_data[0])

    def delete_person(self, person_id) -> Person:
        if not person_id:
            raise ValueError("Person ID must be provided.")
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM people WHERE id = ?",
                (person_id,)
            )

            conn.commit()

    def get_upcoming_birthdays(self) -> list[Person]:
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            today = datetime.today().strftime('%Y-%m-%d')
            tomorrow = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
            cursor.execute(
                "SELECT name, birthday FROM people WHERE birthday IN (?, ?)", (today, tomorrow)
            )
            rows = cursor.fetchall()
            people_list = [Person(row[0], row[1], row[0]) for row in rows]
            cursor.close()
            return people_list
