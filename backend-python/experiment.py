import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import numpy as np
from scipy.optimize import curve_fit

from auth import get_current_user
from database import get_db

router = APIRouter(prefix="/api/experiment", tags=["experiment"])


# ── Models ──────────────────────────────────────────────

class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = None

class PlateCreate(BaseModel):
    experiment_id: int
    name: str
    rows: int = 8
    cols: int = 12

class WellData(BaseModel):
    row_index: int
    col_index: int
    compound_name: Optional[str] = None
    concentration: Optional[float] = None
    concentration_unit: str = "μM"
    batch: Optional[str] = None
    value: Optional[float] = None

class WellBatchUpdate(BaseModel):
    plate_id: int
    wells: List[WellData]


# ── 4PL Logistic Model ─────────────────────────────────

def logistic_4pl(x, a, b, c, d):
    """4-Parameter Logistic: y = d + (a - d) / (1 + (x / c)^b)
    a = bottom, b = hill slope, c = IC50, d = top
    """
    return d + (a - d) / (1.0 + (x / c) ** b)


# ── Experiment CRUD ─────────────────────────────────────

@router.get("/health")
def health():
    return {"status": "ok", "service": "experiment-python"}


@router.post("/experiments")
def create_experiment(data: ExperimentCreate, user=Depends(get_current_user), conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO experiments (name, description, created_by) VALUES (%s, %s, %s) RETURNING id, name, description, status, created_at",
        (data.name, data.description, user["id"]),
    )
    exp = cur.fetchone()
    conn.commit()
    return exp


@router.get("/experiments")
def list_experiments(user=Depends(get_current_user), conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("""
        SELECT e.*, u.username as creator_name,
               (SELECT count(*) FROM plates p WHERE p.experiment_id = e.id) as plate_count
        FROM experiments e
        LEFT JOIN users u ON e.created_by = u.id
        ORDER BY e.created_at DESC
    """)
    return cur.fetchall()


@router.delete("/experiments/{exp_id}")
def delete_experiment(exp_id: int, user=Depends(get_current_user), conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("DELETE FROM experiments WHERE id = %s", (exp_id,))
    conn.commit()
    return {"message": "已删除"}


# ── Plate CRUD ──────────────────────────────────────────

@router.post("/plates")
def create_plate(data: PlateCreate, user=Depends(get_current_user), conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO plates (experiment_id, name, rows, cols) VALUES (%s, %s, %s, %s) RETURNING *",
        (data.experiment_id, data.name, data.rows, data.cols),
    )
    plate = cur.fetchone()
    conn.commit()
    return plate


@router.get("/plates/{experiment_id}")
def list_plates(experiment_id: int, user=Depends(get_current_user), conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("""
        SELECT p.*,
               (SELECT count(*) FROM plate_wells w WHERE w.plate_id = p.id AND w.compound_name IS NOT NULL) as filled_wells
        FROM plates p WHERE p.experiment_id = %s ORDER BY p.created_at
    """, (experiment_id,))
    return cur.fetchall()


@router.delete("/plates/{plate_id}")
def delete_plate(plate_id: int, user=Depends(get_current_user), conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("DELETE FROM plates WHERE id = %s", (plate_id,))
    conn.commit()
    return {"message": "已删除"}


# ── Well Data ───────────────────────────────────────────

@router.get("/wells/{plate_id}")
def get_wells(plate_id: int, user=Depends(get_current_user), conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("SELECT rows, cols FROM plates WHERE id = %s", (plate_id,))
    plate = cur.fetchone()
    if not plate:
        raise HTTPException(status_code=404, detail="孔板不存在")

    cur.execute("SELECT * FROM plate_wells WHERE plate_id = %s ORDER BY row_index, col_index", (plate_id,))
    wells = cur.fetchall()
    return {"plate": plate, "wells": wells}


@router.post("/wells/batch")
def batch_update_wells(data: WellBatchUpdate, user=Depends(get_current_user), conn=Depends(get_db)):
    cur = conn.cursor()
    for w in data.wells:
        cur.execute("""
            INSERT INTO plate_wells (plate_id, row_index, col_index, compound_name, concentration, concentration_unit, batch, value)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (plate_id, row_index, col_index)
            DO UPDATE SET compound_name = EXCLUDED.compound_name,
                          concentration = EXCLUDED.concentration,
                          concentration_unit = EXCLUDED.concentration_unit,
                          batch = EXCLUDED.batch,
                          value = EXCLUDED.value
        """, (data.plate_id, w.row_index, w.col_index, w.compound_name, w.concentration, w.concentration_unit, w.batch, w.value))
    conn.commit()
    return {"message": f"已更新 {len(data.wells)} 个孔位"}


# ── Statistics ──────────────────────────────────────────

@router.get("/statistics/{plate_id}")
def get_statistics(plate_id: int, user=Depends(get_current_user), conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("""
        SELECT compound_name, concentration, concentration_unit, batch, value,
               row_index, col_index
        FROM plate_wells
        WHERE plate_id = %s AND compound_name IS NOT NULL AND value IS NOT NULL
        ORDER BY compound_name, concentration, batch
    """, (plate_id,))
    raw_data = cur.fetchall()

    cur.execute("""
        SELECT compound_name, concentration, concentration_unit,
               COUNT(*) as count,
               AVG(value) as avg_value,
               MAX(value) as max_value,
               MIN(value) as min_value,
               STDDEV(value) as std_value
        FROM plate_wells
        WHERE plate_id = %s AND compound_name IS NOT NULL AND value IS NOT NULL
        GROUP BY compound_name, concentration, concentration_unit
        ORDER BY compound_name, concentration
    """, (plate_id,))
    grouped = cur.fetchall()

    for row in grouped:
        for key in ("avg_value", "max_value", "min_value", "std_value", "concentration"):
            if row[key] is not None:
                row[key] = float(row[key])
        row["count"] = int(row["count"])

    for row in raw_data:
        if row["value"] is not None:
            row["value"] = float(row["value"])
        if row["concentration"] is not None:
            row["concentration"] = float(row["concentration"])

    return {"raw_data": raw_data, "grouped": grouped}


# ── Curve Fitting ───────────────────────────────────────

@router.get("/curve-fit/{plate_id}")
def curve_fit_endpoint(plate_id: int, user=Depends(get_current_user), conn=Depends(get_db)):
    cur = conn.cursor()
    cur.execute("""
        SELECT compound_name, concentration, AVG(value) as avg_value
        FROM plate_wells
        WHERE plate_id = %s AND compound_name IS NOT NULL
              AND value IS NOT NULL AND concentration IS NOT NULL AND concentration > 0
        GROUP BY compound_name, concentration
        ORDER BY compound_name, concentration
    """, (plate_id,))
    rows = cur.fetchall()

    compounds: dict = {}
    for r in rows:
        name = r["compound_name"]
        if name not in compounds:
            compounds[name] = {"concentrations": [], "values": []}
        compounds[name]["concentrations"].append(float(r["concentration"]))
        compounds[name]["values"].append(float(r["avg_value"]))

    results = []
    for name, data in compounds.items():
        conc = np.array(data["concentrations"])
        vals = np.array(data["values"])

        max_val = float(np.max(vals))
        min_val = float(np.min(vals))

        inhibition = ((max_val - vals) / max_val * 100) if max_val != 0 else vals * 0

        fit_result = {
            "compound": name,
            "data_points": [
                {"concentration": float(c), "value": float(v), "inhibition": float(inh)}
                for c, v, inh in zip(conc, vals, inhibition)
            ],
            "max_value": max_val,
            "min_value": min_val,
            "fit_success": False,
            "fit_params": None,
            "fit_curve": [],
            "ic50": None,
        }

        if len(conc) >= 4:
            try:
                p0 = [min_val, 1.0, float(np.median(conc)), max_val]
                bounds = ([0, 0.01, 1e-12, 0], [max_val * 2, 10, max(conc) * 10, max_val * 2])
                popt, pcov = curve_fit(logistic_4pl, conc, vals, p0=p0, bounds=bounds, maxfev=10000)
                a, b, c, d = popt

                x_fit = np.logspace(np.log10(min(conc) / 2), np.log10(max(conc) * 2), 100)
                y_fit = logistic_4pl(x_fit, *popt)
                inh_fit = (max_val - y_fit) / max_val * 100 if max_val != 0 else y_fit * 0

                r_squared = 1 - np.sum((vals - logistic_4pl(conc, *popt)) ** 2) / np.sum((vals - np.mean(vals)) ** 2)

                fit_result["fit_success"] = True
                fit_result["fit_params"] = {
                    "bottom": float(a),
                    "hill_slope": float(b),
                    "ic50": float(c),
                    "top": float(d),
                    "r_squared": float(r_squared),
                }
                fit_result["ic50"] = float(c)
                fit_result["fit_curve"] = [
                    {"concentration": float(x), "fitted_value": float(y), "inhibition": float(inh)}
                    for x, y, inh in zip(x_fit, y_fit, inh_fit)
                    if not (math.isnan(y) or math.isinf(y))
                ]
            except Exception as e:
                fit_result["fit_error"] = str(e)

        results.append(fit_result)

    return {"compounds": results}
