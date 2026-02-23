"""
Test nutrition_values pipeline step by step
"""
import sys
from pathlib import Path

def test_extract():
    """Test extract step"""
    print("\n" + "=" * 70)
    print("📥 TEST 1: EXTRACT")
    print("=" * 70)
    
    from processors.nutrition_values.extract import download_nutrition_values
    result = download_nutrition_values()
    
    if result:
        print(f"✅ Extract succeeded: {result}")
        return True
    else:
        print("❌ Extract failed")
        return False

def test_transform():
    """Test transform step"""
    print("\n" + "=" * 70)
    print("🔄 TEST 2: TRANSFORM")
    print("=" * 70)
    
    from spark.session import get_spark, stop_spark
    from processors.nutrition_values.transform import transform_nutrition_values
    from processors.nutrition_values.config import LOCAL_FILE
    
    spark = get_spark("Test_Transform_Nutrition_Values")
    
    try:
        df = transform_nutrition_values(spark, str(LOCAL_FILE))
        
        if df and df.count() > 0:
            print(f"\n✅ Transform succeeded: {df.count()} rows")
            
            # Show sample
            print("\n📊 Sample data:")
            df.select("name", "calories_100g", "protein_100g", "category_ref").show(5, truncate=False)
            
            return True
        else:
            print("❌ Transform failed: No data")
            return False
            
    except Exception as e:
        print(f"❌ Transform failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        stop_spark()

def test_load():
    """Test load step"""
    print("\n" + "=" * 70)
    print("📦 TEST 3: LOAD")
    print("=" * 70)
    
    from spark.session import get_spark, stop_spark
    from processors.nutrition_values.transform import transform_nutrition_values
    from processors.nutrition_values.load import load_nutrition_values
    from processors.nutrition_values.config import LOCAL_FILE
    
    spark = get_spark("Test_Load_Nutrition_Values")
    
    try:
        # Transform first
        print("🔄 Running transform...")
        df = transform_nutrition_values(spark, str(LOCAL_FILE))
        
        if not df or df.count() == 0:
            print("❌ Transform failed, cannot test load")
            return False
        
        # Load
        print("\n📦 Running load...")
        success = load_nutrition_values(spark, df)
        
        if success:
            print("✅ Load succeeded")
            return True
        else:
            print("❌ Load failed")
            return False
            
    except Exception as e:
        print(f"❌ Load test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        stop_spark()

def test_full_pipeline():
    """Test complete pipeline"""
    print("\n" + "=" * 70)
    print("🚀 TEST 4: FULL PIPELINE")
    print("=" * 70)
    
    from processors.nutrition_values.pipeline import run_pipeline
    
    success = run_pipeline()
    
    if success:
        print("\n✅ Full pipeline succeeded")
        return True
    else:
        print("\n❌ Full pipeline failed")
        return False

def main():
    """Run all tests"""
    print("=" * 70)
    print("🧪 NUTRITION VALUES PIPELINE TESTS")
    print("=" * 70)
    
    tests = [
        ("Extract", test_extract),
        ("Transform", test_transform),
        ("Load", test_load),
        ("Full Pipeline", test_full_pipeline)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 ALL TESTS PASSED")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 70)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
