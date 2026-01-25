import httpx
import sys
import os

BASE_URL = "http://localhost:8000"

def run_test():
    print("🚀 Starting End-to-End Verification")
    
    # 1. Generate Keys
    print("\n1️⃣  Generating Keys...")
    resp = httpx.post(f"{BASE_URL}/keys/generate", json={"count": 1})
    if resp.status_code != 200:
        print(f"❌ Failed to generate keys: {resp.text}")
        return False
    
    data = resp.json()
    public_key = data['keys'][0]['public_key']
    private_key = data['keys'][0]['private_key']
    print(f"✅ Key generated: {public_key[:10]}...")

    # 2. Auth Challenge
    print("\n2️⃣  Requesting Challenge...")
    resp = httpx.post(f"{BASE_URL}/auth/challenge", json={"public_key": public_key})
    if resp.status_code != 200:
        print(f"❌ Failed to get challenge: {resp.text}")
        return False
    
    challenge = resp.json()['challenge']
    print(f"✅ Challenge received: {challenge}")

    # 3. Sign Challenge
    print("\n3️⃣  Signing Challenge...")
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        import base64
        
        priv_bytes = base64.b64decode(private_key)
        priv_key_obj = Ed25519PrivateKey.from_private_bytes(priv_bytes)
        signature = priv_key_obj.sign(challenge.encode())
        signature_b64 = base64.b64encode(signature).decode()
        print("✅ Signature generated")
    except ImportError:
        print("❌ Cryptography library missing in environment!")
        return False

    # 4. Verify & Get Token
    print("\n4️⃣  Verifying & Getting Token...")
    resp = httpx.post(f"{BASE_URL}/auth/verify", json={"public_key": public_key, "signature": signature_b64})
    if resp.status_code != 200:
        print(f"❌ Verification failed: {resp.text}")
        return False
    
    token = resp.json()['token']
    print(f"✅ Token received: {token[:20]}...")

    # 5. Start Session (Triggers Synapse User Creation)
    print("\n5️⃣  Starting Session (Synapse User Creation)...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = httpx.post(f"{BASE_URL}/session/start", headers=headers, timeout=10.0)
    
    if resp.status_code != 200:
        print(f"❌ Session start failed: {resp.text}")
        print("   This likely means Synapse is not reachable/working.")
        return False
    
    session_data = resp.json()
    synapse_user = session_data['synapse_user_id']
    print(f"✅ Session started!")
    print(f"   Synapse User: {synapse_user}")
    
    print("\n🎉 ALL TESTS PASSED! Backend <-> Synapse integration is working.")
    return True

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)

