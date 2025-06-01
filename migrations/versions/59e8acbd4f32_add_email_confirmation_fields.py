"""add email confirmation fields

Revision ID: 59e8acbd4f32
Revises: 8ce9c58b04ec
Create Date: 2025-05-17 13:43:48.860094
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '59e8acbd4f32'
down_revision = '8ce9c58b04ec'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        # Deixa email como opcional por enquanto para evitar erro em registros existentes
        batch_op.alter_column('email',
            existing_type=sa.String(length=150),
            nullable=True
        )
        batch_op.add_column(sa.Column('email_confirmed', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('confirmation_token', sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('email_confirmed')
        batch_op.drop_column('confirmation_token')
        batch_op.alter_column('email',
            existing_type=sa.String(length=150),
            nullable=True
        )
