"""Website pipeline agents (stages S0–S6)."""
from .ingest import Ingest
from .research import Research
from .architecture import Architecture
from .content import Content
from .assemble import Assemble
from .site_qa import SiteQA
from .deploy import Deploy


def pipeline():
    """Ordered website pipeline."""
    return [Ingest(), Research(), Architecture(), Content(), Assemble(), SiteQA(), Deploy()]
