import re


def normalize_phone(raw):
    """
    Приводит любой формат телефона к виду +7XXXXXXXXXX.

    Примеры:
        89171234567        → +79171234567
        +7 (917) 123-45-67 → +79171234567
        7-917-123-45-67    → +79171234567
        8(917)1234567      → +79171234567
    Возвращает '' для невалидного номера.
    """
    if not raw:
        return ''
    digits = re.sub(r'\D', '', raw)  # только цифры
    if len(digits) == 11 and digits.startswith('8'):
        digits = '7' + digits[1:]
    if len(digits) == 11 and digits.startswith('7'):
        return '+' + digits
    if len(digits) == 10:
        return '+7' + digits
    return ''  # невалидный номер
