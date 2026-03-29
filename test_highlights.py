
import sys
import os

# Mock streamlit and pandas before importing taf_functions
class MockSt:
    def spinner(self, text): return self
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def error(self, text): print(f"ERROR: {text}")
    def cache_data(self, **kwargs):
        def decorator(f): return f
        return decorator

import types
import sys
mock_st = MockSt()
sys.modules['streamlit'] = mock_st
sys.modules['pandas'] = types.ModuleType('pandas')

from taf_functions import highlight_taf, VIS_THRESHOLD, CEILING_THRESHOLD

def test_highlighting():
    test_cases = [
        {
            "name": "Visibility below threshold",
            "input": "TAF VHHH 190400Z 1906/2012 08010KT 2500 FEW020",
            "expected": "2500",
            "color": "red"
        },
        {
            "name": "Cloud Ceiling below threshold",
            "input": "TAF VHHH 190400Z 1906/2012 08010KT 5000 BKN008",
            "expected": "BKN008",
            "color": "pink"
        },
        {
            "name": "Snow condition",
            "input": "TAF VHHH 190400Z 1906/2012 08010KT 5000 -SN FEW020",
            "expected": "-SN",
            "color": "green"
        },
        {
            "name": "Freezing conditions",
            "input": "TAF VHHH 190400Z 1906/2012 08010KT 5000 FZRA FEW020",
            "expected": "FZRA",
            "color": "blue"
        },
        {
            "name": "Mixed Snow/Rain",
            "input": "TAF VHHH 190400Z 1906/2012 08010KT 5000 SNRA FEW020",
            "expected": "SNRA",
            "color": "green"
        },
        {
            "name": "User reported bug case (-FZRA)",
            "input": "TAF ENNA 282300Z 2900/2924 18008KT 9999 SCT035 BKN050 PROB30 TEMPO 2903/2906 -FZRA TEMPO 2911/2920 24015G25KT",
            "expected": "-FZRA",
            "color": "blue"
        },
        {
            "name": "User reported bug case (-SHSN)",
            "input": "TAF CYYR 290540Z 2906/3012 23005KT P6SM FEW050 FM291600 25010G20KT P6SM BKN040 TEMPO 2916/2922 5SM -SHSN",
            "expected": "-SHSN",
            "color": "green"
        }
    ]

    print(f"Testing with VIS_THRESHOLD={VIS_THRESHOLD}, CEILING_THRESHOLD={CEILING_THRESHOLD}\n")
    
    for case in test_cases:
        result = highlight_taf(case["input"])
        if f"color: {case['color']}" in result and case["expected"] in result:
            print(f"✅ PASSED: {case['name']}")
        else:
            print(f"❌ FAILED: {case['name']}")
            print(f"   Result: {result}")

if __name__ == "__main__":
    test_highlighting()
