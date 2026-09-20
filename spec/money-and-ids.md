# Money and identifiers

Behaviour that every Nanayam implementation must reproduce exactly. The vectors in `fixtures/money/` and `fixtures/uuid/` are the executable form of this document; if the two disagree, fix the document or the vector, never just one client.

## Encoding in fixtures

**Every 64-bit integer is written as a decimal string** (`"9007199254740993"`, not `9007199254740993`). JSON numbers are parsed as 64-bit floats in some languages, which silently corrupts anything above 2^53. Small integers that are not amounts (exponents, versions, comparison results) stay plain numbers.

A case has `input` and `expected`. On failure, `expected` is `{"error": "<code>"}`.

## Money

A `Money` value is three fields: `amount_minor` (signed 64-bit integer), `currency` (ISO-4217 code) and `exponent` (decimal places of the currency's minor unit). Amounts are signed: money out is negative.

```json
{ "amount_minor": "12345", "currency": "INR", "exponent": 2 }
```

The exponent is stored, not derived from a table. Most currencies use 2, JPY and KRW use 0, and KWD, BHD and TND use 3.

### Validity

- `currency` is exactly three characters, each `A` to `Z`. Anything else is `invalid_currency`.
- `exponent` is an integer from 0 to 18 inclusive. Anything else is `invalid_exponent`. (10^18 is the largest power of ten that fits in 64 bits.)
- `amount_minor` is within -9223372036854775808 and 9223372036854775807 inclusive.

If both currency and exponent are invalid, `invalid_currency` is reported.

### Arithmetic

Arithmetic is exact and **never wraps**. Any result, and any intermediate value that decides the result, outside the signed 64-bit range is `overflow`.

| Operation | Rule | Errors |
|---|---|---|
| `add`, `subtract` | Same currency **and** same exponent required | `currency_mismatch`, `exponent_mismatch`, `overflow` |
| `negate` | Flips the sign | `overflow` for -9223372036854775808 |
| `abs` | Magnitude | `overflow` for -9223372036854775808 |
| `compare` | -1, 0 or 1, same currency and exponent required | `currency_mismatch`, `exponent_mismatch` |

If currencies differ, `currency_mismatch` is reported even when exponents also differ.

### Conversion

`rate_ppm` is the number of **target major units per one source major unit, times 1,000,000**, as a positive integer. For example 1 INR = 0.011890 USD is `11890`; 1 USD = 83.5 INR is `83500000`. It matches `GET /fx/rates` in the API contract.

```
target_minor = round( source_minor * rate_ppm * 10^target_exponent
                      / ( 10^source_exponent * 1_000_000 ) )
```

- The calculation uses arbitrary precision. The intermediate product may exceed 64 bits; only the rounded result is checked against the 64-bit range (`overflow`).
- Rounding is **half away from zero**, so `convert(-x) == -convert(x)` always, and 2.5 rounds to 3 (not to 2 as banker's rounding would).
- `rate_ppm` must be greater than zero, otherwise `invalid_rate`.
- No special case for converting a currency to itself: the formula applies as written.

### Error codes

`invalid_currency`, `invalid_exponent`, `currency_mismatch`, `exponent_mismatch`, `overflow`, `invalid_rate`.

## UUIDv7

Entity identifiers are UUIDv7 (RFC 9562), generated on the client so records can be created offline without a server round trip. They are time-ordered, which keeps database indexes local and makes ids sort by creation.

Layout, most significant byte first:

| Bytes | Content |
|---|---|
| 0–5 | `timestamp_ms`: Unix milliseconds, 48 bits, big-endian |
| 6 | high nibble `7` (version), low nibble = top 4 bits of `rand_a` |
| 7 | low 8 bits of `rand_a` |
| 8 | top two bits `10` (variant), low 6 bits = top 6 bits of `rand_b` |
| 9–15 | low 56 bits of `rand_b` |

`rand_a` is 12 bits (0 to 4095) and `rand_b` is 62 bits. Text form is lowercase hex, `8-4-4-4-12`, so **text order equals byte order equals creation order**.

Generation is monotonic: ids from one generator sort strictly in creation order, even within one millisecond or if the clock steps backwards. How an implementation achieves that (the reference clients use `rand_a` as a counter) is not part of the contract; the vectors cover only `build`, `parse` and `sort`.

### Operations

- `build(timestamp_ms, rand_a, rand_b)` returns the id text. Errors: `invalid_timestamp` (outside 0 to 2^48-1), `invalid_rand_a`, `invalid_rand_b`.
- `parse(text)` returns the lowercase canonical text and `timestamp_ms`. Uppercase input is accepted. Anything that is not `8-4-4-4-12` hex, not version 7, or not the RFC variant is `invalid_uuid`.
- `sort(ids)` orders ids ascending by their canonical text.
