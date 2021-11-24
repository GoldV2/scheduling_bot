from google.oauth2 import service_account
import gspread
import os

path = os.path.dirname(os.path.realpath(__file__))

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = path + '/' + 'keys.json'

credentials = service_account.Credentials.from_service_account_file(
         SERVICE_ACCOUNT_FILE, scopes=SCOPES)

spreadsheetId = "17yp79LEutNZQKA6tIQ_ZQtmHavLof3bQpYyr1hX5yYE"

client = gspread.authorize(credentials)
spreadsheet = client.open_by_key(spreadsheetId)

def update_database_sheet(teachers, evaluators):
    t_sheet_name = 'Teachers'
    e_sheet_name = 'Evaluators'
    t_sheet = spreadsheet.worksheet(t_sheet_name)
    e_sheet = spreadsheet.worksheet(e_sheet_name)
    t_sheetId = t_sheet._properties['sheetId']
    e_sheetId = e_sheet._properties['sheetId']
    t_sheetRowCount = t_sheet._properties['gridProperties']['rowCount']
    e_sheetRowCount = e_sheet._properties['gridProperties']['rowCount']

    requests = {"requests": []}

    if t_sheetRowCount > 2:
        requests["requests"].append({"deleteDimension": {
        "range": {
          "sheetId": t_sheetId,
          "dimension": "ROWS",
          "startIndex": 2
        }
      }
    })
    
    if e_sheetRowCount > 2:
        requests["requests"].append({
      "deleteDimension": {
        "range": {
          "sheetId": e_sheetId,
          "dimension": "ROWS",
          "startIndex": 2,
        }
      }})

    for teacher in teachers:
        requests["requests"].append({
            "appendCells": {
                "sheetId": t_sheetId,
                "rows": [
                    {"values": [{"userEnteredValue": {"stringValue": str(teacher[0])}},
                                {"userEnteredValue": {"stringValue": teacher[1]}},
                                {"userEnteredValue": {"stringValue": teacher[2]}}]}
                ],
                "fields": "userEnteredValue"
            }
        })

    for evaluator in evaluators:
        requests["requests"].append({
            "appendCells": {
                "sheetId": e_sheetId,
                "rows": [
                    {"values": [{"userEnteredValue": {"stringValue": str(evaluator[0])}},
                                {"userEnteredValue": {"stringValue": evaluator[1]}},
                                {"userEnteredValue": {"stringValue": evaluator[2]}},
                                {"userEnteredValue": {"stringValue": evaluator[3]}},
                                {"userEnteredValue": {"stringValue": evaluator[4]}}]}
                ],
                "fields": "userEnteredValue"
            }
        })

    if requests["requests"]:
      spreadsheet.batch_update(requests)