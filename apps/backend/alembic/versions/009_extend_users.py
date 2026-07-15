"""009 extend users — mfa, lockout, audit columns

Revision ID: 009
Revises: 008
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new role values to the enum (idempotent IF NOT EXISTS)
    op.execute("ALTER TYPE global_role ADD VALUE IF NOT EXISTS 'investigador'")
    op.execute("ALTER TYPE global_role ADD VALUE IF NOT EXISTS 'supervisor'")
    op.execute("ALTER TYPE global_role ADD VALUE IF NOT EXISTS 'advogado'")
    op.execute("ALTER TYPE global_role ADD VALUE IF NOT EXISTS 'consultor'")

    # Extend users table
    op.add_column("users", sa.Column("mfa_secret", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("mfa_enabled", sa.Boolean(), nullable=False,
                                      server_default=sa.text("FALSE")))
    op.add_column("users", sa.Column(
        "mfa_backup_codes",
        postgresql.JSONB(),
        nullable=False,
        server_default=sa.text("'[]'::jsonb"),
    ))
    op.add_column("users", sa.Column("failed_login_attempts", sa.Integer(), nullable=False,
                                      server_default=sa.text("0")))
    op.add_column("users", sa.Column("locked_until",
                                      sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("users", sa.Column("last_login_at",
                                      sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("users", sa.Column(
        "updated_at",
        sa.TIMESTAMP(timezone=True),
        nullable=False,
        server_default=sa.text("now()"),
    ))

    # Trigger: keep updated_at current (reuse the set_updated_at function from 008)
    op.execute("""
        CREATE TRIGGER users_set_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION set_updated_at();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS users_set_updated_at ON users")
    op.drop_column("users", "updated_at")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
    op.drop_column("users", "mfa_backup_codes")
    op.drop_column("users", "mfa_enabled")
    op.drop_column("users", "mfa_secret")
    # NOTE: enum values cannot be removed in PostgreSQL without recreating the type.
    # Downgrade leaves the new enum values in place.
