r"""
Standalone helper — run this any time you want a clean slate before
testing, so old failed/step-up attempts don't carry over and cause
an unexpected lockout during a fresh demo run.

Run it like this, from the F:\project-morpholock folder:

    python dashboard\reset_attempts.py

That's it — no other setup needed.
"""

from attempt_tracker import reset_attempts

reset_attempts("default_user")
print("Done — attempt counter reset for 'default_user'. You're clear to test again.")