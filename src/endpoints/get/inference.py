import json

import pandas as pd
import yfinance as yf
from fastapi import APIRouter, HTTPException, Request

# pylint: disable=import-error
from utils.common import load_model_from_config

router = APIRouter()


@router.get("/inference")
async def get_inference(
    request: Request,
):
    # pylint: disable=line-too-long
    """
    This is a dumb endpoint that returns the last prediction value from the model.

    """
    try:

        # get latest price of ETH for thelast couple days from yahoo finance
        eth_ticker = "ETH-USD"

        # Fetch historical data for Ethereum for the last 5 days
        eth_data = yf.Ticker(eth_ticker)
        eth_hist = eth_data.history(period="5d")  # Retrieve the last 5 days of data

        # Extract the necessary columns: date, open, high, low, close, volume
        eth_hist.reset_index(inplace=True)  # Convert the date index to a column
        eth_hist["date"] = pd.to_datetime(
            eth_hist["Date"]
        )  # Ensure it's in datetime format
        eth_hist["open"] = eth_hist["Open"]
        eth_hist["high"] = eth_hist["High"]
        eth_hist["low"] = eth_hist["Low"]
        eth_hist["close"] = eth_hist["Close"]
        eth_hist["volume"] = eth_hist["Volume"]

        # Select the columns in the correct order for the model input
        input_data = eth_hist[["date", "open", "high", "low", "close", "volume"]].copy()
        input_data.loc[:, "date"] = pd.to_datetime(input_data["date"])
        # Drop any rows with NaN values (if needed)
        input_data.dropna(inplace=True)

        # Load the model
        model = load_model_from_config(request.app.state.active_model)
        model.load()

        # Perform inference
        predictions = model.inference(input_data)

        # return proper/full response from model.inference
        # return {"predictions": predictions.to_dict(orient="records")}

        # Get the last prediction value
        last_prediction = predictions.iloc[-1]

        # Assuming the prediction is under the "prediction" key
        return float(last_prediction["prediction"])

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400, detail="Invalid JSON payload for GetInference."
        ) from None
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"GetInference error: {str(e)}"
        ) from e
