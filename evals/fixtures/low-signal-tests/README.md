# Low-signal checkout tests

Run `python3 -m unittest discover -s tests -q` from this directory. The suite passes, but it builds its expected total from the same helper the implementation uses and never checks the quoted shipping charge against the amount paid. A two-item order with shipping therefore undercharges while the tests stay green. Audit the behavioral contract in `checkout.py` and the assertions in `tests/test_checkout.py`.

