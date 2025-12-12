#!/usr/bin/env python3
"""
Test script for i18n functionality
"""
import sys
sys.path.insert(0, '/tmp/gh-issue-solver-1765562091877')

from utils import t9n

def test_t9n():
    """Test translation function"""
    print("Testing t9n function...")

    # Test with explicit locale
    test_msg = "[RU]Привет[EN]Hello"

    result_en = t9n(test_msg, locale='EN')
    print(f"EN: '{test_msg}' -> '{result_en}'")
    assert result_en == "Hello", f"Expected 'Hello', got '{result_en}'"

    result_ru = t9n(test_msg, locale='RU')
    print(f"RU: '{test_msg}' -> '{result_ru}'")
    assert result_ru == "Привет", f"Expected 'Привет', got '{result_ru}'"

    # Test with lowercase locale
    result_en_lower = t9n(test_msg, locale='en')
    print(f"en (lowercase): '{test_msg}' -> '{result_en_lower}'")
    assert result_en_lower == "Hello", f"Expected 'Hello', got '{result_en_lower}'"

    # Test complex message
    complex_msg = "[RU]Введите email и пароль[EN]Enter email and password"
    result_en_complex = t9n(complex_msg, locale='EN')
    print(f"EN complex: '{complex_msg}' -> '{result_en_complex}'")
    assert result_en_complex == "Enter email and password", f"Expected 'Enter email and password', got '{result_en_complex}'"

    result_ru_complex = t9n(complex_msg, locale='RU')
    print(f"RU complex: '{complex_msg}' -> '{result_ru_complex}'")
    assert result_ru_complex == "Введите email и пароль", f"Expected 'Введите email и пароль', got '{result_ru_complex}'"

    # Test message without markers
    plain_msg = "Plain message"
    result_plain = t9n(plain_msg, locale='EN')
    print(f"Plain: '{plain_msg}' -> '{result_plain}'")
    assert result_plain == "Plain message", f"Expected 'Plain message', got '{result_plain}'"

    # Test with only one language
    single_lang = "[EN]Only English"
    result_single = t9n(single_lang, locale='EN')
    print(f"Single lang EN: '{single_lang}' -> '{result_single}'")
    assert result_single == "Only English", f"Expected 'Only English', got '{result_single}'"

    result_single_ru = t9n(single_lang, locale='RU')
    print(f"Single lang RU (fallback): '{single_lang}' -> '{result_single_ru}'")
    # When RU is not available, it should return original or empty

    print("\n✓ All t9n tests passed!")

if __name__ == '__main__':
    test_t9n()
