#!/usr/bin/env python3
"""
Test script to verify bot setup before deployment
"""
import os
import sys

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python 3.11 or higher required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("   Run: cp .env.example .env")
        return False
    print("✅ .env file exists")
    return True


def check_env_variables():
    """Check required environment variables"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("❌ python-dotenv not installed")
        print("   Run: pip install python-dotenv")
        return False
    
    required_vars = ['BOT_TOKEN', 'ADMIN_IDS']
    missing = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your_'):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing or invalid environment variables: {', '.join(missing)}")
        print("   Edit .env file and set proper values")
        return False
    
    print("✅ Required environment variables set")
    return True


def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'telegram',
        'sqlalchemy',
        'dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages installed")
    return True


def check_database():
    """Check database connection"""
    try:
        from database.database import init_db
        init_db()
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def check_file_structure():
    """Check if all required files exist"""
    required_files = [
        'main.py',
        'config.py',
        'requirements.txt',
        'database/models.py',
        'database/database.py',
        'handlers/user_handlers.py',
        'handlers/admin_handlers.py',
        'handlers/callback_handlers.py',
        'keyboards/keyboards.py',
        'utils/helpers.py'
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        return False
    
    print("✅ All required files present")
    return True


def main():
    """Run all checks"""
    print("🃏 BudapestJoker Bot - Setup Verification")
    print("==========================================\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("File Structure", check_file_structure),
        (".env File", check_env_file),
        ("Environment Variables", check_env_variables),
        ("Dependencies", check_dependencies),
        ("Database", check_database)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        try:
            result = check_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Error during {name} check: {e}")
            results.append(False)
    
    print("\n" + "=" * 42)
    
    if all(results):
        print("✅ All checks passed! Bot is ready to run.")
        print("\nTo start the bot:")
        print("  python main.py")
        print("\nFor Railway deployment:")
        print("  See DEPLOY.md for instructions")
        return 0
    else:
        failed = sum(1 for r in results if not r)
        print(f"❌ {failed} check(s) failed. Please fix the issues above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
