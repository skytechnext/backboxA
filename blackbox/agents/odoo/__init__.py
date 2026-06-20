"""Odoo ERP pipeline agents (stages 0–9)."""
from .foundation import ConnectReset, InstallModules, CompanyFinance
from .master_data import MasterData
from .products import ProductsRooms, PosBooking
from .transactions import TransactionsDraft, ConfirmInvoicePay
from .automation import Automations
from .qa import FinalQA


def pipeline():
    """Ordered ERP pipeline."""
    return [
        ConnectReset(), InstallModules(), CompanyFinance(),
        MasterData(),
        ProductsRooms(), PosBooking(),
        TransactionsDraft(), ConfirmInvoicePay(),
        Automations(),
        FinalQA(),
    ]
