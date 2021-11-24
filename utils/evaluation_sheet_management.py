from datetime import datetime, timedelta
from google.oauth2 import service_account
import gspread
import os

path = os.path.dirname(os.path.realpath(__file__))

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = path + '/' + 'keys.json'

credentials = service_account.Credentials.from_service_account_file(
         SERVICE_ACCOUNT_FILE, scopes=SCOPES)

spreadsheetId = "1tgxIUaQHZHo26eA22klbtemsSReQugu3YBVToR3J2bQ"

client = gspread.authorize(credentials)
spreadsheet = client.open_by_key(spreadsheetId)

def append_confirmed_evaluation(values):
    sheetName = "Confirmed Evaluations"
    sheet = spreadsheet.worksheet(sheetName)
    sheetId = sheet._properties['sheetId']

    requests = {"requests": [
        {
            "appendCells": {
                "sheetId": sheetId,
                "rows": [
                    {"values": [{"userEnteredValue": {"stringValue": values[0]}},
                                {"userEnteredValue": {"stringValue": values[1]}},
                                {"userEnteredValue": {"stringValue": values[2]}},
                                {"userEnteredValue": {"stringValue": values[3]}},
                                {"userEnteredValue": {"stringValue": values[4]}},
                                {"userEnteredValue": {"boolValue": False}},
                                {"userEnteredValue": {"boolValue": False}}]}
                ],
                "fields": "userEnteredValue"
            }
        }
    ]}

        # meaning there is only the header
    sheet_values = sheet.get_all_values()
    if len(sheet_values) == 1:
        # formatting the completed part
        requests["requests"].append({
            "repeatCell": {
                "cell": {"dataValidation": {"condition": {"type": "BOOLEAN"}}, "userEnteredFormat": {"textFormat": {"foregroundColor": {"red": 1,"green": 0,"blue": 0,"alpha": 1}}}},
                "range": {"sheetId": sheetId, "startRowIndex": 1, "endRowIndex": 100, "startColumnIndex": 5, "endColumnIndex": 6},
                "fields": "dataValidation"
                }})

        # formatting the canceled part
        requests["requests"].append({
            "repeatCell": {
                "cell": {"dataValidation": {"condition": {"type": "BOOLEAN"}}, "userEnteredFormat": {"textFormat": {"foregroundColor": {"red": 1,"green": 0,"blue": 0,"alpha": 1}}}},
                "range": {"sheetId": sheetId, "startRowIndex": 1, "endRowIndex": 100, "startColumnIndex": 6, "endColumnIndex": 7},
                "fields": "dataValidation"
                }})

    spreadsheet.batch_update(requests)

def find_completed_evaluations():
    sheetName = "Confirmed Evaluations"
    sheet = spreadsheet.worksheet(sheetName)
    sheetId = sheet._properties['sheetId']

    requests = {"requests": []}
    
    completed_evaluations = []
    values = sheet.get_all_values()
    l = len(values)-1
    # looping backwards because if I loop forward and delete a row, I can't delete any subsequent rows
    for index, row in enumerate(values[::-1]):
        # inverting the indexes
        index = l-index
        if row[5] == 'TRUE':
            completed_evaluations.append(row)
            
            requests["requests"].append({
                    "deleteDimension": {
                      "range": {
                        "sheetId": sheetId,
                        "dimension": "ROWS",
                        "startIndex": index,
                        "endIndex": index+1
                      }
                    }
                  })

    # not deleting now because if there is an error, all the entries are deleted, I want to make sure they are transffered before being deleted
    # if requests["requests"]:
    #     spreadsheet.batch_update(requests)

    return completed_evaluations, requests

def update_completed_evaluations(completed_evaluations, to_delete):
    sheetName = "Completed Evaluations"
    sheet = spreadsheet.worksheet(sheetName)
    sheetId = sheet._properties['sheetId']

    requests = {"requests": []}

    for evaluation in completed_evaluations:
        requests["requests"].append({
            "appendCells": {
                "sheetId": sheetId,
                "rows": [
                    {"values": [{"userEnteredValue": {"stringValue": evaluation[0]}},
                                {"userEnteredValue": {"stringValue": evaluation[1]}},
                                {"userEnteredValue": {"stringValue": evaluation[2]}},
                                {"userEnteredValue": {"stringValue": evaluation[3]}},
                                {"userEnteredValue": {"stringValue": evaluation[4]}},
                                {"userEnteredValue": {"stringValue": datetime.now().strftime('%m/%d/%Y %H:%M:%S')}}]} # datetime not imported in this file, but it is in evaluation_bot.py, where this function is used
                ],
                "fields": "userEnteredValue"
            }
        })

    requests["requests"] += to_delete["requests"]

    spreadsheet.batch_update(requests)


# this function is very similar to find_completed_evaluations(), could make it into one func
def find_canceled_evaluations():
    sheetName = "Confirmed Evaluations"
    sheet = spreadsheet.worksheet(sheetName)
    sheetId = sheet._properties['sheetId']

    requests = {"requests": []}
    
    canceled_evaluations = []
    values = sheet.get_all_values()
    l = len(values)-1
    # looping backwards because if I loop forward and delete a row, I can't delete any subsequent rows
    # using values[1:] to not include the header
    for index, row in enumerate(values[1:][::-1]):
        # inverting the indexes
        index = l-index

        #############################################################

        # determining the auto cancelation time of the evaluation
        # could make into its own function
        eval_date_time = row[2].split(' ')
        eval_date = eval_date_time[0].split('/')
        eval_time = eval_date_time[1].split(':')
        evaluation_time = datetime(month=int(eval_date[0]),
                                   day=int(eval_date[1]),
                                   year=int(eval_date[2]),
                                   hour=int(eval_time[0]),
                                   minute=int(eval_time[1]),
                                   second=int(eval_time[2]))

        eval_cancel_time = evaluation_time + timedelta(days=1)
        eval_cancel_time = datetime(month=eval_cancel_time.month,
                                    day=eval_cancel_time.day,
                                    year=eval_cancel_time.year,
                                    hour=11,
                                    minute=59,
                                    second=59)

        #############################################################

        # checking if it was manually cancelled or if its auto cancelation time was reached
        # could do this in two if-statements instead of 3 nested
        if row[6] == 'TRUE' or datetime.now() > eval_cancel_time:
            if row[6] == 'TRUE':
                canceled_evaluations.append(row + ['Canceled manually by evaluator'])

            else:
                # an evaluator may forget to mark it as complete
                # a manager should be able to manually add this evaluation to sheet Completed Evaluations
                    # evaluation completion time will not be available accurately
                canceled_evaluations.append(row + ['Not completed before cancelation time'])

            requests["requests"].append({
                    "deleteDimension": {
                      "range": {
                        "sheetId": sheetId,
                        "dimension": "ROWS",
                        "startIndex": index,
                        "endIndex": index+1
                      }
                    }
                  })

    # if requests["requests"]:
    #     spreadsheet.batch_update(requests)

    return canceled_evaluations, requests

# very similar to update_completed_evaluations, could possibly make both into one function
def update_canceled_evaluations(canceled_evaluations, to_delete):
    sheetName = "Canceled Evaluations"
    sheet = spreadsheet.worksheet(sheetName)
    sheetId = sheet._properties['sheetId']

    requests = {"requests": []}

    for evaluation in canceled_evaluations:
        requests["requests"].append({
            "appendCells": {
                "sheetId": sheetId,
                "rows": [
                    {"values": [{"userEnteredValue": {"stringValue": evaluation[0]}},
                                {"userEnteredValue": {"stringValue": evaluation[1]}},
                                {"userEnteredValue": {"stringValue": evaluation[2]}},
                                {"userEnteredValue": {"stringValue": evaluation[3]}},
                                {"userEnteredValue": {"stringValue": evaluation[4]}},
                                {"userEnteredValue": {"stringValue": datetime.now().strftime('%m/%d/%Y %H:%M:%S')}}, # datetime not imported in this file, but it is in evaluation_bot.py, where this function is used
                                {"userEnteredValue": {"stringValue": evaluation[7]}}]} # reason for cancelation
                ],
                "fields": "userEnteredValue"
            }
        })

    requests["requests"] += to_delete["requests"]
    
    spreadsheet.batch_update(requests)

# used within requests to apply validation to rows
    # {
    #     "repeatCell": {
    #         "cell": {"dataValidation": {"condition": {"type": "BOOLEAN"}}},
    #         "range": {"sheetId": sheetId, "startRowIndex": 1, "endRowIndex": 100, "startColumnIndex": 5, "endColumnIndex": 6},
    #         "fields": "dataValidation"
    #     }
    # },