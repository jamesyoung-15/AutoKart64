import time
from collections import deque

import cv2
import numpy as np

from screen_capture.wayland_screen_capture import WaylandScreenCapture


def process_image(image: np.ndarray) -> np.ndarray:
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # Edge detection
    edges = cv2.Canny(blurred, 50, 150)
    return edges


def main():
    capture = WaylandScreenCapture()

    try:
        # Start capture (this will show the portal dialog)
        capture.start_capture()
        last_time = time.time()
        frame_times = deque(maxlen=30)

        print("Screen capture active. Press 'q' to quit.")

        while True:
            # Read frame
            frame = capture.read_frame()

            if frame is not None:
                # Process with OpenCV
                # Example: Add frame counter and FPS info
                elapsed_time = time.time() - last_time
                frame_times.append(elapsed_time)
                last_time = time.time()
                if len(frame_times) > 1:
                    fps = len(frame_times) / sum(frame_times)
                else:
                    fps = 0.0

                # cv2.putText(frame, f'Frame: {frame_count}', (10, 30),
                # cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                processed_frame = process_image(frame)
                frame = cv2.cvtColor(processed_frame, cv2.COLOR_GRAY2BGR)
                # Example: Convert to grayscale (optional)
                # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                cv2.putText(
                    frame,
                    f"FPS: {fps:.2f}",
                    (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )
                print(f"FPS: {fps:.2f}")

                # Display
                cv2.namedWindow("Screen Capture", cv2.WINDOW_NORMAL)
                cv2.resizeWindow("Screen Capture", 640, 480)
                frame_resize = cv2.resize(frame, (640, 480))
                cv2.imshow("Screen Capture", frame_resize)
                # cv2.imshow("Processed Frame", frame)

                # Optional: Save frames
                # cv2.imwrite(f'frame_{frame_count:06d}.png', frame)

            # Check for quit
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        capture.stop()
        cv2.destroyAllWindows()
        print("Capture stopped")


if __name__ == "__main__":
    main()
