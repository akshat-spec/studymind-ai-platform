import requests
import os
import time

BASE_URL = "http://localhost:8000/api"
DEMO_EMAIL = "demo@studymind.ai"
DEMO_PASSWORD = "demo1234"

def seed_demo():
    print("🚀 Starting demo seeding process...")

    # 1. Create/Login User
    login_resp = requests.post(f"{BASE_URL}/auth/login", data={
        "username": DEMO_EMAIL,
        "password": DEMO_PASSWORD
    })

    if login_resp.status_code != 200:
        print("Registering new demo user...")
        reg_resp = requests.post(f"{BASE_URL}/auth/register", json={
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
            "full_name": "Demo Student"
        })
        if reg_resp.status_code == 200:
            login_resp = requests.post(f"{BASE_URL}/auth/login", data={
                "username": DEMO_EMAIL,
                "password": DEMO_PASSWORD
            })
        else:
            print(f"❌ Failed to create user: {reg_resp.text}")
            return

    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check if documents already exist
    docs_resp = requests.get(f"{BASE_URL}/documents/", headers=headers)
    if docs_resp.status_code == 200 and len(docs_resp.json()) > 0:
        print("✅ Demo data already exists. Skipping seeding.")
        return

    # 3. Upload Sample PDF
    # Creating a dummy text-based PDF content for demonstration
    # In a real scenario, we'd have a small sample.pdf file in the scripts folder.
    print("Uploading sample document...")
    dummy_pdf_path = "sample_textbook.txt"
    with open(dummy_pdf_path, "w") as f:
        f.write("Quantum physics is the study of matter and energy at the most fundamental level. " * 100)
    
    with open(dummy_pdf_path, "rb") as f:
        upload_resp = requests.post(f"{BASE_URL}/documents/upload", headers=headers, files={"file": ("quantum_physics.pdf", f, "application/pdf")})
    
    os.remove(dummy_pdf_path)
    
    if upload_resp.status_code != 200:
        print(f"❌ Failed to upload document: {upload_resp.text}")
        return
    
    doc_id = upload_resp.json()["id"]
    print(f"✅ Uploaded document ID: {doc_id}")

    # Wait for processing
    time.sleep(2)

    # 4. Create Chat Session & 5 Exchanges
    print("Creating chat session...")
    session_resp = requests.post(f"{BASE_URL}/chat/sessions", headers=headers, json={"title": "Introduction to Quantum Physics"})
    session_id = session_resp.json()["id"]

    exchanges = [
        "What is quantum physics?",
        "Explain superposition in simple terms.",
        "How does it differ from classical physics?",
        "What is a quantum bit or qubit?",
        "Why is it important for the future of computing?"
    ]

    for msg in exchanges:
        print(f"Sending message: {msg}")
        requests.post(f"{BASE_URL}/chat/sessions/{session_id}/messages", headers=headers, json={"content": msg})
        time.sleep(1)

    # 5. Generate Quiz
    print("Generating demo quiz...")
    requests.post(f"{BASE_URL}/quiz/generate", headers=headers, json={"document_id": doc_id, "num_questions": 5})

    # 6. Generate 10 Flashcards
    print("Generating demo flashcards...")
    requests.post(f"{BASE_URL}/flashcards/generate", headers=headers, json={"document_id": doc_id, "num_cards": 10})

    print("🏁 Demo seeding completed successfully!")

if __name__ == "__main__":
    seed_demo()
