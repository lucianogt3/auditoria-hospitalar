"""Adiciona campo data_registro manualmente

Revision ID: 34945db0c0e9
Revises: 2953ad2a241e
Create Date: 2025-05-21 04:51:38.634937

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '34945db0c0e9'
down_revision = '2953ad2a241e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('auditoria') as batch_op:
        batch_op.add_column(
            sa.Column('data_registro', sa.DateTime(), server_default=sa.text("now()")),
        )

def downgrade():
    with op.batch_alter_table('auditoria') as batch_op:
        batch_op.drop_column('data_registro')