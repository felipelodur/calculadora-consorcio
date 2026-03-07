from dataclasses import dataclass, field


@dataclass
class ConsorcioParams:
    carta_credito: float
    num_months: int
    taxa_admin: float
    fundo_reserva: float
    seguro: float
    parcela_pos_contemplacao: float
    parcela_pre_contemplacao: float | None = None
    rendimento_fundo: float = 1.0
    reajuste_anual: float | None = None

    def get_installment(self, contemplated: bool) -> float:
        if not contemplated and self.parcela_pre_contemplacao is not None:
            return self.parcela_pre_contemplacao
        return self.parcela_pos_contemplacao


@dataclass
class SimulationResult:
    contemplation_month: int
    total_paid: float
    carta_credito_final: float
    consorcio_final_value: float
    investment_final_value: float
    net_cost: float
    opportunity_cost: float
    npv: float
    cet: float
    monthly_cashflows: list[float]


@dataclass
class SweepResult:
    results: list[SimulationResult]
    break_even_month: int | None
