"""Analyze all test cards with the content interpreter."""
import subprocess
import json

def analyze_hash(hash_value):
    print(f"\n{'='*80}")
    print(f"Analyzing card: {hash_value}")
    print('='*80)
    
    result = subprocess.run(
        ['python3', 'examples/content_interpreter/app.py', hash_value],
        capture_output=True,
        text=True
    )
    
    try:
        # Parse and pretty print the JSON output
        analysis = json.loads(result.stdout)
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print("Raw output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

def main():
    hashes = [
        "05334725bf5cf4b306b4e785d24208b0a4460ecaf858de258c96dfed48212c2d",  # Spanish
        "f5a28c065ea6f3eca8fe903349e569f44ae408696182d938fc7a8119d5ed18c1",  # JSON
        "337a1e86b89df6e42f932fd5c1badb3145ee2bb54051af17f9769df35aad6521",  # French
        "4ac4034d3ca093da8e7e558e6902bd092e314d8b6ed9fe9d436da95bcc7e2e8b"   # Binary
    ]
    
    for hash_value in hashes:
        analyze_hash(hash_value)

if __name__ == "__main__":
    main()
