"""ERP stage 3: master data (partners, employees, departments, dive sites, resources)."""
from __future__ import annotations

from ..base import EntityStage


class MasterData(EntityStage):
    stage_id = "3"
    order = 3
    title = "Master data"
    stage_num = 3
