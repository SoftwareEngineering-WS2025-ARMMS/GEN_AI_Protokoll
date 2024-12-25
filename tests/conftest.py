import pytest
import random
from datetime import date

@pytest.fixture
def generate_protocol_mock():
    r = random.Random()
    mock_id = r.randint(1, 10000)
    return lambda :\
        {'title' : f"Protocol number {mock_id}",
            'date': date(r.randint(2000, 2024), r.randint(1, 12), r.randint(1, 28)),
            'place': f"Room number {mock_id}",
            'numberOfAttendees': len(bin(mock_id)),
            'agendaItems': [
                {"title": f"Title N°{i}",
                 "explanation": f"Some explanation of the title {i} should be here."}
            for i in range(random.randint(1, 7))]}