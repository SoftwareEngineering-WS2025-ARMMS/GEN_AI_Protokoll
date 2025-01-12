import pytest

from src.utils.DataBaseConnection import DataBaseConnection

db = None


@pytest.fixture(autouse=True)
def setup_and_teardown():
    global db
    db = DataBaseConnection(
        db_name="protocols_test",
        user_name="protocol_server",
        password="server_pwd",
        host="localhost",
        port=5800,
    )
    cursor = db.connection.cursor()
    cursor.execute("DELETE FROM agendaitem WHERE true")
    cursor.close()
    cursor = db.connection.cursor()
    cursor.execute("DELETE FROM protocolmetadata WHERE true")
    cursor.close()
    yield
    db.drop_db()
    db.close()


def test_initialize_tables():
    global db
    assert db.connection is not None
    cursor = db.connection.cursor()
    cursor.execute("SELECT * FROM agendaitem")
    assert cursor.fetchall() == []
    cursor.close()
    cursor = db.connection.cursor()
    cursor.execute("SELECT * FROM protocolmetadata")
    assert cursor.fetchall() == []
    cursor.close()


@pytest.mark.parametrize("n", [i for i in range(1, 10)])
def test_save_protocol_valid(generate_protocol_mock, n):
    global db
    items = 0
    for i in range(n):
        protocols = [generate_protocol_mock() for _ in range(10)]
        for protocol in protocols:
            assert db.save_protocol(protocol, f'User number {protocol["title"][16:]}')

        query = "SELECT * FROM protocolmetadata"
        cursor = db.connection.cursor()
        cursor.execute(query)
        assert len(cursor.fetchall()) == 10 * (i + 1)
        cursor.close()
        cursor = db.connection.cursor()
        cursor.execute("SELECT * FROM agendaitem")
        new_items = sum([len(protocol["agendaItems"]) for protocol in protocols])
        items += new_items
        assert len(cursor.fetchall()) == items
        cursor.close()


def test_save_protocol_invalid(generate_protocol_mock):
    global db
    keys = generate_protocol_mock().keys()
    for key in keys:
        protocol = generate_protocol_mock()
        protocol.pop(key)
        assert not db.save_protocol(protocol, "abcdefg")
    assert not db.save_protocol(generate_protocol_mock(), None)


def test_get_protocol_by_id_valid(generate_protocol_mock):
    global db
    protocol = generate_protocol_mock()
    db.save_protocol(protocol, "User ID must be here")
    cursor = db.connection.cursor()
    cursor.execute("SELECT * FROM protocolmetadata")
    protocol_id = cursor.fetchone()[0]
    cursor.close()
    assert db.get_protocol_by_id(protocol_id, "User ID must be here") == protocol


def test_get_protocol_by_id_invalid(generate_protocol_mock):
    global db
    protocol = generate_protocol_mock()
    db.save_protocol(protocol, "User ID must be here")
    cursor = db.connection.cursor()
    cursor.execute("SELECT * FROM protocolmetadata")
    protocol_id = cursor.fetchall()
    assert len(protocol_id) == 1
    protocol_id = protocol_id[0][0]
    cursor.close()
    with pytest.raises(Exception):
        db.get_protocol_by_id(protocol_id, "User ID must be her")
    cursor = db.connection.cursor()
    cursor.execute("SELECT * FROM protocolmetadata")
    protocol_id = cursor.fetchall()
    assert len(protocol_id) == 1
    with pytest.raises(Exception):
        db.get_protocol_by_id(protocol_id + 1, "User ID must be here")
    cursor = db.connection.cursor()
    cursor.execute("SELECT * FROM protocolmetadata")
    protocol_id = cursor.fetchall()
    assert len(protocol_id) == 1
