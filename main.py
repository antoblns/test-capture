import asyncio
import random
from websockets import exceptions
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import FileResponse
import cv2
import os
import datetime
import json

app = FastAPI()
#
# We can consider using context object which is passed to every task instead of all these vars.
#
ConnectedList = set[WebSocket]

connected: ConnectedList = set()


def get_ws_clients():
    return connected
# tasks = set()


#
# Sync webcam shooting a new picture and sending it to clients. Replacement for an event bus.
#
number_event = asyncio.Event()

#
# Internal Data source
#


class Store():
    value = 1
    status = 'ok'
    filename = './capture.jpg'


store = Store()


def get_store() -> Store:
    return store


#
# Create a VideoCapture object to capture video from the default camera
#
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise RuntimeError("Could not open camera")


async def broadcast_status(store: Store, connected_clients: ConnectedList, sync_event: asyncio.Event):
    """
    Task for broadcasting messages over ws.

    In case of generator:
    
    capture_gen = generate_capture()
    for (status,) in capture_gen:
        message = ...
    """
    while True:
        await sync_event.wait()
        message = json.dumps({
            "status": store.status
        })
        if len(connected_clients) > 0:
            # websockets.broadcast(connected, message)
            [await ws.send_text(message) for ws in connected_clients]
        sync_event.clear()

# We can have manager object instead


async def register(websocket):
    await websocket.accept()
    connected.add(websocket)


async def unregister(websocket):
    connected.remove(websocket)


async def server(websocket, path):
    connected.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected.remove(websocket)

# async def main():
#     asyncio.create_task(generate_number())
#     # start_server = websockets.serve(server, "localhost", 8765)
#     asyncio.create_task(broadcast_number())
#     # await asyncio.gather(start_server, broadcast_task)
#     async with websockets.serve(server, "localhost", 8001):
#         await asyncio.Future()  # run forever


def put_text(frame):
    # Get the current date and time as a string
    now = datetime.datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

    # Write the date and time onto the image
    font = cv2.FONT_HERSHEY_SIMPLEX
    bottomLeftCornerOfText = (10, 30)
    fontScale = 1
    fontColor = (255, 255, 255)
    lineType = 2
    cv2.putText(frame, dt_string, bottomLeftCornerOfText,
                font, fontScale, fontColor, lineType)
    return frame


async def generate_capture(store: Store, cap: cv2.VideoCapture, sync_event: asyncio.Event):
    """
    This can be a generator too.
    """
    
    class CaptureException(BaseException):
        pass

    while True:
        await asyncio.sleep(1)
        # Capture a single frame from the camera
        ret, frame = cap.read()
        if not ret:
            store.status="not ok"
            ### yield (False, CaptureException)
            raise CaptureException
        cv2.imwrite(store.filename, put_text(frame))
        ### yield (True,)
        sync_event.set()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Ideally dependencies come from Depends but we don't need it here
    """
    await register(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await unregister(websocket)


@app.on_event("startup")
async def startup_event():
    t1 = asyncio.create_task(generate_capture(store, cap, number_event))
    t2 = asyncio.create_task(broadcast_status(store, connected, number_event))


@app.get("/image")
async def capture_image():
    # Return the captured image as a file response
    if os.path.exists(store.filename):
        return FileResponse(store.filename)
    else:
        raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8765)
