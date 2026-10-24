import re
from typing import Optional

UZ_NUMS = {
    'nol': 0, 'bir': 1, 'ikki': 2, 'uch': 3, 'to\'rt': 4, 'tort': 4, 'to‘rt': 4, 'toʼrt': 4,
    'besh': 5, 'olti': 6, 'yetti': 7, 'sakkiz': 8, 'to\'qqiz': 9, 'toqqiz': 9, 'to‘qqiz': 9,
    'o\'n': 10, 'on': 10, 'yigirma': 20, 'o\'ttiz': 30, 'ottiz': 30, 'qirq': 40,
    'ellik': 50, 'oltmish': 60, 'yetmish': 70, 'sakson': 80, 'to\'qson': 90, 'toqson': 90,
    'yuz': 100, 'ming': 1000
}

def _words_to_nums(text: str) -> str:
    """O'zbekcha so'z bilan yozilgan sonlarni raqamlarga aylantirish."""
    clean = text.lower()
    for w, n in sorted(UZ_NUMS.items(), key=lambda x: len(x[0]), reverse=True):
        clean = re.sub(rf'\b{w}(ni|ga|dan|da|ta|si|i|cha)?\b', str(n), clean)
    return clean

def is_math_question(text: str) -> bool:
    """Savol matematik hisoblash haqidami?"""
    t = text.lower()
    has_math_words = any(w in t for w in [
        'qo\'sh', 'qosh', 'ayir', 'ko\'paytir', 'kopaytir', 'bo\'l', 'bol',
        'necha bo\'ladi', 'necha boladi', 'nechchi', 'hisobla', 'javobi nima',
        'plus', 'minus', '+', '-', '*', '/', '×', '÷'
    ])
    has_digits = bool(re.search(r'\d+', _words_to_nums(t)))
    return has_math_words and has_digits

def solve_math(query: str, child_name: str = "bolajon", age: int = 7) -> Optional[str]:
    """
    Bolalar uchun sodda, vizual va tushunarli matematik yechim.
    O'zbekcha tabiiy gaplarni to'liq tushunadi (masalan: '5 ga 3 ni qo'shsak nechi bo'ladi').
    """
    clean = _words_to_nums(query)

    n1, n2, op = None, None, None

    # 1-shablon: "5 ga 3 ni qo'shsak", "10 dan 4 ni ayirsak", "3 ni 4 ga ko'paytirsak"
    m_uz = re.search(
        r'(\d+)\s*(?:ga|dan|ni|va|bilan)?\s*(\d+)\s*(?:ni|ga|dan)?\s*(qo[\'\`‘ʼ]?sh|ayir|ko[\'\`‘ʼ]?paytir|bo[\'\`‘ʼ]?l|plus|minus)',
        clean, re.IGNORECASE
    )
    if m_uz:
        n1 = int(m_uz.group(1))
        n2 = int(m_uz.group(2))
        op_root = m_uz.group(3).lower()
        if 'qosh' in op_root or 'qo\'sh' in op_root or 'plus' in op_root:
            op = '+'
        elif 'ayir' in op_root or 'minus' in op_root:
            op = '-'
        elif 'paytir' in op_root or 'ko\'paytir' in op_root:
            op = '*'
        elif 'bol' in op_root or 'bo\'l' in op_root:
            op = '/'

    # 2-shablon: "5 + 3", "10 - 2", "4 * 5"
    if not op:
        m_std = re.search(r'(\d+)\s*([\+\-\*\/xX×÷])\s*(\d+)', clean)
        if m_std:
            n1 = int(m_std.group(1))
            op_sym = m_std.group(2)
            n2 = int(m_std.group(3))
            if op_sym in ['+', 'plus']: op = '+'
            elif op_sym in ['-', 'minus']: op = '-'
            elif op_sym in ['*', 'x', 'X', '×']: op = '*'
            elif op_sym in ['/', '÷']: op = '/'

    if n1 is None or n2 is None or op is None:
        return None

    if op == '+':
        res = n1 + n2
        if age <= 6:
            return f"{n1} ga {n2} ni qo'shsak {res} bo'ladi, {child_name}! Tasavvur qil, likopchada {n1} ta shirin qizil olma bor edi, unga yana {n2} ta qo'shdik va jami {res} ta shirin olma bo'ldi!"
        else:
            return f"{n1} ga {n2} ni qo'shganda natija {res} bo'ladi, {child_name}! Bu xuddi {n1} ta qadamga yana {n2} ta qadam qo'shilib, jami {res} ta bo'lganiga o'xshaydi."
    elif op == '-':
        res = n1 - n2
        if res < 0:
            return f"{n1} dan {n2} ni ayirganda manfiy son {res} hosil bo'ladi, {child_name}."
        if age <= 6:
            return f"{n1} dan {n2} ni ayirsak {res} qoladi, {child_name}! Tasavvur qil, savatda {n1} ta shirin olma bor edi, {n2} tasini do'stlaring bilan yeding va savatda {res} ta qoldi!"
        else:
            return f"{n1} dan {n2} ni ayirsak natija {res} bo'ladi, {child_name}."
    elif op == '*':
        res = n1 * n2
        return f"{n1} ni {n2} ga ko'paytirganda {res} bo'ladi, {child_name}! Bu degani {n1} sonini {n2} marta o'ziga qo'shish demakdir."
    elif op == '/':
        if n2 == 0:
            return f"Hech qanday sonni nolga bo'lib bo'lmaydi, {child_name}!"
        res = n1 // n2 if n1 % n2 == 0 else round(n1 / n2, 2)
        return f"{n1} ni {n2} ga bo'lganda natija {res} bo'ladi, {child_name}!"

    return None
