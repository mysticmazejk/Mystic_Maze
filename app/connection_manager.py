from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """
    Verwaltet die aktiven WebSocket-Verbindungen der Spieler.

    Pro Spiel und Spielerindex wird maximal eine aktive
    WebSocket-Verbindung gespeichert.
    """

    def __init__(self):
        # Struktur:
        #
        # game_id
        #   └── player_index
        #         └── WebSocket
        self.connections: dict[
            str,
            dict[int, WebSocket]
        ] = {}

    async def connect(
        self,
        game_id: str,
        player_index: int,
        websocket: WebSocket
    ) -> None:
        """
        Registriert eine neue WebSocket-Verbindung.

        Existiert für denselben Spieler bereits eine Verbindung,
        wird diese durch die neue Verbindung ersetzt.

        :param game_id: ID des Spiels.
        :param player_index: Index des Spielers.
        :param websocket: Neue WebSocket-Verbindung.
        """

        game_id = game_id.upper()

        await websocket.accept()

        if game_id not in self.connections:
            self.connections[game_id] = {}

        old_connection = self.connections[
            game_id
        ].get(player_index)

        # Beispielsweise bei einem Browser-Refresh kann bereits
        # eine alte Verbindung vorhanden sein.
        if old_connection is not None:
            try:
                await old_connection.close(
                    code=4000,
                    reason="Neue Verbindung geöffnet."
                )
            except Exception:
                pass

        self.connections[
            game_id
        ][player_index] = websocket

    def disconnect(
        self,
        game_id: str,
        player_index: int,
        websocket: WebSocket
    ) -> None:
        """
        Entfernt eine WebSocket-Verbindung.

        Die Verbindung wird nur entfernt, wenn sie noch die
        aktuell gespeicherte Verbindung dieses Spielers ist.

        :param game_id: ID des Spiels.
        :param player_index: Index des Spielers.
        :param websocket: Zu entfernende Verbindung.
        """

        game_id = game_id.upper()

        game_connections = self.connections.get(
            game_id
        )

        if game_connections is None:
            return

        current_connection = game_connections.get(
            player_index
        )

        # Wichtig bei Reconnects:
        # Eine alte Verbindung darf die inzwischen neue
        # Verbindung nicht aus dem Manager entfernen.
        if current_connection is websocket:
            del game_connections[player_index]

        # Leere Spieleinträge ebenfalls entfernen.
        if not game_connections:
            del self.connections[game_id]

    async def send_to_player(
        self,
        game_id: str,
        player_index: int,
        message: dict
    ) -> None:
        """
        Sendet eine Nachricht an einen bestimmten Spieler.

        :param game_id: ID des Spiels.
        :param player_index: Index des Spielers.
        :param message: Zu sendende JSON-Nachricht.
        """

        game_id = game_id.upper()

        connection = self.connections.get(
            game_id,
            {}
        ).get(player_index)

        if connection is None:
            return

        try:
            await connection.send_json(
                message
            )

        except WebSocketDisconnect:
            self.disconnect(
                game_id,
                player_index,
                connection
            )

    async def broadcast(
        self,
        game_id: str,
        message: dict
    ) -> None:
        """
        Sendet eine Nachricht an alle verbundenen Spieler
        eines Spiels.

        :param game_id: ID des Spiels.
        :param message: Zu sendende JSON-Nachricht.
        """

        game_id = game_id.upper()

        game_connections = self.connections.get(
            game_id,
            {}
        )

        # Kopie erstellen, da während des Sendens Verbindungen
        # entfernt werden können.
        connections = list(
            game_connections.items()
        )

        for player_index, connection in connections:
            try:
                await connection.send_json(
                    message
                )

            except WebSocketDisconnect:
                self.disconnect(
                    game_id,
                    player_index,
                    connection
                )