# -*- coding: utf-8 -*-
"""
Planejamento de Sistemas Elétricos — PDE Adaptada (refatorado)
Autor: ChatGPT (para Vitor)

Principais melhorias:
- Estrutura modular com dataclasses e tipagem
- Substitui cvxopt.modeling por cvxpy (mais moderno e legível)
- Funções claras: solve_stage(), build_cuts(), run_sdp(), dispatch()
- Suporte a N UHEs e N UTEs; múltiplos estágios e cenários
- Cálculo limpo de multiplicadores duais (CMO e "valor da água")
- Plot opcional da FCF (1 ou 2 UHEs)
- Comentários explicativos e checagens de consistência

Dependências: cvxpy, numpy, matplotlib
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import cvxpy as cp
import time
import math

# =============================
# Dados & Estruturas
# =============================

@dataclass
class HydroPlant:
    Nome: str
    Vmax: float
    Vmin: float
    Prod: float   # MWmed por hm^3
    Engol: float  # hm^3
    Afl: List[List[float]]  # [estágio][cenário]

@dataclass
class ThermalPlant:
    Nome: str
    Capac: float  # MWmed
    Custo: float  # $/MWmed

@dataclass
class GeneralData:
    CDef: float
    Carga: List[float]      # por estágio (0..Nr_Est-1)
    Nr_Disc: int
    Nr_Est: int
    Nr_Cen: int

@dataclass
class SystemData:
    DGer: GeneralData
    UHE: List[HydroPlant]
    UTE: List[ThermalPlant]


# =============================
# Utilidades
# =============================

def from_legacy_dict(sistema: Dict[str, Any]) -> SystemData:
    """Converte o dicionário legado para as dataclasses novas."""
    uhes = [HydroPlant(**d) for d in sistema["UHE"]]
    utes = [ThermalPlant(**d) for d in sistema["UTE"]]
    dg = GeneralData(**sistema["DGer"])
    # validações simples
    assert len(dg.Carga) == dg.Nr_Est, "Carga deve ter Nr_Est elementos"
    for u in uhes:
        assert len(u.Afl) == dg.Nr_Est, f"Afl da {u.Nome} deve ter Nr_Est linhas"
        for row in u.Afl:
            assert len(row) == dg.Nr_Cen, f"Cada linha de Afl deve ter Nr_Cen cenários"
    return SystemData(DGer=dg, UHE=uhes, UTE=utes)


def volume_from_percentages(uhe: List[HydroPlant], discretizacao_pct: Tuple[float, ...]) -> List[float]:
    """Converte uma discretização em % (0..100) para VI em hm^3 por UHE."""
    VI = []
    for i, u in enumerate(uhe):
        p = discretizacao_pct[i]
        VI.append(u.Vmin + (u.Vmax - u.Vmin) * (p/100.0))
    return VI


# =============================
# Modelo de 1 estágio (cvxpy)
# =============================

def solve_stage(
    system: SystemData,
    stage: int,                # 0-based
    VI: List[float],           # hm^3 por UHE
    AFL: List[float],          # hm^3 por UHE, para este estágio e cenário
    cuts: List[Dict[str, Any]] # lista de cortes (inequações) já construídos
) -> Dict[str, Any]:
    """
    Resolve o despacho hidrotérmico para um estágio fixo e uma realização de AFL.
    Retorna primal, custo, duais de balanço hídrico (valor d'água) e CMO.
    """
    nH = len(system.UHE)
    nT = len(system.UTE)

    # Variáveis de decisão
    vf = cp.Variable(nH, name="vf")  # volume final
    vt = cp.Variable(nH, name="vt")  # turbinado
    vv = cp.Variable(nH, name="vv")  # vertido
    gt = cp.Variable(nT, name="gt")  # térmicas
    deficit = cp.Variable(nonneg=True, name="deficit")
    alpha = cp.Variable(nonneg=True, name="alpha")

    # Objetivo: custo térmico + custo de déficit + penaliz. vertimento + custo futuro
    obj = 0
    for i, t in enumerate(system.UTE):
        obj += t.Custo * gt[i]
    obj += system.DGer.CDef * deficit
    obj += 0.01 * cp.sum(vv)
    obj += alpha

    constraints = []

    # Balanço hídrico por UHE (capturar duais)
    hydro_bal_duals = []
    for i, u in enumerate(system.UHE):
        c = (vf[i] == VI[i] + AFL[i] - vt[i] - vv[i])
        constraints.append(c)
        hydro_bal_duals.append(c)

    # Atendimento à demanda (CMO é o dual desta restrição)
    gen_h = cp.sum(cp.hstack([system.UHE[i].Prod * vt[i] for i in range(nH)]))
    gen_t = cp.sum(gt) if nT > 0 else 0
    cmo_constr = (gen_h + gen_t + deficit == system.DGer.Carga[stage])
    constraints.append(cmo_constr)

    # Limites físicos
    for i, u in enumerate(system.UHE):
        constraints += [
            u.Vmin <= vf[i], vf[i] <= u.Vmax,
            0 <= vt[i], vt[i] <= u.Engol,
            0 <= vv[i]
        ]
    for i, t in enumerate(system.UTE):
        constraints += [0 <= gt[i], gt[i] <= t.Capac]

    # Cortes (função de custo futuro do próximo estágio = stage+1)
    next_stage = stage + 1
    has_cuts = False
    for c in cuts:
        if int(c["Estagio"]) == next_stage:
            expr = sum(float(c["Coefs"][j]) * vf[j] for j in range(nH)) + float(c["Termo_Indep"])
            constraints.append(alpha >= expr)
            has_cuts = True
    if not has_cuts:
        # último estágio: custo futuro nulo
        constraints.append(alpha == 0)

    # Resolver (LP) — GLPK, ECOS ou CBC se disponível
    prob = cp.Problem(cp.Minimize(obj), constraints)
    # Tenta GLPK; se não houver, deixa default
    try:
        prob.solve(solver=cp.GLPK, glpk={'msg_lev': 'GLP_MSG_OFF'})
        if prob.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
            prob.solve()  # fallback
    except Exception:
        prob.solve()  # fallback

    if prob.status not in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
        raise RuntimeError(f"Problema não ótimo no estágio {stage}: status {prob.status}")

    # Extrair duais
    cmo = cmo_constr.dual_value  # CMO
    cma = [con.dual_value for con in hydro_bal_duals]  # valor da água por UHE

    res = {
        "objective": float(prob.value),
        "vf": vf.value.tolist(),
        "vt": vt.value.tolist(),
        "vv": vv.value.tolist(),
        "gt": gt.value.tolist() if nT > 0 else [],
        "deficit": float(deficit.value),
        "alpha": float(alpha.value),
        "CMO": float(cmo),
        "CMA": [float(x) for x in cma],
    }
    return res


# =============================
# Construção de cortes (backward)
# =============================

def build_discretizations(system: SystemData) -> List[Tuple[float, ...]]:
    nH = len(system.UHE)
    step = 100.0 / (system.DGer.Nr_Disc - 1)
    grid = np.arange(0.0, 100.0 + step/2, step)
    from itertools import product
    return list(product(*(grid for _ in range(nH))))


def run_sdp(
    system: SystemData,
    plot_fcf: bool = False,
    verbose: bool = False,
) -> Tuple[List[Dict[str, Any]], Dict[int, float]]:
    """
    Roda o backward para construir cortes para todos os estágios.
    Além dos cortes, calcula e retorna o CMO médio de cada estágio.

    Retorna:
        cuts: lista de cortes (inequações)
        cmo_por_estagio: dicionário {estagio: CMO médio}
    """
    nH = len(system.UHE)
    cuts: List[Dict[str, Any]] = []
    discretizacoes = build_discretizations(system)

    cmo_por_estagio: Dict[int, float] = {}

    t0 = time.time()
    # loop backward
    for s in range(system.DGer.Nr_Est - 1, -1, -1):
        if verbose:
            print(f"Estágio {s} (0-based)")

        # acumula CMO em todas as discretizações/cenários
        cmo_sum = 0.0
        ncen_total = len(discretizacoes) * system.DGer.Nr_Cen

        # variáveis auxiliares para plot
        if plot_fcf and nH == 1:
            xs, ys = [], []
        if plot_fcf and nH == 2:
            import matplotlib.pyplot as plt
            from matplotlib import cm
            step = 100.0 / (system.DGer.Nr_Disc - 1)
            grid = np.arange(0.0, 100.0 + step/2, step)
            U1, U2 = np.meshgrid(grid, grid)
            Z = np.zeros_like(U1)

        for disc in discretizacoes:
            VI = volume_from_percentages(system.UHE, disc)

            # médias
            cost_sum = 0.0
            cma_sum = np.zeros(nH)

            for k in range(system.DGer.Nr_Cen):
                AFL = [system.UHE[i].Afl[s][k] for i in range(nH)]
                sol = solve_stage(system, s, VI, AFL, cuts)

                cost_sum += sol["objective"]
                cma_sum += np.array(sol["CMA"])
                cmo_sum += sol["CMO"]  # acumula CMO

            # médias por discretização
            cost_avg = cost_sum / system.DGer.Nr_Cen
            cma_avg = cma_sum / system.DGer.Nr_Cen

            # corte
            a = (-cma_avg).tolist()
            b = float(cost_avg - np.dot(VI, a))
            cut = {"Estagio": s, "Coefs": a, "Termo_Indep": b}
            cuts.append(cut)

            # plot
            if plot_fcf and nH == 1:
                xs.append(VI[0])
                ys.append(cost_avg)
            if plot_fcf and nH == 2:
                i = int(round((disc[0]/100.0) * (system.DGer.Nr_Disc - 1)))
                j = int(round((disc[1]/100.0) * (system.DGer.Nr_Disc - 1)))
                Z[j, i] = cost_avg

        # calcula CMO médio do estágio
        cmo_por_estagio[s] = cmo_sum / ncen_total

        # plot
        if plot_fcf and nH == 1:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(6,4))
            plt.title(f"FCF — Estágio {s}")
            plt.plot(xs, ys, marker="o")
            plt.xlabel("Volume Inicial (hm³)")
            plt.ylabel("Custo total ($)")
            plt.grid(True, alpha=0.3)
            plt.show()

        if plot_fcf and nH == 2:
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
            from matplotlib import cm
            fig = plt.figure(figsize=(7,5))
            ax = fig.add_subplot(111, projection='3d')
            ax.plot_surface(U1, U2, Z, cmap=cm.coolwarm)
            ax.set_title(f"FCF — Estágio {s}")
            ax.set_xlabel("Vol. inicial UHE 1 (%)")
            ax.set_ylabel("Vol. inicial UHE 2 (%)")
            ax.set_zlabel("FCF ($)")
            plt.show()

    if verbose:
        print(f"Tempo total (backward): {time.time() - t0:.3f} s")

    return cuts, cmo_por_estagio



# =============================
# Despacho (estágio inicial)
# =============================

def dispatch(
    system: SystemData,
    VI: List[float],
    AFL: List[float],
    stage: int,
    cuts: List[Dict[str, Any]],
    printout: bool = True,
) -> Dict[str, Any]:
    sol = solve_stage(system, stage, VI, AFL, cuts)

    if printout:
        print("\n=== Resultado do despacho ===")
        print(f"Estágio: {stage}")
        print(f"Custo total: {sol['objective']:.4f} ($)")
        for i, u in enumerate(system.UHE):
            print(f"UHE {u.Nome}: vf={sol['vf'][i]:.3f} hm³, vt={sol['vt'][i]:.3f} hm³, vv={sol['vv'][i]:.3f} hm³, CMA={sol['CMA'][i]:.4f}")
        for i, t in enumerate(system.UTE):
            print(f"UTE {t.Nome}: gt={sol['gt'][i]:.3f} MWmed")
        print(f"Déficit: {sol['deficit']:.3f} MWmed")
        print(f"Alpha (custo futuro): {sol['alpha']:.4f}")
        print(f"CMO: {sol['CMO']:.4f}")
    return sol


# =============================
# Exemplo com os dados originais do usuário
# =============================
if __name__ == "__main__":
    # Dados originais
    lista_uhe = []
    lista_uhe.append({
        "Nome": "UHE DO MARCATO",
        "Vmax": 100.,
        "Vmin": 20.,
        "Prod": 0.95,
        "Engol": 60.,
        "Afl": [
            [23, 16],
            [19, 14],
            [15, 11]
        ]
    })

    # Para 2 UHEs, descomente e ajuste cargas/afluências
    # lista_uhe.append({
    #     "Nome": "UHE DO VASCAO",
    #     "Vmax": 200.,
    #     "Vmin": 40.,
    #     "Prod": 0.85,
    #     "Engol": 100.,
    #     "Afl": [
    #         [46, 32],
    #         [38, 28],
    #         [30, 22]
    #     ]
    # })

    lista_ute = []
    lista_ute.append({"Nome": "GT_1", "Capac": 15., "Custo": 10.})
    lista_ute.append({"Nome": "GT_2", "Capac": 10., "Custo": 25.})

    d_gerais = {
        "CDef": 500.,
        "Carga": [50., 50., 50.],
        "Nr_Disc": 12,
        "Nr_Est": 3,
        "Nr_Cen": 2,
    }

    sistema_legacy = {"DGer": d_gerais, "UHE": lista_uhe, "UTE": lista_ute}
    system = from_legacy_dict(sistema_legacy)

    # Backward: construir cortes
    cuts = run_sdp(system, plot_fcf=False, verbose=True)

    # Despacho no estágio inicial (0), com VI e AFL fornecidos
    # Exemplo do usuário: VI=[62], AFL=[16] para 1 UHE
    VI0 = [62.0] * len(system.UHE)
    AFL0 = [system.UHE[i].Afl[0][0] for i in range(len(system.UHE))]  # usa cenário 0 do estágio 0

    _ = dispatch(system, VI0, AFL0, stage=0, cuts=cuts, printout=True)
