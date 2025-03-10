"""Add created_at to Customer model

Revision ID: 73e188c3df01
Revises: 
Create Date: 2025-03-09 22:17:04.741764

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '73e188c3df01'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.alter_column('phone',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
        batch_op.alter_column('address',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=255),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.alter_column('address',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=200),
               nullable=False)
        batch_op.alter_column('phone',
               existing_type=sa.VARCHAR(length=20),
               nullable=False)

    # ### end Alembic commands ###
