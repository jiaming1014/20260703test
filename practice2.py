from fastapi import FastAPI
import uvicorn
from source import get_camera_position, CameraPosition

app = FastAPI()


@app.get("/")
def read_root(bureau:str | None = None):
    data:list[CameraPosition] = get_camera_position()
    if not bureau :        
        return data
    
    bureau_datas:list[CameraPosition] = []
    for camera in data:        
        if camera.bureau == bureau:
            bureau_datas.append(camera)
        
    return bureau_datas



#@app.get("/items/{item_id}")
#def read_item(item_id: int, q: str | None = None):
#    return {"item_id": item_id, "q": q}

if __name__ == "__main__":
    uvicorn.run("practice2:app",reload=True)