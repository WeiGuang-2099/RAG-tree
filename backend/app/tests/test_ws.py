import asyncio
from app.ws.manager import ConnectionManager, manager


def test_manager_initial_state():
    m = ConnectionManager()
    assert len(m.active_connections) == 0


def test_manager_is_global():
    assert manager is not None
    assert isinstance(manager, ConnectionManager)


def test_manager_disconnect_nonexistent():
    m = ConnectionManager()
    m.disconnect("nonexistent")


def test_manager_send_personal_message_not_connected():
    m = ConnectionManager()
    asyncio.get_event_loop().run_until_complete(
        m.send_personal_message({"type": "test"}, "nonexistent")
    )


def test_manager_send_progress():
    m = ConnectionManager()
    asyncio.get_event_loop().run_until_complete(
        m.send_progress("client1", current=1, total=10, status="parsing", detail="main.py")
    )


def test_manager_send_graph_update():
    m = ConnectionManager()
    asyncio.get_event_loop().run_until_complete(
        m.send_graph_update("client1", nodes=[{"id": "1"}], edges=[{"source": "1", "target": "2"}])
    )


def test_manager_send_complete():
    m = ConnectionManager()
    asyncio.get_event_loop().run_until_complete(
        m.send_complete("client1", result={"message": "Done"})
    )


def test_manager_send_error():
    m = ConnectionManager()
    asyncio.get_event_loop().run_until_complete(
        m.send_error("client1", error="Something went wrong")
    )


def test_manager_send_ai_stream():
    m = ConnectionManager()
    asyncio.get_event_loop().run_until_complete(
        m.send_ai_stream("client1", chunk="Hello ")
    )


def test_manager_broadcast_no_connections():
    m = ConnectionManager()
    asyncio.get_event_loop().run_until_complete(
        m.broadcast({"type": "test"})
    )
