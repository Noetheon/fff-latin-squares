#!/usr/bin/env python3
"""Check fixed-family binary minors using only this paper package and stdlib."""
import argparse
import hashlib
from itertools import permutations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
DATA = HERE / "evidence/data"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def table_hash(table):
    return hashlib.sha256(bytes(x for row in table for x in row)).hexdigest()


def validate_latin(table):
    n = len(table)
    require(n > 0 and all(len(row) == n for row in table), "non-square input")
    require(all(type(x) is int for row in table for x in row), "noninteger symbol")
    require(all(sorted(row) == list(range(n)) for row in table), "non-Latin row")
    require(all(sorted(col) == list(range(n)) for col in zip(*table)), "non-Latin column")


def cycles(permutation):
    require(sorted(permutation) == list(range(len(permutation))), "invalid permutation")
    unseen, result = set(range(len(permutation))), []
    while unseen:
        node, cycle = min(unseen), []
        while node in unseen:
            unseen.remove(node)
            cycle.append(node)
            node = permutation[node]
        require(node == cycle[0], "cycle did not close")
        result.append(cycle)
    return result


def tables():
    base = read(DATA / "steiner20.json")
    if isinstance(base, dict):
        base = base.get("table", base.get("square"))
    validate_latin(base)
    inverse = {value: c for c, value in enumerate(base[1])}
    components = cycles([inverse[value] for value in base[0]])
    require(len(base) == 20 and len(components) == 10 and
            all(len(cycle) == 2 for cycle in components), "incorrect trade family")
    for mask in range(1024):
        table = [row[:] for row in base]
        for bit, component in enumerate(components):
            if mask & (1 << bit):
                for c in component:
                    table[0][c], table[1][c] = table[1][c], table[0][c]
        yield mask, table
    candidates = read(DATA / "quadratic_sources.json")["quadratic_f19"]["fff_candidates"]
    for a in (2, 8):
        selected = [item["table"] for item in candidates if item["coefficients"] == [a, a]]
        require(len(selected) == 1, "missing or ambiguous quadratic control")
        yield f"Q19_{a}", selected[0]


def minor_rows(n):
    return list(range(2*n-1)) + list(range(2*n, 3*n-1))


def verify_minor(table, cells):
    """Explicit matrix elimination; no certificate producer or search result used."""
    validate_latin(table)
    n = len(table)
    rows = minor_rows(n)
    size = 3*n-2
    require(len(cells) == size, "wrong minor size")
    require(all(type(cell) is int and 0 <= cell < n*n for cell in cells), "invalid cell")
    require(len(set(cells)) == size, "duplicate cells")
    matrix = []
    for cell in cells:
        r, c = divmod(cell, n)
        matrix.append([int(line in (r, n+c, 2*n+table[r][c])) for line in rows])
    for column in reversed(range(size)):
        pivot = next((r for r in range(column+1) if matrix[r][column]), None)
        require(pivot is not None, "singular minor")
        matrix[column], matrix[pivot] = matrix[pivot], matrix[column]
        for r in range(column):
            if matrix[r][column]:
                matrix[r] = [a ^ b for a, b in zip(matrix[r], matrix[column])]


def check_record(identity, table, record):
    require(record["id"] == identity, "wrong table identity")
    require(record["rank"] == 58, "wrong claimed rank")
    require(record["table_sha256_raw_bytes"] == table_hash(table), "table hash mismatch")
    verify_minor(table, record["cell_columns"])


def verify_coverage(payload):
    require(payload["minor_rows"] == minor_rows(20), "incorrect minor line set")
    expected = set(range(1024)) | {"Q19_2", "Q19_8"}
    records = payload["certificates"]
    require(len(records) == 1026 and {x["id"] for x in records} == expected,
            "duplicate or incomplete certificate coverage")
    return {item["id"]: item for item in records}


def reject(function, *args):
    try:
        function(*args)
    except ValueError:
        return
    raise ValueError("malformed certificate incorrectly accepted")


def verify_bundle():
    path = DATA / "frozen_order20_rank_certificates.json"
    payload = read(path)
    records = verify_coverage(payload)
    distinct = set()
    first_table = None
    for identity, table in tables():
        check_record(identity, table, records[identity])
        distinct.add(table_hash(table))
        if identity == 0:
            first_table = table
    require(len(distinct) == 1026, "duplicate table in fixed family")
    first = records[0]
    cells = first["cell_columns"]
    reject(verify_minor, first_table, cells[:-1])
    reject(verify_minor, first_table, [cells[0]]*58)
    reject(verify_minor, first_table, cells[:-1]+[400])
    reject(check_record, 0, first_table, {**first, "table_sha256_raw_bytes": "0"*64})
    reject(verify_coverage, {**payload, "certificates": payload["certificates"][:-1]})
    reject(verify_coverage, {**payload, "certificates": [first]*1026})
    cyclic20 = [[(r+c) % 20 for c in range(20)] for r in range(20)]
    require(all(((r+c) % 20) % 2 == (r % 2) ^ (c % 2)
                for r in range(20) for c in range(20)), "binary quotient control failed")
    reject(verify_minor, cyclic20, cells)
    return {"passed": True, "tables_checked": len(distinct), "rank": 58,
            "minor_shape": [58, 58], "negative_controls_rejected": 7,
            "certificate_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "C157_dependency": False, "scope": "Fixed 1026-table family only, not all FFF20."}


def field_mul(a, b, modulus=19):
    result = 0
    degree = modulus.bit_length()-1
    while b:
        if b & 1:
            result ^= a
        a <<= 1
        if a & (1 << degree):
            a ^= modulus
        b >>= 1
    return result


def scope_control(scan):
    payload = read(DATA / "m3_gf16_scope_control.json")
    r, t, q = 6, [0, 1, 2], 16
    powers = [1, r, field_mul(r, r)]
    require(field_mul(powers[2], r) == 1 and r != 1, "incorrect cube root")
    s = [field_mul(a, b) for a, b in zip(powers, t)]
    table = [[((i+j) % 3)*q + (a ^ field_mul(powers[i], b) ^ field_mul(s[i], powers[j]))
              for j in range(3) for b in range(q)] for i in range(3) for a in range(q)]
    require(payload["field_modulus"] == 19 and payload["s"] == s and
            payload["table"] == table, "scope-control input drift")
    result, _ = scan(table)
    require(result["fff"], "larger-field scope control is not FFF")
    derangements = [p for p in permutations(range(5)) if all(i != x for i, x in enumerate(p))]
    require(len(derangements) == 44 and all(any(len(c) % 2 for c in cycles(p))
                                          for p in derangements), "odd-block control failed")
    return {"order48": result, "five_point_derangements": 44,
            "purpose": "GF4 scope and elementary odd-block controls; not novelty evidence."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify_bundle()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
