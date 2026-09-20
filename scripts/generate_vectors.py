"""Author the money and uuid test vectors.

This is a *reference implementation*: exact integer arithmetic (Python integers have arbitrary
precision) that shares no code with any client. It computes the expected value of every case, so the
JSON files are not typed by hand. The JSON files are the contract; regenerate them only when
spec/money-and-ids.md changes, and cut a new tag when you do.

Usage: uv run python scripts/generate_vectors.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INT64_MIN = -(1 << 63)
INT64_MAX = (1 << 63) - 1
MAX = str(INT64_MAX)
MIN = str(INT64_MIN)


def money(amount, currency="INR", exponent=2):
    return {"amount_minor": str(amount), "currency": currency, "exponent": exponent}


def error(code):
    return {"error": code}


def in_range(value):
    return INT64_MIN <= value <= INT64_MAX


def valid_currency(code):
    return len(code) == 3 and all("A" <= ch <= "Z" for ch in code)


def mismatch(a, b):
    if a["currency"] != b["currency"]:
        return "currency_mismatch"
    if a["exponent"] != b["exponent"]:
        return "exponent_mismatch"
    return None


def amount(m):
    return int(m["amount_minor"])


def wrap(value, like):
    return money(value, like["currency"], like["exponent"]) if in_range(value) else error("overflow")


def ref_construct(m):
    if not valid_currency(m["currency"]):
        return error("invalid_currency")
    if not 0 <= m["exponent"] <= 18:
        return error("invalid_exponent")
    return m


def ref_add(a, b):
    return error(mismatch(a, b)) if mismatch(a, b) else wrap(amount(a) + amount(b), a)


def ref_subtract(a, b):
    return error(mismatch(a, b)) if mismatch(a, b) else wrap(amount(a) - amount(b), a)


def ref_negate(a):
    return wrap(-amount(a), a)


def ref_abs(a):
    return wrap(abs(amount(a)), a)


def ref_compare(a, b):
    if mismatch(a, b):
        return error(mismatch(a, b))
    x, y = amount(a), amount(b)
    return {"result": (x > y) - (x < y)}


def ref_convert(source, target, rate):
    if rate <= 0:
        return error("invalid_rate")
    numerator = amount(source) * rate * 10 ** target["exponent"]
    denominator = 10 ** source["exponent"] * 1_000_000
    quotient, remainder = divmod(abs(numerator), denominator)
    if 2 * remainder >= denominator:  # half away from zero
        quotient += 1
    value = quotient if numerator >= 0 else -quotient
    return wrap(value, {"currency": target["currency"], "exponent": target["exponent"]})


# ---- hand-checked anchors: if the reference is wrong, fail before writing anything -------------
assert ref_convert(money(100000), {"currency": "USD", "exponent": 2}, 11890) == money(1189, "USD")
assert ref_convert(money(1189, "USD"), {"currency": "INR", "exponent": 2}, 83_500_000) == money(99282)
assert ref_convert(money(5), {"currency": "USD", "exponent": 2}, 100_000) == money(1, "USD")
assert ref_convert(money(-5), {"currency": "USD", "exponent": 2}, 100_000) == money(-1, "USD")
assert ref_convert(money(25), {"currency": "USD", "exponent": 2}, 100_000) == money(3, "USD")
assert ref_convert(money(100000), {"currency": "JPY", "exponent": 0}, 1_750_000) == money(1750, "JPY", 0)
assert ref_convert(money(1000, "KWD", 3), {"currency": "INR", "exponent": 2}, 270_000_000) == money(27000)
assert ref_add(money(MAX), money(1)) == error("overflow")
assert ref_negate(money(MIN)) == error("overflow")


def suite(name, description, cases):
    return {
        "suite": name,
        "version": 1,
        "description": description,
        "cases": [{"name": n, "input": i, "expected": e} for n, i, e in cases],
    }


def op2(op, a, b):
    return {"op": op, "a": a, "b": b}


def op1(op, a):
    return {"op": op, "a": a}


def arithmetic_cases():
    cases = []

    def add(name, a, b):
        cases.append((name, op2("add", a, b), ref_add(a, b)))

    def sub(name, a, b):
        cases.append((name, op2("subtract", a, b), ref_subtract(a, b)))

    def neg(name, a):
        cases.append((name, op1("negate", a), ref_negate(a)))

    def absolute(name, a):
        cases.append((name, op1("abs", a), ref_abs(a)))

    def cmp(name, a, b):
        cases.append((name, op2("compare", a, b), ref_compare(a, b)))

    def construct(name, m):
        cases.append((name, {"op": "construct", **m}, ref_construct(m)))

    add("add two INR amounts", money(12345), money(655))
    add("add positive and negative", money(1000), money(-2500))
    add("add zero", money(777), money(0))
    add("add zero-decimal currency", money(500, "JPY", 0), money(250, "JPY", 0))
    add("add three-decimal currency", money(1500, "KWD", 3), money(2, "KWD", 3))
    add("add across 2^53", money("9007199254740993"), money(2))
    add("add to int64 max, no change", money(MAX), money(0))
    add("add int64 max plus one overflows", money(MAX), money(1))
    add("add int64 min plus minus one overflows", money(MIN), money(-1))
    add("add int64 min and max gives minus one", money(MIN), money(MAX))
    add("add different currencies", money(100), money(100, "USD"))
    add("add same currency, different exponent", money(100), money(100, "INR", 3))
    add("add different currency and exponent reports currency first", money(100), money(100, "JPY", 0))

    sub("subtract two INR amounts", money(12345), money(345))
    sub("subtract to a negative result", money(100), money(250))
    sub("subtract equal amounts", money(4242), money(4242))
    sub("subtract from int64 min overflows", money(MIN), money(1))
    sub("subtract int64 min from zero overflows", money(0), money(MIN))
    sub("subtract minus one from int64 max overflows", money(MAX), money(-1))
    sub("subtract int64 max from int64 min overflows", money(MIN), money(MAX))
    sub("subtract different currencies", money(100), money(50, "EUR"))

    neg("negate positive", money(500))
    neg("negate negative", money(-500))
    neg("negate zero", money(0))
    neg("negate int64 max", money(MAX))
    neg("negate int64 min overflows", money(MIN))

    absolute("abs of negative", money(-1234))
    absolute("abs of positive", money(1234))
    absolute("abs of int64 min overflows", money(MIN))

    cmp("compare less", money(100), money(200))
    cmp("compare equal", money(200), money(200))
    cmp("compare greater", money(300), money(200))
    cmp("compare negative with positive", money(-1), money(1))
    cmp("compare across 2^53", money("9007199254740993"), money("9007199254740992"))
    cmp("compare extremes", money(MIN), money(MAX))
    cmp("compare different currencies", money(1), money(1, "USD"))

    construct("construct a valid INR amount", money(12345))
    construct("construct int64 min", money(MIN))
    construct("construct int64 max", money(MAX))
    construct("construct exponent 0", money(1, "JPY", 0))
    construct("construct exponent 18", money(1, "XXX", 18))
    construct("construct lowercase currency", money(1, "inr"))
    construct("construct two-letter currency", money(1, "IN"))
    construct("construct four-letter currency", money(1, "INRR"))
    construct("construct currency with a digit", money(1, "IN1"))
    construct("construct negative exponent", money(1, "INR", -1))
    construct("construct exponent 19", money(1, "INR", 19))
    construct("construct invalid currency and exponent reports currency first", money(1, "in", 99))
    return cases


def conversion_cases():
    cases = []

    def convert(name, source, currency, exponent, rate):
        target = {"currency": currency, "exponent": exponent}
        cases.append(
            (
                name,
                {"op": "convert", "amount": source, "to": target, "rate_ppm": str(rate)},
                ref_convert(source, target, rate),
            )
        )

    convert("INR to USD", money(100000), "USD", 2, 11890)
    convert("USD to INR rounds a half up", money(1189, "USD"), "INR", 2, 83_500_000)
    convert("half rounds away from zero, positive", money(5), "USD", 2, 100_000)
    convert("half rounds away from zero, negative", money(-5), "USD", 2, 100_000)
    convert("below a half rounds down", money(4), "USD", 2, 100_000)
    convert("2.5 rounds to 3, not banker's 2", money(25), "USD", 2, 100_000)
    convert("3.5 rounds to 4", money(35), "USD", 2, 100_000)
    convert("negative 2.5 rounds to minus 3", money(-25), "USD", 2, 100_000)
    convert("two decimals to zero decimals", money(100000), "JPY", 0, 1_750_000)
    convert("zero decimals to two decimals", money(1750, "JPY", 0), "INR", 2, 571_428)
    convert("three decimals to two decimals", money(1000, "KWD", 3), "INR", 2, 270_000_000)
    convert("two decimals to three decimals", money(27000), "KWD", 3, 3_703)
    convert("identity rate keeps the amount", money(12345), "INR", 2, 1_000_000)
    convert("zero stays zero", money(0), "USD", 2, 11890)
    convert("negative amount", money(-100000), "USD", 2, 11890)
    convert("intermediate product exceeds 64 bits", money("9000000000000000"), "USD", 2, 11890)
    convert("large exact conversion", money("9000000000000000"), "INR", 2, 1_000_000)
    convert("int64 min at identity rate", money(MIN), "INR", 2, 1_000_000)
    convert("result overflows", money(MAX), "INR", 2, 83_500_000)
    convert("result overflows on the negative side", money(MIN), "INR", 2, 2_000_000)
    convert("zero rate is invalid", money(100), "USD", 2, 0)
    convert("negative rate is invalid", money(100), "USD", 2, -5)
    convert("tiny rate rounds to zero", money(100), "USD", 2, 1)
    return cases


# ---- UUIDv7 -----------------------------------------------------------------------------------
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
TS_MAX = (1 << 48) - 1
RAND_B_MAX = (1 << 62) - 1


def build_uuid(ts, rand_a, rand_b):
    if not 0 <= ts <= TS_MAX:
        return error("invalid_timestamp")
    if not 0 <= rand_a <= 0xFFF:
        return error("invalid_rand_a")
    if not 0 <= rand_b <= RAND_B_MAX:
        return error("invalid_rand_b")
    b = bytearray(16)
    b[0:6] = ts.to_bytes(6, "big")
    b[6] = 0x70 | (rand_a >> 8)
    b[7] = rand_a & 0xFF
    b[8] = 0x80 | (rand_b >> 56)
    b[9:16] = (rand_b & ((1 << 56) - 1)).to_bytes(7, "big")
    h = b.hex()
    return {"uuid": f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"}


def parse_uuid(text):
    if not UUID_RE.match(text):
        return error("invalid_uuid")
    canonical = text.lower()
    hexed = canonical.replace("-", "")
    if hexed[12] != "7" or hexed[16] not in "89ab":
        return error("invalid_uuid")
    return {"canonical": canonical, "timestamp_ms": str(int(hexed[:12], 16))}


assert build_uuid(TS_MAX, 0xFFF, RAND_B_MAX) == {"uuid": "ffffffff-ffff-7fff-bfff-ffffffffffff"}
assert build_uuid(0, 0, 0) == {"uuid": "00000000-0000-7000-8000-000000000000"}


def uuid_build_cases():
    def case(name, ts, ra, rb):
        return (
            name,
            {"op": "build", "timestamp_ms": str(ts), "rand_a": ra, "rand_b": str(rb)},
            build_uuid(ts, ra, rb),
        )

    return [
        case("typical id", 1758268800123, 0x123, 0x2AAAAAAAAAAAAAAA),
        case("all zero", 0, 0, 0),
        case("all maximum", TS_MAX, 0xFFF, RAND_B_MAX),
        case("timestamp only", 1758268800123, 0, 0),
        case("rand_a only, high nibble", 0, 0xF00, 0),
        case("rand_a only, low byte", 0, 0x0FF, 0),
        case("rand_b only, top bits", 0, 0, 1 << 61),
        case("rand_b only, low bits", 0, 0, 1),
        case("timestamp above 48 bits", TS_MAX + 1, 0, 0),
        case("rand_a above 12 bits", 0, 0x1000, 0),
        case("rand_b above 62 bits", 0, 0, RAND_B_MAX + 1),
        case("negative timestamp", -1, 0, 0),
    ]


def uuid_parse_cases():
    valid = build_uuid(1758268800123, 0x123, 0x2AAAAAAAAAAAAAAA)["uuid"]
    texts = [
        ("valid lowercase", valid),
        ("valid uppercase is normalised", valid.upper()),
        ("all zero", "00000000-0000-7000-8000-000000000000"),
        ("all maximum", "ffffffff-ffff-7fff-bfff-ffffffffffff"),
        ("wrong version 4", "3b241101-e2bb-4255-8caf-4136c566a962"),
        ("wrong variant", "01930000-0000-7000-c000-000000000000"),
        ("missing hyphens", valid.replace("-", "")),
        ("too short", valid[:-1]),
        ("too long", valid + "0"),
        ("non-hex character", valid[:-1] + "g"),
        ("empty string", ""),
    ]
    return [(name, {"op": "parse", "uuid": text}, parse_uuid(text)) for name, text in texts]


def uuid_sort_cases():
    ids = [
        build_uuid(1758268800123, 0x001, 5)["uuid"],
        build_uuid(1758268800124, 0x000, 0)["uuid"],
        build_uuid(1758268800123, 0x000, 9)["uuid"],
        build_uuid(1758268800000, 0xFFF, 1)["uuid"],
        build_uuid(1758268800123, 0x001, 4)["uuid"],
    ]
    return [
        ("sorts by timestamp, then rand_a, then rand_b", {"op": "sort", "uuids": ids}, {"sorted": sorted(ids)}),
        ("single id", {"op": "sort", "uuids": ids[:1]}, {"sorted": ids[:1]}),
        ("empty list", {"op": "sort", "uuids": []}, {"sorted": []}),
    ]


def write(relative, document):
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2) + "\n")
    print(f"wrote {relative} ({len(document['cases'])} cases)")


def main():
    write(
        "fixtures/money/arithmetic.json",
        suite("money", "Construction, add, subtract, negate, abs and compare, including int64 edges.", arithmetic_cases()),
    )
    write(
        "fixtures/money/conversion.json",
        suite("money", "FX conversion with integer parts-per-million rates and half-away-from-zero rounding.", conversion_cases()),
    )
    write("fixtures/uuid/build.json", suite("uuid", "Assembling a UUIDv7 from its parts.", uuid_build_cases()))
    write("fixtures/uuid/parse.json", suite("uuid", "Parsing and validating UUIDv7 text.", uuid_parse_cases()))
    write("fixtures/uuid/sort.json", suite("uuid", "Ordering of UUIDv7 ids.", uuid_sort_cases()))


if __name__ == "__main__":
    main()
