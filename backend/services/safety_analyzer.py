"""
Safety analyzer: mengubah hasil deteksi YOLO menjadi status kepatuhan PPE.

Logic ini TERPISAH dari detector.py agar:
- mudah di-unit test tanpa model YOLO
- mudah dikembangkan (person-to-PPE association, per-region, dst.)
- mudah diganti tanpa menyentuh inference layer
"""

from dataclasses import asdict, dataclass
from typing import Any

# Class names sesuai mapping model best.pt
PERSON = "person"
HELMET = "helmet"
NO_HELMET = "no-helmet"
VEST = "vest"
NO_VEST = "no-vest"

# Status keseluruhan
STATUS_COMPLIANT = "Compliant"
STATUS_VIOLATION = "Violation"
STATUS_UNKNOWN = "Unknown"


@dataclass
class SafetyResult:
    total_person: int
    compliant_count: int
    violation_count: int
    compliance_rate: float
    overall_status: str
    violation_types: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _count_classes(detections: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for det in detections:
        name = det.get("class_name")
        if not name:
            continue
        counts[name] = counts.get(name, 0) + 1
    return counts


def analyze(detections: list[dict[str, Any]]) -> SafetyResult:
    """
    Analisis kepatuhan PPE berdasarkan hasil deteksi YOLO.

    MVP logic (sederhana & transparan):
    - total_person      = jumlah deteksi class 'person'
    - violation_types   = jenis pelanggaran yang muncul ('no-helmet', 'no-vest')
    - violation_signals = jumlah deteksi no-helmet + no-vest
    - violation_count   = min(violation_signals, total_person)
                          (supaya tidak melebihi jumlah pekerja yang terdeteksi)
    - compliant_count   = total_person - violation_count
    - compliance_rate   = compliant_count / total_person * 100

    Limitation (jujur, sesuai spesifikasi):
    Model ini tidak melakukan person-to-PPE association yang kompleks,
    sehingga penghitungan mengasumsikan 1 sinyal pelanggaran ≈ 1 pekerja melanggar.
    Ini cukup untuk MVP dan akan dikembangkan di iterasi berikutnya.
    """
    counts = _count_classes(detections)

    total_person = counts.get(PERSON, 0)
    no_helmet = counts.get(NO_HELMET, 0)
    no_vest = counts.get(NO_VEST, 0)

    violation_types: list[str] = []
    if no_helmet > 0:
        violation_types.append(NO_HELMET)
    if no_vest > 0:
        violation_types.append(NO_VEST)

    violation_signals = no_helmet + no_vest

    # Tidak ada pekerja terdeteksi → status tidak diketahui
    if total_person == 0:
        return SafetyResult(
            total_person=0,
            compliant_count=0,
            violation_count=0,
            compliance_rate=0.0,
            overall_status=STATUS_UNKNOWN,
            violation_types=violation_types,
        )

    violation_count = min(violation_signals, total_person)
    compliant_count = max(0, total_person - violation_count)
    compliance_rate = round((compliant_count / total_person) * 100, 2)

    overall_status = STATUS_VIOLATION if violation_count > 0 else STATUS_COMPLIANT

    return SafetyResult(
        total_person=total_person,
        compliant_count=compliant_count,
        violation_count=violation_count,
        compliance_rate=compliance_rate,
        overall_status=overall_status,
        violation_types=violation_types,
    )