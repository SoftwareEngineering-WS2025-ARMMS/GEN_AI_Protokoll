import psycopg2


class DataBaseConnection:
    def __init__(
        self, db_name: str, user_name: str, password: str, host: str, port: int
    ):
        self._DB_CONFIG = {
            "dbname": db_name,
            "user": user_name,
            "password": password,
            "host": host,
            "port": port,
        }
        # Establish the connection
        self.connection = psycopg2.connect(**self._DB_CONFIG)
        self.connection.autocommit = True
        self.initialize_tables()

    def __del__(self):
        try:
            self.connection.close()
        except Exception:
            pass

    def drop_db(self):
        cursor = self.connection.cursor()
        query = (
            "DROP TABLE IF EXISTS agendaitem; " "DROP TABLE IF EXISTS protocolmetadata"
        )
        cursor.execute(query)
        cursor.close()

    def initialize_tables(self):
        query = """
        CREATE TABLE IF NOT EXISTS ProtocolMetadata(
        id bigint generated always as IDENTITY primary key, 
        user_id varchar(100) not null, 
        title varchar(100), date date, 
        place varchar(100), 
        numberOfAttendees int);
        CREATE TABLE IF NOT EXISTS AgendaItem(
        id int not null references ProtocolMetadata on delete cascade, 
        title varchar(100), 
        explanation varchar(10000));
        """
        cursor = self.connection.cursor()
        cursor.execute(query)
        cursor.close()

    def close(self):
        del self

    def save_protocol(self, protocol: dict, user_id: str) -> bool:
        try:
            assert {
                "title",
                "date",
                "place",
                "numberOfAttendees",
                "agendaItems",
            } == set(protocol.keys())
            cursor = self.connection.cursor()
            query_1 = (
                "INSERT INTO ProtocolMetadata "
                "(title, date, place, user_id, numberOfAttendees) "
                "VALUES (%s, %s, %s, %s, %s)"
            )
            cursor.execute(
                query_1,
                vars=(
                    protocol["title"],
                    protocol["date"],
                    protocol["place"],
                    user_id,
                    protocol["numberOfAttendees"],
                ),
            )
            cursor.close()
            cursor = self.connection.cursor()
            cursor.execute(
                """SELECT MAX(id) 
                FROM protocolmetadata 
                WHERE user_id= %s
                      AND title = %s 
                      AND place = %s 
                      AND numberOfAttendees = %s""",
                vars=(
                    user_id,
                    protocol["title"],
                    protocol["place"],
                    protocol["numberOfAttendees"],
                ),
            )
            protocol_id = cursor.fetchone()[0]
            cursor.close()
            n = len(protocol["agendaItems"])
            query_2 = (
                "INSERT INTO AgendaItem (id, title, explanation) "
                "VALUES (%s, %s, %s)" + ", (%s, %s, %s)" * (n - 1)
            )
            cursor = self.connection.cursor()
            parameters = list(
                sum(
                    [
                        (
                            protocol_id,
                            protocol["agendaItems"][i]["title"],
                            protocol["agendaItems"][i]["explanation"],
                        )
                        for i in range(n)
                    ],
                    (),
                )
            )
            parameters = tuple(parameters)
            cursor.execute(query_2, vars=parameters)
            cursor.close()
            return True
        except Exception as e:
            print(e)
            return False

    def get_protocol_by_id(self, protocol_id: int, user_id: str) -> dict:
        cursor = self.connection.cursor()
        query_1 = (
            "SELECT title, date, place, numberofattendees "
            "FROM ProtocolMetadata WHERE id = %s AND user_id = %s;"
        )
        cursor.execute(query_1, vars=(protocol_id, user_id))
        protocol_metadata = cursor.fetchone()
        if protocol_metadata is None:
            raise RuntimeError("Incorrect user or protocol not found")
        cursor.close()
        cursor = self.connection.cursor()
        query_2 = "SELECT title, explanation FROM agendaitem WHERE id = %s"
        cursor.execute(query_2, vars=(protocol_id,))
        protocol_items = cursor.fetchall()
        cursor.close()
        return {
            "title": protocol_metadata[0],
            "date": protocol_metadata[1],
            "place": protocol_metadata[2],
            "numberOfAttendees": protocol_metadata[3],
            "agendaItems": [
                {
                    "title": x[0],
                    "explanation": x[1],
                }
                for x in protocol_items
            ],
        }

    def get_protocol_summaries(self, user_id: str) -> list:
        cursor = self.connection.cursor()
        query_1 = """SELECT p.id, p.title, p.date, p.place, p.numberofattendees
        FROM ProtocolMetadata p
        WHERE user_id = %s;"""
        cursor.execute(query_1, vars=(user_id,))
        datas = cursor.fetchall()
        cursor.close()
        cursor = self.connection.cursor()
        query_2 = (
            "SELECT p.id, a.title "
            "FROM protocolmetadata p, agendaitem a "
            "WHERE user_id = %s AND p.id = a.id;"
        )
        cursor.execute(query_2, vars=(user_id,))
        items = cursor.fetchall()
        cursor.close()
        return [
            {
                "id": d[0],
                "title": d[1],
                "date": d[2],
                "place": d[3],
                "numberOfAttendees": d[4],
                "agendaItems": [item[1] for item in items if item[0] == d[0]],
            }
            for d in datas
        ]

    def remove_protocol(self, protocol_id, user_id) -> None:
        cursor = self.connection.cursor()
        query = "DELETE FROM ProtocolMetadata WHERE id = %s AND user_id = %s;"
        cursor.execute(query, (protocol_id, user_id))
        cursor.close()


if __name__ == "__main__":
    db = DataBaseConnection(
        "protocols", "protocol_server", "server-pwd", "localhost", 5800
    )
    """
    db.initialize_tables()
    protocol = {'title': 'Title',
                'date': '01.01.2001',
                'place': 'Place',
                'numberOfAttendees': 10,
                'agendaItems': [
                    {'title': 'Title_1', 'explanation': 'Explanation_1'},
                    {'title': 'Title_2', 'explanation': 'Explanation_2'},
                    {'title': 'Title_3', 'explanation': 'Explanation_3'},
                    {'title': 'Title_4', 'explanation': 'Explanation_4'},
                ]}

    x= db.save_protocol(protocol, user_id='abcdefghijklmnop')
    print(x)
    """
    db.remove_protocol(3, "abcdefghijklmnop")
