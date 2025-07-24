import json
import os
import sys
from pathlib import Path

def load_json(dir_path):
    data = {}
    for f in os.listdir(dir_path):
        if f.lower().endswith('.json'):
            with open(os.path.join(dir_path, f), encoding='utf-8') as fp:
                try:
                    data[f] = json.load(fp)
                except json.JSONDecodeError:
                    print(f"Warning: failed to parse {f}")
    return data

def compare(actual, expected):
    diffs = []
    # Compare titles
    a_title = actual.get('title', '')
    e_title = expected.get('title', '')
    if a_title != e_title:
        diffs.append(f"Title differs:\n    Expected: {e_title}\n    Actual:   {a_title}")

    # Compare outlines
    a_outline = actual.get('outline', [])
    e_outline = expected.get('outline', [])
    if len(a_outline) != len(e_outline):
        diffs.append(f"Outline length differs: expected {len(e_outline)}, actual {len(a_outline)}")
    # Compare each outline entry
    for i, (e_item, a_item) in enumerate(zip(e_outline, a_outline)):
        if e_item != a_item:
            diffs.append(f"Outline item {i} differs:\n    Expected: {e_item}\n    Actual:   {a_item}")
    return diffs

def main(actual_dir, expected_dir):
    actuals = load_json(actual_dir)
    expecteds = load_json(expected_dir)

    for fname in sorted(expecteds.keys()):
        print(f"Comparing {fname}...")
        actual = actuals.get(fname)
        expected = expecteds[fname]
        if actual is None:
            print(f"  Missing actual output for {fname}")
            continue
        diffs = compare(actual, expected)
        if diffs:
            print("  Differences found:")
            for d in diffs:
                print(f"    - {d}")
        else:
            print("  OK")
        print()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python compare_outputs.py <actual_output_dir> <expected_output_dir>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
