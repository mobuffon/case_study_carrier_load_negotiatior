"""Convert numeric load fields into spoken English for voice agents."""

_ONES = (
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
)
_TENS = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")
_SCALES = ("", "thousand", "million")


def _join_parts(parts: list[str]) -> str:
    if not parts:
        return "zero"
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return ", ".join(parts[:-1]) + f", and {parts[-1]}"


def _under_thousand(n: int) -> str:
    if n == 0:
        return ""
    if n < 20:
        return _ONES[n]
    if n < 100:
        tens, ones = divmod(n, 10)
        return _TENS[tens] if ones == 0 else f"{_TENS[tens]}-{_ONES[ones]}"
    hundreds, remainder = divmod(n, 100)
    if remainder == 0:
        return f"{_ONES[hundreds]} hundred"
    return f"{_ONES[hundreds]} hundred {_under_thousand(remainder)}"


def int_to_words(n: int) -> str:
    if n == 0:
        return "zero"
    if n < 0:
        return f"negative {int_to_words(-n)}"

    parts: list[str] = []
    scale_idx = 0
    while n > 0:
        chunk = n % 1000
        if chunk:
            chunk_words = _under_thousand(chunk)
            scale = _SCALES[scale_idx]
            parts.insert(0, f"{chunk_words} {scale}".strip() if scale else chunk_words)
        n //= 1000
        scale_idx += 1
    return _join_parts(parts)


def dollars_to_words(amount: float) -> str:
    dollars = int(round(amount))
    words = int_to_words(dollars)
    suffix = "dollar" if dollars == 1 else "dollars"
    return f"{words} {suffix}"


def pounds_to_words(weight: float) -> str:
    pounds = int(round(weight))
    words = int_to_words(pounds)
    suffix = "pound" if pounds == 1 else "pounds"
    return f"{words} {suffix}"


def miles_to_words(miles: float) -> str:
    whole_miles = int(round(miles))
    words = int_to_words(whole_miles)
    suffix = "mile" if whole_miles == 1 else "miles"
    return f"{words} {suffix}"


def pieces_to_words(count: int) -> str:
    words = int_to_words(count)
    suffix = "piece" if count == 1 else "pieces"
    return f"{words} {suffix}"


def load_id_to_words(load_id: str) -> str:
    parts: list[str] = []
    for char in load_id:
        if char.isdigit():
            parts.append(_ONES[int(char)])
        elif char == "-":
            parts.append("dash")
        else:
            parts.append(char)
    return " ".join(parts)


def build_load_spoken(
    *,
    load_id: str,
    loadboard_rate: float,
    weight: float | None = None,
    num_of_pieces: int | None = None,
    miles: float | None = None,
) -> dict[str, str]:
    spoken = {
        "load_id": load_id_to_words(load_id),
        "loadboard_rate": dollars_to_words(loadboard_rate),
    }
    if weight is not None:
        spoken["weight"] = pounds_to_words(weight)
    if num_of_pieces is not None:
        spoken["num_of_pieces"] = pieces_to_words(num_of_pieces)
    if miles is not None:
        spoken["miles"] = miles_to_words(miles)
    return spoken
