"""
Test script for DistilBERT integration.
Run this to verify the model loads correctly.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from blog.predictor.utils import get_predictor

def test_short_text():
    """Test with short sensational text (where CNN struggles)."""
    print("\n" + "="*60)
    print("TEST 1: Short Sensational Text (50 words)")
    print("="*60)
    
    text = """
    BREAKING NEWS: Miracle cure discovered! 
    Doctors HATE this one simple trick that cures ALL diseases!
    Big Pharma doesn't want you to know this secret!
    Click here NOW before it's too late!
    """
    
    print(f"\nInput text ({len(text.split())} words):")
    print(text)
    
    try:
        predictor = get_predictor()
        result = predictor.predict(text)
        
        print("\n📊 Prediction Results:")
        print(f"   Model Type: {result.get('model_type', 'Unknown')}")
        print(f"   Prediction: {result['prediction']}")
        print(f"   Confidence: {result['confidence_label']}")
        print(f"   Trueness Probability: {result['trueness_probability']}%")
        print(f"   Text Length: {result['text_length']} characters")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    
    return True


def test_medium_text():
    """Test with medium length article excerpt."""
    print("\n" + "="*60)
    print("TEST 2: Medium Article Excerpt (150 words)")
    print("="*60)
    
    text = """
    The Federal Reserve announced today a 0.25% interest rate hike, 
    marking the third consecutive increase this quarter. This decision 
    comes amid ongoing concerns about inflation, which has remained above 
    the Fed's 2% target for several months. Federal Reserve Chairman 
    Jerome Powell stated in a press conference that the central bank 
    remains committed to bringing inflation back to sustainable levels 
    while maintaining maximum employment. Economists had widely anticipated 
    this move, with most projecting a continuation of rate increases 
    throughout the remainder of the year. Stock markets reacted with 
    mixed sentiment, with the S&P 500 closing down 0.8% following the 
    announcement. The unemployment rate currently stands at 3.7%, near 
    historical lows, suggesting a robust labor market despite the 
    monetary tightening. Consumer spending data released last week 
    showed continued strength in retail sales, further supporting 
    the Fed's decision to proceed with rate normalization.
    """
    
    print(f"\nInput text ({len(text.split())} words):")
    print(text[:200] + "...")
    
    try:
        predictor = get_predictor()
        result = predictor.predict(text)
        
        print("\n📊 Prediction Results:")
        print(f"   Model Type: {result.get('model_type', 'Unknown')}")
        print(f"   Prediction: {result['prediction']}")
        print(f"   Confidence: {result['confidence_label']}")
        print(f"   Trueness Probability: {result['trueness_probability']}%")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    
    return True


def test_performance():
    """Benchmark inference speed."""
    print("\n" + "="*60)
    print("TEST 3: Performance Benchmark")
    print("="*60)
    
    import time
    
    text = "This is a short test article for performance benchmarking. " * 20
    
    print(f"\nRunning 5 predictions to measure average inference time...")
    
    try:
        predictor = get_predictor()
        
        times = []
        for i in range(5):
            start = time.time()
            result = predictor.predict(text)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            times.append(elapsed)
            print(f"   Run {i+1}: {elapsed:.2f}ms")
        
        avg_time = sum(times) / len(times)
        print(f"\n⚡ Average inference time: {avg_time:.2f}ms")
        
        if avg_time < 100:
            print("   ✅ Excellent performance!")
        elif avg_time < 200:
            print("   ✅ Good performance")
        else:
            print("   ⚠️  Slower than expected - check GPU settings")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    
    return True


def check_gpu():
    """Check if PyTorch can access the GPU."""
    print("\n" + "="*60)
    print("GPU Status Check")
    print("="*60)
    
    try:
        import torch
        
        print(f"\n🔧 PyTorch Version: {torch.__version__}")
        print(f"   CUDA Available: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"   GPU Device: {torch.cuda.get_device_name(0)}")
            print(f"   CUDA Version: {torch.version.cuda}")
            print("   ✅ GPU acceleration is enabled!")
        else:
            print("   ⚠️  GPU not available - using CPU (slower)")
            print("   To fix: Install PyTorch with CUDA support")
            print("   Visit: https://pytorch.org/get-started/locally/")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print(" DistilBERT Fake News Detection - Integration Test")
    print("="*60)
    
    # Check GPU first
    check_gpu()
    
    # Run tests
    tests_passed = 0
    tests_total = 3
    
    if test_short_text():
        tests_passed += 1
    
    if test_medium_text():
        tests_passed += 1
    
    if test_performance():
        tests_passed += 1
    
    # Summary
    print("\n" + "="*60)
    print(f" Test Summary: {tests_passed}/{tests_total} tests passed")
    print("="*60)
    
    if tests_passed == tests_total:
        print("\n✅ All tests passed! DistilBERT is working correctly.")
    else:
        print(f"\n⚠️  {tests_total - tests_passed} test(s) failed. Check errors above.")
    
    print("\n" + "="*60)
