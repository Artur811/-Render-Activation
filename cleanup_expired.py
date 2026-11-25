"""Delete licenses two days after their access expiration.

Run hourly on Render using: python cleanup_expired.py
Expired licenses remain visible/available for 48 hours after expires_at.
Lifetime and legacy licenses have expires_at=NULL and are never deleted here.
"""
from app import connect, ensure_schema


def main():
    with connect() as connection:
        ensure_schema(connection)
        deleted = connection.execute(
            """
            DELETE FROM licenses
            WHERE expires_at IS NOT NULL
              AND expires_at <= NOW() - INTERVAL '2 days'
            RETURNING id
            """
        ).fetchall()
        print(f"Deleted {len(deleted)} license(s) expired for at least 48 hours.")


if __name__ == "__main__":
    main()
