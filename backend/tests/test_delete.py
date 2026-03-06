import urllib.request
import json
import sys

BASE_URL = "http://localhost:3001/api"

def test_delete_flow():
    try:
        print("Testing Delete Flow...")
        
        # 1. Create Unit to Delete
        print("Creating Unit to Delete...")
        unit_payload = {
            "title": "Delete Me Unit",
            "description": "To be deleted",
            "orderIndex": 100,
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

        # 2. Create Lesson in that Unit (to test cascade/constraint)
        print("Creating Lesson in Unit...")
        lesson_payload = {
            "unitId": unit_id,
            "title": "Delete Me Lesson",
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

        # 3. Create Task in Lesson
        print("Creating Task in Lesson...")
        task_payload = {
            "lessonId": lesson_id,
            "type": "REPEAT_SIGN",
            "promptText": "Delete Me Task",
            "orderIndex": 1,
            "showMascot": False
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

        # 4. Delete Unit
        print(f"Deleting Unit {unit_id}...")
        delete_req = urllib.request.Request(
            f"{BASE_URL}/admin/units/{unit_id}",
            method='DELETE'
        )
        with urllib.request.urlopen(delete_req) as response:
            print(f"Delete Response Code: {response.getcode()}")
            delete_resp = json.loads(response.read().decode('utf-8'))
            print(f"Delete Response: {delete_resp}")

    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(f"Error Content: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_delete_flow()
