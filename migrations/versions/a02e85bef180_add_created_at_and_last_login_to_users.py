"""add created_at and last_login to users

Revision ID: a02e85bef180
Revises: 950f9bcff86c
Create Date: 2025-08-16 10:54:30.646351

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import func


# revision identifiers, used by Alembic.
revision = 'a02e85bef180'
down_revision = '950f9bcff86c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        # created_at con valor por defecto actual
        batch_op.add_column(
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now())
        )
        # last_login puede ser NULL
        batch_op.add_column(
            sa.Column('last_login', sa.DateTime(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('last_login')
        batch_op.drop_column('created_at')
