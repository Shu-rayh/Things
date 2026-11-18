import time
import cv2
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

def track_frame(frame):
    """Return a list of tracked objects for one frame."""
    result = model.track(frame, persist=True, conf=0.4, verbose=False)[0]
    objects = []
    if result.boxes.id is None:  # nothing tracked this frame
        return objects
    for box, tid, cls, conf in zip(
        result.boxes.xyxy.tolist(),
        result.boxes.id.int().tolist(),
        result.boxes.cls.int().tolist(),
        result.boxes.conf.tolist(),
    ):
        objects.append({
            "id": tid,
            "label": model.names[cls],
            "conf": conf,
            "box": tuple(map(int, box)),
        })
    return objects

def draw(frame, objects):
    for o in objects:
        x1, y1, x2, y2 = o["box"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f'{o["label"]} #{o["id"]}', (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

def main():
    cap = cv2.VideoCapture(0)  # try 1 if the wrong camera opens
    prev = time.time()
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        objects = track_frame(frame)
        draw(frame, objects)

        now = time.time()
        fps = 1 / max(now - prev, 1e-6)
        prev = now
        cv2.putText(frame, f"FPS {fps:.0f} | Objects {len(objects)}",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Identity Tracker", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()