import json

import pandas as pd
from fastapi import APIRouter, HTTPException, Request

from utils.common import load_model_from_config

router = APIRouter()


@router.get("/update-model/")
async def do_train(
    request: Request,
):
    """
    Perform inference on the given input data passed as a URL-encoded JSON string.
    The input data should be passed in the 'data' parameter, and 'topic_id' is passed as a query parameter.

    Example usage:
    curl "http://127.0.0.1:8000/update-model"
    """

    try:
        # [TODO] Put your own data in whatever topic your running is key in this regard.
        # fake BAD data for now
        input_data = pd.DataFrame(
            {
                "date": pd.date_range(
                    start="2024-09-06", periods=90, freq="D"
                ),  # 90 periods for LSTM time_steps
                "open": [2400, 2700, 3700] * 30,
                "high": [2500, 2800, 4000] * 30,
                "low": [1500, 1900, 2500] * 30,
                "close": [1200, 2300, 3300, 2200, 2100, 3200, 1100, 2100, 2000, 2500]
                * 9,
                "volume": [1000000, 2000000, 3000000] * 30,
            }
        )

        # Load the model
        model = load_model_from_config(request.app.state.active_model)

        # train the model
        model.train(input_data)

        return {"training": "Model training and saving complete!"}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.") from None
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}") from e
