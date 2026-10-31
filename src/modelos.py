"""Mapeo declarativo exclusivo SQLAlchemy 2.x."""
from sqlalchemy import Float, Integer, String, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ClienteChurn(Base):
    __tablename__ = 'clientes_churn'
    __table_args__ = (
        CheckConstraint('churn IN (0, 1)', name='ck_churn_binario'),
        CheckConstraint('tenure >= 0', name='ck_tenure_no_negativo'),
        CheckConstraint('monthly_charges >= 0', name='ck_cargos_no_negativos'),
    )

    customer_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    senior_citizen: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tenure: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_charges: Mapped[float] = mapped_column(Float, nullable=False)
    total_charges: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_monthly_paid: Mapped[float | None] = mapped_column(Float, nullable=True)
    contract: Mapped[str] = mapped_column(String(80), nullable=False)
    internet_service: Mapped[str] = mapped_column(String(80), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(120), nullable=False)
    tech_support: Mapped[str] = mapped_column(String(80), nullable=False)
    paperless_billing: Mapped[str] = mapped_column(String(30), nullable=False)
    online_security: Mapped[str] = mapped_column(String(80), nullable=False)
    churn: Mapped[int] = mapped_column(Integer, nullable=False)
