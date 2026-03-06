import urllib.request
import json
import time

BASE_URL = "http://localhost:3001/api"

def test_admin_flow():
    try:
        print("Testing Admin Flow...")
        
        # 1. Create Unit
        print("Creating Unit...")
        unit_payload = {
            "title": "API Test Unit",
            "description": "Created via API Test",
            "orderIndex": 99,
            "isChallenge": False,
            "isPublished": True
        }
        unit_req = urllib.request.Request(
            f"{BASE_URL}/admin/units",
            data=json.dumps(unit_payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(unit_req) as response:
            unit_resp = json.loads(response.read().decode('utf-8'))
            unit_id = unit_resp["data"]["id"]
            print(f"Unit Created: {unit_id}")

        # 2. Create Lesson
        print("Creating Lesson...")
        lesson_payload = {
            "unitId": unit_id,
            "title": "API Test Lesson",
            "description": "Lesson Desc",
            "orderIndex": 1,
            "xpReward": 50,
            "isPublished": True
        }
        lesson_req = urllib.request.Request(
            f"{BASE_URL}/admin/lessons",
            data=json.dumps(lesson_payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(lesson_req) as response:
            lesson_resp = json.loads(response.read().decode('utf-8'))
            lesson_id = lesson_resp["data"]["id"]
            print(f"Lesson Created: {lesson_id}")

        # 3. Create Task
        print("Creating Task...")
        task_payload = {
            "lessonId": lesson_id,
            "type": "REPEAT_SIGN",
            "promptText": "Test Prompt",
            "orderIndex": 1,
        }
        task_req = urllib.request.Request(
            f"{BASE_URL}/admin/tasks",
            data=json.dumps(task_payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(task_req) as response:
            task_resp = json.loads(response.read().decode('utf-8'))
            task_id = task_resp["data"]["id"]
            print(f"Task Created: {task_id}")

        # 4. Verify Content Fetch
        print("Verifying Content...")
        content_req = urllib.request.Request(f"{BASE_URL}/admin/content")
        with urllib.request.urlopen(content_req) as response:
            content_data = json.loads(response.read().decode('utf-8'))
            
            # Find our unit
            found_unit = next((u for u in content_data["data"] if u["id"] == unit_id), None)
            if found_unit:
                print("Unit found in content list.")
                found_lesson = next((l for l in found_unit["lessons"] if l["id"] == lesson_id), None)
                if found_lesson:
                    print("Lesson found in unit.")
                    found_task = next((t for t in found_lesson["tasks"] if t["id"] == task_id), None)
                    if found_task:
                        print("Task found in lesson. SUCCESS!")
                    else:
                        print("Task NOT found.")
                else:
                    print("Lesson NOT found.")
            else:
                print("Unit NOT found.")

    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(f"Error Content: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_admin_flow()
