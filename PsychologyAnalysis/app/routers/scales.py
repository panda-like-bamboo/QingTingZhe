# app/routers/scales.py
import logging
import json # Ensure json is imported
from fastapi import APIRouter, HTTPException, Depends

# Import Pydantic models and other necessary components
from app.schemas.scale import ScaleInfo, ScaleQuestion, ScaleOption, AvailableScalesResponse, ScaleQuestionsResponse
from src.data_handler import DataHandler
from app.core.config import settings

# Get the logger instance configured in main.py
# Ensure the logger name matches the one used in main.py's setup_logging call
logger = logging.getLogger(settings.APP_NAME)

# Create an APIRouter instance
router = APIRouter()

# --- Dependency Injection ---
# def get_data_handler():
#     """Dependency function to get a DataHandler instance."""
#     try:
#         # Use the database path from the application settings
#         return DataHandler(db_path=settings.DB_PATH)
#     except Exception as e:
#         # Log the error and raise an HTTP exception if DataHandler fails to initialize
#         logger.error(f"Failed to initialize DataHandler: {e}", exc_info=True)
#         raise HTTPException(status_code=500, detail="Database handler initialization failed.")
def get_data_handler():
    try:
        # <<< FIX: 使用 DB_PATH_SQLITE >>>
        return DataHandler(db_path=settings.DB_PATH_SQLITE)
    except Exception as e:
        logger.error(f"Failed to initialize DataHandler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"数据库处理程序初始化失败: {e}")

# --- API Endpoints ---

@router.get(
    "/scales",
    response_model=AvailableScalesResponse, # Use keyword argument for response_model
    tags=["Scales"]                          # Use keyword argument for tags
)
async def get_available_scales(dh: DataHandler = Depends(get_data_handler)):
    """
    Retrieves a list of all available scale types (code and name).
    """
    logger.info("Request received for available scales.")
    try:
        # Fetch scale types from the data handler
        scales = dh.get_all_scale_types() # This should return List[Dict] e.g. [{'code': 'SAS', 'name': '...'}, ...]

        # Convert the list of dictionaries to a list of Pydantic models
        scale_infos = [ScaleInfo(code=s["code"], name=s["name"]) for s in scales]

        # Return the response using the Pydantic response model
        return AvailableScalesResponse(scales=scale_infos)
    except Exception as e:
        # Log any unexpected errors during the process
        logger.error(f"Error fetching available scales: {e}", exc_info=True)
        # Raise a generic 500 error to the client
        raise HTTPException(status_code=500, detail="Failed to fetch scale types from database.")


@router.get(
    "/scales/{scale_code}/questions",
    response_model=ScaleQuestionsResponse, # Use keyword argument
    tags=["Scales"]                          # Use keyword argument
)
async def get_scale_questions(scale_code: str, dh: DataHandler = Depends(get_data_handler)):
    """
    Retrieves all questions for a specific scale based on its code.
    """
    logger.info(f"Request received for questions of scale: {scale_code}")
    try:
        # Load question data using the data handler
        # This method should return List[Dict] or None
        questions_data = dh.load_questions_by_type(scale_code)

        # Handle case where no questions are found for the given scale code
        if questions_data is None:
            logger.warning(f"No questions found for scale code: {scale_code}")
            raise HTTPException(status_code=404, detail=f"Scale with code '{scale_code}' not found or has no questions.")

        questions_list = []
        # Iterate through the raw question data from the database
        for q_data in questions_data:
            # --- Data Validation and Transformation ---
            # Ensure the basic structure of question data is present
            if not all(k in q_data for k in ('number', 'text', 'options')):
                logger.warning(f"Skipping question data due to missing keys: {q_data}")
                continue # Skip this malformed question data

            options_list = []
            options_data_from_db = q_data.get('options', [])

            # Ensure options data is a list before processing
            if not isinstance(options_data_from_db, list):
                logger.warning(f"Options data for Q{q_data['number']} is not a list, skipping options. Data: {options_data_from_db}")
            else:
                # Iterate through options for the current question
                for opt in options_data_from_db:
                    # Ensure option structure is correct
                    if not isinstance(opt, dict) or not all(k in opt for k in ('text', 'score')):
                        logger.warning(f"Skipping invalid option data for Q{q_data['number']}: {opt}")
                        continue # Skip malformed option data

                    text_val = opt['text']
                    score_val_raw = opt['score']
                    score_val_numeric = None

                    # Explicitly convert score to a numeric type (int or float)
                    try:
                        if isinstance(score_val_raw, (int, float)):
                            score_val_numeric = score_val_raw
                        elif isinstance(score_val_raw, str):
                            # Attempt conversion from string
                            try:
                                score_float = float(score_val_raw)
                                score_val_numeric = int(score_float) if score_float.is_integer() else score_float
                            except ValueError:
                                logger.error(f"Could not convert score string '{score_val_raw}' to number for Q{q_data['number']}, option '{text_val}'. Skipping option.")
                                continue # Skip this option if conversion fails
                        else:
                            # Handle unexpected score types
                            logger.warning(f"Unexpected type for score ({type(score_val_raw)}) for Q{q_data['number']}, option '{text_val}'. Using 0 as fallback.")
                            score_val_numeric = 0

                    except Exception as conv_err:
                         logger.error(f"Error converting score '{score_val_raw}' for Q{q_data['number']}, option '{text_val}': {conv_err}", exc_info=True)
                         continue # Skip option on unexpected conversion error

                    # Only create ScaleOption if score conversion was successful
                    if score_val_numeric is not None:
                        try:
                            # Create Pydantic model instance for the option
                            options_list.append(ScaleOption(text=str(text_val), score=score_val_numeric))
                        except Exception as pydantic_option_err:
                            # Catch potential errors during Pydantic model instantiation
                            logger.error(f"Pydantic error creating ScaleOption for Q{q_data['number']}, option '{text_val}': {pydantic_option_err}", exc_info=True)
                            continue # Skip option if it fails validation

            # Create Pydantic model instance for the question
            try:
                questions_list.append(ScaleQuestion(
                    number=int(q_data['number']), # Ensure number is integer
                    text=str(q_data['text']),    # Ensure text is string
                    options=options_list
                ))
            except Exception as pydantic_q_err:
                # Catch potential errors during Pydantic model instantiation
                logger.error(f"Pydantic error creating ScaleQuestion for Q{q_data.get('number', 'N/A')}: {pydantic_q_err}", exc_info=True)
                continue # Skip this question if it fails validation

        # Log successful processing and return the validated response
        logger.info(f"Successfully processed {len(questions_list)} questions for scale {scale_code}.")
        return ScaleQuestionsResponse(questions=questions_list)

    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions (like 404)
        raise http_exc
    except Exception as e:
        # Log unexpected errors and return a generic 500 response
        logger.error(f"Unexpected error fetching/processing questions for scale {scale_code}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch questions for scale {scale_code}.")