### Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")


def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }


def validate_data(age, investment_amount, intent_request):
    """
    Validates the data provided by the user.
    """

    # Validate the retirement age based on the user's current age.
    # Validate the age, it should be > 0 and <= 65
    if age is not None:
        age = parse_int(age)  # Since parameters are strings it's important to cast values
        if (age < 0) or (age >= 65):
            return build_validation_result(
                False,
                "age",
                "The age you provided is either below 0 or above 65, which is above our retirment target."
                "Please provide a new age, thank you.",
            )

    # Validate the investment amount, it should be >= 5000
    if investment_amount is not None:
        investment_amount = parse_int(investment_amount)
        if investment_amount < 5000:
            return build_validation_result(
                False,
                "investmentAmount",
                "The minimum investment amount is $5,000, "
                "could you please provide a greater amount?",
            )

    return build_validation_result(True, None, None)


### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response


### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """

    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]
    source = intent_request["invocationSource"]

    if source == "DialogCodeHook":
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt
        # for the first violation detected.
        slots = get_slots(intent_request)

        validation_result = validate_data(age, investment_amount, intent_request)
        if not validation_result["isValid"]:
            slots[validation_result["violatedSlot"]] = None  # Cleans invalid slot

            # Returns an elicitSlot dialog to request new data for the invalid slot
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )

        # Fetch current session attributes
        output_session_attributes = intent_request["sessionAttributes"]

        return delegate(output_session_attributes, get_slots(intent_request))

    # Figure Out Next Steps and the clients risk profile
    age = parse_int(age)
    investment_amount = parse_int(investment_amount)
        
    if (age <=20) or (investment_amount >= 5000000):
        context = "Given your age and investment amount we recomend a, "
        goal = 'high risk:, 20% bonds (AGG), 80% equities (SPY) strategy.'
    elif age >= 60:
        context = "Given your age profile we recomend a, "
        goal = 'no risk, 100% bonds (AGG), 0% equities (SPY) strategy.'
    elif risk_level.lower() == 'low':
        context = "Given your risk profile we recommend a, "
        goal = 'low risk, 60% bonds (AGG), 40% equities (SPY) strategy.'
    elif risk_level.lower() == 'medium':
        context = "Given your risk profile we recommend a, "
        goal = 'medium risk, 40% bonds (AGG), 60% equities (SPY) strategy.'
    elif risk_level.lower() == 'high':
        context = "Given your risk profile we recommend a, "
        goal = 'high risk, 20% bonds (AGG), 80% equities (SPY) strategy.'

    # Return a message with the initial recommendation based on the risk level.
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": """Thank you {} for your information.
            {}
            {}""".format(
                first_name, context, goal
            ),
        },
    )


### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to bot's intent handlers
    if intent_name == "recommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    return dispatch(event)