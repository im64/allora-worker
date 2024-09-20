import json
import urllib.parse
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Request

from utils.common import load_model_from_config

router = APIRouter()


@router.get("/getinference/")
async def get_inference(
    request: Request,
    payload: str = Query(
        ..., description="Input data and topic ID as a URL-encoded JSON string"
    ),
):
    """
    Perform inference on the given input data passed as a URL-encoded JSON string.
    The payload should be passed as a single parameter, containing 'topic_id' and 'data'.

    Example usage:
    curl "http://127.0.0.1:8000/getinference/?payload=%7B%22topic_id%22%3A%201%2C%20%22data%22%3A%20%7B%22date%22%3A%20%5B%222024-09-06%22%2C%20%222024-09-07%22%5D%2C%20%22open%22%3A%20%5B2400%2C%202700%5D%2C%20%22high%22%3A%20%5B2500%2C%202800%5D%2C%20%22low%22%3A%20%5B1500%2C%201900%5D%2C%20%22close%22%3A%20%5B1200%2C%202300%5D%2C%20%22volume%22%3A%20%5B1000000%2C%202000000%5D%7D%7D"
    """
    try:
        # Parse the URL-encoded JSON payload
        decoded_payload = urllib.parse.unquote(payload)
        parsed_payload = json.loads(decoded_payload)

        # Ensure 'topic_id' and 'data' are present in the payload
        topic_id = parsed_payload.get("topic_id")
        input_data = parsed_payload.get("data")

        if not topic_id:
            raise HTTPException(
                status_code=400, detail="Topic ID is required in the payload."
            )
        if not input_data:
            raise HTTPException(
                status_code=400, detail="Input data is required in the payload."
            )

        # Convert input_data into a DataFrame
        input_data = pd.DataFrame(input_data)

        # Load the model
        model = load_model_from_config(request.app.state.active_model)
        model.load()

        # Perform inference
        predictions = model.inference(input_data)
        return {"predictions": predictions.to_dict(orient="records")}

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400, detail="Invalid JSON payload for Get Inference."
        ) from None
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Get Inference error: {str(e)}"
        ) from e
