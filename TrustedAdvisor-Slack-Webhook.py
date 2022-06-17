import boto3
import json
#import requests
import urllib.parse
import urllib.request

def lambda_handler(event, context):
   
   print(json.dumps(event))
   slack_webhook_url = event["SlackWebhookURL"]
   client = boto3.client('support', region_name='us-east-1')
   response = client.describe_trusted_advisor_checks(language='en') 
   #print("Check Summaries....\n\n\n")

   ##Number of elements returned
   num_checks = len(response["checks"])

   ##Create List of TA CheckIds
   checks = []
   ta_checks_dict = {}
   for x in range(num_checks):
      checks.append(response["checks"][x]["id"])
      
      ##Store TA Checks in nested dict for cross referencing via TA check Id
      ta_checks_dict[response["checks"][x]["id"]] = {"name":response["checks"][x]["name"],"category":response["checks"][x]["category"]}

   ##Get TA Check Summaries
   result = client.describe_trusted_advisor_check_summaries(checkIds=checks)

   count_ok = 0
   count_critical = 0
   count_warn = 0
   message = ""
   summary = ""

   for x in range(num_checks):
      check_status = result['summaries'][x]['status']
      check_id = result['summaries'][x]['checkId']
      #print(check_status)

      ## Can't use match/case. Use If/else as Python 3.10 runtime not supported in Lambda. 
      
      if(check_status == 'ok'):
        count_ok += 1
      elif(check_status == 'warning'):
        count_warn += 1
      elif(check_status == 'error'):
        count_critical += 1
        message += "HIGH RISK  - " + "[" + str(ta_checks_dict[check_id]['category'])+ "] " + str(ta_checks_dict[check_id]['name']) + "\n"
      else:
       #print("Check Status Undefined : ", str(check_status))
       continue

   #print("\n========= Summary of Trusted Advisor Findings =======\n")
   summary += "\n========= Summary of Trusted Advisor Findings =======\n\n"

   #print("GREEN - OK = ", count_ok)
   summary += "GREEN - OK = " + str(count_ok)  + "\n"

   #print("YELLOW (Investigate) = ", count_warn)
   summary += "YELLOW (Investigate) = " + str(count_warn)  + "\n"

   #print("RED (High Risk) = ", count_critical)
   summary += "RED (High Risk) = " + str(count_critical)  + "\n\n"

   #print("\n\n========== SLACK OUTPUT ===========")
   #print(summary)
   #print(message)

   print("============= Post to Slack ===========")

   headers = {
      'Content-type': 'application/json'
   }

   data = "{content:" + '"' + summary + message + '"}'

   ## NOT USING Python "requests" library to avoid creating Lambda Layer in CloudFormation. Preserve CF portability
   #response = requests.post(slack_webhook_url, headers=headers, data=data)

   ## USING Python "urllib" instead

   data = data.encode('ascii')
   #print("DATA_4: ", data)

   headers = {}
   headers['Content-Type'] = "application/json"

   ## Send the request
   print("URL = ", slack_webhook_url)
   req = urllib.request.Request(slack_webhook_url, data=data, headers=headers)
   resp = urllib.request.urlopen(req)
   
   return {
     'statusCode': 200
   }

 
