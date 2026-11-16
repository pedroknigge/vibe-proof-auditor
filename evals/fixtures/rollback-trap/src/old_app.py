def get_customer(connection, customer_id):
    return connection.execute(
        "SELECT full_name FROM customers WHERE id = ?", (customer_id,)
    ).fetchone()[0]
