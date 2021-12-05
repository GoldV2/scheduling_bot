from discord.ext import commands
from google.oauth2 import service_account
import gspread
import os

class DBSheet(commands.Cog):

  path = os.path.dirname(os.path.realpath(__file__))

  SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
  SERVICE_ACCOUNT_FILE = path + '/' + 'keys.json'

  credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
  spreadsheetId = "17yp79LEutNZQKA6tIQ_ZQtmHavLof3bQpYyr1hX5yYE"

  client = gspread.authorize(credentials)
  spreadsheet = client.open_by_key(spreadsheetId)

  def __init__(self, bot):
    self.bot = bot

  @staticmethod
  def update_database_sheet(members, evaluators):
      m_sheet_name = 'Members'
      e_sheet_name = 'Evaluators'
      m_sheet = DBSheet.spreadsheet.worksheet(m_sheet_name)
      e_sheet = DBSheet.spreadsheet.worksheet(e_sheet_name)
      m_sheetId = m_sheet._properties['sheetId']
      e_sheetId = e_sheet._properties['sheetId']
      m_sheetRowCount = m_sheet._properties['gridProperties']['rowCount']
      e_sheetRowCount = e_sheet._properties['gridProperties']['rowCount']

      requests = {"requests": []}

      if m_sheetRowCount > 2:
          requests["requests"].append({"deleteDimension": {
          "range": {
            "sheetId": m_sheetId,
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

      for member in members:
          requests["requests"].append({
              "appendCells": {
                  "sheetId": m_sheetId,
                  "rows": [
                      {"values": [{"userEnteredValue": {"stringValue": str(member[0])}},
                                  {"userEnteredValue": {"stringValue": member[1]}},
                                  {"userEnteredValue": {"stringValue": member[2]}},
                                  {"userEnteredValue": {"stringValue": str(member[3])}}]}
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
                                  {"userEnteredValue": {"stringValue": evaluator[2]}}]}
                  ],
                  "fields": "userEnteredValue"
              }
          })

      if requests["requests"]:
        DBSheet.spreadsheet.batch_update(requests)

def setup(bot):
  bot.add_cog(DBSheet(bot))

