#!/usr/bin/env python3
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "rest.api:app",
        host="0.0.0.0",
        port=8800,
        reload=False
    )
