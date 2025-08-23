def write_to_postgres_parallel(triggering_asset_events):
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    import logging, json

    pg = PostgresHook("pg01")

    # Ensure it's dict-like
    events = triggering_asset_events.get("candle_stick", []) \
        if isinstance(triggering_asset_events, dict) else triggering_asset_events

    for event in events:
        logging.info("Inserting candle event: %s", json.dumps(event))
        pg.run(
            """
            INSERT INTO candle_sticks (
                source, type, market, symbol, interval,
                event_time, open_time, close_time, is_closed,
                open, high, low, close, volume,
                quote_volume, trades,
                taker_buy_base, taker_buy_quote
            )
            VALUES (
                %(source)s, %(type)s, %(market)s, %(symbol)s, %(interval)s,
                %(event_time)s, %(open_time)s, %(close_time)s, %(is_closed)s,
                %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s,
                %(quote_volume)s, %(trades)s,
                %(taker_buy_base)s, %(taker_buy_quote)s
            )
            ON CONFLICT DO NOTHING;
            """,
            parameters=event,
        )

def write_to_postgres(data):
    import logging
    from airflow.sdk import Connection
    import psycopg2

    conn_uri = Connection.get("pg01").get_uri()
    conn = psycopg2.connect(conn_uri)
    cur = conn.cursor()

    rows = 0
    for asset, asset_list in data:
        for event in asset_list:   # <-- loop AssetEvents
            payload = (event.extra or {}).get("payload", {})
            candle_sticks = payload.get("candle_stick", [])
            for rec in candle_sticks:
                logging.info(f"Inserting {rec['symbol']} {rec['interval']} {rec['close_time']}")
                cur.execute(
                    """
                    INSERT INTO candle_sticks (
                        source, type, market, symbol, interval,
                        event_time, open_time, close_time, is_closed,
                        open, high, low, close, volume,
                        quote_volume, trades,
                        taker_buy_base, taker_buy_quote
                    )
                    VALUES (
                        %(source)s, %(type)s, %(market)s, %(symbol)s, %(interval)s,
                        %(event_time)s, %(open_time)s, %(close_time)s, %(is_closed)s,
                        %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s,
                        %(quote_volume)s, %(trades)s,
                        %(taker_buy_base)s, %(taker_buy_quote)s
                    )
                    ON CONFLICT DO NOTHING;
                    """,
                    rec,
                )
                rows += 1

    conn.commit()
    logging.info(f"Inserted {rows} rows into candle_sticks")
    cur.close()
    conn.close()

    return {
        "insert_rows" : rows,
    }